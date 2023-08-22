"""APK SOS Downloader Class."""
from typing import Any, Tuple

import requests
from bs4 import BeautifulSoup

from src.downloader.download import Downloader
from src.downloader.sources import apk_sources
from src.exceptions import APKSosAPKDownloadFailure
from src.utils import bs4_parser, request_header


class ApkSos(Downloader):
    """Files downloader."""

    def extract_download_link(self, page: str, app: str) -> Tuple[str, str]:
        """Function to extract the download link from apkmirror html page.

        :param page: Url of the page
        :param app: Name of the app
        """
        r = requests.get(page, headers=request_header, allow_redirects=True)
        soup = BeautifulSoup(r.text, bs4_parser)
        download_button = soup.find(class_="col-sm-12 col-md-8 text-center")
        possible_links = download_button.find_all("a")
        for possible_link in possible_links:
            if possible_link.get("href"):
                file_name = f"{app}.apk"
                self._download(possible_link["href"], file_name)
                return file_name, possible_link["href"]
        raise APKSosAPKDownloadFailure(f"Unable to download {app}", url=page)

    def latest_version(self, app: str, **kwargs: Any) -> Tuple[str, str]:
        """Function to download whatever the latest version of app from
        apkmirror.

        :param app: Name of the application
        :return: Version of downloaded apk
        """
        package_name = self.patcher.get_package_name(app)
        download_url = apk_sources[app].format(package_name)
        return self.extract_download_link(download_url, app)
