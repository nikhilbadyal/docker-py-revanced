"""Downloader Class."""
import os
from concurrent.futures import ThreadPoolExecutor
from queue import PriorityQueue
from time import perf_counter
from typing import Tuple

import requests
from loguru import logger
from tqdm import tqdm

from src.config import RevancedConfig
from src.patches import Patches
from src.utils import handle_response, update_changelog


class Downloader(object):
    """Files downloader."""

    def __init__(self, patcher: Patches, config: RevancedConfig):
        self._CHUNK_SIZE = 10485760
        self._QUEUE: PriorityQueue[Tuple[float, str]] = PriorityQueue()
        self._QUEUE_LENGTH = 0
        self.config = config
        self.patcher = patcher

    def _download(self, url: str, file_name: str) -> None:
        if os.path.exists(self.config.temp_folder.joinpath(file_name)):
            logger.debug(f"Skipping download of {file_name}. File already exists.")
            return
        logger.info(f"Trying to download {file_name} from {url}")
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
        """Extract download link from web page."""
        raise NotImplementedError("Please implement the method")

    def specific_version(self, app: str, version: str) -> None:
        """Function to download the specified version of app from  apkmirror.

        :param app: Name of the application
        :param version: Version of the application to download
        :return: Version of downloaded apk
        """
        raise NotImplementedError("Please implement the method")

    def latest_version(self, app: str) -> None:
        """Function to download the latest version of app.

        :param app: Name of the application
        :return: Version of downloaded apk
        """
        raise NotImplementedError("Please implement the method")

    def download(self, version: str, app: str) -> None:
        """Public function to download apk to patch.

        :param version: version to download
        :param app: App to download
        """
        if app in self.config.existing_downloaded_apks:
            logger.debug(f"Will not download {app} -v{version} from the internet.")
            return
        if version and version != "latest":
            self.specific_version(app, version)
        else:
            self.latest_version(app)

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
                ["inotia00", "mMicroG", "mMicroG-output.apk"],
            ]
        with ThreadPoolExecutor(7) as executor:
            executor.map(lambda repo: self.repository(*repo), assets)
        logger.info("Downloaded revanced microG ,cli, integrations and patches.")
