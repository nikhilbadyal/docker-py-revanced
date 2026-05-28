"""Regression tests for the ReVanced v5 status-check path."""

# The status check now bridges the v5 API release object and ReVanced CLI output, so tests focus on that contract.
# ruff: noqa: PT009

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Self
from unittest import TestCase
from unittest.mock import patch

from scripts.status_check import _build_v5_list_patches_command, _compatible_apps_from_patches, _write_missing_apps_file


class StatusCheckV5Tests(TestCase):
    """Verify the status check consumes v5 bundle metadata without the removed v4 JSON list."""

    def test_v5_list_patches_command_uses_bundle_flags(self: Self) -> None:
        """ReVanced CLI v6 requires explicit patch bundle and bypass flags for API-hosted `.rvp` files."""
        command = _build_v5_list_patches_command(Path("revanced-cli.jar"), Path("patches.rvp"))

        self.assertEqual("java", command[0])
        self.assertIn("list-patches", command)
        self.assertIn("--packages", command)
        self.assertIn("--versions", command)
        self.assertIn("-p", command)
        self.assertIn("patches.rvp", command)
        self.assertIn("-b", command)

    def test_compatible_apps_are_collected_from_parser_shape(self: Self) -> None:
        """Parsed v5 patch metadata stores compatible package names under each package object."""
        patches: list[dict[str, Any]] = [
            {
                "name": "Video ads",
                "compatiblePackages": [
                    {"name": "com.google.android.youtube", "versions": ["20.47.62"]},
                    {"name": "com.google.android.apps.youtube.music", "versions": ["8.45.54"]},
                ],
            },
            {
                "name": "Universal patch",
                "compatiblePackages": None,
            },
        ]

        self.assertEqual(
            {"com.google.android.youtube", "com.google.android.apps.youtube.music"},
            _compatible_apps_from_patches(patches),
        )

    def test_missing_apps_file_is_compact_json_for_workflow_output(self: Self) -> None:
        """The PR job consumes a compact JSON handoff from the status job instead of reparsing markdown."""
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "missing_apps.json"
            with patch("scripts.status_check.missing_apps_file", str(path)):
                _write_missing_apps_file(["com.example.one", "com.example.two"])

            self.assertEqual(["com.example.one", "com.example.two"], json.loads(path.read_text(encoding="utf_8")))
            self.assertEqual('["com.example.one","com.example.two"]\n', path.read_text(encoding="utf_8"))
