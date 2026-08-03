"""Regression tests for Obtainium export metadata."""

# Obtainium support is optional but user-facing, so these tests pin URL and update identity behavior.
# unittest keeps this file aligned with the rest of the repository test suite.
# ruff: noqa: PT009

import json
import re
from contextlib import chdir
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from typing import Self, cast
from unittest import TestCase
from urllib.parse import unquote

from environs import Env

from src.app import APP
from src.config import RevancedConfig
from src.utils import generate_obtainium_export


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

    def test_output_file_name_collapses_repeated_dots(self: Self) -> None:
        """Generated release asset names should match GitHub's uploaded asset names."""
        app = _app_with_patch_bundles("v2.0.0")
        app.app_version = "50.1.1..5001014"

        self.assertIn("Version50.1.1.5001014", app.get_output_file_name())

    def test_generate_obtainium_export_encodes_url_and_slugifies_html_name(self: Self) -> None:
        """Generated HTML should be safe to serve and should link to the exact encoded release asset."""
        with TemporaryDirectory() as temp_dir, chdir(temp_dir):
            # This config mirrors the runtime fields used by generate_obtainium_export without booting Env.
            config = cast(
                "RevancedConfig",
                SimpleNamespace(
                    obtainium_export=True,
                    obtainium_github_tag="release tag",
                    obtainium_site_export=False,
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

    def test_generate_obtainium_export_site_export_builds_deep_link(self: Self) -> None:
        """Site export should add a package-scoped obtainium://app/ deep link and an index page."""
        with TemporaryDirectory() as temp_dir, chdir(temp_dir):
            config = cast(
                "RevancedConfig",
                SimpleNamespace(
                    obtainium_export=True,
                    obtainium_github_tag="latest",
                    obtainium_site_export=True,
                    obtainium_version_extraction_regex=r"Version([\w.]+)-PatchVersion[v]?([\w.]+)-PatchSet",
                    obtainium_version_match_group="$1+$2",
                    env=_Env("owner/repo"),
                ),
            )
            updates_info = {
                "YouTube": {
                    "app_version": "20.47.62",
                    "patches_versions": ["v1.0.0"],
                    "output_file_name": "ReYouTube-Version20.47.62-PatchVersionv1.0.0-PatchSetabc123-output.apk",
                    "app_dump": {"package_name": "app.revanced.android.youtube"},
                },
            }

            generate_obtainium_export(updates_info, config)
            index_content = Path(temp_dir, "index.html").read_text(encoding="utf_8")

        self.assertIn('<span class="app-name">YouTube</span>', index_content)
        self.assertIn('<code class="package-name">app.revanced.android.youtube</code>', index_content)
        self.assertIn('<span class="meta-chip">App 20.47.62</span>', index_content)
        self.assertIn('<span class="meta-chip">Patch v1.0.0</span>', index_content)
        self.assertIn(
            'class="source-link" href="https://raw.githubusercontent.com/owner/repo/changelogs/'
            'obtainium_sources/youtube.html"',
            index_content,
        )
        self.assertIn("https://github.com/ImranR98/Obtainium", index_content)
        deep_link_match = re.search(r'href="(obtainium://app/[^"]+)"', index_content)
        self.assertIsNotNone(deep_link_match)
        payload = json.loads(unquote(deep_link_match.group(1).removeprefix("obtainium://app/")))  # type: ignore[union-attr]

        self.assertEqual(payload["id"], "app.revanced.android.youtube")
        self.assertEqual(payload["overrideSource"], "HTML")
        self.assertEqual(
            payload["url"],
            "https://raw.githubusercontent.com/owner/repo/changelogs/obtainium_sources/youtube.html",
        )

        additional_settings = json.loads(payload["additionalSettings"])
        self.assertEqual(additional_settings["matchGroupToUse"], "$1+$2")
        self.assertTrue(additional_settings["versionDetection"])

    def test_generate_obtainium_export_site_export_skips_app_without_package_name(self: Self) -> None:
        """An app_dump missing package_name should skip its deep link but not crash the export."""
        with TemporaryDirectory() as temp_dir, chdir(temp_dir):
            config = cast(
                "RevancedConfig",
                SimpleNamespace(
                    obtainium_export=True,
                    obtainium_github_tag="latest",
                    obtainium_site_export=True,
                    obtainium_version_extraction_regex="",
                    obtainium_version_match_group="",
                    env=_Env("owner/repo"),
                ),
            )
            updates_info = {
                "YouTube": {
                    "app_version": "20.47.62",
                    "output_file_name": "youtube-output.apk",
                    "app_dump": {},
                },
            }

            generate_obtainium_export(updates_info, config)
            index_path = Path(temp_dir, "index.html")

        self.assertFalse(index_path.exists())

    def test_default_version_extraction_regex_handles_optional_patch_prefix(self: Self) -> None:
        """The shipped default regex must match patch bundle versions with or without a leading 'v'."""
        config = RevancedConfig(Env())
        regex = config.obtainium_version_extraction_regex

        with_v = re.search(regex, "ReYouTube-Version20.47.62-PatchVersionv1.0.0-PatchSetabc123-output.apk")
        without_v = re.search(regex, "ReYouTube-Version20.47.62-PatchVersion1.0.0-PatchSetabc123-output.apk")

        self.assertIsNotNone(with_v)
        self.assertIsNotNone(without_v)
        self.assertEqual(with_v.groups(), ("20.47.62", "1.0.0"))  # type: ignore[union-attr]
        self.assertEqual(without_v.groups(), ("20.47.62", "1.0.0"))  # type: ignore[union-attr]
