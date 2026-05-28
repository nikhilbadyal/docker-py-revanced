"""Regression tests for builder cache policy."""

# Cache policy bugs can silently reuse stale artifacts, so these tests exercise the public resource path.
# ruff: noqa: PT009

from threading import Lock
from types import SimpleNamespace
from typing import TYPE_CHECKING, Self, cast
from unittest import TestCase
from unittest.mock import patch

from src.app import APP

if TYPE_CHECKING:
    from src.config import RevancedConfig


class AppCachingTests(TestCase):
    """Verify DISABLE_CACHING prevents shared cache reads and writes."""

    def test_disabled_resource_cache_downloads_and_leaves_shared_cache_unchanged(self: Self) -> None:
        """Disabled cache mode should resolve resources freshly without mutating shared cache state."""
        app = APP.__new__(APP)
        # The public resource downloader only needs these initialized fields for this cache-policy path.
        app.cli_dl = "https://example.test/resource.jar"
        app.patches_dl_list = []
        app.patch_bundles = []
        app.resource = {}
        config = cast(
            "RevancedConfig",
            SimpleNamespace(disable_caching=True, max_resource_workers=1),
        )
        cached_resources = {"https://example.test/resource.jar": ("cached-tag", "cached.jar")}

        with patch("src.app.APP.download", return_value=("v1.0.0", "resource.jar")) as download:
            app.download_patch_resources(config, cached_resources, Lock())

        download.assert_called_once_with("https://example.test/resource.jar", config, ".*jar")
        expected_cache = {"https://example.test/resource.jar": ("cached-tag", "cached.jar")}
        self.assertEqual(expected_cache, cached_resources)
        self.assertEqual({"file_name": "resource.jar", "version": "v1.0.0"}, app.resource["cli"])
