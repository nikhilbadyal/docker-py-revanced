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
from src.utils import update_changelog


class Downloader(object):
    """Files downloader."""

    def __init__(self, config: RevancedConfig):
        self._CHUNK_SIZE = 10485760
        self._QUEUE: PriorityQueue[Tuple[float, str]] = PriorityQueue()
        self._QUEUE_LENGTH = 0
        self.config = config
        self.download_revanced()

    def _download(self, url: str, file_name: str) -> None:
        logger.debug(f"Trying to download {file_name} from {url}")
        self._QUEUE_LENGTH += 1
        start = perf_counter()
        resp = self.config.session.get(url, stream=True)
        total = int(resp.headers.get("content-length", 0))
        bar = tqdm(
            desc=file_name,
            total=total,
            unit="iB",
            unit_scale=True,
            unit_divisor=1024,
            colour="green",
        )
        with self.config.temp_folder.joinpath(file_name).open("wb") as dl_file, bar:
            for chunk in resp.iter_content(self._CHUNK_SIZE):
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
            if "APK" in is_apm.text():
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
        page = "https://spotify.en.uptodown.com/android/download"
        parser = LexborHTMLParser(self.config.session.get(page).text)
        main_page = parser.css_first("#detail-download-button")
        download_url = main_page.attributes["data-url"]
        app_version: str = parser.css_first(".version").text()
        self._download(download_url, "spotify.apk")
        logger.debug(f"Downloaded {app} apk from apkmirror_specific_version in rt")
        return app_version

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
        main_page = parser.css_first(".appRowVariantTag>.accent_color").attributes[
            "href"
        ]
        match = re.search(r"\d", main_page)
        if not match:
            logger.error("Cannot find app main page")
            sys.exit(-1)
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
        r = requests.get(
            repo_url, headers={"Content-Type": "application/vnd.github.v3+json"}
        )
        if name == "revanced-patches":
            download_url = r.json()["assets"][1]["browser_download_url"]
        else:
            download_url = r.json()["assets"][0]["browser_download_url"]
        update_changelog(f"{owner}/{name}", r.json())
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

    def download_apk_to_patch(self, version: str, app: str) -> str:
        """Public function to download apk to patch.

        :param version: version to download
        :param app: App to download
        :return: Version of apk
        """
        if app in self.config.upto_down:
            return self.upto_down_downloader(app)
        else:
            return self.download_from_apkmirror(version, app)
