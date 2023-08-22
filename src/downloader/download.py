"""Downloader Class."""
import os
import subprocess
from pathlib import Path
from queue import PriorityQueue
from time import perf_counter
from typing import Any, Tuple

from loguru import logger
from tqdm import tqdm

from src.config import RevancedConfig
from src.downloader.utils import implement_method
from src.exceptions import DownloadFailure
from src.patches import Patches
from src.utils import handle_request_response


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
        if not url:
            raise DownloadFailure("No url provided to download")
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
        handle_request_response(response)
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

    def extract_download_link(self, page: str, app: str) -> Tuple[str, str]:
        """Extract download link from web page."""
        raise NotImplementedError(implement_method)

    def specific_version(self, app: str, version: str) -> Tuple[str, str]:
        """Function to download the specified version of app from  apkmirror.

        :param app: Name of the application
        :param version: Version of the application to download
        :return: Version of downloaded apk
        """
        raise NotImplementedError(implement_method)

    def latest_version(self, app: str, **kwargs: Any) -> Tuple[str, str]:
        """Function to download the latest version of app.

        :param app: Name of the application
        :return: Version of downloaded apk
        """
        raise NotImplementedError(implement_method)

    def convert_to_apk(self, file_name: str) -> str:
        """Convert apks to apk."""
        if file_name.endswith(".apk"):
            return file_name
        output_apk_file = self.replace_file_extension(file_name, ".apk")
        output_path = f"{self.config.temp_folder}/{output_apk_file}"
        Path(output_path).unlink(missing_ok=True)
        subprocess.run(
            [
                "java",
                "-jar",
                f"{self.config.temp_folder}/{self.config.apk_editor}",
                "m",
                "-i",
                f"{self.config.temp_folder}/{file_name}",
                "-o",
                output_path,
            ],
            capture_output=True,
            check=True,
        )
        logger.info("Converted zip to apk.")
        return output_apk_file

    @staticmethod
    def replace_file_extension(filename: str, new_extension: str) -> str:
        """Replace the extension of a file."""
        base_name, _ = os.path.splitext(filename)
        return base_name + new_extension

    def download(self, version: str, app: str, **kwargs: Any) -> Tuple[str, str]:
        """Public function to download apk to patch.

        :param version: version to download
        :param app: App to download
        """
        if self.config.dry_run:
            return "", ""
        if app in self.config.existing_downloaded_apks:
            logger.debug(f"Will not download {app} -v{version} from the internet.")
            return app, f"local://{app}"
        if version and version != "latest":
            file_name, app_dl = self.specific_version(app, version)
        else:
            file_name, app_dl = self.latest_version(app, **kwargs)
        return self.convert_to_apk(file_name), app_dl

    def direct_download(self, dl: str, file_name: str) -> None:
        """Download from DL."""
        self._download(dl, file_name)
