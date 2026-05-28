"""Tests for direct binary resource downloads."""

# Direct download headers are part of the integration contract with binary bundle endpoints.
# unittest keeps this test consistent with the existing test suite dependencies.
# ruff: noqa: PT009

from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from typing import Self, cast
from unittest import TestCase
from unittest.mock import patch

from src.config import RevancedConfig
from src.downloader.download import Downloader


class _BinaryResponse:
    """Small response double that behaves like a successful streaming binary response."""

    status_code = 200
    text = ""

    def __init__(self: Self, body: bytes) -> None:
        """Store bytes so the downloader writes a real file during the test."""
        self._body = body
        self.headers = {"content-length": str(len(body))}
        self.closed = False

    def iter_content(self: Self, chunk_size: int) -> list[bytes]:
        """Return one chunk because chunking behavior is not what this test is verifying."""
        return [self._body]

    def close(self: Self) -> None:
        """Record close calls because streamed responses must release their connection."""
        self.closed = True


def _config(temp_folder: Path) -> RevancedConfig:
    """Build only the config fields needed by the direct downloader."""
    return cast(
        "RevancedConfig",
        # These are the downloader policy fields exercised by the tests without constructing the full env config.
        SimpleNamespace(personal_access_token=None, dry_run=False, disable_caching=False, temp_folder=temp_folder),
    )


class DirectDownloadTests(TestCase):
    """Verify generic direct downloads handle patch bundle endpoints explicitly."""

    def test_patch_bundle_direct_download_requests_octet_stream(self: Self) -> None:
        """ReVanced API's `.rvp` endpoint should be requested as raw binary content."""
        with TemporaryDirectory() as tmp_dir:
            config = _config(Path(tmp_dir))
            response = _BinaryResponse(b"patch-bundle")

            with patch("src.downloader.download.session.get", return_value=response) as request_get:
                Downloader(config).direct_download("https://api.revanced.app/v5/patches.rvp", "patches.rvp")

        self.assertEqual("application/octet-stream", request_get.call_args.kwargs["headers"]["Accept"])
        self.assertIn("timeout", request_get.call_args.kwargs)

    def test_existing_partial_file_is_replaced_when_size_does_not_match(self: Self) -> None:
        """Interrupted downloads should be retried instead of treating a partial target as cache-valid."""
        with TemporaryDirectory() as tmp_dir:
            config = _config(Path(tmp_dir))
            target = Path(tmp_dir, "patches.rvp")
            target.write_bytes(b"partial")
            response = _BinaryResponse(b"complete-patch-bundle")

            with patch("src.downloader.download.session.get", return_value=response):
                Downloader(config).direct_download("https://api.revanced.app/v5/patches.rvp", "patches.rvp")

            self.assertEqual(b"complete-patch-bundle", target.read_bytes())
            self.assertEqual([], list(Path(tmp_dir).glob(".patches.rvp.*.part")))
            self.assertTrue(response.closed)

    def test_existing_complete_file_is_kept_when_size_matches(self: Self) -> None:
        """Matching content length is the cache-valid signal for an already downloaded artifact."""
        with TemporaryDirectory() as tmp_dir:
            config = _config(Path(tmp_dir))
            target = Path(tmp_dir, "patches.rvp")
            target.write_bytes(b"cached-patch-bundle")
            response = _BinaryResponse(b"cached-patch-bundle")

            with patch("src.downloader.download.session.get", return_value=response):
                Downloader(config).direct_download("https://api.revanced.app/v5/patches.rvp", "patches.rvp")

            self.assertEqual(b"cached-patch-bundle", target.read_bytes())
            self.assertEqual([], list(Path(tmp_dir).glob(".patches.rvp.*.part")))
            self.assertTrue(response.closed)

    def test_existing_complete_file_is_replaced_when_caching_is_disabled(self: Self) -> None:
        """DISABLE_CACHING should force a fresh download even when a complete artifact exists."""
        with TemporaryDirectory() as tmp_dir:
            config = _config(Path(tmp_dir))
            config.disable_caching = True
            target = Path(tmp_dir, "patches.rvp")
            target.write_bytes(b"cached-patch-bundle")
            response = _BinaryResponse(b"fresh-patch-bundle")

            with patch("src.downloader.download.session.get", return_value=response):
                Downloader(config).direct_download("https://api.revanced.app/v5/patches.rvp", "patches.rvp")

            self.assertEqual(b"fresh-patch-bundle", target.read_bytes())
            self.assertEqual([], list(Path(tmp_dir).glob(".patches.rvp.*.part")))
            self.assertTrue(response.closed)
