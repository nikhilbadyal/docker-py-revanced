"""Regression tests for APKMirror Cloudflare fallback behavior."""

# APKMirror's challenge shape is external and unstable, so these tests pin the local fallback decisions.
# Private helper coverage is intentional because the public path would perform live APKMirror downloads.
# ruff: noqa: PT009, SLF001

from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from typing import Self, cast
from unittest import TestCase
from unittest.mock import patch

from src.config import RevancedConfig
from src.downloader.apkmirror import ApkMirror
from src.downloader.sources import APK_MIRROR_BASE_URL
from src.exceptions import ScrapingError


class _APKMirrorResponse(SimpleNamespace):
    """Small response double with only the fields used by the APKMirror source fetcher."""

    status_code: int
    text: str


def _config(temp_folder: Path) -> RevancedConfig:
    """Build the downloader config surface needed before patching out network downloads."""
    return cast(
        "RevancedConfig",
        # The browser download fallback needs these policy fields without constructing the full env config.
        SimpleNamespace(dry_run=False, temp_folder=temp_folder),
    )


class APKMirrorDownloaderTests(TestCase):
    """Verify APKMirror can fall back from HTTP scraping to CloakBrowser."""

    def test_extract_source_uses_cloak_when_cloudscraper_gets_http_challenge(self: Self) -> None:
        """HTTP challenge failures should be retried through CloakBrowser instead of failing immediately."""
        response = _APKMirrorResponse(status_code=403, text="<title>Just a moment...</title>")

        with (
            patch("src.downloader.apkmirror.apkmirror_scraper.get", return_value=response),
            patch.object(ApkMirror, "_extract_source_with_cloak", return_value="<html>real app page</html>") as cloak,
        ):
            source = ApkMirror._extract_source("https://www.apkmirror.com/apk/example/app/")

        self.assertEqual("<html>real app page</html>", source)
        cloak.assert_called_once()

    def test_extract_source_uses_cloak_when_cloudscraper_gets_challenge_html(self: Self) -> None:
        """Cloudflare can return challenge markup with HTTP 200, so body markers must trigger fallback."""
        response = _APKMirrorResponse(status_code=200, text="<html>Checking your browser before access</html>")

        with (
            patch("src.downloader.apkmirror.apkmirror_scraper.get", return_value=response),
            patch.object(ApkMirror, "_extract_source_with_cloak", return_value="<html>real app page</html>") as cloak,
        ):
            source = ApkMirror._extract_source("https://www.apkmirror.com/apk/example/app/")

        self.assertEqual("<html>real app page</html>", source)
        cloak.assert_called_once_with("https://www.apkmirror.com/apk/example/app/")

    def test_force_download_uses_cloak_when_binary_download_is_challenged(self: Self) -> None:
        """The final `download.php` endpoint can be challenged separately from the HTML pages."""
        force_download_page = """
            <span class="apkm-badge">APK</span>
            <div class="tab-pane">
                <a href="/download.php?id=12345">Download APK</a>
            </div>
        """

        with TemporaryDirectory() as tmp_dir:
            downloader = ApkMirror(_config(Path(tmp_dir)))
            with (
                patch.object(downloader, "_extract_source", return_value=force_download_page),
                patch.object(downloader, "_download", side_effect=ScrapingError("Cloudflare captcha")),
                patch.object(downloader, "_download_file_with_cloak") as cloak_download,
            ):
                file_name, download_url = downloader._extract_force_download_link(
                    "https://www.apkmirror.com/apk/example/app/download/",
                    "EXAMPLE_APP",
                )

        self.assertEqual("EXAMPLE_APP.apk", file_name)
        self.assertEqual(f"{APK_MIRROR_BASE_URL}/download.php?id=12345", download_url)
        cloak_download.assert_called_once()
