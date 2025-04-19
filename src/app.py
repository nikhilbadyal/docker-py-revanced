"""Class to represent apk to be patched."""

import concurrent
import hashlib
import pathlib
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any, Self

from loguru import logger
from pytz import timezone

from src.config import RevancedConfig
from src.downloader.sources import apk_sources
from src.exceptions import BuilderError, DownloadError, PatchingFailedError
from src.utils import slugify, time_zone


class APP(object):
    """Patched APK."""

    def __init__(self: Self, app_name: str, package_name: str, config: RevancedConfig) -> None:
        """Initialize APP.

        Args:
        ----
            app_name (str): Name of the app.
            config (RevancedConfig): Configuration object.
        """
        self.app_name = app_name
        self.app_version = config.env.str(f"{app_name}_VERSION".upper(), None)
        self.experiment = False
        self.cli_dl = config.env.str(f"{app_name}_CLI_DL".upper(), config.global_cli_dl)
        self.patches_dl = config.env.str(f"{app_name}_PATCHES_DL".upper(), config.global_patches_dl)
        self.exclude_request: list[str] = config.env.list(f"{app_name}_EXCLUDE_PATCH".upper(), [])
        self.include_request: list[str] = config.env.list(f"{app_name}_INCLUDE_PATCH".upper(), [])
        self.resource: dict[str, dict[str, str]] = {}
        self.no_of_patches: int = 0
        self.keystore_name = config.env.str(f"{app_name}_KEYSTORE_FILE_NAME".upper(), config.global_keystore_name)
        self.archs_to_build = config.env.list(f"{app_name}_ARCHS_TO_BUILD".upper(), config.global_archs_to_build)
        self.options_file = config.env.str(f"{app_name}_OPTIONS_FILE".upper(), config.global_options_file)
        self.download_file_name = ""
        self.download_dl = config.env.str(f"{app_name}_DL".upper(), "")
        self.download_source = config.env.str(f"{app_name}_DL_SOURCE".upper(), "")
        self.package_name = package_name
        self.old_key = config.env.bool(f"{app_name}_OLD_KEY".upper(), config.global_old_key)
        self.patches: list[dict[Any, Any]] = []
        self.space_formatted = config.env.bool(
            f"{app_name}_SPACE_FORMATTED_PATCHES".upper(),
            config.global_space_formatted,
        )

    def download_apk_for_patching(
        self: Self,
        config: RevancedConfig,
        download_cache: dict[tuple[str, str], tuple[str, str]],
    ) -> None:
        """Download apk to be patched, skipping if already downloaded (matching source and version)."""
        from src.downloader.download import Downloader
        from src.downloader.factory import DownloaderFactory

        if self.download_dl:
            logger.info("Downloading apk to be patched using provided dl")
            self.download_file_name = f"{self.app_name}.apk"
            Downloader(config).direct_download(self.download_dl, self.download_file_name)
        else:
            logger.info("Downloading apk to be patched by scrapping")
            try:
                if not self.download_source:
                    self.download_source = apk_sources[self.app_name.lower()].format(self.package_name)
            except KeyError as key:
                msg = f"App {self.app_name} not supported officially yet. Please provide download source in env."
                raise DownloadError(msg) from key

            cache_key = (self.download_source, self.app_version)

            if cache_key in download_cache:
                logger.info(f"Skipping download. Reusing APK from cache for {self.app_name} ({self.app_version})")
                self.download_file_name, self.download_dl = download_cache[cache_key]
                return

            downloader = DownloaderFactory.create_downloader(config=config, apk_source=self.download_source)
            self.download_file_name, self.download_dl = downloader.download(self.app_version, self)

            # Save to cache using (source, version) tuple
            download_cache[cache_key] = (self.download_file_name, self.download_dl)

    def get_output_file_name(self: Self) -> str:
        """The function returns a string representing the output file name.

        Returns
        -------
            a string that represents the output file name for an APK file.
        """
        current_date = datetime.now(timezone(time_zone))
        formatted_date = current_date.strftime("%Y%b%d.%I%M%p").upper()
        return f"Re{self.app_name}-Version{slugify(self.app_version)}-PatchVersion{slugify(self.resource["patches"]["version"])}-{formatted_date}-output.apk"  # noqa: E501

    def __str__(self: "APP") -> str:
        """Returns the str representation of the app."""
        attrs = vars(self)
        return ", ".join([f"{key}: {value}" for key, value in attrs.items()])

    def for_dump(self: Self) -> dict[str, Any]:
        """Convert the instance of this class to json."""
        return self.__dict__

    @staticmethod
    def download(url: str, config: RevancedConfig, assets_filter: str, file_name: str = "") -> tuple[str, str]:
        """The `download` function downloads a file from a given URL & filters the assets based on a given filter.

        Parameters
        ----------
        url : str
            The `url` parameter is a string that represents the URL of the resource you want to download.
        It can be a URL from GitHub or a local file URL.
        config : RevancedConfig
            The `config` parameter is an instance of the `RevancedConfig` class. It is used to provide
        configuration settings for the download process.
        assets_filter : str
            The `assets_filter` parameter is a string that is used to filter the assets to be downloaded
        from a GitHub repository. It is used when the `url` parameter starts with "https://github". The
        `assets_filter` string is matched against the names of the assets in the repository, and only
        file_name : str
            The `file_name` parameter is a string that represents the name of the file that will be
        downloaded. If no value is provided for `file_name`, the function will generate a filename based
        on the URL of the file being downloaded.

        Returns
        -------
            tuple of strings, which is the tag,file name of the downloaded file.
        """
        from src.downloader.download import Downloader

        url = url.strip()
        tag = "latest"
        if url.startswith("https://github"):
            from src.downloader.github import Github

            tag, url = Github.patch_resource(url, assets_filter, config)
            if tag.startswith("tags/"):
                tag = tag.split("/")[-1]
        elif url.startswith("local://"):
            return tag, url.split("/")[-1]
        if not file_name:
            extension = pathlib.Path(url).suffix
            file_name = APP.generate_filename(url) + extension
        Downloader(config).direct_download(url, file_name)
        return tag, file_name

    def download_patch_resources(
        self: Self,
        config: RevancedConfig,
        resource_cache: dict[str, tuple[str, str]],
    ) -> None:
        """The function `download_patch_resources` downloads various resources req. for patching.

        Parameters
        ----------
        config : RevancedConfig
            The `config` parameter is an instance of the `RevancedConfig` class. It is used to provide
        configuration settings for the resource download tasks.
        resource_cache: dict[str, tuple[str, str]]
        """
        logger.info("Downloading resources for patching.")

        download_tasks = [
            ("cli", self.cli_dl, config, ".*jar"),
            ("patches", self.patches_dl, config, ".*rvp"),
        ]

        with ThreadPoolExecutor(1) as executor:
            futures: dict[str, concurrent.futures.Future[tuple[str, str]]] = {}

            for resource_name, raw_url, cfg, assets_filter in download_tasks:
                url = raw_url.strip()
                if url in resource_cache:
                    logger.info(f"Skipping {resource_name} download, using cached resource: {url}")
                    tag, file_name = resource_cache[url]
                    self.resource[resource_name] = {
                        "file_name": file_name,
                        "version": tag,
                    }
                    continue

                futures[resource_name] = executor.submit(self.download, url, cfg, assets_filter)

            concurrent.futures.wait(futures.values())

            for resource_name, future in futures.items():
                try:
                    tag, file_name = future.result()
                    self.resource[resource_name] = {
                        "file_name": file_name,
                        "version": tag,
                    }
                    resource_cache[download_tasks[["cli", "patches"].index(resource_name)][1].strip()] = (
                        tag,
                        file_name,
                    )
                except BuilderError as e:
                    msg = f"Failed to download {resource_name} resource."
                    raise PatchingFailedError(msg) from e

    @staticmethod
    def generate_filename(url: str) -> str:
        """The function `generate_filename` takes URL as input and returns a hashed version of the URL as the filename.

        Parameters
        ----------
        url : str
            The `url` parameter is a string that represents a URL.

        Returns
        -------
            the encoded URL as a string.
        """
        encoded_url: str = hashlib.sha256(url.encode()).hexdigest()
        return encoded_url
