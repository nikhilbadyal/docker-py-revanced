"""Github Downloader."""
from typing import Dict, List

import requests
from lastversion import latest
from loguru import logger

from src.downloader.download import Downloader
from src.utils import handle_response, update_changelog


class Github(Downloader):
    """Files downloader."""

    def latest_version(self, app: str, **kwargs: Dict[str, str]) -> None:
        """Function to download files from GitHub repositories.

        :param app: App to download
        """
        logger.debug(f"Trying to download {app} from github")
        if self.config.dry_run or app == "microg":
            logger.debug(
                f"Skipping download of {app}. File already exists or dry running."
            )
            return
        owner = str(kwargs["owner"])
        repo_name = str(kwargs["name"])
        repo_url = f"https://api.github.com/repos/{owner}/{repo_name}/releases/latest"
        headers = {
            "Content-Type": "application/vnd.github.v3+json",
        }
        if self.config.personal_access_token:
            logger.debug("Using personal access token")
            headers["Authorization"] = f"token {self.config.personal_access_token}"
        response = requests.get(repo_url, headers=headers)
        handle_response(response)
        if repo_name == "revanced-patches":
            download_url = response.json()["assets"][1]["browser_download_url"]
        else:
            download_url = response.json()["assets"][0]["browser_download_url"]
        update_changelog(f"{owner}/{repo_name}", response.json())
        self._download(download_url, file_name=app)

    @staticmethod
    def patch_resource(repo_url: str, assets_filter: str) -> list[str]:
        """Fetch patch resource from repo url."""
        latest_resource_version: List[str] = latest(
            repo_url, assets_filter=assets_filter, output_format="assets"
        )
        return latest_resource_version
