"""Class to represent apk to be patched."""
import concurrent
import hashlib
import pathlib
from concurrent.futures import ThreadPoolExecutor
from typing import Dict

from loguru import logger

from src.config import RevancedConfig
from src.exceptions import PatchingFailed
from src.utils import slugify


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
            f"{app_name}_INTEGRATIONS_DL".upper(), config.global_integrations_dl
        )
        self.patches_json_dl = config.env.str(
            f"{app_name}_PATCHES_JSON_DL".upper(), config.global_patches_json_dl
        )
        self.exclude_request = config.env.list(f"{app_name}_EXCLUDE_PATCH".upper(), [])
        self.include_request = config.env.list(f"{app_name}_INCLUDE_PATCH".upper(), [])
        self.resource: Dict[str, str] = {}
        self.no_of_patches = 0
        self.keystore_name = config.env.str(
            f"{app_name}_KEYSTORE_FILE_NAME".upper(), config.global_keystore_name
        )
        self.archs_to_build = config.env.list(
            f"{app_name}_ARCHS_TO_BUILD".upper(), config.global_archs_to_build
        )
        self.download_file_name = None
        self.download_dl = None
        self.download_patch_resources(config)

    def get_output_file_name(self) -> str:
        """The function returns a string representing the output file name for
        an APK file appended with version.

        Returns
        -------
            a string that represents the output file name for an APK file.
        """
        return f"Re-{self.app_name}-{slugify(self.app_version)}-output.apk"

    def set_recommended_version(self, version: str, exp: bool = False) -> None:
        """The function sets the recommended version and experiment flag for an
        app.

        Parameters
        ----------
        version : str
            The version parameter is a string that represents the recommended version of the app.
        exp : bool, optional
            The "exp" parameter is a boolean flag that indicates whether the specified version is for an
        experimental or regular release. If "exp" is set to True, it means the version is for an
        experimental release. If "exp" is set to False or not provided, it means the version is for
        """
        self.app_version = version
        self.experiment = exp

    def __str__(self: "APP") -> str:
        attrs = vars(self)
        return ", ".join([f"{key}: {value}" for key, value in attrs.items()])

    @staticmethod
    def download(
        url: str, config: RevancedConfig, assets_filter: str, file_name: str = ""
    ) -> str:
        """The `download` function downloads a file from a given URL using a
        specified configuration and filters the assets based on a given filter.

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
            a string, which is the file name of the downloaded file.
        """
        from src.downloader.download import Downloader

        url = url.strip()
        if url.startswith("https://github"):
            from src.downloader.github import Github

            url = Github.patch_resource(url, assets_filter, config)
        elif url.startswith("local://"):
            return url.split("/")[-1]
        if not file_name:
            extension = pathlib.Path(url).suffix
            file_name = APP.generate_filename(url) + extension
        Downloader(None, config).direct_download(url, file_name)  # type: ignore
        return file_name

    def download_patch_resources(self, config: RevancedConfig) -> None:
        """The function `download_patch_resources` downloads various resources
        for patching in parallel using a ThreadPoolExecutor.

        Parameters
        ----------
        config : RevancedConfig
            The `config` parameter is an instance of the `RevancedConfig` class. It is used to provide
        configuration settings for the resource download tasks.
        """
        logger.info("Downloading resources for patching.")
        # Create a list of resource download tasks
        download_tasks = [
            ("cli", self.cli_dl, config, ".*jar"),
            ("integrations", self.integrations_dl, config, ".*apk"),
            ("patches", self.patches_dl, config, ".*jar"),
            ("patches_json", self.patches_json_dl, config, ".*json"),
        ]

        # Using a ThreadPoolExecutor for parallelism
        with ThreadPoolExecutor(4) as executor:
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
                    raise PatchingFailed(e) from e

    @staticmethod
    def generate_filename(url: str) -> str:
        """The function `generate_filename` takes a URL as input and returns a
        hashed version of the URL as the filename.

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
