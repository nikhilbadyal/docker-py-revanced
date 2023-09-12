"""Upto Down Downloader."""
from typing import Any, Self

import requests
from bs4 import BeautifulSoup
from loguru import logger

from src.app import APP
from src.downloader.download import Downloader
from src.exceptions import UptoDownAPKDownloadError
from src.utils import bs4_parser, handle_request_response, request_header, request_timeout, session


class UptoDown(Downloader):
    """Files downloader."""

    def extract_download_link(self: Self, page: str, app: str) -> tuple[str, str]:
        """Extract download link from uptodown url."""
        r = requests.get(page, headers=request_header, allow_redirects=True, timeout=request_timeout)
        handle_request_response(r, page)
        soup = BeautifulSoup(r.text, bs4_parser)
        download_button = soup.find(id="detail-download-button")
        if not download_button:
            msg = f"Unable to download {app} from uptodown."
            raise UptoDownAPKDownloadError(msg, url=page)
        download_url = download_button.get("data-url")  # type: ignore[union-attr]
        if not download_url:
            msg = f"Unable to download {app} from uptodown."
            raise UptoDownAPKDownloadError(msg, url=page)
        file_name = f"{app}.apk"
        if isinstance(download_url, str):
            self._download(download_url, file_name)
            return file_name, download_url
        msg = f"Unable to download {app} from uptodown."
        raise UptoDownAPKDownloadError(msg, url=page)

    def specific_version(self: Self, app: APP, version: str) -> tuple[str, str]:
        """Function to download the specified version of app from  apkmirror.

        :param app: Name of the application
        :param version: Version of the application to download
        :return: Version of downloaded apk
        """
        logger.debug("downloading specified version of app from uptodown.")
        url = f"{app.download_source}/versions"
        html = session.get(url).text
        soup = BeautifulSoup(html, bs4_parser)
        versions_list = soup.find("section", {"id": "versions"})
        download_url = None
        for version_item in versions_list.find_all("div", {"data-url": True}):  # type: ignore[union-attr]
            extracted_version = version_item.find("span", {"class": "version"}).text
            if extracted_version == version:
                download_url = version_item["data-url"]
                break
        if download_url is None:
            msg = f"Unable to download {app.app_name} from uptodown."
            raise UptoDownAPKDownloadError(msg, url=url)
        return self.extract_download_link(download_url, app.app_name)

    def latest_version(self: Self, app: APP, **kwargs: Any) -> tuple[str, str]:
        """Function to download the latest version of app from uptodown."""
        logger.debug("downloading latest version of app from uptodown.")
        page = f"{app.download_source}/download"
        return self.extract_download_link(page, app.app_name)
