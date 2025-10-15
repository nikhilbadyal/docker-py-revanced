"""APK Pure Downloader Class."""

from functools import cmp_to_key
from typing import Any, Self
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup
from loguru import logger

from src.app import APP
from src.downloader.download import Downloader
from src.exceptions import APKPureAPKDownloadError
from src.utils import bs4_parser, handle_request_response, request_header, request_timeout, slugify


class ApkPure(Downloader):
    """Files downloader."""

    default_archs_priority: tuple[str, ...] = ("arm64-v8a", "armeabi-v7a", "x86_64", "x86")

    @staticmethod
    def _select_preferred_dl(app: str, apk_dls: list[str], xapk_dls: list[str]) -> tuple[str | None, str | None]:
        file_name = None
        app_dl = None
        if apk_dls:
            file_name = f"{app}.apk"
            app_dl = apk_dls[0]
        elif xapk_dls:
            file_name = f"{app}.zip"
            app_dl = xapk_dls[0]
        return file_name, app_dl

    def _sort_by_priority(self: Self, arch_list: list[str] | tuple[str]) -> list[str]:
        """Specifically used to sort the arch list based on order of elements of default archs priority list."""
        return [darch for darch in self.default_archs_priority if darch in arch_list]

    def _get_apk_type(self: Self, dl: str) -> list[str] | None:
        """Extract apk type from download link."""
        query_params = parse_qs(urlparse(dl).query)
        return query_params.get("nc")

    def _compare_apk_types(self: Self, apk_type1: list[str], apk_type2: list[str]) -> int:
        """Compare two apk types for prioritization."""
        l1, l2 = len(apk_type1), len(apk_type2)
        if l1 != l2:
            # Longer list indicates support for multiple archs, higher priority
            return -1 if l1 > l2 else 1

        # Same length, compare by priority order
        priority = self.global_archs_priority or self.default_archs_priority
        for arch in priority:
            has_arch1 = arch in apk_type1
            has_arch2 = arch in apk_type2
            if has_arch1 != has_arch2:
                return -1 if has_arch1 else 1
        return 0

    def _compare_dls(self: Self, dl1: str, dl2: str) -> int:
        """Compare two dls of same type (apk or xapk) to prioritise the archs on lower indices."""
        apk_type1 = self._get_apk_type(dl1)
        apk_type2 = self._get_apk_type(dl2)

        if apk_type1 and apk_type2:
            return self._compare_apk_types(apk_type1, apk_type2)
        if not apk_type1 and apk_type2:
            return 1
        if apk_type1 and not apk_type2:
            return -1
        return 0

    def extract_download_link(self: Self, page: str, app: str) -> tuple[str, str]:
        """Function to extract the download link from apkpure download page.

        :param page: Url of the page
        :param app: Name of the app
        :return: Tuple of filename and app direct download link
        """
        logger.debug(f"Extracting download link from\n{page}")
        r = requests.get(page, headers=request_header, timeout=request_timeout)
        handle_request_response(r, page)
        soup = BeautifulSoup(r.text, bs4_parser)
        apks = soup.select("#version-list a.download-btn")
        _apk_dls: list[str] = []
        _xapk_dls: list[str] = []
        for apk in apks:
            if _apk_dl := apk.get("href"):
                if "/b/XAPK/" in _apk_dl:
                    _xapk_dls.append(_apk_dl)  # type: ignore  # noqa: PGH003
                else:
                    _apk_dls.append(_apk_dl)  # type: ignore  # noqa: PGH003
        _apk_dls.sort(key=cmp_to_key(self._compare_dls))
        _xapk_dls.sort(key=cmp_to_key(self._compare_dls))
        file_name, app_dl = self._select_preferred_dl(app, _apk_dls, _xapk_dls)
        if not file_name or not app_dl:
            msg = f"Unable to extract link from {app} version list"
            raise APKPureAPKDownloadError(msg, url=page)
        if app_version := soup.select_one("span.info-sdk > span"):
            self.app_version = slugify(app_version.get_text(strip=True))
            logger.info(f"Will be downloading {app}'s version {self.app_version}...")
        else:
            self.app_version = "latest"
            logger.info(f"Unable to guess latest version of {app}")
        return file_name, app_dl

    def specific_version(self: Self, app: APP, version: str) -> tuple[str, str]:
        """
        Downloads the specified version of an app from APKPure.

        Parameters
        ----------
        app : APP
            The application object containing metadata.
        version : str
            The specific version of the application to download.

        Returns
        -------
        tuple[str, str]
            A tuple containing:
            - The filename of the downloaded APK.
            - The direct download link of the APK.

        Raises
        ------
        APKPureAPKDownloadError
            If the specified version is not found.
        """
        self.global_archs_priority = tuple(self._sort_by_priority(app.archs_to_build))
        version_page = f"{app.download_source}/versions"

        response = requests.get(version_page, headers=request_header, timeout=request_timeout)
        handle_request_response(response, version_page)

        soup = BeautifulSoup(response.text, bs4_parser)

        for box in soup.select("ul.ver-wrap > *"):
            download_link = box.select_one("a.ver_download_link")
            if not download_link:
                continue

            found_version = download_link.get("data-dt-version")
            if found_version == version:
                download_page = download_link.get("href")
                file_name, download_source = self.extract_download_link(
                    str(download_page),
                    app.app_name,
                )

                app.app_version = self.app_version
                logger.info(f"Guessed {app.app_version} for {app.app_name}")

                self._download(download_source, file_name)
                return file_name, download_source
        msg = f"Unable to find specific version '{version}' for {app} from version list"
        raise APKPureAPKDownloadError(msg, url=version_page)

    def latest_version(self: Self, app: APP, **kwargs: Any) -> tuple[str, str]:
        """Function to download whatever the latest version of app from apkpure.

        :param app: Name of the application
        :return: Tuple of filename and app direct download link
        """
        self.global_archs_priority = tuple(self._sort_by_priority(app.archs_to_build))
        download_page = app.download_source + "/download"
        file_name, download_source = self.extract_download_link(download_page, app.app_name)
        app.app_version = self.app_version
        if self.app_version != "latest":
            logger.info(f"Guessed {app.app_version} for {app.app_name}")
        self._download(download_source, file_name)
        return file_name, download_source
