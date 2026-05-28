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

    @staticmethod
    def _is_xapk_variant_page(page: str) -> bool:
        """Detect Uptodown variant URLs that expose the real XAPK file instead of the store bridge."""
        return page.rstrip("/").endswith("-x")

    @staticmethod
    def _is_xapk_store_bridge(detail_download_button: Tag, page: str) -> bool:
        """Detect generic XAPK download pages whose button downloads the Uptodown installer app."""
        button_classes = detail_download_button.get("class", [])
        # Direct variant pages also point at XAPK bytes, so only generic pages should be rewritten.
        return "xapk" in button_classes and not UptoDown._is_xapk_variant_page(page)

    def _resolve_xapk_variant_page(self: Self, detail_download_button: Tag, page: str, app: str) -> str:
        """Build the direct XAPK variant URL from Uptodown's generic app-store bridge button."""
        download_version = detail_download_button.get("data-download-version")
        if not download_version:
            msg = f"Unable to resolve direct XAPK download for {app} from uptodown."
            raise UptoDownAPKDownloadError(msg, url=page)

        # Uptodown encodes the real file endpoint as `/download/<file-id>-x` behind the variants UI.
        return f"{page.rstrip('/')}/{download_version}-x"

    def extract_download_link(self: Self, page: str, app: str) -> tuple[str, str]:
        """Extract download link from uptodown url."""
        r = requests.get(page, headers=request_header, allow_redirects=True, timeout=request_timeout)
        handle_request_response(r, page)
        soup = BeautifulSoup(r.text, bs4_parser)
        detail_download_button = soup.find("button", id="detail-download-button")

        if not isinstance(detail_download_button, Tag):
            msg = f"Unable to download {app} from uptodown."
            raise UptoDownAPKDownloadError(msg, url=page)

        if self._is_xapk_store_bridge(detail_download_button, page):
            # Generic XAPK pages download Uptodown App Store; recurse into the real variant page before downloading.
            return self.extract_download_link(self._resolve_xapk_variant_page(detail_download_button, page, app), app)

        data_url = detail_download_button.get("data-url")
        download_url = f"https://dw.uptodown.com/dwn/{data_url}"
        # XAPK archives must keep their extension so APKEditor can merge them into a patchable APK later.
        file_name = f"{app}.xapk" if self._is_xapk_variant_page(page) else f"{app}.apk"
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

        app_code = detail_app_name.get("data-code")
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
                    version_url_data = item["versionURL"]
                    if isinstance(version_url_data, dict):
                        download_url = (
                            f"{version_url_data['url']}/{version_url_data['extraURL']}/"
                            f"{version_url_data['versionID']}"
                        )
                    else:
                        download_url = f"{version_url_data}-x"
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
