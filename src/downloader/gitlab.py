"""GitLab release downloader."""

import re
from collections.abc import Iterator
from typing import Any, Self
from urllib.parse import quote, urlparse

import requests
from loguru import logger

from src.app import APP
from src.config import RevancedConfig
from src.downloader.download import Downloader
from src.exceptions import DownloadError
from src.utils import handle_request_response, request_timeout, update_changelog


class Gitlab(Downloader):
    """Files downloader for GitLab release assets."""

    MIN_PROJECT_SEGMENTS = 2  # GitLab project paths need at least namespace/project.
    RELEASE_VALUE_POSITION = 2  # Release path values begin after the `releases/<kind>` prefix.
    LATEST_RELEASE = "permalink/latest"  # GitLab exposes latest release through a permanent API path.
    LATEST_PRERELEASE = "latest-prerelease"  # Keep GitHub-compatible config syntax even though GitLab has no flag.

    def latest_version(self: Self, app: APP, **kwargs: dict[str, str]) -> tuple[str, str]:
        """Download the latest APK-like release asset from a GitLab project source.

        GitHub source downloads historically select a release asset automatically.
        GitLab gets the same operational behavior by selecting an APK asset from
        the latest release when users provide an app download source.
        """
        logger.debug(f"Trying to download {app.app_name} from gitlab")
        if self.config.dry_run:
            logger.debug(f"Skipping download of {app.app_name}. File already exists or dry running.")
            return app.app_name, f"local://{app.app_name}"
        _, download_url = self.patch_resource(app.download_source, ".*apk", self.config)
        self._download(download_url, file_name=app.app_name)
        return app.app_name, download_url

    @staticmethod
    def is_gitlab_url(url: str) -> bool:
        """Return whether the URL should use GitLab release API handling."""
        parsed_url = urlparse(url)
        host = parsed_url.netloc.lower()
        return parsed_url.scheme in {"http", "https"} and (host == "gitlab.com" or host.startswith("gitlab."))

    @staticmethod
    def _extract_project_and_tag(url: str) -> tuple[str, str, str]:
        """Extract GitLab API base URL, project path, and release reference from a GitLab URL."""
        parsed_url = urlparse(url)
        path_segments = [segment for segment in parsed_url.path.strip("/").split("/") if segment]
        project_segments, release_segments = Gitlab._split_project_and_release_segments(path_segments)
        if len(project_segments) < Gitlab.MIN_PROJECT_SEGMENTS:
            msg = f"Invalid GitLab URL format: {url}"
            raise DownloadError(msg)
        release_ref = Gitlab._extract_release_ref(release_segments)
        return f"{parsed_url.scheme}://{parsed_url.netloc}", "/".join(project_segments), release_ref

    @staticmethod
    def _split_project_and_release_segments(path_segments: list[str]) -> tuple[list[str], list[str]]:
        """Split GitLab project path segments from UI or GitHub-like release path segments."""
        if "-" in path_segments:
            marker_position = path_segments.index("-")
            return path_segments[:marker_position], path_segments[marker_position + 1 :]
        if "releases" in path_segments:
            marker_position = path_segments.index("releases")
            return path_segments[:marker_position], path_segments[marker_position:]
        return path_segments, []

    @staticmethod
    def _extract_release_ref(release_segments: list[str]) -> str:
        """Map GitLab UI release path segments onto the matching GitLab API release reference."""
        if not release_segments or release_segments[0] != "releases" or len(release_segments) == 1:
            return Gitlab.LATEST_RELEASE
        release_ref = release_segments[1]
        if (
            release_ref == "permalink"
            and len(release_segments) > Gitlab.RELEASE_VALUE_POSITION
            and release_segments[Gitlab.RELEASE_VALUE_POSITION] == "latest"
        ):
            return Gitlab.LATEST_RELEASE
        if release_ref in {"latest", Gitlab.LATEST_PRERELEASE}:
            if release_ref == Gitlab.LATEST_PRERELEASE:
                logger.info("GitLab releases do not expose a prerelease flag; selecting the latest release by date.")
            return Gitlab.LATEST_RELEASE
        if release_ref == "tag" and len(release_segments) > Gitlab.RELEASE_VALUE_POSITION:
            return "/".join(release_segments[Gitlab.RELEASE_VALUE_POSITION :])
        return "/".join(release_segments[1:])

    @staticmethod
    def _get_headers(config: RevancedConfig) -> dict[str, str]:
        """Build GitLab API headers using GitLab's documented token header."""
        headers = {
            "Content-Type": "application/json",
        }
        if config.personal_access_token:
            headers["PRIVATE-TOKEN"] = config.personal_access_token
        return headers

    @staticmethod
    def _get_release_api_url(base_url: str, project_path: str, release_ref: str) -> str:
        """Build the GitLab release API URL for latest or tagged release lookups."""
        project_id = quote(project_path, safe="")
        if release_ref == Gitlab.LATEST_RELEASE:
            return f"{base_url}/api/v4/projects/{project_id}/releases/{Gitlab.LATEST_RELEASE}"
        return f"{base_url}/api/v4/projects/{project_id}/releases/{quote(release_ref, safe='')}"

    @staticmethod
    def _normalize_changelog_response(base_url: str, project_path: str, release: dict[str, Any]) -> dict[str, str]:
        """Convert GitLab release fields into the changelog shape shared with GitHub releases."""
        tag_name = str(release.get("tag_name", ""))
        links = release.get("_links", {})
        release_url = links.get("self") if isinstance(links, dict) else ""
        return {
            "html_url": str(release_url or f"{base_url}/{project_path}/-/releases/{tag_name}"),
            "tag_name": tag_name,
            "body": str(release.get("description", "")),
            "published_at": str(release.get("released_at") or release.get("created_at") or ""),
        }

    @staticmethod
    def _iter_release_asset_candidates(release: dict[str, Any]) -> Iterator[tuple[str, str]]:
        """Yield all GitLab release asset names and download URLs that can represent downloadable files."""
        assets = release.get("assets", {})
        if not isinstance(assets, dict):
            return
        for link in assets.get("links", []):
            if isinstance(link, dict):
                asset_url = link.get("direct_asset_url") or link.get("url")
                if asset_url:
                    yield str(link.get("name", "")), str(asset_url)
        for source in assets.get("sources", []):
            if isinstance(source, dict) and source.get("url"):
                yield str(source.get("format", "")), str(source["url"])
        evidence_file_path = assets.get("evidence_file_path")
        if evidence_file_path:
            yield "evidence", str(evidence_file_path)

    @staticmethod
    def _select_release_asset(release: dict[str, Any], asset_filter: str) -> str:
        """Select the first GitLab release asset whose URL or name matches the configured asset regex."""
        try:
            filter_pattern = re.compile(asset_filter)
        except re.error as e:
            msg = f"Invalid regex {asset_filter} pattern provided."
            raise DownloadError(msg) from e
        for asset_name, asset_url in Gitlab._iter_release_asset_candidates(release):
            if filter_pattern.search(asset_url) or filter_pattern.search(asset_name):
                logger.debug(f"Found {asset_name} to be downloaded from {asset_url}")
                return asset_url
        return ""

    @staticmethod
    def _get_release_assets(
        base_url: str,
        project_path: str,
        release_ref: str,
        asset_filter: str,
        config: RevancedConfig,
    ) -> tuple[str, str]:
        """Get matching assets from a GitLab release."""
        api_url = Gitlab._get_release_api_url(base_url, project_path, release_ref)
        response = requests.get(api_url, headers=Gitlab._get_headers(config), timeout=request_timeout)
        handle_request_response(response, api_url)
        release = response.json()
        update_changelog(
            f"{urlparse(base_url).netloc}/{project_path}",
            Gitlab._normalize_changelog_response(base_url, project_path, release),
        )
        return str(release.get("tag_name", "")), Gitlab._select_release_asset(release, asset_filter)

    @staticmethod
    def patch_resource(repo_url: str, assets_filter: str, config: RevancedConfig) -> tuple[str, str]:
        """Fetch a patching resource from a GitLab release URL."""
        base_url, project_path, release_ref = Gitlab._extract_project_and_tag(repo_url)
        return Gitlab._get_release_assets(base_url, project_path, release_ref, assets_filter, config)
