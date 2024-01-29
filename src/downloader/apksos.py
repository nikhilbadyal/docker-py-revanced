"""APK SOS Downloader Class."""

from typing import Any, Self

import requests
from bs4 import BeautifulSoup

from src.app import APP
from src.downloader.download import Downloader
from src.exceptions import APKSosAPKDownloadError
from src.utils import bs4_parser, handle_request_response, request_header, request_timeout


class ApkSos(Downloader):
    """Files downloader."""

    def extract_download_link(self: Self, page: str, app: str) -> tuple[str, str]:
        """Function to extract the download link from apkmirror html page.

        :param page: Url of the page
        :param app: Name of the app
        """
        r = requests.get(page, headers=request_header, allow_redirects=True, timeout=request_timeout)
        handle_request_response(r, page)
        soup = BeautifulSoup(r.text, bs4_parser)
        download_button = soup.find(class_="col-sm-12 col-md-8 text-center")
        possible_links = download_button.find_all("a")  # type: ignore[union-attr]
        for possible_link in possible_links:
            if possible_link.get("href"):
                file_name = f"{app}.apk"
                self._download(possible_link["href"], file_name)
                return file_name, possible_link["href"]
        msg = f"Unable to download {app}"
        raise APKSosAPKDownloadError(msg, url=page)

    def latest_version(self: Self, app: APP, **kwargs: Any) -> tuple[str, str]:
        """Function to download whatever the latest version of app from apkmirror.

        :param app: Name of the application
        :return: Version of downloaded apk
        """
        return self.extract_download_link(app.download_source, app.app_name)
