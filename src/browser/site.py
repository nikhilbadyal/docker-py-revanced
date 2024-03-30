"""Methods for fetching the site and source."""

import asyncio
import atexit
import base64
import json
import time
from typing import Any, Self

import websockets
from bs4 import BeautifulSoup
from cdp_socket.exceptions import CDPError
from loguru import logger
from requests.structures import CaseInsensitiveDict
from selenium_driverless import webdriver
from selenium_driverless.types.by import By

from src.browser.browser import Browser
from src.browser.cookies import Cookies
from src.browser.exceptions import JSONExtractError, PageLoadError


class Source:
    """The `Response` like object from the browser request.

    Major purpose is to denote the page's html content
    hence, `text` attribute will contain the source html content.
    """

    def __init__(
        self: Self,
        source: str,
        status_code: str | int | None = None,
        headers: dict[str, str] | CaseInsensitiveDict | None = None,
        user_agent: str | None = None,
    ) -> None:
        self.__default__()
        self._text = source
        if isinstance(status_code, int):
            self.status_code = status_code
        elif isinstance(status_code, str):
            try:  # noqa: SIM105
                self.status_code = int(status_code)
            except:  # noqa: E722, S110
                pass
        if isinstance(headers, dict | CaseInsensitiveDict):
            self.headers.update(headers)
        self.user_agent = user_agent

    def __default__(self: Self) -> None:
        """Set attributes to default values."""
        self.status_code = None
        self.headers = CaseInsensitiveDict()
        self.user_agent = None

    @property
    def text(self: Self) -> str:
        """Returns the html content of the page."""
        return self._text

    def json(self: Self, **kwargs) -> Any:  # noqa: ANN003
        r"""Returns the json-encoded content of a response, if any.

        :param \*\*kwargs: Optional arguments that ``json.loads`` takes.
        :raises JSONDecodeError: If the response body does not
            contain valid json.
        :raises JSONExtractError: If the json extraction impl
            fails or no such json.

        The idea is basically that if the content view shows raw json,
        then it's possible to extract it. As done using `requests` package,
        i.e. if this fails with `JSONExtractError` then most likely `requests`
        would also fail for the same.
        """
        soup = BeautifulSoup(self.text, "html.parser")
        data = soup.select_one("body > pre")
        if not data:
            msg = "the json extractor implementation failed"
            raise JSONExtractError(msg)
        return json.loads(data.text, **kwargs)


