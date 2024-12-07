"""APK Pure Downloader Class."""

from typing import Any, Self

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

    def _compare_dls(self: Self, dl1: str, dl2: str) -> int:
        """Compare two dls of same type (apk or xapk) to prioritise the archs on lower indices."""
        from urllib.parse import parse_qs, urlparse

        apk_type1 = parse_qs(urlparse(dl1).query).get("nc")
        apk_type2 = parse_qs(urlparse(dl2).query).get("nc")
        if apk_type1 and apk_type2:
            l1 = len(apk_type1)
            l2 = len(apk_type2)
            # Indicates support for multiple archs, hence longer length
            if l1 > l2:
                return -1
            if l1 < l2:
                return 1
            # Arrange based on priority list
            priority = self.global_archs_priority or self.default_archs_priority
            for arch in priority:
                if arch in apk_type1 and arch not in apk_type2:
                    return -1
                if arch not in apk_type1 and arch in apk_type2:
                    return 1
        elif not apk_type1 and apk_type2:
            return 1
        elif apk_type1 and not apk_type2:
            return -1
        return 0

    def extract_download_link(self: Self, page: str, app: str) -> tuple[str, str]:
        """Function to extract the download link from apkpure download page.

        :param page: Url of the page
        :param app: Name of the app
        :return: Tuple of filename and app direct download link
        """
        from functools import cmp_to_key

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
        """Function to download the specified version of app from apkpure.

        :param app: Name of the application
        :param version: Version of the application to download
        :return: Tuple of filename and app direct download link
        """
        self.global_archs_priority = tuple(self._sort_by_priority(app.archs_to_build))
        version_page = app.download_source + "/versions"
        r = requests.get(version_page, headers=request_header, timeout=request_timeout)
        handle_request_response(r, version_page)
        soup = BeautifulSoup(r.text, bs4_parser)
        version_box_list = soup.select("ul.ver-wrap > *")
        for box in version_box_list:
            if (
                (_data := box.select_one("a.ver_download_link"))
                and (found_version := _data.get("data-dt-version"))
                and found_version == version
            ):
                download_page = _data.get("href")
                file_name, download_source = self.extract_download_link(download_page, app.app_name)  # type: ignore  # noqa: PGH003
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
