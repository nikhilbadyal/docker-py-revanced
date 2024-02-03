"""APK Monk Downloader Class."""

import re
from typing import Any, Self

import requests
from bs4 import BeautifulSoup

from scripts.status_check import combo_headers
from src.app import APP
from src.downloader.download import Downloader
from src.downloader.sources import APK_MONK_BASE_URL
from src.exceptions import APKMonkAPKDownloadError
from src.utils import bs4_parser, handle_request_response, request_header, request_timeout


class ApkMonk(Downloader):
    """Files downloader."""

    def extract_download_link(self: Self, page: str, app: str) -> tuple[str, str]:
        """Function to extract the download link from apkmonk html page.

        :param page: Url of the page
        :param app: Name of the app
        """
        file_name = f"{app}.apk"
        r = requests.get(page, headers=request_header, allow_redirects=True, timeout=request_timeout)
        handle_request_response(r, page)
        soup = BeautifulSoup(r.text, bs4_parser)
        download_scripts = soup.find_all("script", type="text/javascript")
        key_value_pattern = r'\{"pkg":"([^"]+)","key":"([^"]+)"\}'
        url = None
        for script in download_scripts:
            if match := re.search(key_value_pattern, script.text):
                pkg_value = match.group(1)
                key_value = match.group(2)
                url = f"{APK_MONK_BASE_URL}/down_file?pkg={pkg_value}&key={key_value}"
                break
        if not url:
            msg = "Unable to get key-value link"
            raise APKMonkAPKDownloadError(
                msg,
                url=page,
            )
        request_header["User-Agent"] = combo_headers["User-Agent"]
        r = requests.get(url, headers=request_header, allow_redirects=True, timeout=request_timeout)
        handle_request_response(r, url)
        final_download_url = r.json()["url"]
        self._download(final_download_url, file_name)
        return file_name, final_download_url

    def specific_version(self: Self, app: APP, version: str, main_page: str = "") -> tuple[str, str]:
        """Function to download the specified version of app from  apkmirror.

        :param app: Name of the application
        :param version: Version of the application to download
        :param main_page: Version of the application to download
        :return: Version of downloaded apk
        """
        r = requests.get(app.download_source, headers=request_header, allow_redirects=True, timeout=request_timeout)
        handle_request_response(r, app.download_source)
        soup = BeautifulSoup(r.text, bs4_parser)
        version_table = soup.find_all(class_="striped")
        for version_row in version_table:
            version_links = version_row.find_all("a")
            for link in version_links:
                app_version = link.text
                if app_version == app.app_version:
                    download_link = link["href"]
                    return self.extract_download_link(APK_MONK_BASE_URL + download_link, app.app_name)
        msg = "Unable to scrap version link"
        raise APKMonkAPKDownloadError(
            msg,
            url=app.download_source,
        )

    def latest_version(self: Self, app: APP, **kwargs: Any) -> tuple[str, str]:
        """Function to download whatever the latest version of app from apkmonkP.

        :param app: Name of the application
        :return: Version of downloaded apk
        """
        r = requests.get(app.download_source, headers=request_header, allow_redirects=True, timeout=request_timeout)
        handle_request_response(r, app.download_source)
        soup = BeautifulSoup(r.text, bs4_parser)
        latest_download_url = soup.find(id="download_button")["href"]  # type: ignore[index]
        return self.extract_download_link(latest_download_url, app.app_name)  # type: ignore[arg-type]
