"""Downloader Class."""
import os
from pathlib import Path
from queue import PriorityQueue
from time import perf_counter
from typing import Any, Tuple

from loguru import logger
from tqdm import tqdm

from src.config import RevancedConfig
from src.downloader.utils import implement_method
from src.patches import Patches
from src.utils import handle_response


class Downloader(object):
    """Files downloader."""

    def __init__(self, patcher: Patches, config: RevancedConfig):
        self._CHUNK_SIZE = 10485760
        self._QUEUE: PriorityQueue[Tuple[float, str]] = PriorityQueue()
        self._QUEUE_LENGTH = 0
        self.config = config
        self.patcher = patcher

    @staticmethod
    def file_status_check(file_name: Path, dry_run: bool, url: str) -> bool:
        """Check if file already exists."""
        if os.path.exists(file_name) or dry_run:
            logger.debug(
                f"Skipping download of {file_name} from {url}. File already exists or dry running."
            )
            return True
        return False

    def _download(self, url: str, file_name: str) -> None:
        if self.file_status_check(
            self.config.temp_folder.joinpath(file_name), self.config.dry_run, url
        ):
            return
        logger.info(f"Trying to download {file_name} from {url}")
        self._QUEUE_LENGTH += 1
        start = perf_counter()
        headers = {}
        if self.config.personal_access_token and "github" in url:
            logger.debug("Using personal access token")
            headers["Authorization"] = f"token {self.config.personal_access_token}"
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
        raise NotImplementedError(implement_method)

    def specific_version(self, app: str, version: str) -> None:
        """Function to download the specified version of app from  apkmirror.

        :param app: Name of the application
        :param version: Version of the application to download
        :return: Version of downloaded apk
        """
        raise NotImplementedError(implement_method)

    def latest_version(self, app: str, **kwargs: Any) -> None:
        """Function to download the latest version of app.

        :param app: Name of the application
        :return: Version of downloaded apk
        """
        raise NotImplementedError(implement_method)

    def download(self, version: str, app: str, **kwargs: Any) -> None:
        """Public function to download apk to patch.

        :param version: version to download
        :param app: App to download
        """
        if self.config.dry_run:
            return
        if app in self.config.existing_downloaded_apks:
            logger.debug(f"Will not download {app} -v{version} from the internet.")
            return
        if version and version != "latest":
            self.specific_version(app, version)
        else:
            self.latest_version(app, **kwargs)

    def direct_download(self, dl: str, file_name: str) -> None:
        """Download from DL."""
        self._download(dl, file_name)
