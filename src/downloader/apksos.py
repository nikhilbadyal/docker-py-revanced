"""APK SOS Downloader Class."""
from typing import Any

import requests
from bs4 import BeautifulSoup

from scripts.status_check import headers
from src.downloader.download import Downloader
from src.exceptions import AppNotFound
from src.utils import bs4_parser


class ApkSos(Downloader):
    """Files downloader."""

    def extract_download_link(self, page: str, app: str) -> None:
        """Function to extract the download link from apkmirror html page.

        :param page: Url of the page
        :param app: Name of the app
        """
        r = requests.get(page, headers=headers, allow_redirects=True)
        soup = BeautifulSoup(r.text, bs4_parser)
        download_button = soup.find(class_="col-sm-12 col-md-8 text-center")
        possible_links = download_button.find_all("a")
        for possible_link in possible_links:
            if possible_link.get("href"):
                return self._download(possible_link["href"], f"{app}.apk")
        raise AppNotFound("Unable to download apk from apk_combo")

    def latest_version(self, app: str, **kwargs: Any) -> None:
        """Function to download whatever the latest version of app from
        apkmirror.

        :param app: Name of the application
        :return: Version of downloaded apk
        """
        package_name = self.patcher.get_package_name(app)
        download_url = f"https://apksos.com/download-app/{package_name}"
        self.extract_download_link(download_url, app)
