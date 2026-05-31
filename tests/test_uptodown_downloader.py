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


def _download_headers() -> dict[str, str]:
    """Mirror the auth headers Uptodown expects when resolving signed direct download tokens."""
    return {
        "User-Agent": request_header["User-Agent"],
        "Authorization": request_header["Authorization"],
    }


class UptodownDownloaderTests(TestCase):
    """Verify that Uptodown pages resolve to app files, not Uptodown's installer app."""

    def test_generic_xapk_download_page_uses_current_direct_token(self: Self) -> None:
        """Current XAPK pages advertise the store while still exposing a direct app-file token."""
        generic_page = """
            <button id="detail-download-button" class="button download xapk"
                    data-download-version="1174126433"
                    data-url="youtube-music-token">
                Download with UPTODOWN app store
            </button>
        """
        downloader = UptoDown(_config())

        with (
            patch(
                "src.downloader.uptodown.requests.get",
                return_value=_UptodownResponse(text=generic_page),
            ) as request_get,
            patch.object(downloader, "_download") as download,
        ):
            file_name, download_url = downloader.extract_download_link(
                "https://youtube-music.en.uptodown.com/android/download/1164645913",
                "YOUTUBE_MUSIC_MORPHE",
            )

        self.assertEqual("YOUTUBE_MUSIC_MORPHE.apk", file_name)
        self.assertEqual("https://dw.uptodown.com/dwn/youtube-music-token", download_url)
        download.assert_called_once_with(
            "https://dw.uptodown.com/dwn/youtube-music-token",
            "YOUTUBE_MUSIC_MORPHE.apk",
            extra_headers=_download_headers(),
        )
        request_get.assert_called_once_with(
            "https://youtube-music.en.uptodown.com/android/download/1164645913",
            headers=request_header,
            allow_redirects=True,
            timeout=request_timeout,
        )

    def test_generic_xapk_download_page_without_token_resolves_legacy_variant_file(self: Self) -> None:
        """Legacy XAPK bridge pages without a direct token still need the variant file ID fallback."""
        generic_page = """
            <button id="detail-download-button" class="button download xapk"
                    data-download-version="1174126433">
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
        download.assert_called_once_with(
            "https://dw.uptodown.com/dwn/reddit-xapk-token",
            "REDDIT_ANDEA.xapk",
            extra_headers=_download_headers(),
        )
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
        download.assert_called_once_with(
            "https://dw.uptodown.com/dwn/plain-apk-token",
            "EXAMPLE_APP.apk",
            extra_headers=_download_headers(),
        )
