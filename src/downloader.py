"""Downloader Class."""
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from queue import PriorityQueue
from time import perf_counter
from typing import Tuple

import requests
from loguru import logger
from selectolax.lexbor import LexborHTMLParser
from tqdm import tqdm

from src.config import RevancedConfig
from src.patches import Patches
from src.utils import AppNotFound, handle_response, update_changelog


class Downloader(object):
    """Files downloader."""

    def __init__(self, patcher: Patches, config: RevancedConfig):
        self._CHUNK_SIZE = 10485760
        self._QUEUE: PriorityQueue[Tuple[float, str]] = PriorityQueue()
        self._QUEUE_LENGTH = 0
        self.config = config
        self.download_revanced()
        self.patcher = patcher

    def _download(self, url: str, file_name: str) -> None:
        logger.debug(f"Trying to download {file_name} from {url}")
        self._QUEUE_LENGTH += 1
        start = perf_counter()
        headers = {}
        if self.config.personal_access_token and "github" in url:
            logger.debug("Using personal access token")
            headers.update(
                {"Authorization": "token " + self.config.personal_access_token}
            )
        response = self.config.session.get(
            url,
            stream=True,
            headers=headers,
        )
        handle_response(response)
        total = int(response.headers.get("content-length", 0))
        bar = tqdm(
            desc=file_name,
            total=total,
            unit="iB",
            unit_scale=True,
            unit_divisor=1024,
            colour="green",
        )
        with self.config.temp_folder.joinpath(file_name).open("wb") as dl_file, bar:
            for chunk in response.iter_content(self._CHUNK_SIZE):
                size = dl_file.write(chunk)
                bar.update(size)
        self._QUEUE.put((perf_counter() - start, file_name))
        logger.debug(f"Downloaded {file_name}")

    def extract_download_link(self, page: str, app: str) -> None:
        """Function to extract the download link from apkmirror html page.

        :param page: Url of the page
        :param app: Name of the app
        """
        logger.debug(f"Extracting download link from\n{page}")
        parser = LexborHTMLParser(self.config.session.get(page).text)

        resp = self.config.session.get(
            self.config.apk_mirror + parser.css_first("a.accent_bg").attributes["href"]
        )
        parser = LexborHTMLParser(resp.text)

        href = parser.css_first(
            "p.notes:nth-child(3) > span:nth-child(1) > a:nth-child(1)"
        ).attributes["href"]
        self._download(self.config.apk_mirror + href, f"{app}.apk")
        logger.debug("Finished Extracting link and downloading")

    def get_download_page(self, parser: LexborHTMLParser, main_page: str) -> str:
        """Function to get the download page in apk_mirror.

        :param parser: Parser
        :param main_page: Main Download Page in APK mirror(Index)
        :return:
        """
        apm = parser.css(".apkm-badge")
        sub_url = ""
        for is_apm in apm:
            parent_text = is_apm.parent.parent.text()
            if "APK" in is_apm.text() and (
                "arm64-v8a" in parent_text
                or "universal" in parent_text
                or "noarch" in parent_text
            ):
                parser = is_apm.parent
                sub_url = parser.css_first(".accent_color").attributes["href"]
                break
        if sub_url == "":
            logger.exception(
                f"Unable to find any apk on apkmirror_specific_version on {main_page}"
            )
            sys.exit(-1)
        download_url = self.config.apk_mirror + sub_url
        return download_url

    def __upto_down_downloader(self, app: str) -> str:
        page = f"https://{app}.en.uptodown.com/android/download"
        parser = LexborHTMLParser(self.config.session.get(page).text)
        main_page = parser.css_first("#detail-download-button")
        download_url = main_page.attributes["data-url"]
        app_version: str = parser.css_first(".version").text()
        self._download(download_url, f"{app}.apk")
        logger.debug(f"Downloaded {app} apk from upto_down_downloader in rt")
        return app_version

    def __apk_pure_downloader(self, app: str) -> str:
        package_name = None
        for package, app_tuple in self.patcher.revanced_app_ids.items():
            if app_tuple[0] == app:
                package_name = package
        if not package_name:
            logger.info("Unable to download from apkpure")
            raise AppNotFound()
        download_url = f"https://d.apkpure.com/b/APK/{package_name}?version=latest"
        self._download(download_url, f"{app}.apk")
        logger.debug(f"Downloaded {app} apk from apk_pure_downloader in rt")
        return "latest"

    def __apk_sos_downloader(self, app: str) -> str:
        package_name = None
        for package, app_tuple in self.patcher.revanced_app_ids.items():
            if app_tuple[0] == app:
                package_name = package
        if not package_name:
            logger.info("Unable to download from apkcombo")
            raise AppNotFound()
        download_url = f"https://apksos.com/download-app/{package_name}"
        parser = LexborHTMLParser(self.config.session.get(download_url).text)
        download_url = parser.css_first(
            r"body > div > div > div > div > div.col-sm-12.col-md-8 > div.card.fluid.\.idma > "
            "div.section.row > div.col-sm-12.col-md-8.text-center > p > a"
        ).attributes["href"]
        self._download(download_url, f"{app}.apk")
        logger.debug(f"Downloaded {app} apk from apk_combo_downloader in rt")
        return "latest"

    def apkmirror_specific_version(self, app: str, version: str) -> str:
        """Function to download the specified version of app from  apkmirror.

        :param app: Name of the application
        :param version: Version of the application to download
        :return: Version of downloaded apk
        """
        logger.debug(f"Trying to download {app},specific version {version}")
        version = version.replace(".", "-")
        main_page = f"{self.config.apk_mirror_version_urls.get(app)}-{version}-release/"
        parser = LexborHTMLParser(self.config.session.get(main_page).text)
        download_page = self.get_download_page(parser, main_page)
        self.extract_download_link(download_page, app)
        logger.debug(f"Downloaded {app} apk from apkmirror_specific_version")
        return version

    def apkmirror_latest_version(self, app: str) -> str:
        """Function to download whatever the latest version of app from
        apkmirror.

        :param app: Name of the application
        :return: Version of downloaded apk
        """
        logger.debug(f"Trying to download {app}'s latest version from apkmirror")
        page = self.config.apk_mirror_urls.get(app)
        if not page:
            logger.debug("Invalid app")
            sys.exit(1)
        parser = LexborHTMLParser(self.config.session.get(page).text)
        try:
            main_page = parser.css_first(".appRowVariantTag>.accent_color").attributes[
                "href"
            ]
        except AttributeError:
            # Handles a case when variants are not available
            main_page = parser.css_first(".downloadLink").attributes["href"]
        match = re.search(r"\d", main_page)
        if not match:
            logger.error("Cannot find app main page")
            raise AppNotFound()
        int_version = match.start()
        extra_release = main_page.rfind("release") - 1
        version: str = main_page[int_version:extra_release]
        version = version.replace("-", ".")
        main_page = f"{self.config.apk_mirror}{main_page}"
        parser = LexborHTMLParser(self.config.session.get(main_page).text)
        download_page = self.get_download_page(parser, main_page)
        self.extract_download_link(download_page, app)
        logger.debug(f"Downloaded {app} apk from apkmirror_specific_version in rt")
        return version

    def repository(self, owner: str, name: str, file_name: str) -> None:
        """Function to download files from GitHub repositories.

        :param owner: github user/organization
        :param name: name of the repository
        :param file_name: name of the file after downloading
        """
        logger.debug(f"Trying to download {name} from github")
        repo_url = f"https://api.github.com/repos/{owner}/{name}/releases/latest"
        headers = {
            "Content-Type": "application/vnd.github.v3+json",
        }
        if self.config.personal_access_token:
            logger.debug("Using personal access token")
            headers.update(
                {"Authorization": "token " + self.config.personal_access_token}
            )
        response = requests.get(repo_url, headers=headers)
        handle_response(response)
        if name == "revanced-patches":
            download_url = response.json()["assets"][1]["browser_download_url"]
        else:
            download_url = response.json()["assets"][0]["browser_download_url"]
        update_changelog(f"{owner}/{name}", response.json())
        self._download(download_url, file_name=file_name)

    def download_revanced(self) -> None:
        """Download Revanced and Extended Patches, Integration and CLI."""
        if os.path.exists("changelog.md"):
            logger.debug("Deleting old changelog.md")
            os.remove("changelog.md")
        assets = [
            ["revanced", "revanced-cli", self.config.normal_cli_jar],
            ["revanced", "revanced-integrations", self.config.normal_integrations_apk],
            ["revanced", "revanced-patches", self.config.normal_patches_jar],
        ]
        if self.config.build_extended:
            assets += [
                ["inotia00", "revanced-cli", self.config.cli_jar],
                ["inotia00", "revanced-integrations", self.config.integrations_apk],
                ["inotia00", "revanced-patches", self.config.patches_jar],
            ]
        if "youtube" in self.config.apps or "youtube_music" in self.config.apps:
            assets += [
                ["inotia00", "VancedMicroG", "VancedMicroG-output.apk"],
            ]
        with ThreadPoolExecutor(7) as executor:
            executor.map(lambda repo: self.repository(*repo), assets)
        logger.info("Downloaded revanced microG ,cli, integrations and patches.")

    def upto_down_downloader(self, app: str) -> str:
        """Function to download from UptoDown.

        :param app: Name of the application
        :return: Version of downloaded APK
        """
        return self.__upto_down_downloader(app)

    def apk_pure_downloader(self, app: str) -> str:
        """Function to download from Apk Pure.

        :param app: Name of the application
        :return: Version of downloaded APK
        """
        return self.__apk_pure_downloader(app)

    def download_from_apkmirror(self, version: str, app: str) -> str:
        """Function to download from apkmirror.

        :param version: version to download
        :param app: App to download
        :return: Version of downloaded APK
        """
        if version and version != "latest":
            return self.apkmirror_specific_version(app, version)
        else:
            return self.apkmirror_latest_version(app)

    def apk_sos_downloader(self, app: str) -> str:
        """Function to download from Apk Pure.

        :param app: Name of the application
        :return: Version of downloaded APK
        """
        return self.__apk_sos_downloader(app)

    def download_apk_to_patch(self, version: str, app: str) -> str:
        """Public function to download apk to patch.

        :param version: version to download
        :param app: App to download
        :return: Version of apk.
        """
        if app in self.config.existing_downloaded_apks:
            logger.debug("Will not download apk from the internet as it already exist.")
            # Returning Latest as I don't know, which version user provided.
            return "latest"
        if app in self.config.upto_down:
            return self.upto_down_downloader(app)
        elif app in self.config.apk_pure:
            return self.apk_pure_downloader(app)
        elif app in self.config.apk_sos:
            return self.apk_sos_downloader(app)
        else:
            return self.download_from_apkmirror(version, app)
