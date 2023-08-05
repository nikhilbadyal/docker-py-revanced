"""Class to represent apk to be patched."""
import concurrent
import hashlib
import pathlib
from concurrent.futures import ThreadPoolExecutor
from typing import Dict

from loguru import logger

from src.config import RevancedConfig
from src.utils import PatcherDownloadFailed, slugify


class APP(object):
    """Patched APK."""

    def __init__(self, app_name: str, config: RevancedConfig):
        self.app_name = app_name
        self.app_version = config.env.str(f"{app_name}_VERSION".upper(), None)
        self.experiment = False
        self.cli_dl = config.env.str(f"{app_name}_CLI_DL".upper(), config.global_cli_dl)
        self.patches_dl = config.env.str(
            f"{app_name}_PATCHES_DL".upper(), config.global_patches_dl
        )
        self.integrations_dl = config.env.str(
            f"{app_name}_INTEGRATION_DL".upper(), config.global_integrations_dl
        )
        self.exclude_request = config.env.list(f"EXCLUDE_PATCH_{app_name}".upper(), [])
        self.include_request = config.env.list(f"INCLUDE_PATCH_{app_name}".upper(), [])
        self.resource: Dict[str, str] = {}
        self.no_of_patches = 0
        self.download_patch_resources(config)

    def get_output_file_name(self) -> str:
        """Get output file appended with version."""
        return f"Re-{self.app_name}-{slugify(self.app_version)}.apk"

    def set_recommended_version(self, version: str, exp: bool = False) -> None:
        """Update if cooking non-recommended."""
        self.app_version = version
        self.experiment = exp

    def __str__(self: "APP") -> str:
        attrs = vars(self)
        return ", ".join("%s: %s" % item for item in attrs.items())

    @staticmethod
    def download(url: str, config: RevancedConfig, assets_filter: str = None) -> str:  # type: ignore
        """Downloader."""
        from src.downloader.download import Downloader

        url = url.strip()
        if url.startswith("https://github"):
            from src.downloader.github import Github

            url = Github.patch_resource(url, assets_filter)[0]
        extension = pathlib.Path(url).suffix
        file_name = APP.generate_filename(url) + extension
        Downloader(None, config).direct_download(url, file_name)  # type: ignore
        return file_name

    def download_patch_resources(self, config: RevancedConfig) -> None:
        """Download resource for patching."""
        logger.info("Downloading resources for patching.")
        # Create a list of resource download tasks
        download_tasks = [
            ("cli", self.cli_dl, config),
            ("integrations", self.integrations_dl, config),
            ("patches", self.patches_dl, config, ".*jar"),
            ("patches_json", self.patches_dl, config, ".*json"),
        ]

        # Using a ThreadPoolExecutor for parallelism
        with ThreadPoolExecutor() as executor:
            futures = {
                resource_name: executor.submit(self.download, *args)
                for resource_name, *args in download_tasks
            }

            # Wait for all tasks to complete
            concurrent.futures.wait(futures.values())

            # Retrieve results from completed tasks
            for resource_name, future in futures.items():
                try:
                    self.resource[resource_name] = future.result()
                except Exception as e:
                    raise PatcherDownloadFailed(f"An exception occurred: {e}")

    @staticmethod
    def generate_filename(url: str) -> str:
        """Get file name from url."""
        encoded_url: str = hashlib.sha256(url.encode()).hexdigest()
        return encoded_url