class Site:
    """Convenient default class to load any site."""

    def __init__(self: Self, browser: Browser) -> None:
        self._browser = browser
        self.driver = browser.driver
        self.status_code = None
        self.response_found = False
        self.redirected_url = None
        self.cf_encountered = False
        self.cf_encountered_on_url = None
        self.user_agent = None

    async def get(self: Self, url: str, timeout: float) -> Source:
        """Loads the url.

        Waits for the page to load until timeout is hit.
        Raises `PageLoadError` on load failure.
        """
        self.url = url
        self.timeout = timeout
        logger.info(f"Non-exclusive impl to fetch page for url -> {self.url} : Fetching with default config...")
        try:
            self.start = time.perf_counter()
            self.global_conn = self.driver.base_target
            await self.add_network_listeners()
            await self.driver.get(self.url, timeout=self.timeout, wait_load=False)
            if not await self.check_if_loaded():
                msg = f"page load check mechanism failed out... for: {url}"
                raise PageLoadError(msg)

            await self.driver.refresh()
            await self.driver.sleep(3)
            source = await self.driver.page_source

            """
            # if await find_and_click(driver=self.driver, check=True):
            #     logger.debug("[Cloudflare] found and clicked another checkbox")
            #     await self.driver.sleep(5)
            #     source = await self.driver.page_source
            """

            soup = BeautifulSoup(source, "html.parser")
            title = soup.select_one("title")
            if title and title.text.lower().startswith("just a moment"):
                msg = "cloudflare protection (captcha verification required)"
                raise PageLoadError(msg)

            return Source(
                source,
                status_code=self.status_code,
                headers=self.response_headers,
                user_agent=self.user_agent,
            )
        except Exception as e:  # noqa: BLE001
            msg = f"unknown error while loading --> {e!r}"
            raise PageLoadError(msg) from e

    async def check_if_loaded(self: Self) -> bool:
        """Checks if the page was loaded.

        Better to Implement it explicitly for any site based on element visibility or any other mechanism. Used with
        Browsers's Network Monitor (CDP).
        """
        try:
            while not self.response_found and self.timeout > time.perf_counter() - self.start:
                await asyncio.sleep(1)
            await self.remove_network_listeners()
            if self.response_found:
                logger.success(f"Response found set from interceptor [loaded]: {self.status_code}")
            else:
                logger.error(f"Response failed with possible status code: {self.status_code}")
                return False
        except Exception as e:  # noqa: BLE001
            logger.error(f"{e!r}")
            return False
        else:
            return self.response_found is not None

    async def on_request(self: Self, params: dict[str, Any]) -> None:  # noqa: C901
        """Intercepts requests using CDP for the page."""
        _params = {"requestId": params["requestId"]}
        url = params["request"]["url"]
        status_code = params.get("responseStatusCode")
        self.user_agent = params["request"]["headers"]["User-Agent"]
        if url == (self.cf_encountered_on_url or self.redirected_url or self.url):
            self.status_code = status_code
            self.response_headers = _generate_headers(params.get("responseHeaders", []))
        logger.info(f"Status code: {status_code} -> Site: {url}")
        if url == self.url and self.cf_encountered and not str(status_code).startswith("2"):
            self.cf_encountered = False
            logger.debug("CF re-encounter; Box appeared again")
        if params.get("responseStatusCode") in [301, 302, 303, 307, 308]:
            # redirected request
            if url == (self.redirected_url or self.url):
                lheader = next(
                    filter(lambda obj: obj["name"].lower() == "location", params["responseHeaders"]),
                    None,
                )
                self.redirected_url: str | None = lheader["value"] if lheader else None
            await self.global_conn.execute_cdp_cmd("Fetch.continueResponse", _params)
            return

        try:
            body = await self.global_conn.execute_cdp_cmd(
                "Fetch.getResponseBody",
                _params,
                timeout=1,
            )
        except CDPError as e:
            if (
                e.code == -32000  # noqa: PLR2004
                and e.message == "Can only get response body on requests captured after headers received."
            ):
                await self.global_conn.execute_cdp_cmd("Fetch.continueResponse", _params)
                return
            raise
        else:
            await self.global_conn.execute_cdp_cmd("Fetch.continueRequest", _params)
            if not self.cf_encountered:
                await self._check_cf_encounter(url, body)

            if url == (self.redirected_url or self.url) and str(params["responseStatusCode"]).startswith("2"):
                await self.remove_network_listeners()
                self.status_code = status_code
                self.response_headers = _generate_headers(params.get("responseHeaders", []))
                self.response_found = True

            if url == self.cf_encountered_on_url and str(params["responseStatusCode"]).startswith("2"):
                await self.remove_network_listeners()
                self.status_code = status_code
                self.response_headers = _generate_headers(params.get("responseHeaders", []))
                self.response_found = True

        return

    async def add_network_listeners(self: Self) -> None:
        """Add network listeners to the browser session."""
        await self.global_conn.execute_cdp_cmd(
            "Fetch.enable",
            cmd_args={"patterns": [{"requestStage": "Response", "urlPattern": "*"}]},
        )
        await self.global_conn.add_cdp_listener("Fetch.requestPaused", self.on_request)

    async def remove_network_listeners(self: Self) -> None:
        """Remove network listeners from the browser session."""
        try:
            await self.global_conn.remove_cdp_listener("Fetch.requestPaused", self.on_request)
            await self.global_conn.execute_cdp_cmd("Fetch.disable")
        except ValueError:
            pass

    async def _check_cf_encounter(self: Self, url: str, body: dict[str, Any]) -> None:
        """Check if cf was encountered on the page."""
        try:
            body_decoded = body["body"]
            if body["base64Encoded"]:
                body_decoded = base64.b64decode(body["body"]).decode()
            soup = BeautifulSoup(body_decoded, "html.parser")
            title = soup.select_one("title")
        except:  # noqa: E722, S110
            pass
        else:
            if title and title.text.startswith("Just a moment"):
                self.cf_encountered = True
                self.cf_encountered_on_url = url
                logger.debug("[Cloudflare] encountered the checkbox challenge")
                await find_and_click(self.driver, check=False)


