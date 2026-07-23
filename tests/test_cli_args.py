"""Regression tests for CLI argument profile behavior."""

# CLI profile flags are release-sensitive, so tests pin the intended defaults for each known family.
# ruff: noqa: PT009

from typing import Self
from unittest import TestCase

from src.cli_args import append_cli_argument, merge_cli_arg_maps


class CliArgProfileTests(TestCase):
    """Verify profile defaults that affect patch command safety."""

    def test_morphe_profile_enables_continue_on_error(self: Self) -> None:
        """Morphe supports continuing after one patch fails, so the profile should emit the flag by default."""
        list_patch_args, patch_args = merge_cli_arg_maps("morphe-cli", ("", ""))

        self.assertEqual("--continue-on-error", patch_args["CONTINUE_ON_ERROR"])
        self.assertEqual("", patch_args["PURGE"])
        self.assertEqual("-t", list_patch_args["TEMPORARY_FILES_PATH"])
        self.assertEqual("-t", patch_args["TEMPORARY_FILES_PATH"])

    def test_revanced_cli_profile_does_not_emit_morphe_only_flag(self: Self) -> None:
        """The ReVanced profile should avoid Morphe-only flags while keeping ReVanced-supported temp isolation."""
        _, patch_args = merge_cli_arg_maps("revanced-cli", ("", ""))

        self.assertEqual("", patch_args["CONTINUE_ON_ERROR"])
        self.assertEqual("-t", patch_args["TEMPORARY_FILES_PATH"])

    def test_continue_on_error_can_be_overridden_for_custom_profiles(self: Self) -> None:
        """Operators can opt other CLI builds into the flag without changing built-in profile defaults.

        This test verifies that override injection continues to function properly on the updated
        standard 'revanced-cli' profile.
        """
        _, patch_args = merge_cli_arg_maps(
            "revanced-cli",
            ("", "CONTINUE_ON_ERROR=--continue-on-error"),
        )

        self.assertEqual("--continue-on-error", patch_args["CONTINUE_ON_ERROR"])

    def test_empty_template_disables_dynamic_values(self: Self) -> None:
        """Disabled profile keys must not leak dynamic values into commands as positional arguments."""
        args: list[str] = []

        append_cli_argument(args, "", "apks/patch-source-temporary-files/example")

        self.assertEqual([], args)
