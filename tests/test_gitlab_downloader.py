"""Tests for GitLab release asset support."""

# Private helpers are exercised here because URL parsing is the compatibility contract.
# unittest assertions keep these tests runnable without adding pytest as a project dependency.
# ruff: noqa: SLF001, PT009

from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from unittest import TestCase
from unittest.mock import patch

from src.app import APP
from src.config import RevancedConfig
from src.downloader.factory import DownloaderFactory
from src.downloader.gitlab import Gitlab


class _GitlabResponse:
    """Small response double that exercises the same status/json contract as requests.Response."""

    status_code = 200
    text = ""

    def __init__(self, payload: dict[str, Any]) -> None:
        """Store the GitLab API payload that the downloader will inspect."""
        self._payload = payload

    def json(self) -> dict[str, Any]:
        """Return the prepared payload so tests stay independent of network calls."""
        return self._payload


def _config(token: str | None = None) -> RevancedConfig:
    """Build the narrow config surface needed by the GitLab downloader tests."""
    return cast("RevancedConfig", SimpleNamespace(personal_access_token=token, dry_run=False, temp_folder=Path("apks")))


class GitlabDownloaderTests(TestCase):
    """Verify GitLab release URLs behave like the existing GitHub resource URLs."""

    def test_extracts_latest_release_from_project_root(self) -> None:
        """A bare GitLab project URL should resolve to the latest release API path."""
        base_url, project_path, release_ref = Gitlab._extract_project_and_tag(
            "https://gitlab.com/group/subgroup/revanced-patches",
        )

        self.assertEqual("https://gitlab.com", base_url)
        self.assertEqual("group/subgroup/revanced-patches", project_path)
        self.assertEqual(Gitlab.LATEST_RELEASE, release_ref)

    def test_extracts_tagged_release_from_gitlab_ui_url(self) -> None:
        """GitLab UI release URLs should map their tag segment directly to the release API."""
        base_url, project_path, release_ref = Gitlab._extract_project_and_tag(
            "https://gitlab.com/group/revanced-cli/-/releases/v5.0.0",
        )

        self.assertEqual("https://gitlab.com", base_url)
        self.assertEqual("group/revanced-cli", project_path)
        self.assertEqual("v5.0.0", release_ref)

    def test_extracts_release_from_github_like_gitlab_url(self) -> None:
        """GitLab URLs without the UI marker should still support the existing GitHub-style config shape."""
        base_url, project_path, release_ref = Gitlab._extract_project_and_tag(
            "https://gitlab.com/group/revanced-cli/releases/latest",
        )

        self.assertEqual("https://gitlab.com", base_url)
        self.assertEqual("group/revanced-cli", project_path)
        self.assertEqual(Gitlab.LATEST_RELEASE, release_ref)

    def test_latest_prerelease_uses_gitlab_latest_release_contract(self) -> None:
        """GitLab has no prerelease flag, so the GitHub-compatible suffix should use latest-by-date."""
        _, _, release_ref = Gitlab._extract_project_and_tag(
            "https://gitlab.com/group/revanced-patches/-/releases/latest-prerelease",
        )

        self.assertEqual(Gitlab.LATEST_RELEASE, release_ref)

    def test_get_release_assets_uses_gitlab_api_and_direct_asset_url(self) -> None:
        """GitLab asset links should be filtered with the existing regex resource selection contract."""
        release_payload: dict[str, Any] = {
            "tag_name": "v1.2.3",
            "description": "Release notes",
            "released_at": "2026-05-01T00:00:00Z",
            "_links": {"self": "https://gitlab.com/group/revanced-patches/-/releases/v1.2.3"},
            "assets": {
                "links": [
                    {
                        "name": "notes.txt",
                        "direct_asset_url": "https://gitlab.com/group/revanced-patches/-/releases/v1.2.3/downloads/notes.txt",
                    },
                    {
                        "name": "revanced-patches.rvp",
                        "direct_asset_url": (
                            "https://gitlab.com/group/revanced-patches"
                            "/-/releases/v1.2.3/downloads/revanced-patches.rvp"
                        ),
                    },
                ],
            },
        }

        with (
            patch("src.downloader.gitlab.requests.get", return_value=_GitlabResponse(release_payload)) as request_get,
            patch("src.downloader.gitlab.update_changelog") as update_changelog,
        ):
            tag, download_url = Gitlab._get_release_assets(
                "https://gitlab.com",
                "group/revanced-patches",
                Gitlab.LATEST_RELEASE,
                ".*(rvp|mpp)",
                _config("glpat-token"),
            )

        self.assertEqual("v1.2.3", tag)
        self.assertEqual(
            "https://gitlab.com/group/revanced-patches/-/releases/v1.2.3/downloads/revanced-patches.rvp",
            download_url,
        )
        self.assertEqual(
            "https://gitlab.com/api/v4/projects/group%2Frevanced-patches/releases/permalink/latest",
            request_get.call_args.args[0],
        )
        self.assertEqual("glpat-token", request_get.call_args.kwargs["headers"]["PRIVATE-TOKEN"])
        self.assertEqual("gitlab.com/group/revanced-patches", update_changelog.call_args.args[0])
        self.assertEqual("Release notes", update_changelog.call_args.args[1]["body"])

    def test_asset_name_can_match_when_url_hides_file_extension(self) -> None:
        """GitLab asset links can point at external URLs, so keep the release asset name in the match surface."""
        release_payload: dict[str, Any] = {
            "assets": {
                "links": [
                    {
                        "name": "revanced-cli.jar",
                        "url": "https://downloads.example.com/artifacts/12345",
                    },
                ],
            },
        }

        self.assertEqual(
            "https://downloads.example.com/artifacts/12345",
            Gitlab._select_release_asset(release_payload, ".*jar"),
        )

    def test_app_download_routes_gitlab_release_urls_through_gitlab_resolver(self) -> None:
        """Resource downloads should resolve GitLab release URLs before invoking the generic stream downloader."""
        resolved_url = "https://gitlab.com/group/revanced-cli/-/releases/v5.0.0/downloads/revanced-cli.jar"

        with (
            patch("src.downloader.gitlab.Gitlab.patch_resource", return_value=("v5.0.0", resolved_url)),
            patch("src.downloader.download.Downloader.direct_download") as direct_download,
        ):
            tag, file_name = APP.download(
                "https://gitlab.com/group/revanced-cli/-/releases/permalink/latest",
                _config(),
                ".*jar",
            )

        self.assertEqual("v5.0.0", tag)
        self.assertTrue(file_name.endswith(".jar"))
        direct_download.assert_called_once_with(resolved_url, file_name)

    def test_factory_routes_gitlab_app_sources_to_gitlab_downloader(self) -> None:
        """App download sources hosted on GitLab should get the GitLab release asset selector."""
        downloader = DownloaderFactory.create_downloader(_config(), "https://gitlab.com/group/app-release")

        self.assertIsInstance(downloader, Gitlab)
