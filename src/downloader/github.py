"""Github Downloader."""

import re
from typing import Self
from urllib.parse import urlparse

import requests
from lastversion import latest
from loguru import logger

from src.app import APP
from src.config import RevancedConfig
from src.downloader.download import Downloader
from src.exceptions import DownloadError
from src.utils import handle_request_response, request_timeout, update_changelog


class Github(Downloader):
    """Files downloader."""

    def latest_version(self: Self, app: APP, **kwargs: dict[str, str]) -> tuple[str, str]:
        """Function to download files from GitHub repositories.

        :param app: App to download
        """
        logger.debug(f"Trying to download {app.app_name} from github")
        if self.config.dry_run:
            logger.debug(f"Skipping download of {app.app_name}. File already exists or dry running.")
            return app.app_name, f"local://{app.app_name}"
        owner = str(kwargs["owner"])
        repo_name = str(kwargs["name"])
        repo_url = f"https://api.github.com/repos/{owner}/{repo_name}/releases/latest"
        headers = {
            "Content-Type": "application/vnd.github.v3+json",
        }
        if self.config.personal_access_token:
            logger.debug("Using personal access token")
            headers["Authorization"] = f"Bearer {self.config.personal_access_token}"
        response = requests.get(repo_url, headers=headers, timeout=request_timeout)
        handle_request_response(response, repo_url)
        if repo_name == "revanced-patches":
            download_url = response.json()["assets"][1]["browser_download_url"]
        else:
            download_url = response.json()["assets"][0]["browser_download_url"]
        update_changelog(f"{owner}/{repo_name}", response.json())
        self._download(download_url, file_name=app.app_name)
        return app.app_name, download_url

    @staticmethod
    def _extract_repo_owner_and_tag(url: str) -> tuple[str, str, str]:
        """Extract repo owner and url from github url."""
        parsed_url = urlparse(url)
        path_segments = parsed_url.path.strip("/").split("/")

        github_repo_owner = path_segments[0]
        github_repo_name = path_segments[1]
        tag_position = 3
        if len(path_segments) > tag_position and path_segments[3] == "latest-prerelease":
            logger.info(f"Including pre-releases/beta for {github_repo_name} selection.")
            latest_tag = str(latest(f"{github_repo_owner}/{github_repo_name}", output_format="tag", pre_ok=True))
            release_tag = f"tags/{latest_tag}"
        else:
            release_tag = next(
                (f"tags/{path_segments[i + 1]}" for i, segment in enumerate(path_segments) if segment == "tag"),
                "latest",
            )
        return github_repo_owner, github_repo_name, release_tag

    @staticmethod
    def _get_release_assets(
        github_repo_owner: str,
        github_repo_name: str,
        release_tag: str,
        asset_filter: str,
        config: RevancedConfig,
    ) -> tuple[str, str]:
        """Get assets from given tag."""
        api_url = f"https://api.github.com/repos/{github_repo_owner}/{github_repo_name}/releases/{release_tag}"
        headers = {
            "Content-Type": "application/vnd.github.v3+json",
        }
        if config.personal_access_token:
            headers["Authorization"] = f"Bearer {config.personal_access_token}"
        response = requests.get(api_url, headers=headers, timeout=request_timeout)
        handle_request_response(response, api_url)
        update_changelog(f"{github_repo_owner}/{github_repo_name}", response.json())
        assets = response.json()["assets"]
        try:
            filter_pattern = re.compile(asset_filter)
        except re.error as e:
            msg = f"Invalid regex {asset_filter} pattern provided."
            raise DownloadError(msg) from e
        for asset in assets:
            assets_url = asset["browser_download_url"]
            assets_name = asset["name"]
            if match := filter_pattern.search(assets_url):
                logger.debug(f"Found {assets_name} to be downloaded from {assets_url}")
                return response.json()["tag_name"], match.group()
        return "", ""

    @staticmethod
    def patch_resource(repo_url: str, assets_filter: str, config: RevancedConfig) -> tuple[str, str]:
        """Fetch patch resource from repo url."""
        repo_owner, repo_name, latest_tag = Github._extract_repo_owner_and_tag(repo_url)
        return Github._get_release_assets(repo_owner, repo_name, latest_tag, assets_filter, config)
