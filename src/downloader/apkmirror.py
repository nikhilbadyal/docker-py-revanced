"""Downloader Class."""

from typing import Any, Self

import requests
from bs4 import BeautifulSoup, Tag
from loguru import logger

from src.app import APP
from src.downloader.download import Downloader
from src.downloader.sources import APK_MIRROR_BASE_URL
from src.exceptions import APKMirrorAPKDownloadError, ScrapingError
from src.utils import bs4_parser, contains_any_word, handle_request_response, request_header, request_timeout, slugify


class ApkMirror(Downloader):
    """Files downloader."""

    def _extract_force_download_link(self: Self, link: str, app: str) -> tuple[str, str]:
        """Extract force download link."""
        link_page_source = self._extract_source(link)
        notes_divs = self._extracted_search_source_div(link_page_source, "tab-pane")
        apk_type = self._extracted_search_source_div(link_page_source, "apkm-badge").get_text()
        extension = "zip" if apk_type == "BUNDLE" else "apk"
        possible_links = notes_divs.find_all("a")
        for possible_link in possible_links:
            if possible_link.get("href") and "download.php?id=" in possible_link.get("href"):
                file_name = f"{app}.{extension}"
                self._download(APK_MIRROR_BASE_URL + possible_link["href"], file_name)
                return file_name, APK_MIRROR_BASE_URL + possible_link["href"]
        msg = f"Unable to extract force download for {app}"
        raise APKMirrorAPKDownloadError(msg, url=link)

    def extract_download_link(self: Self, page: str, app: str) -> tuple[str, str]:
        """Function to extract the download link from apkmirror html page.

        :param page: Url of the page
        :param app: Name of the app
        """
        logger.debug(f"Extracting download link from\n{page}")
        download_button = self._extracted_search_div(page, "center")
        download_links = download_button.find_all("a")
        if final_download_link := next(
            (
                download_link["href"]
                for download_link in download_links
                if download_link.get("href") and "download/?key=" in download_link.get("href")
            ),
            None,
        ):
            return self._extract_force_download_link(APK_MIRROR_BASE_URL + final_download_link, app)
        msg = f"Unable to extract link from {app} version list"
        raise APKMirrorAPKDownloadError(msg, url=page)

    def get_download_page(self: Self, main_page: str) -> str:
        """Function to get the download page in apk_mirror.

        :param main_page: Main Download Page in APK mirror(Index)
        :return:
        """
        list_widget = self._extracted_search_div(main_page, "tab-pane noPadding")
        table_rows = list_widget.find_all(class_="table-row headerFont")
        links: dict[str, str] = {}
        apk_archs = ["arm64-v8a", "universal", "noarch"]
        for row in table_rows:
            if row.find(class_="accent_color"):
                apk_type = row.find(class_="apkm-badge").get_text()
                sub_url = row.find(class_="accent_color")["href"]
                text = row.text.strip()
                if apk_type == "APK" and (not contains_any_word(text, apk_archs)):
                    continue
                links[apk_type] = f"{APK_MIRROR_BASE_URL}{sub_url}"
        if preferred_link := links.get("APK", links.get("BUNDLE")):
            return preferred_link
        msg = "Unable to extract download page"
        raise APKMirrorAPKDownloadError(msg, url=main_page)

    @staticmethod
    def _extract_source(url: str) -> str:
        """Extracts the source from the url incase of reuse."""
        response = requests.get(url, headers=request_header, timeout=request_timeout)
        handle_request_response(response, url)
        return response.text

    @staticmethod
    def _extracted_search_source_div(source: str, search_class: str) -> Tag:
        """Extract search div from source."""
        soup = BeautifulSoup(source, bs4_parser)
        return soup.find(class_=search_class)  # type: ignore[return-value]

    def _extracted_search_div(self: Self, url: str, search_class: str) -> Tag:
        """Extract search div from url."""
        return self._extracted_search_source_div(self._extract_source(url), search_class)

    def specific_version(self: Self, app: APP, version: str, main_page: str = "") -> tuple[str, str]:
        """Function to download the specified version of app from  apkmirror.

        :param app: Name of the application
        :param version: Version of the application to download
        :param main_page: Version of the application to download
        :return: Version of downloaded apk
        """
        if not main_page:
            version = version.replace(".", "-")
            apk_main_page = app.download_source
            version_page = apk_main_page + apk_main_page.split("/")[-2]
            main_page = f"{version_page}-{version}-release/"
        download_page = self.get_download_page(main_page)
        if app.app_version == "latest":
            try:
                logger.info(f"Trying to guess {app.app_name} version.")
                appsec_val = self._extracted_search_div(download_page, "appspec-value")
                appsec_version = str(appsec_val.find(text=lambda text: "Version" in text))
                app.app_version = slugify(appsec_version.split(":")[-1].strip())
                logger.info(f"Guessed {app.app_version} for {app.app_name}")
            except ScrapingError:
                pass
        return self.extract_download_link(download_page, app.app_name)

    def latest_version(self: Self, app: APP, **kwargs: Any) -> tuple[str, str]:
        """Function to download whatever the latest version of app from apkmirror.

        :param app: Name of the application
        :return: Version of downloaded apk
        """
        app_main_page = app.download_source
        versions_div = self._extracted_search_div(app_main_page, "listWidget p-relative")
        app_rows = versions_div.find_all(class_="appRow")
        version_urls = [
            app_row.find(class_="downloadLink")["href"]
            for app_row in app_rows
            if "beta" not in app_row.find(class_="appRowTitle").get_text().lower()
            and "alpha" not in app_row.find(class_="appRowTitle").get_text().lower()
        ]
        return self.specific_version(app, "latest", APK_MIRROR_BASE_URL + max(version_urls))
