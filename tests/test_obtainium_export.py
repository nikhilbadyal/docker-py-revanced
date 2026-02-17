"""Regression tests for Obtainium export metadata."""

# Obtainium support is optional but user-facing, so these tests pin URL and update identity behavior.
# unittest keeps this file aligned with the rest of the repository test suite.
# ruff: noqa: PT009

from contextlib import chdir
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from typing import TYPE_CHECKING, Self, cast
from unittest import TestCase

from src.app import APP
from src.utils import generate_obtainium_export

if TYPE_CHECKING:
    from src.config import RevancedConfig


class _Env:
    """Small env double for only the config lookup used by Obtainium export."""

    def __init__(self: Self, github_repository: str) -> None:
        """Store the repository value so tests do not depend on real environment variables."""
        self.github_repository = github_repository

    def str(self: Self, key: str, default: str = "") -> str:
        """Return GitHub repository for export URL generation and defaults for unrelated keys."""
        if key == "GITHUB_REPOSITORY":
            return self.github_repository
        return default


def _app_with_patch_bundles(second_bundle_version: str) -> APP:
    """Build the minimum APP-shaped object needed to exercise output filename generation."""
    # APP initialization needs a full RevancedConfig, so allocate an instance and set only fields this method reads.
    app = APP.__new__(APP)
    app.app_name = "youtube"
    app.app_version = "20.47.62"
    app.patch_bundles = [
        {"file_name": "revanced.rvp", "version": "v1.0.0"},
        {"file_name": "extra.mpp", "version": second_bundle_version},
    ]
    # The method under test reads the private cache, so the test seeds it through __dict__ without lint noise.
    app.__dict__["_cached_output_file_name"] = ""
    return app


class ObtainiumExportTests(TestCase):
    """Verify Obtainium export data changes when app or patch metadata changes."""

    def test_output_file_name_includes_all_patch_bundle_versions(self: Self) -> None:
        """Patch-only updates in any bundle should change the release asset link Obtainium hashes."""
        first_name = _app_with_patch_bundles("v2.0.0").get_output_file_name()
        second_name = _app_with_patch_bundles("v3.0.0").get_output_file_name()

        self.assertIn("PatchVersionv1.0.0.v2.0.0", first_name)
        self.assertIn("PatchVersionv1.0.0.v3.0.0", second_name)
        self.assertNotEqual(first_name, second_name)

    def test_generate_obtainium_export_encodes_url_and_slugifies_html_name(self: Self) -> None:
        """Generated HTML should be safe to serve and should link to the exact encoded release asset."""
        with TemporaryDirectory() as temp_dir, chdir(temp_dir):
            # This config mirrors the runtime fields used by generate_obtainium_export without booting Env.
            config = cast(
                "RevancedConfig",
                SimpleNamespace(
                    obtainium_export=True,
                    obtainium_github_tag="release tag",
                    env=_Env("owner/repo"),
                ),
            )
            updates_info = {
                "YouTube Music": {
                    "app_version": "1<2",
                    "output_file_name": "My APK #1.apk",
                },
            }

            generate_obtainium_export(updates_info, config)
            html_path = Path(temp_dir, "obtainium_sources", "youtube.music.html")
            html_content = html_path.read_text(encoding="utf_8")

        self.assertIn(
            "https://github.com/owner/repo/releases/download/release%20tag/My%20APK%20%231.apk",
            html_content,
        )
        self.assertIn("1&lt;2", html_content)
