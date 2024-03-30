"""Methods to load the page in the browser using webdriver."""

from typing import Self

from loguru import logger
from selenium_driverless import webdriver
from selenium_driverless.utils.utils import find_chrome_executable


class Browser:
    """Convenient class to load urls in the browser opposed to HTTPRequest."""

    def __init__(self: Self) -> None:
        """Initialises the browser by setting up the dependencies and async the webdriver.

        Not meant to be invoked directly instead `create()` when using outside of async context manager.
        """
        if not find_chrome_executable():
            self.setup_dependencies()
        self.options = BrowserOptions()
        self.driver = webdriver.Chrome(options=self.options)

    @classmethod
    async def create(cls: type[Self]) -> Self:
        """Creates the browser instance.

        Exceptions are raised by the `webdriver.Chrome()` impls.
        """
        instance = cls()
        await instance.driver
        return instance

    async def quit(self: Self) -> None:
        """Cleares up the browser instance."""
        return await self.driver.quit(clean_dirs=True)

    async def get(self: Self, url: str, timeout: float = 60):  # noqa: ANN201
        """Loads the url.

        Waits for the page to load until timeout is hit.
        Raises `PageLoadError` on load failure.
        """
        site = self.map_url(url)
        return await site.get(url, timeout)

    def map_url(self: Self, url: str):  # noqa: ANN201
        """Maps the url, to their site implementation based on the pattern matching.

        Returns default `Site` on no match.
        """
        from src.browser.apkmirror import APKMirror
        from src.browser.site import Site

        site = Site(self)
        if "www.apkmirror.com" in url:
            site = APKMirror(self)

        return site

    def setup_dependencies(self: Self) -> bool:
        """Not implemented yet for all (linux only for now).

        Setups the browser dependencies based on systems and returns the bool result.
        """
        import platform

        system = platform.system().lower()
        if system == "linux":
            setup = self.setup_dependencies_on_linux()
        elif system == "windows":
            setup = self.setup_dependencies_on_windows()
        elif system == "darwin":
            setup = self.setup_dependencies_on_mac()
        else:
            setup = self.setup_dependencies_on_unknown(system)
        return setup

    @staticmethod
    def setup_dependencies_on_linux() -> bool:
        """Setups the browser dependencies on linux.

        Returns the bool result.
        """
        import subprocess
        from pathlib import Path

        setup = False
        setup_script = Path(__file__).parent.joinpath("setup_browser.sh").as_posix()
        try:
            subprocess.run(["bash", setup_script], check=True)
            setup = True
        except subprocess.CalledProcessError as e:
            logger.error(f"failed to setup browser dependencies: {e!r}")
        return setup

    @staticmethod
    def setup_dependencies_on_windows() -> bool:
        """Not implemented yet.

        Setups the browser dependencies on windows.

        Returns the bool result.
        """
        try:
            msg = (
                "setup not yet implemented for Windows, kindly setup chrome and chromedriver manuallly "
                "or write yourself a powershell script"
            )
            raise NotImplementedError(msg)
        except NotImplementedError as e:
            logger.error(f"failed to setup browser dependencies: {e!r}")
        return False

    @staticmethod
    def setup_dependencies_on_mac() -> bool:
        """Not implemented yet.

        Setups the browser dependencies on mac.

        Returns the bool result.
        """
        try:
            msg = (
                "setup not yet implemented for Mac OS, kindly setup chrome and chromedriver manually "
                "or write yourself a zsh script"
            )
            raise NotImplementedError(msg)
        except NotImplementedError as e:
            logger.error(f"failed to setup browser dependencies: {e!r}")
        return False

    @staticmethod
    def setup_dependencies_on_unknown(system: str) -> bool:
        """Not implemented yet.

        Setups the browser dependencies on unknown.

        Returns the bool result.
        """
        try:
            msg = f"unexpected system: {system}, kindly setup chrome and chromedriver manually"
            raise NotImplementedError(msg)
        except NotImplementedError as e:
            logger.error(f"failed to setup browser dependencies: {e!r}")
        return False


class BrowserOptions:
    """Simple class to form and return a predefined instance of chrome `ChromeOptions()`."""

    def __new__(cls: type[Self]) -> webdriver.ChromeOptions:
        """Return an instance of chrome `ChromeOptions()`."""
        ## Ref1: https://github.com/Ulyssedev/Rust-undetected-chromedriver/blob/29222ff29fdf8bf018eb7ce668aa3ef4f9d84ab3/src/lib.rs#L107
        ## Ref2: https://stackoverflow.com/a/59678801

        cls.rand_ua()
        options = webdriver.ChromeOptions()
        """# options.add_argument("--headless=new")"""
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--log-level=3")
        options.add_argument("--disable-blink-features=AutomationControlled")
        """# options.add_argument(f"--user-agent={cls.user_agent}")"""
        return options

    @classmethod
    def rand_ua(cls: type[Self]) -> None:
        """Set a random user agent."""
        import secrets

        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36 Config/91.2.3711.12",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36",
        ]
        cls.user_agent = secrets.choice(user_agents)
