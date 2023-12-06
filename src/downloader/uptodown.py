"""Upto Down Downloader."""
from typing import Any, Self

import requests
from bs4 import BeautifulSoup
from loguru import logger

from src.app import APP
from src.downloader.download import Downloader
from src.exceptions import UptoDownAPKDownloadError
from src.utils import bs4_parser, handle_request_response, request_header, request_timeout


class UptoDown(Downloader):
    """Files downloader."""

    def extract_download_link(self: Self, page: str, app: APP) -> tuple[str, str]:
        """Extract download link from uptodown url."""
        r = requests.get(page, headers=request_header, allow_redirects=True, timeout=request_timeout)
        handle_request_response(r, page)
        soup = BeautifulSoup(r.text, bs4_parser)
        file_id = soup.find(id="detail-app-name").get("data-file-id")
        app_name = app.app_name

        if not file_id:
            msg = f"Unable to download {app_name} from uptodown."
            raise UptoDownAPKDownloadError(msg, url=page)

        download_page_url = f"{app.download_source}/post-download/{file_id}"
        download_page_html = requests.get(download_page_url, headers=request_header).text
        soup = BeautifulSoup(download_page_html, bs4_parser)
        data_url = soup.find("div", class_="post-download").get("data-url")

        if not data_url:
            msg = f"Unable to download {app_name} from uptodown."
            raise UptoDownAPKDownloadError(msg, url=page)

        download_url = f"https://dw.uptodown.com/dwn/{data_url}"
        file_name = f"{app_name}.apk"
        self._download(download_url, file_name)

        return file_name, download_url

    def specific_version(self: Self, app: APP, version: str) -> tuple[str, str]:
        """Function to download the specified version of app from uptodown.

        :param app: Name of the application
        :param version: Version of the application to download
        :return: Version of downloaded apk
        """
        logger.debug("downloading specified version of app from uptodown.")
        url = f"{app.download_source}/versions"
        html = requests.get(url, headers=request_header).text
        soup = BeautifulSoup(html, bs4_parser)
        app_code = soup.find(id="detail-app-name").get("code")
        page = 1
        download_url = None

        while True:
            version_url = f"{app.download_source}/apps/{app_code}/versions/{page}"
            r = requests.get(version_url)
            handle_request_response(r, version_url)
            json = r.json()

            if "data" not in json:
                break

            for item in json["data"]:
                if item["version"] == version:
                    download_url = item["versionURL"]
                    break

            page += 1

        if download_url is None:
            msg = f"Unable to download {app.app_name} from uptodown."
            raise UptoDownAPKDownloadError(msg, url=url)

        return self.extract_download_link(download_url, app)

    def latest_version(self: Self, app: APP, **kwargs: Any) -> tuple[str, str]:
        """Function to download the latest version of app from uptodown."""
        logger.debug("downloading latest version of app from uptodown.")
        page = f"{app.download_source}/download"
        return self.extract_download_link(page, app)
