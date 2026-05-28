"""Regression tests for parsing ReVanced-family list-patches output."""

# These samples mirror the three live CLI dialects the builder supports today.
# unittest keeps this parser coverage aligned with the existing project test style.
# ruff: noqa: PT009

from contextlib import chdir
from tempfile import TemporaryDirectory
from typing import Any, Self
from unittest import TestCase
from unittest.mock import patch

from src.cli_args import merge_cli_arg_maps
from src.patches import Patches
from src.patches_gen import convert_command_output_to_json, parse_text_to_json

EXPECTED_REVANCED_PATCH_COUNT = 2
EXPECTED_REVANCED_OPTION_COUNT = 2

REVANCED_SAMPLE = """INFO: Name: Spoof build info
Description: Spoofs the device build information.
Enabled: false
Options:
\tName: Board
\tDescription: The name of the underlying board.
\tRequired: false
\t
\tType: kotlin.String
\t
\tName: Bootloader
\tDescription: The system bootloader version.
\tRequired: false
\tDefault: unknown
\tType: kotlin.String
Compatible packages:
\tPackage name: com.google.android.youtube
\tCompatible versions:
\t\t20.47.62

Name: Spoof client
Description: Spoofs the Reddit OAuth client.
Enabled: true
Options:
\tName: Application client ID
\tDescription: The Reddit OAuth application client ID.
\tRequired: true
\tDefault: redreader-client-id
\tPossible values:
\t\tredreader-client-id (RedReader)
\tType: kotlin.String
Compatible packages:
\tPackage name: com.onelouder.baconreader
"""

MORPHE_SAMPLE = """INFO: Name: Custom branding
Description: Adds custom branding.
Enabled: false
Options:
\tTitle: Custom icon
\tDescription: Folder path to a custom icon.
\t
\tThe folder must contain density-specific resources:
\t- mipmap-mdpi
\tRequired: false
\tKey: customIcon
\tType: kotlin.String
Compatible packages:
\tPackage name: com.google.android.youtube
\tCompatible versions:
\t\t20.47.62
"""

ANDDEA_SAMPLE = """INFO: Name: GmsCore support
Description: Adds GmsCore support.
Enabled: true
Options:
\tTitle: GmsCore vendor group ID
\tDescription: The package name of the GmsCore vendor.
\tRequired: true
\tKey: gmsCoreVendorGroupId
\tDefault: app.revanced
\tPossible values:
\t\tapp.revanced
\t\tcom.google
\t\tcom.mgoogle
\tType: kotlin.String
Compatible packages:
\tPackage name: com.google.android.youtube
\tCompatible versions:
\t\t20.47.62
\t\t20.48.46
"""


def _patch_by_name(patches: list[dict[Any, Any]], name: str) -> dict[Any, Any]:
    """Find patches by name so tests stay focused on parser behavior instead of list ordering."""
    return next(patch for patch in patches if patch["name"] == name)


class PatchesGenParserTests(TestCase):
    """Verify parser compatibility with current ReVanced, Morphe, and Anddea output shapes."""

    def test_recommended_version_uses_newest_compatible_version(self: Self) -> None:
        """Compatible versions may be listed newest-to-oldest, so the builder must not pick the final entry."""
        selected_version = Patches.select_recommended_version(["8.47.56", "7.29.52"])

        self.assertEqual("8.47.56", selected_version)

    def test_recommended_version_falls_back_to_first_unparseable_version(self: Self) -> None:
        """Non-standard app versions should stay deterministic instead of crashing patch metadata parsing."""
        selected_version = Patches.select_recommended_version(["beta-current", "beta-old"])

        self.assertEqual("beta-current", selected_version)

    def test_revanced_indented_option_names_do_not_split_patch_sections(self: Self) -> None:
        """ReVanced v6 option `Name:` fields should not become fake patch sections."""
        patches = parse_text_to_json(REVANCED_SAMPLE)
        patch_names = {patch["name"] for patch in patches}
        build_info = _patch_by_name(patches, "Spoof build info")
        spoof_client = _patch_by_name(patches, "Spoof client")

        self.assertEqual(EXPECTED_REVANCED_PATCH_COUNT, len(patches))
        self.assertNotIn("Board", patch_names)
        self.assertEqual(EXPECTED_REVANCED_OPTION_COUNT, len(build_info["options"]))
        self.assertEqual("Application client ID", spoof_client["options"][0]["key"])
        self.assertEqual(["redreader-client-id (RedReader)"], spoof_client["options"][0]["possible_values"])

    def test_morphe_title_key_options_preserve_multiline_description(self: Self) -> None:
        """Morphe options expose a title plus explicit key and can include multiline descriptions."""
        patches = parse_text_to_json(MORPHE_SAMPLE)
        custom_branding = _patch_by_name(patches, "Custom branding")
        option = custom_branding["options"][0]

        self.assertEqual("Custom icon", option["title"])
        self.assertEqual("customIcon", option["key"])
        self.assertIn("- mipmap-mdpi", option["description"])
        self.assertEqual(["20.47.62"], custom_branding["compatiblePackages"][0]["versions"])

    def test_anddea_keyed_options_preserve_possible_values(self: Self) -> None:
        """Anddea options use Morphe-style keys and line-based possible values."""
        patches = parse_text_to_json(ANDDEA_SAMPLE)
        gms_core = _patch_by_name(patches, "GmsCore support")
        option = gms_core["options"][0]

        self.assertEqual("GmsCore vendor group ID", option["title"])
        self.assertEqual("gmsCoreVendorGroupId", option["key"])
        self.assertEqual(["app.revanced", "com.google", "com.mgoogle"], option["possible_values"])
        self.assertEqual(["20.47.62", "20.48.46"], gms_core["compatiblePackages"][0]["versions"])

    def test_morphe_list_patches_uses_isolated_temp_path(self: Self) -> None:
        """Morphe list-patches also supports temp paths, so parallel scans should not share its default."""
        list_patch_args, _ = merge_cli_arg_maps("morphe-cli", ("", ""))

        with (
            TemporaryDirectory() as temp_dir,
            chdir(temp_dir),
            patch("src.patches_gen.run_command_and_capture_output", return_value=MORPHE_SAMPLE) as run_command,
        ):
            convert_command_output_to_json("morphe-cli.jar", "patches.mpp", list_patch_args, "tmp/youtube")

        command = run_command.call_args.args[0]
        self.assertIn("-t", command)
        self.assertIn("tmp/youtube", command)