def _generate_headers(headers: list[dict[str, str]]) -> CaseInsensitiveDict:
    gen_headers = CaseInsensitiveDict()
    for _header in headers:
        gen_headers.update({_header["name"]: _header["value"]})
    return gen_headers


async def find_iframe(driver: webdriver.Chrome, *, check: bool) -> webdriver.WebElement | None:
    """Find if checkbox is there; to complete cf challenge.

    `check` refers to whether check if the page title is Just a moment indicating cf.
    """
    iframe = None
    if check:
        try:
            source = await driver.page_source
            soup = BeautifulSoup(source, "html.parser")
            title = soup.select_one("title")
        except:  # noqa: E722, S110
            pass
        else:
            if not title or not title.text.startswith("Just a moment"):
                return iframe
    await asyncio.sleep(0.1)

    try:
        async with asyncio.timeout(10):
            while not iframe:
                try:
                    iframe = await driver.find_element(By.TAG_NAME, "iframe")
                except:  # noqa: E722
                    await asyncio.sleep(1)
    except TimeoutError:
        pass
    return iframe


async def find_and_click(driver: webdriver.Chrome, *, check: bool = True) -> bool:
    """Find and clicks the checkbox to complete cf challenge.

    `check` refers to whether check if the page title is Just a moment indicating cf.
    """
    button = None
    is_clicked = False
    iframe = await find_iframe(driver, check=check)
    if not iframe:
        return is_clicked
    try:
        async with asyncio.timeout(10):
            while not button:
                await asyncio.sleep(1)
                try:
                    iframe_document = await iframe.content_document
                    button = (
                        await iframe_document.find_element(By.CSS_SELECTOR, "#challenge-stage")
                        if iframe_document
                        else None
                    )
                except:  # noqa: E722
                    await asyncio.sleep(0.1)
    except TimeoutError:
        await asyncio.sleep(0.1)
    if not button:
        return is_clicked
    await asyncio.sleep(2)
    logger.debug("[Cloudflare] trying to click cf checkbox")
    try:
        await button.click()
    except websockets.exceptions.ConnectionClosedError:
        logger.debug("[Cloudflare] no need to click the box")
    else:
        is_clicked = True
        logger.debug("[Cloudflare] clicked cf checkbox")
    return is_clicked


async def source(url: str, timeout: float = 60) -> Source:
    """Wrapper to return html source of the url on successful loading.

    Waits for the page to load until timeout is hit.
    Raises `PageLoadError` on load failure.

    Still be prepared for any other exceptions for example, for now,
    setup won't run on Windows and you are responsible to download chrome,
    hence can error if they aren't detected when starting the Browser instance.
    """
    try:
        browser = await Browser.create()
        stored_cookies = Cookies()
        for cookie in stored_cookies:
            await browser.driver.add_cookie(cookie_dict=cookie)
        source = await browser.get(url, timeout)
        stored_cookies.update_cookies(await browser.driver.get_cookies())
        return source
    finally:
        await browser.quit()


def _clear_stored_cookies() -> None:
    cookies = Cookies()
    cookies.delete_cookies()


atexit.register(_clear_stored_cookies)
