"""Regression tests for APKMirror app registration helpers."""

# The surrounding test suite uses unittest assertions, so keep the same style while testing script helpers.
# ruff: noqa: PT009, PT027

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Self
from unittest import TestCase
from unittest.mock import patch

from scripts.add_apkmirror_app import (
    APKMirrorApp,
    _metadata_from_api_response,
    derive_app_key,
    insert_kv_into_dict,
)
from scripts.auto_apkmirror_prs import load_missing_packages, resolve_candidates


class APKMirrorAppRegistrationTests(TestCase):
    """Verify APKMirror metadata can drive the standard source/patch/README registration."""

    def test_metadata_parser_prefers_app_link_and_unescapes_display_name(self: Self) -> None:
        """APKMirror's app link is the canonical source path and app names can contain HTML entities."""
        metadata = _metadata_from_api_response(
            "ch.protonvpn.android",
            {
                "data": [
                    {
                        "pname": "ch.protonvpn.android",
                        "exists": True,
                        "app": {
                            "name": "Proton VPN: Fast &amp; Secure VPN",
                            "link": "/apk/proton-technologies-ag/protonvpn-secure-and-free-vpn/",
                        },
                    },
                ],
            },
        )

        self.assertEqual("proton-technologies-ag", metadata.org)
        self.assertEqual("protonvpn-secure-and-free-vpn", metadata.app)
        self.assertEqual("Proton VPN: Fast & Secure VPN", metadata.display_name)

    def test_metadata_parser_falls_back_to_release_link(self: Self) -> None:
        """Some API items may only expose a release link, which still carries the org/app path."""
        metadata = _metadata_from_api_response(
            "com.example.reader",
            {
                "data": [
                    {
                        "pname": "com.example.reader",
                        "exists": True,
                        "release": {
                            "link": "/apk/example/example-reader/example-reader-1-0-release/",
                        },
                    },
                ],
            },
        )

        self.assertEqual("example", metadata.org)
        self.assertEqual("example-reader", metadata.app)
        self.assertEqual("example-reader", metadata.display_name)

    def test_metadata_parser_rejects_missing_apkmirror_app(self: Self) -> None:
        """Missing APKMirror hits should be skipped by automation instead of producing placeholder PRs."""
        with self.assertRaisesRegex(RuntimeError, "does not have an app"):
            _metadata_from_api_response(
                "com.example.missing",
                {"data": [{"pname": "com.example.missing", "exists": False}]},
            )

    def test_derive_app_key_uses_primary_name_and_avoids_collisions(self: Self) -> None:
        """Generated keys should be recognizable while remaining unique against existing app keys."""
        metadata = APKMirrorApp(
            package_name="ch.protonvpn.android",
            org="proton-technologies-ag",
            app="protonvpn-secure-and-free-vpn",
            display_name="Proton VPN: Fast & Secure VPN",
        )

        self.assertEqual("proton-vpn", derive_app_key(metadata))
        self.assertEqual("proton-vpn-android", derive_app_key(metadata, {"proton-vpn"}))
        self.assertEqual(
            "disney-plus",
            derive_app_key(
                APKMirrorApp(
                    package_name="com.disney.disneyplus",
                    org="disney",
                    app="disney",
                    display_name="Disney+",
                ),
            ),
        )

    def test_missing_packages_json_must_be_a_string_array(self: Self) -> None:
        """Workflow handoff JSON should fail clearly if the status job writes an unexpected shape."""
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "missing_apps.json"
            path.write_text('["com.example.one","com.example.two"]\n', encoding="utf_8")
            self.assertEqual(["com.example.one", "com.example.two"], load_missing_packages(path))

            path.write_text('{"package":"com.example.one"}\n', encoding="utf_8")
            with self.assertRaisesRegex(ValueError, "JSON array"):
                load_missing_packages(path)

    def test_resolve_candidates_uses_apkmirror_metadata_for_branch_and_key(self: Self) -> None:
        """The PR planner should use APKMirror metadata only when the package is not already supported."""
        metadata = APKMirrorApp(
            package_name="com.example.reader",
            org="example",
            app="example-reader",
            display_name="Example Reader",
        )

        with (
            patch("scripts.auto_apkmirror_prs.reserved_app_keys", return_value=set()),
            patch("scripts.auto_apkmirror_prs.discover_apkmirror_app_via_api", return_value=metadata),
        ):
            candidates = resolve_candidates(
                ["com.example.reader"],
                "new-app/apkmirror-",
                "auth",
                "agent",
            )

        self.assertEqual(1, len(candidates))
        self.assertEqual("example-reader", candidates[0].app_key)
        self.assertEqual("new-app/apkmirror-com-example-reader", candidates[0].branch)

    def test_insert_kv_into_class_dict_preserves_closing_brace_indentation(self: Self) -> None:
        """Generated PRs should append one dict item without blank spacer lines or closing-brace drift."""
        content = 'class Patches:\n    values = {\n        "existing.package": "existing-app",\n    }\n'

        new_content, changed = insert_kv_into_dict(
            content,
            r"values\s*=\s*\{",
            "new.package",
            '"new-app"',
        )

        self.assertTrue(changed)
        self.assertEqual(
            "class Patches:\n"
            "    values = {\n"
            '        "existing.package": "existing-app",\n'
            '        "new.package": "new-app",\n'
            "    }\n",
            new_content,
        )
