"""Regression tests for runtime guardrails."""

# These tests cover local runtime safety checks that are easy to regress without full CI.
# The repo's local test command is unittest, so assertion contexts stay on TestCase instead of pytest.
# ruff: noqa: PT009, PT027

import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from typing import TYPE_CHECKING, Self, cast
from unittest import TestCase
from unittest.mock import patch

from src.config import RevancedConfig
from src.downloader.apkeep import Apkeep
from src.utils import _check_version

if TYPE_CHECKING:
    from src.app import APP


class _Env:
    """Small env double that returns APKEEP credentials by key."""

    def str(self: Self, key: str) -> str:
        """Return stable fake credentials so log assertions can detect leaks."""
        values = {"APKEEP_EMAIL": "user@example.test", "APKEEP_TOKEN": "super-secret-token"}
        return values[key]


def _apkeep_config(temp_folder: Path) -> RevancedConfig:
    """Build the minimum RevancedConfig-shaped object needed by Apkeep."""
    return cast(
        "RevancedConfig",
        SimpleNamespace(env=_Env(), temp_folder=temp_folder, temp_folder_name=str(temp_folder)),
    )


class _ApkeepProcess:
    """Process double that creates the expected APK when apkeep completes."""

    def __init__(self: Self, output_file: Path) -> None:
        """Store the file path that simulates apkeep's output side effect."""
        self.output_file = output_file
        self.stdout = [b"downloaded\n"]
        self.returncode = 0

    def wait(self: Self) -> int:
        """Create the expected APK before returning success."""
        self.output_file.write_bytes(b"apk")
        return self.returncode


class RuntimeGuardTests(TestCase):
    """Verify runtime checks and logs fail safely."""

    def test_java_version_parser_accepts_current_major_versions(self: Self) -> None:
        """Java 21+ should pass regardless of vendor wording or release year."""
        _check_version('openjdk version "26.0.1" 2026-04-21\nOpenJDK Runtime Environment')

    def test_java_version_parser_rejects_unsupported_major_versions(self: Self) -> None:
        """Java versions below 21 cannot run the current patching toolchain."""
        with self.assertRaises(subprocess.CalledProcessError):
            _check_version('openjdk version "17.0.24" 2024-07-16\nOpenJDK Runtime Environment')

    def test_apkeep_command_log_redacts_credentials(self: Self) -> None:
        """APKEEP credentials should be used for execution but never written to debug logs."""
        with TemporaryDirectory() as tmp_dir:
            temp_folder = Path(tmp_dir)
            process = _ApkeepProcess(temp_folder / "com.example.apk")

            with (
                patch("src.downloader.apkeep.Popen", return_value=process),
                patch("src.downloader.apkeep.logger.debug") as debug_log,
            ):
                # latest_version is the public APKEEP path that internally builds and logs the command.
                app = cast("APP", SimpleNamespace(package_name="com.example"))
                Apkeep(_apkeep_config(temp_folder)).latest_version(app)

        logged_text = "\n".join(str(call.args) for call in debug_log.call_args_list)
        self.assertNotIn("user@example.test", logged_text)
        self.assertNotIn("super-secret-token", logged_text)
        self.assertIn("<redacted-email>", logged_text)
        self.assertIn("<redacted-token>", logged_text)
