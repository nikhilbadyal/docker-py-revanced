"""Class to represent apk to be patched."""

import concurrent
import hashlib
import pathlib
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from threading import Lock
from typing import Any, Self
from zoneinfo import ZoneInfo

from loguru import logger

from src.config import RevancedConfig
from src.downloader.sources import APKEEP, apk_sources
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

        # Support multiple patch bundles via comma-separated URLs
        patches_dl_raw = config.env.str(f"{app_name}_PATCHES_DL".upper(), config.global_patches_dl)
        self.patches_dl_list = [url.strip() for url in patches_dl_raw.split(",") if url.strip()]
        # Keep backward compatibility
        self.patches_dl = patches_dl_raw

        self.exclude_request: list[str] = config.env.list(f"{app_name}_EXCLUDE_PATCH".upper(), [])
        self.include_request: list[str] = config.env.list(f"{app_name}_INCLUDE_PATCH".upper(), [])
        self.resource: dict[str, dict[str, str]] = {}
        self.patch_bundles: list[dict[str, str]] = []  # Store multiple patch bundles
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
        download_lock: Lock,
    ) -> None:
        """Download apk to be patched, skipping if already downloaded (matching source and version)."""
        from src.downloader.download import Downloader  # noqa: PLC0415
        from src.downloader.factory import DownloaderFactory  # noqa: PLC0415

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

            # Get unique cache key for this app
            cache_key = self.get_download_cache_key()

            # Optimistic cache check (outside lock for better performance)
            if cache_key in download_cache:
                logger.info(f"Skipping download. Reusing APK from cache for {self.app_name} ({self.app_version})")
                self.download_file_name, self.download_dl = download_cache[cache_key]
                return

            # Thread-safe cache check and download
            with download_lock:
                # Double-check after acquiring lock to handle race conditions
                if cache_key in download_cache:
                    logger.info(f"Skipping download. Reusing APK from cache for {self.app_name} ({self.app_version})")
                    self.download_file_name, self.download_dl = download_cache[cache_key]
                    return

                logger.info(f"Cache miss for {self.app_name} ({self.app_version}). Proceeding with download.")
                downloader = DownloaderFactory.create_downloader(config=config, apk_source=self.download_source)
                self.download_file_name, self.download_dl = downloader.download(self.app_version, self)

                # Save to cache using the unique cache key
                download_cache[cache_key] = (self.download_file_name, self.download_dl)
                logger.info(f"Added {self.app_name} ({self.app_version}) to download cache.")

    def get_download_cache_key(self: Self) -> tuple[str, str]:
        """Generate a unique cache key for APK downloads.

        For apkeep sources, includes package name to prevent cache collisions
        when multiple apps use the same version (e.g., "latest").

        Returns
        -------
            tuple[str, str]: Cache key as (source, identifier) where identifier
                            includes package name for apkeep sources.
        """
        version = self.app_version or "latest"

        if self.download_source == APKEEP:
            # Use package@version format for apkeep to ensure uniqueness
            return (self.download_source, f"{self.package_name}@{version}")

        # For URL-based sources, source+version is already unique
        return (self.download_source, version)

    def get_output_file_name(self: Self) -> str:
        """The function returns a string representing the output file name.

        Returns
        -------
            a string that represents the output file name for an APK file.
        """
        current_date = datetime.now(ZoneInfo(time_zone))
        formatted_date = current_date.strftime("%Y%b%d.%I%M%p").upper()
        return (
            f"Re{self.app_name}-Version{slugify(self.app_version)}"
            f"-PatchVersion{slugify(self.patch_bundles[0]["version"])}-{formatted_date}-output.apk"
        )

    def get_patch_bundles_versions(self: Self) -> list[str]:
        """Get versions of all patch bundles."""
        return [bundle["version"] for bundle in self.patch_bundles]

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
        from src.downloader.download import Downloader  # noqa: PLC0415

        url = url.strip()
        tag = "latest"
        if url.startswith("https://github"):
            from src.downloader.github import Github  # noqa: PLC0415

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

    def _setup_download_tasks(self: Self) -> list[tuple[str, str, None, str]]:
        """Setup download tasks for CLI and patch bundles."""
        download_tasks = [
            ("cli", self.cli_dl, None, ".*jar"),
        ]

        # Download multiple patch bundles
        for i, patches_url in enumerate(self.patches_dl_list):
            bundle_name = f"patches_{i}" if len(self.patches_dl_list) > 1 else "patches"
            download_tasks.append((bundle_name, patches_url, None, ".*rvp"))

        return download_tasks

    def _handle_cached_resource(self: Self, resource_name: str, tag: str, file_name: str) -> None:
        """Handle cached resource and update appropriate data structures."""
        if resource_name.startswith("patches"):
            self.patch_bundles.append(
                {
                    "name": resource_name,
                    "file_name": file_name,
                    "version": tag,
                },
            )
            # Keep backward compatibility for single bundle
            if resource_name == "patches" or len(self.patches_dl_list) == 1:
                self.resource["patches"] = {
                    "file_name": file_name,
                    "version": tag,
                }
        else:
            self.resource[resource_name] = {
                "file_name": file_name,
                "version": tag,
            }

    def _handle_downloaded_resource(
        self: Self,
        resource_name: str,
        tag: str,
        file_name: str,
        download_tasks: list[tuple[str, str, RevancedConfig, str]],
        resource_cache: dict[str, tuple[str, str]],
    ) -> None:
        """Handle newly downloaded resource and update cache."""
        self._handle_cached_resource(resource_name, tag, file_name)

        # Update cache for the corresponding URL
        for task_name, task_url, _, _ in download_tasks:
            if task_name == resource_name:
                resource_cache[task_url.strip()] = (tag, file_name)
                break

    def _prepare_download_tasks(
        self: Self,
        config: RevancedConfig,
    ) -> list[tuple[str, str, RevancedConfig, str]]:
        """Prepare download tasks with configuration."""
        base_tasks = self._setup_download_tasks()
        return [(name, url, config, filter_pattern) for name, url, _, filter_pattern in base_tasks]

    def _filter_cached_resources(
        self: Self,
        download_tasks: list[tuple[str, str, RevancedConfig, str]],
        resource_cache: dict[str, tuple[str, str]],
        resource_lock: Lock,
    ) -> list[tuple[str, str, RevancedConfig, str]]:
        """Filter out cached resources and handle cached ones."""
        resources_to_download: list[tuple[str, str, RevancedConfig, str]] = []

        with resource_lock:
            for resource_name, raw_url, cfg, assets_filter in download_tasks:
                url = raw_url.strip()
                if url in resource_cache:
                    logger.info(f"Skipping {resource_name} download, using cached resource: {url}")
                    tag, file_name = resource_cache[url]
                    self._handle_cached_resource(resource_name, tag, file_name)
                else:
                    resources_to_download.append((resource_name, url, cfg, assets_filter))

        return resources_to_download

    def _download_and_cache_resources(
        self: Self,
        resources_to_download: list[tuple[str, str, RevancedConfig, str]],
        download_tasks: list[tuple[str, str, RevancedConfig, str]],
        config: RevancedConfig,
        resource_cache: dict[str, tuple[str, str]],
        resource_lock: Lock,
    ) -> None:
        """Download resources in parallel and update cache thread-safely."""
        with ThreadPoolExecutor(config.max_resource_workers) as executor:
            futures: dict[str, concurrent.futures.Future[tuple[str, str]]] = {}

            for resource_name, url, cfg, assets_filter in resources_to_download:
                futures[resource_name] = executor.submit(self.download, url, cfg, assets_filter)

            concurrent.futures.wait(futures.values())
            self._update_resource_cache(futures, resources_to_download, download_tasks, resource_cache, resource_lock)

    def _update_resource_cache(
        self: Self,
        futures: dict[str, concurrent.futures.Future[tuple[str, str]]],
        resources_to_download: list[tuple[str, str, RevancedConfig, str]],
        download_tasks: list[tuple[str, str, RevancedConfig, str]],
        resource_cache: dict[str, tuple[str, str]],
        resource_lock: Lock,
    ) -> None:
        """Update resource cache with downloaded resources."""
        with resource_lock:
            for resource_name, future in futures.items():
                try:
                    tag, file_name = future.result()
                    corresponding_url = next(url for name, url, _, _ in resources_to_download if name == resource_name)
                    if corresponding_url not in resource_cache:
                        self._handle_downloaded_resource(
                            resource_name,
                            tag,
                            file_name,
                            download_tasks,
                            resource_cache,
                        )
                        logger.info(f"Added {resource_name} to resource cache: {corresponding_url}")
                    else:
                        logger.info(
                            f"Resource {resource_name} was already cached by another thread: {corresponding_url}",
                        )
                        cached_tag, cached_file_name = resource_cache[corresponding_url]
                        self._handle_cached_resource(resource_name, cached_tag, cached_file_name)
                except BuilderError as e:
                    msg = f"Failed to download {resource_name} resource."
                    raise PatchingFailedError(msg) from e

    def download_patch_resources(
        self: Self,
        config: RevancedConfig,
        resource_cache: dict[str, tuple[str, str]],
        resource_lock: Lock,
    ) -> None:
        """Download various resources required for patching.

        Parameters
        ----------
        config : RevancedConfig
            Configuration settings for the resource download tasks.
        resource_cache: dict[str, tuple[str, str]]
            Cache of previously downloaded resources.
        resource_lock: Lock
            Thread lock for safe access to resource_cache.
        """
        logger.info("Downloading resources for patching.")

        download_tasks = self._prepare_download_tasks(config)
        resources_to_download = self._filter_cached_resources(download_tasks, resource_cache, resource_lock)

        if resources_to_download:
            self._download_and_cache_resources(
                resources_to_download,
                download_tasks,
                config,
                resource_cache,
                resource_lock,
            )

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
