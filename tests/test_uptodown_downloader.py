"""Regression tests for Uptodown's app and XAPK download pages."""

# Uptodown changes markup often, so these tests pin the parser decisions that protect release artifacts.
# ruff: noqa: PT009

from types import SimpleNamespace
from typing import TYPE_CHECKING, Self, cast
from unittest import TestCase
from unittest.mock import patch

from src.downloader.uptodown import UptoDown
from src.utils import request_header, request_timeout

if TYPE_CHECKING:
    from src.config import RevancedConfig


class _UptodownResponse(SimpleNamespace):
    """Small response double with the fields consumed by `handle_request_response` and BeautifulSoup."""

    status_code: int = 200
    text: str


def _config() -> "RevancedConfig":
    """Build the narrow config object needed while `_download` is mocked out."""
    return cast("RevancedConfig", SimpleNamespace())


class UptodownDownloaderTests(TestCase):
    """Verify that Uptodown pages resolve to app files, not Uptodown's installer app."""

    def test_generic_xapk_download_page_resolves_real_variant_file(self: Self) -> None:
        """Generic XAPK pages advertise the Uptodown store, so the downloader must follow the variant file ID."""
        generic_page = """
            <button id="detail-download-button" class="button download xapk"
                    data-download-version="1174126433"
                    data-url="uptodown-store-token">
                Download with UPTODOWN app store
            </button>
        """
        variant_page = """
            <button id="detail-download-button" class="button download"
                    data-url="reddit-xapk-token">
                Download 81.92 MB free
            </button>
        """
        downloader = UptoDown(_config())

        with (
            patch(
                "src.downloader.uptodown.requests.get",
                side_effect=[_UptodownResponse(text=generic_page), _UptodownResponse(text=variant_page)],
            ) as request_get,
            patch.object(downloader, "_download") as download,
        ):
            file_name, download_url = downloader.extract_download_link(
                "https://reddit-official-app.en.uptodown.com/android/download",
                "REDDIT_ANDEA",
            )

        self.assertEqual("REDDIT_ANDEA.xapk", file_name)
        self.assertEqual("https://dw.uptodown.com/dwn/reddit-xapk-token", download_url)
        download.assert_called_once_with("https://dw.uptodown.com/dwn/reddit-xapk-token", "REDDIT_ANDEA.xapk")
        request_get.assert_any_call(
            "https://reddit-official-app.en.uptodown.com/android/download/1174126433-x",
            headers=request_header,
            allow_redirects=True,
            timeout=request_timeout,
        )

    def test_plain_apk_download_page_keeps_apk_extension(self: Self) -> None:
        """Plain APK pages are already direct app downloads and should not be rewritten as XAPK variants."""
        apk_page = """
            <button id="detail-download-button" class="button download"
                    data-url="plain-apk-token">
                Download 20 MB free
            </button>
        """
        downloader = UptoDown(_config())

        with (
            patch("src.downloader.uptodown.requests.get", return_value=_UptodownResponse(text=apk_page)),
            patch.object(downloader, "_download") as download,
        ):
            file_name, download_url = downloader.extract_download_link(
                "https://example-app.en.uptodown.com/android/download",
                "EXAMPLE_APP",
            )

        self.assertEqual("EXAMPLE_APP.apk", file_name)
        self.assertEqual("https://dw.uptodown.com/dwn/plain-apk-token", download_url)
        download.assert_called_once_with("https://dw.uptodown.com/dwn/plain-apk-token", "EXAMPLE_APP.apk")
