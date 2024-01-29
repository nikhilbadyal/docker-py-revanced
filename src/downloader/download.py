"""Downloader Class."""

import os
import subprocess
from pathlib import Path
from queue import PriorityQueue
from time import perf_counter
from typing import Any, Self

from loguru import logger
from tqdm import tqdm

from src.app import APP
from src.config import RevancedConfig
from src.downloader.utils import implement_method
from src.exceptions import DownloadError
from src.utils import handle_request_response, session


class Downloader(object):
    """Files downloader."""

    def __init__(self: Self, config: RevancedConfig) -> None:
        self._CHUNK_SIZE = 10485760
        self._QUEUE: PriorityQueue[tuple[float, str]] = PriorityQueue()
        self._QUEUE_LENGTH = 0
        self.config = config

    def _download(self: Self, url: str, file_name: str) -> None:
        if not url:
            msg = "No url provided to download"
            raise DownloadError(msg)
        if self.config.dry_run or self.config.temp_folder.joinpath(file_name).exists():
            logger.debug(f"Skipping download of {file_name} from {url}. File already exists or dry running.")
            return
        logger.info(f"Trying to download {file_name} from {url}")
        self._QUEUE_LENGTH += 1
        start = perf_counter()
        headers = {}
        if self.config.personal_access_token and "github" in url:
            logger.debug("Using personal access token")
            headers["Authorization"] = f"token {self.config.personal_access_token}"
        response = session.get(
            url,
            stream=True,
            headers=headers,
        )
        handle_request_response(response, url)
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

    def extract_download_link(self: Self, page: str, app: str) -> tuple[str, str]:
        """Extract download link from web page."""
        raise NotImplementedError(implement_method)

    def specific_version(self: Self, app: APP, version: str) -> tuple[str, str]:
        """Function to download the specified version of app from  apkmirror.

        :param app: Name of the application
        :param version: Version of the application to download
        :return: Version of downloaded apk
        """
        raise NotImplementedError(implement_method)

    def latest_version(self: Self, app: APP, **kwargs: Any) -> tuple[str, str]:
        """Function to download the latest version of app.

        :param app: Name of the application
        :return: Version of downloaded apk
        """
        raise NotImplementedError(implement_method)

    def convert_to_apk(self: Self, file_name: str) -> str:
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

    def download(self: Self, version: str, app: APP, **kwargs: Any) -> tuple[str, str]:
        """Public function to download apk to patch.

        :param version: version to download
        :param app: App to download
        """
        if self.config.dry_run:
            return "", ""
        if app in self.config.existing_downloaded_apks:
            logger.debug(f"Will not download {app.app_name} -v{version} from the internet.")
            return app.app_name, f"local://{app.app_name}"
        if version and version != "latest":
            file_name, app_dl = self.specific_version(app, version)
        else:
            file_name, app_dl = self.latest_version(app, **kwargs)
        return self.convert_to_apk(file_name), app_dl

    def direct_download(self: Self, dl: str, file_name: str) -> None:
        """Download from DL."""
        self._download(dl, file_name)

    @staticmethod
    def extra_downloads(config: RevancedConfig) -> None:
        """The function `extra_downloads` downloads extra files specified.

        Parameters
        ----------
        config : RevancedConfig
            The `config` parameter is an instance of the `RevancedConfig` class. It is used to provide
        configuration settings for the download process.
        """
        try:
            for extra in config.extra_download_files:
                url, file_name = extra.split("@")
                file_name_without_extension, file_extension = os.path.splitext(file_name)
                new_file_name = f"{file_name_without_extension}-output{file_extension}"
                APP.download(
                    url,
                    config,
                    assets_filter=f".*{file_extension}",
                    file_name=new_file_name,
                )
        except (ValueError, IndexError):
            logger.info("Unable to download extra file. Provide input in url@name.apk format.")
