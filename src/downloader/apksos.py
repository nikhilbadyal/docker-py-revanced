"""APK SOS Downloader Class."""
from typing import Any

from loguru import logger
from selectolax.lexbor import LexborHTMLParser

from src.downloader.download import Downloader
from src.utils import AppNotFound


class ApkSos(Downloader):
    """Files downloader."""

    def extract_download_link(self, page: str, app: str) -> None:
        """Function to extract the download link from apkmirror html page.

        :param page: Url of the page
        :param app: Name of the app
        """
        parser = LexborHTMLParser(self.config.session.get(page).text)
        download_url = parser.css_first(
            r"body > div > div > div > div > div.col-sm-12.col-md-8 > div.card.fluid.\.idma > "
            "div.section.row > div.col-sm-12.col-md-8.text-center > p > a"
        ).attributes["href"]
        self._download(download_url, f"{app}.apk")
        logger.debug(f"Downloaded {app} apk from apk_combo_downloader in rt")

    def latest_version(self, app: str, **kwargs: Any) -> None:
        """Function to download whatever the latest version of app from
        apkmirror.

        :param app: Name of the application
        :return: Version of downloaded apk
        """
        package_name = None
        for package, app_tuple in self.patcher.revanced_app_ids.items():
            if app_tuple[0] == app:
                package_name = package
        if not package_name:
            logger.info("Unable to download from apkcombo")
            raise AppNotFound()
        download_url = f"https://apksos.com/download-app/{package_name}"
        self.extract_download_link(download_url, app)
