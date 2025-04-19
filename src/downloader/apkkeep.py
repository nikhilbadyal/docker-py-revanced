"""Apkeep Downloader Class."""

import subprocess
from time import perf_counter
from typing import Any, Self

from loguru import logger

from src.app import APP
from src.downloader.download import Downloader
from src.exceptions import DownloadError


class Apkeep(Downloader):
    """Apkeep-based Downloader."""

    def _run_apkeep(self: Self, package_name: str, version: str = "") -> str:
        """Run apkeep CLI to fetch APK from Google Play."""
        email = self.config.env.str("APKEEP_EMAIL")
        token = self.config.env.str("APKEEP_TOKEN")

        if not email or not token:
            msg = "APKEEP_EMAIL and APKEEP_TOKEN must be set in environment."
            raise DownloadError(msg)

        file_name = f"{package_name}.apk"
        file_path = self.config.temp_folder / file_name

        if file_path.exists():
            logger.debug(f"{file_name} already downloaded.")
            return file_name

        cmd = [
            "apkeep",
            "-a",
            f"{package_name}@{version}" if version and version != "latest" else package_name,
            "-d",
            "google-play",
            "-e",
            email,
            "-t",
            token,
            self.config.temp_folder_name,
        ]
        logger.debug(f"Running command: {cmd}")

        start = perf_counter()
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        output = process.stdout
        if not output:
            msg = "Failed to send request for patching."
            raise DownloadError(msg)
        for line in output:
            logger.debug(line.decode(), flush=True, end="")
        process.wait()
        if process.returncode != 0:
            msg = f"Command failed with exit code {process.returncode} for app {package_name}"
            raise DownloadError(msg)
        logger.info(f"Downloading completed for app {package_name} in {perf_counter() - start:.2f} seconds.")
        return file_name

    def latest_version(self: Self, app: APP, **kwargs: Any) -> tuple[str, str]:
        """Download latest version from Google Play via Apkeep."""
        file_name = self._run_apkeep(app.package_name)
        logger.info(f"Got file name as {file_name}")
        return file_name, f"apkeep://google-play/{app.package_name}"
