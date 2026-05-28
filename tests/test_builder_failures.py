"""Regression tests for builder failure propagation."""

# These tests guard CI/release behavior: failed patch commands and failed apps must fail the build.
# The repo's local test command is unittest, so assertion contexts stay on TestCase instead of pytest.
# ruff: noqa: PT027

from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Self, cast
from unittest import TestCase
from unittest.mock import patch

import main as builder_main
from src.app import APP
from src.config import RevancedConfig
from src.exceptions import PatchingFailedError
from src.parser import Parser

if TYPE_CHECKING:
    from src.patches import Patches


class _FailedProcess:
    """Process double that emits output but exits non-zero like a failed CLI invocation."""

    def __init__(self: Self) -> None:
        """Store process output on the instance so each mocked run is isolated."""
        self.stdout = [b"patching failed\n"]
        self.returncode = 2

    def wait(self: Self) -> int:
        """Return the configured non-zero code after stdout has been drained."""
        return self.returncode


def _patch_app() -> APP:
    """Build the minimum APP-shaped object needed to assemble a patch command."""
    return cast(
        "APP",
        SimpleNamespace(
            app_name="youtube",
            archs_to_build=[],
            cli_p_args={
                "APK": "__POSITIONAL__",
                "CMD": "patch",
                "DISABLED": "-d",
                "ENABLED": "-e",
                "EXCLUSIVE": "--exclusive",
                "FORCE": "--force",
                "KEYSTORE": "--keystore",
                "KEYSTORE_ENTRY_ALIAS": "",
                "KEYSTORE_ENTRY_PASSWORD": "",
                "KEYSTORE_PASSWORD": "",
                "OPTIONS": "-O",
                "OUTPUT": "-o",
                "PATCHES": "-p",
                "PATCHES_POST": "-b",
                "PURGE": "--purge",
                "RIP_LIB": "",
                "STRIPLIBS": "",
            },
            download_file_name="youtube.apk",
            get_output_file_name=lambda: "youtube-output.apk",
            keystore_name="revanced.keystore",
            old_key=False,
            patch_bundles=[{"file_name": "patches.rvp"}],
            resource={"cli": {"file_name": "revanced-cli.jar"}},
        ),
    )


def _config() -> RevancedConfig:
    """Build the minimum RevancedConfig-shaped object needed by Parser.patch_app."""
    return cast(
        "RevancedConfig",
        SimpleNamespace(ci_test=False, rip_libs_apps=[], temp_folder=Path("apks")),
    )


class BuilderFailureTests(TestCase):
    """Verify failed builder work is surfaced as a failed build."""

    def test_patch_app_raises_when_cli_exits_non_zero(self: Self) -> None:
        """CLI log output is not success; the exit code must be enforced."""
        parser = Parser(cast("Patches", object()), _config())

        with patch("src.parser.Popen", return_value=_FailedProcess()), self.assertRaises(PatchingFailedError):
            parser.patch_app(_patch_app())

    def test_main_fails_after_writing_partial_metadata_for_failed_apps(self: Self) -> None:
        """The builder should write successful metadata but still fail when any requested app fails."""
        env = SimpleNamespace(read_env=lambda: None)
        config = SimpleNamespace(
            apps=["youtube", "reddit"],
            ci_test=True,
            disable_caching=False,
            dry_run=False,
            max_parallel_apps=4,
        )
        side_effects = [{"youtube": {"output_file_name": "youtube.apk"}}, PatchingFailedError("reddit failed")]

        with (
            patch("main.Env", return_value=env),
            patch("main.RevancedConfig", return_value=config),
            patch("main.Downloader.extra_downloads"),
            patch("main.check_java"),
            patch("main.delete_old_changelog"),
            patch("main.load_older_updates", return_value={}),
            patch("main.process_single_app", side_effect=side_effects),
            patch("main.write_changelog_to_file") as write_changelog,
            patch("main.generate_obtainium_export") as generate_obtainium,
            self.assertRaisesRegex(PatchingFailedError, "reddit"),
        ):
            builder_main.main()

        write_changelog.assert_called_once()
        generate_obtainium.assert_called_once()
