"""Tests for direct binary resource downloads."""

# Direct download headers are part of the integration contract with binary bundle endpoints.
# unittest keeps this test consistent with the existing test suite dependencies.
# ruff: noqa: PT009

from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from typing import TYPE_CHECKING, Self, cast
from unittest import TestCase
from unittest.mock import patch
from zipfile import ZipFile

from src.config import RevancedConfig
from src.downloader.download import Downloader

if TYPE_CHECKING:
    from src.app import APP


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
        SimpleNamespace(
            apk_editor="apkeditor.jar",
            existing_downloaded_apks=[],
            personal_access_token=None,
            dry_run=False,
            disable_caching=False,
            temp_folder=temp_folder,
        ),
    )


def _write_zip(path: Path, names: list[str]) -> None:
    """Create a small archive with controlled entries so APK shape detection is deterministic."""
    with ZipFile(path, "w") as zip_file:
        for name in names:
            # Entry contents do not matter; only root filenames drive the merge decision.
            zip_file.writestr(name, b"content")


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

    def test_convert_to_apk_keeps_real_apk_without_apkeditor(self: Self) -> None:
        """A proper APK should not be passed through APKEditor just because APKs are zip archives."""
        with TemporaryDirectory() as tmp_dir:
            config = _config(Path(tmp_dir))
            _write_zip(Path(tmp_dir, "youtube.apk"), ["AndroidManifest.xml", "resources.arsc"])

            with patch("src.downloader.download.subprocess.run") as subprocess_run:
                output_file = Downloader(config).convert_to_apk("youtube.apk")

        self.assertEqual("youtube.apk", output_file)
        subprocess_run.assert_not_called()

    def test_convert_to_apk_merges_xapk_archive_misnamed_as_apk(self: Self) -> None:
        """Uptodown can return split APK archives with `.apk` names, so content decides conversion."""
        with TemporaryDirectory() as tmp_dir:
            config = _config(Path(tmp_dir))
            app_archive = Path(tmp_dir, "youtube_music.apk")
            _write_zip(app_archive, ["base.apk", "split_config.arm64_v8a.apk"])

            with patch("src.downloader.download.subprocess.run") as subprocess_run:
                output_file = Downloader(config).convert_to_apk("youtube_music.apk")

            command = subprocess_run.call_args.args[0]

        self.assertEqual("youtube_music.apk", output_file)
        self.assertIn(f"{tmp_dir}/youtube_music.xapk", command)
        self.assertIn(f"{tmp_dir}/youtube_music.apk", command)

    def test_download_passes_morphe_apkm_to_patcher_without_apkeditor(self: Self) -> None:
        """Morphe can patch APKM inputs directly, so preserving them avoids corrupting split-bundle patch targets."""
        with TemporaryDirectory() as tmp_dir:
            config = _config(Path(tmp_dir))
            app = cast(
                "APP",
                # The downloader only needs the app name for logging and the effective profile for conversion policy.
                SimpleNamespace(app_name="PIKO_TWITTER", effective_cli_argsf="morphe-cli"),
            )
            downloader = Downloader(config)

            with (
                patch.object(
                    downloader,
                    "latest_version",
                    return_value=("PIKO_TWITTER.apkm", "https://example/apkm"),
                ),
                patch.object(downloader, "convert_to_apk") as convert_to_apk,
            ):
                output_file, download_url = downloader.download("latest", app)

        self.assertEqual("PIKO_TWITTER.apkm", output_file)
        self.assertEqual("https://example/apkm", download_url)
        convert_to_apk.assert_not_called()

    def test_download_keeps_non_morphe_bundle_merge_path(self: Self) -> None:
        """ReVanced-style profiles still need APKEditor conversion for bundle-shaped downloads."""
        with TemporaryDirectory() as tmp_dir:
            config = _config(Path(tmp_dir))
            app = cast(
                "APP",
                # The non-Morphe profile keeps the historical merge behavior even if the source suffix is APKM.
                SimpleNamespace(app_name="INSTAGRAM_REVANCED", effective_cli_argsf="revanced-cli"),
            )
            downloader = Downloader(config)

            with (
                patch.object(
                    downloader,
                    "latest_version",
                    return_value=("INSTAGRAM_REVANCED.apkm", "https://example/apkm"),
                ),
                patch.object(downloader, "convert_to_apk", return_value="INSTAGRAM_REVANCED.apk") as convert_to_apk,
            ):
                output_file, download_url = downloader.download("latest", app)

        self.assertEqual("INSTAGRAM_REVANCED.apk", output_file)
        self.assertEqual("https://example/apkm", download_url)
        convert_to_apk.assert_called_once_with("INSTAGRAM_REVANCED.apkm")
