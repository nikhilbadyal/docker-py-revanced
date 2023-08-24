"""Upto Down Downloader."""
from typing import Any, Tuple

import requests
from bs4 import BeautifulSoup
from loguru import logger

from src.app import APP
from src.downloader.download import Downloader
from src.exceptions import UptoDownAPKDownloadFailure
from src.utils import bs4_parser, request_header


class UptoDown(Downloader):
    """Files downloader."""

    def extract_download_link(self, page: str, app: str) -> Tuple[str, str]:
        r = requests.get(page, headers=request_header, allow_redirects=True, timeout=60)
        soup = BeautifulSoup(r.text, bs4_parser)
        soup = soup.find(id="detail-download-button")
        download_url = soup.get("data-url")
        if not download_url:
            raise UptoDownAPKDownloadFailure(
                f"Unable to download {app} from uptodown.", url=page
            )
        file_name = f"{app}.apk"
        self._download(download_url, file_name)
        return file_name, download_url

    def specific_version(self, app: APP, version: str) -> Tuple[str, str]:
        """Function to download the specified version of app from  apkmirror.

        :param app: Name of the application
        :param version: Version of the application to download
        :return: Version of downloaded apk
        """
        logger.debug("downloading specified version of app from uptodown.")
        url = f"{app.download_source}/versions"
        html = self.config.session.get(url).text
        soup = BeautifulSoup(html, bs4_parser)
        versions_list = soup.find("section", {"id": "versions"})
        download_url = None
        for version_item in versions_list.find_all("div", {"data-url": True}):
            extracted_version = version_item.find("span", {"class": "version"}).text
            if extracted_version == version:
                download_url = version_item["data-url"]
                break
        if download_url is None:
            raise UptoDownAPKDownloadFailure(
                f"Unable to download {app.app_name} from uptodown.", url=url
            )
        return self.extract_download_link(download_url, app.app_name)

    def latest_version(self, app: APP, **kwargs: Any) -> Tuple[str, str]:
        page = f"{app.download_source}/download"
        return self.extract_download_link(page, app.app_name)
