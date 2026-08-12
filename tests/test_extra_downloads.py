"""Tests for EXTRA_FILES download parsing and regex support."""

# Validates the two EXTRA_FILES formats: exact-name (url@file.ext) and regex (url@/pattern/).
# ruff: noqa: PT009

from types import SimpleNamespace
from typing import Self, cast
from unittest import TestCase
from unittest.mock import call, patch

from src.config import RevancedConfig
from src.downloader.download import Downloader


def _config() -> RevancedConfig:
    """Build only the config fields needed by extra_downloads without constructing the full env."""
    return cast(
        "RevancedConfig",
        SimpleNamespace(
            extra_download_files=[],
        ),
    )


class ExtraDownloadsExactModeTests(TestCase):
    """Verify the existing url@filename.ext exact-match format."""

    def test_exact_mode_passes_extension_filter_and_output_filename(self: Self) -> None:
        """Exact mode should use the file extension as assets_filter and append -output to the save name."""
        config = _config()
        config.extra_download_files = ["https://github.com/REAndroid/APKEditor@apkeditor.jar"]

        with patch.object(Downloader, "__init__", return_value=None), patch(
            "src.downloader.download.APP.download",
            return_value=("latest", "apkeditor-output.jar"),
        ) as mock_download:
            Downloader.extra_downloads(config)

        mock_download.assert_called_once_with(
            "https://github.com/REAndroid/APKEditor",
            config,
            assets_filter=".*.jar",
            file_name="apkeditor-output.jar",
        )

    def test_exact_mode_handles_multiple_entries(self: Self) -> None:
        """Multiple EXTRA_FILES entries should each trigger a separate download call."""
        config = _config()
        config.extra_download_files = [
            "https://github.com/foo/bar@widget.apk",
            "https://github.com/baz/qux@helper.jar",
        ]

        with patch.object(Downloader, "__init__", return_value=None), patch(
            "src.downloader.download.APP.download",
            return_value=("latest", ""),
        ) as mock_download:
            Downloader.extra_downloads(config)

        self.assertEqual(mock_download.call_count, 2)
        mock_download.assert_any_call(
            "https://github.com/foo/bar",
            config,
            assets_filter=".*.apk",
            file_name="widget-output.apk",
        )
        mock_download.assert_any_call(
            "https://github.com/baz/qux",
            config,
            assets_filter=".*.jar",
            file_name="helper-output.jar",
        )

    def test_exact_mode_malformed_entry_logs_error(self: Self) -> None:
        """An entry without an @ separator should not crash; it should log and stop processing."""
        config = _config()
        # No @ separator, so split("@") raises ValueError
        config.extra_download_files = ["https://github.com/foo/bar"]

        with patch.object(Downloader, "__init__", return_value=None), patch(
            "src.downloader.download.APP.download",
        ) as mock_download:
            # Should not raise
            Downloader.extra_downloads(config)

        mock_download.assert_not_called()


class ExtraDownloadsRegexModeTests(TestCase):
    """Verify the new url@/regex/ pattern-matching format."""

    def test_regex_mode_passes_pattern_as_assets_filter(self: Self) -> None:
        """When file_spec is wrapped in /, the inner text should be used as assets_filter regex."""
        config = _config()
        # MicroG use case: match versioned filename via regex
        config.extra_download_files = [
            r"https://github.com/microg/GmsCore/releases/latest@/com\.google\.android\.gms-\d+\.apk$/",
        ]

        with patch.object(Downloader, "__init__", return_value=None), patch(
            "src.downloader.download.APP.download",
            return_value=("latest", ""),
        ) as mock_download:
            Downloader.extra_downloads(config)

        # Regex mode: no file_name arg, pattern passed directly as assets_filter
        mock_download.assert_called_once_with(
            "https://github.com/microg/GmsCore/releases/latest",
            config,
            assets_filter=r"com\.google\.android\.gms-\d+\.apk$",
        )

    def test_regex_mode_does_not_include_delimiters_in_filter(self: Self) -> None:
        """The leading and trailing / must be stripped before passing to assets_filter."""
        config = _config()
        config.extra_download_files = ["https://example.com@/foo-\\d+\\.jar$/"]

        with patch.object(Downloader, "__init__", return_value=None), patch(
            "src.downloader.download.APP.download",
            return_value=("latest", ""),
        ) as mock_download:
            Downloader.extra_downloads(config)

        # The / delimiters should not appear in the filter
        filter_arg = (
            mock_download.call_args.kwargs.get("assets_filter")
            or mock_download.call_args[1].get("assets_filter")
            or mock_download.call_args[0][2]
        )
        self.assertFalse(filter_arg.startswith("/"))
        self.assertFalse(filter_arg.endswith("/"))

    def test_mixed_exact_and_regex_entries(self: Self) -> None:
        """Exact and regex entries in the same EXTRA_FILES list should each route correctly."""
        config = _config()
        config.extra_download_files = [
            "https://github.com/foo/bar@widget.apk",
            r"https://github.com/microg/GmsCore/releases/latest@/com\.google\.android\.gms-\d+\.apk$/",
        ]

        with patch.object(Downloader, "__init__", return_value=None), patch(
            "src.downloader.download.APP.download",
            return_value=("latest", ""),
        ) as mock_download:
            Downloader.extra_downloads(config)

        # First call: exact mode
        exact_call = mock_download.call_args_list[0]
        self.assertEqual(
            exact_call,
            call(
                "https://github.com/foo/bar",
                config,
                assets_filter=".*.apk",
                file_name="widget-output.apk",
            ),
        )

        # Second call: regex mode (no file_name kwarg)
        regex_call = mock_download.call_args_list[1]
        self.assertEqual(
            regex_call,
            call(
                "https://github.com/microg/GmsCore/releases/latest",
                config,
                assets_filter=r"com\.google\.android\.gms-\d+\.apk$",
            ),
        )

    def test_single_slash_is_not_treated_as_regex(self: Self) -> None:
        """A file_spec starting with / but not ending with / should fall through to exact mode."""
        config = _config()
        # Edge case: only starts with /, not a valid regex delimiter pair
        config.extra_download_files = ["https://example.com@/some-file.apk"]

        with patch.object(Downloader, "__init__", return_value=None), patch(
            "src.downloader.download.APP.download",
            return_value=("latest", ""),
        ) as mock_download:
            Downloader.extra_downloads(config)

        # Should be treated as exact mode (file_spec = "/some-file.apk")
        mock_download.assert_called_once_with(
            "https://example.com",
            config,
            assets_filter=".*.apk",
            file_name="/some-file-output.apk",
        )
