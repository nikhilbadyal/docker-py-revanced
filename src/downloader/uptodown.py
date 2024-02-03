"""Upto Down Downloader."""

from typing import Any, Self

import requests
from bs4 import BeautifulSoup, Tag
from loguru import logger

from src.app import APP
from src.downloader.download import Downloader
from src.exceptions import UptoDownAPKDownloadError
from src.utils import bs4_parser, handle_request_response, request_header, request_timeout


class UptoDown(Downloader):
    """Files downloader."""

    def extract_download_link(self: Self, page: str, app: str) -> tuple[str, str]:
        """Extract download link from uptodown url."""
        r = requests.get(page, headers=request_header, allow_redirects=True, timeout=request_timeout)
        handle_request_response(r, page)
        download_page_url = page.replace("/download", "/post-download")
        download_page_html = requests.get(download_page_url, headers=request_header, timeout=request_timeout).text
        soup = BeautifulSoup(download_page_html, bs4_parser)
        post_download = soup.find("div", class_="post-download")

        if not isinstance(post_download, Tag):
            msg = f"Unable to download {app} from uptodown."
            raise UptoDownAPKDownloadError(msg, url=page)

        data_url = post_download.get("data-url")
        download_url = f"https://dw.uptodown.com/dwn/{data_url}"
        file_name = f"{app}.apk"
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
        html = requests.get(url, headers=request_header, timeout=request_timeout).text
        soup = BeautifulSoup(html, bs4_parser)
        detail_app_name = soup.find("h1", id="detail-app-name")

        if not isinstance(detail_app_name, Tag):
            msg = f"Unable to download {app} from uptodown."
            raise UptoDownAPKDownloadError(msg, url=url)

        app_code = detail_app_name.get("code")
        version_page = 1
        download_url = None
        version_found = False

        while not version_found:
            version_url = f"{app.download_source}/apps/{app_code}/versions/{version_page}"
            r = requests.get(version_url, headers=request_header, timeout=request_timeout)
            handle_request_response(r, version_url)
            json = r.json()

            if "data" not in json:
                break

            for item in json["data"]:
                if item["version"] == version:
                    download_url = item["versionURL"]
                    version_found = True
                    break

            version_page += 1

        if download_url is None:
            msg = f"Unable to download {app.app_name} from uptodown."
            raise UptoDownAPKDownloadError(msg, url=url)

        return self.extract_download_link(download_url, app.app_name)

    def latest_version(self: Self, app: APP, **kwargs: Any) -> tuple[str, str]:
        """Function to download the latest version of app from uptodown."""
        logger.debug("downloading latest version of app from uptodown.")
        page = f"{app.download_source}/download"
        return self.extract_download_link(page, app.app_name)
