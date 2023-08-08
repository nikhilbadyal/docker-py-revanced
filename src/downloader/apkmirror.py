"""Downloader Class."""
import re
from typing import Any

from loguru import logger
from selectolax.lexbor import LexborHTMLParser

from src.downloader.download import Downloader
from src.utils import AppNotFound


class ApkMirror(Downloader):
    """Files downloader."""

    def extract_download_link(self, page: str, app: str) -> None:
        """Function to extract the download link from apkmirror html page.

        :param page: Url of the page
        :param app: Name of the app
        """
        logger.debug(f"Extracting download link from\n{page}")
        parser = LexborHTMLParser(self.config.session.get(page).text)

        resp = self.config.session.get(
            self.config.apk_mirror + parser.css_first("a.accent_bg").attributes["href"]
        )
        parser = LexborHTMLParser(resp.text)

        href = parser.css_first(
            "p.notes:nth-child(3) > span:nth-child(1) > a:nth-child(1)"
        ).attributes["href"]
        self._download(self.config.apk_mirror + href, f"{app}.apk")

    def get_download_page(self, parser: LexborHTMLParser, main_page: str) -> str:
        """Function to get the download page in apk_mirror.

        :param parser: Parser
        :param main_page: Main Download Page in APK mirror(Index)
        :return:
        """
        logger.debug(f"Getting download page from {main_page}")
        apm = parser.css(".apkm-badge")
        sub_url = ""
        for is_apm in apm:
            parent_text = is_apm.parent.parent.text()
            if "APK" in is_apm.text() and (
                "arm64-v8a" in parent_text
                or "universal" in parent_text
                or "noarch" in parent_text
            ):
                parser = is_apm.parent
                sub_url = parser.css_first(".accent_color").attributes["href"]
                break
        if sub_url == "":
            logger.exception(
                f"Unable to find any apk on apkmirror_specific_version on {main_page}"
            )
            raise AppNotFound("Unable to find apk on apkmirror site.")
        return self.config.apk_mirror + sub_url

    def specific_version(self, app: str, version: str) -> None:
        """Function to download the specified version of app from  apkmirror.

        :param app: Name of the application
        :param version: Version of the application to download
        :return: Version of downloaded apk
        """
        version = version.replace(".", "-")
        main_page = f"{self.config.apk_mirror_version_urls.get(app)}-{version}-release/"
        parser = LexborHTMLParser(
            self.config.session.get(main_page, allow_redirects=True).text
        )
        download_page = self.get_download_page(parser, main_page)
        self.extract_download_link(download_page, app)

    def latest_version(self, app: str, **kwargs: Any) -> None:
        """Function to download whatever the latest version of app from
        apkmirror.

        :param app: Name of the application
        :return: Version of downloaded apk
        """
        logger.debug(f"Trying to download {app}'s latest version from apkmirror")
        page = self.config.apk_mirror_urls.get(app)
        if not page:
            logger.debug("Invalid app")
            raise AppNotFound("Invalid app")
        parser = LexborHTMLParser(self.config.session.get(page).text)
        try:
            main_page = parser.css_first(".appRowVariantTag>.accent_color").attributes[
                "href"
            ]
        except AttributeError:
            # Handles a case when variants are not available
            main_page = parser.css_first(".downloadLink").attributes["href"]
        match = re.search(r"\d", main_page)
        if not match:
            logger.error("Cannot find app main page")
            raise AppNotFound()
        main_page = f"{self.config.apk_mirror}{main_page}"
        parser = LexborHTMLParser(self.config.session.get(main_page).text)
        download_page = self.get_download_page(parser, main_page)
        self.extract_download_link(download_page, app)
