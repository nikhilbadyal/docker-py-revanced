"""Downloader Class."""

import os
import subprocess
from pathlib import Path
from queue import PriorityQueue
from time import perf_counter
from typing import Any, Self
from urllib.parse import urlparse
from uuid import uuid4

from loguru import logger
from requests import Session
from tqdm import tqdm

from src.app import APP
from src.config import RevancedConfig
from src.exceptions import DownloadError
from src.utils import handle_request_response, implement_method, request_timeout, session


class Downloader(object):
    """Files downloader."""

    def __init__(self: Self, config: RevancedConfig) -> None:
        self._CHUNK_SIZE = 10485760
        self._QUEUE: PriorityQueue[tuple[float, str]] = PriorityQueue()
        self._QUEUE_LENGTH = 0
        self.config = config
        self.global_archs_priority: Any = None
        self.app_version: Any = None

    @staticmethod
    def _existing_file_size(file_path: Path) -> int | None:
        """Return an existing artifact size when the final cache path is present."""
        # Returning None keeps the caller's branch explicit without overloading zero-byte files as "missing."
        if not file_path.exists():
            return None
        return file_path.stat().st_size

    @staticmethod
    def _existing_download_is_complete(existing_size: int | None, expected_size: int) -> bool:
        """Decide whether an existing artifact can be reused instead of redownloaded."""
        # Zero-byte files are always treated as broken because interrupted downloads commonly leave empty targets.
        if not existing_size:
            return False
        # Some endpoints omit content length, so a non-empty target is the best safe cache signal in that case.
        return not expected_size or existing_size == expected_size

    def _build_download_headers(self: Self, url: str, extra_headers: dict[str, str] | None) -> dict[str, str]:
        """Build request headers for authenticated and binary artifact downloads."""
        headers: dict[str, str] = {}
        if self.config.personal_access_token and "github" in url:
            logger.debug("Using personal access token")
            headers["Authorization"] = f"token {self.config.personal_access_token}"
        # GitLab's API uses a different personal-token header than GitHub's download endpoints.
        if self.config.personal_access_token and "gitlab" in url:
            logger.debug("Using personal access token")
            headers["PRIVATE-TOKEN"] = self.config.personal_access_token
        if urlparse(url).path.lower().endswith((".rvp", ".mpp")):
            # Patch bundle endpoints can use content negotiation, so direct downloads request raw binary bytes.
            headers["Accept"] = "application/octet-stream"
        # Caller-supplied headers, such as APKMirror Referer, intentionally override the generic defaults.
        if extra_headers:
            headers.update(extra_headers)
        return headers

    def _download(
        self: Self,
        url: str,
        file_name: str,
        http_session: Session | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        """Download a file from url to the configured temp folder.

        Parameters
        ----------
        url : str
            URL to download from.
        file_name : str
            Name of the file to save.
        http_session : Session | None
            Optional HTTP session to use for the request. Defaults to the shared
            plain requests.Session. Pass apkmirror_scraper for APKMirror URLs so
            that Cloudflare challenges are solved transparently.
        extra_headers : dict[str, str] | None
            Optional additional headers merged on top of the default headers (e.g.
            a Referer for APKMirror file downloads to satisfy Cloudflare checks).
        """
        if not url:
            msg = "No url provided to download"
            raise DownloadError(msg)
        # Resolve the final target once so existence, size checks, and atomic publishing all reference the same path.
        file_path = self.config.temp_folder.joinpath(file_name)
        if self.config.dry_run:
            logger.debug(f"Skipping download of {file_name} from {url}. Dry run is enabled.")
            return

        # Use the caller-supplied session (e.g. cloudscraper for APKMirror) or
        # fall back to the module-level plain requests session.
        effective_session = http_session if http_session is not None else session

        response = effective_session.get(
            url,
            stream=True,
            headers=self._build_download_headers(url, extra_headers),
            # External artifact hosts occasionally hang; bounded requests let CI fail and retry instead of timing out.
            timeout=request_timeout,
        )
        handle_request_response(response, url)
        total = int(response.headers.get("content-length", 0))

        if not self.config.disable_caching:
            # An interrupted parallel worker can leave a partial artifact, so size must match before reuse.
            existing_size = self._existing_file_size(file_path)
            if self._existing_download_is_complete(existing_size, total):
                logger.debug(f"Skipping download of {file_name} from {url}. File already exists with expected size.")
                response.close()
                return
            if existing_size is not None:
                logger.warning(
                    f"Re-downloading {file_name} from {url}; "
                    f"existing size {existing_size} differs from expected {total}.",
                )
        elif file_path.exists():
            # DISABLE_CACHING means the caller wants a fresh artifact even when a same-sized file is already present.
            logger.debug(f"Ignoring cached {file_name} because caching is disabled.")

        logger.info(f"Trying to download {file_name} from {url}")
        self._QUEUE_LENGTH += 1
        start = perf_counter()
        bar = tqdm(
            desc=file_name,
            total=total,
            unit="iB",
            unit_scale=True,
            unit_divisor=1024,
            colour="green",
        )
        # Each worker writes to a unique temp file so another thread can never observe a half-written final artifact.
        partial_file_path = file_path.with_name(f".{file_path.name}.{uuid4().hex}.part")
        try:
            with partial_file_path.open("wb") as dl_file, bar:
                for chunk in response.iter_content(self._CHUNK_SIZE):
                    size = dl_file.write(chunk)
                    bar.update(size)
            # Atomic replace publishes the completed download only after all bytes are written.
            partial_file_path.replace(file_path)
        except Exception:
            # Failed downloads should not poison the cache path for the next retry.
            partial_file_path.unlink(missing_ok=True)
            raise
        finally:
            # Closing the streamed response releases the connection after body copy or write failure.
            response.close()
        self._QUEUE.put((perf_counter() - start, file_name))
        logger.debug(f"Downloaded {file_name}")

    def extract_download_link(self: Self, page: str, app: str) -> tuple[str, str]:
        """Extract download link from web page."""
        raise NotImplementedError(implement_method)

    def specific_version(self: Self, app: "APP", version: str) -> tuple[str, str]:
        """Function to download the specified version of app..

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
        if app.app_name in self.config.existing_downloaded_apks:
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
