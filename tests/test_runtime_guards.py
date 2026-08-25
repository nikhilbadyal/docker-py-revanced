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

    def str(self: Self, key: str, default: str = "") -> str:
        """Return stable fake credentials so log assertions can detect leaks."""
        values = {"APKEEP_EMAIL": "user@example.test", "APKEEP_TOKEN": "super-secret-token"}
        return values.get(key, default)


class _NoCredsEnv:
    """Env double with no APKEEP credentials configured, for providers that don't need them."""

    def str(self: Self, key: str, default: str = "") -> str:
        """Always fall back to the default, simulating unset credentials."""
        return default


def _apkeep_config(temp_folder: Path, env: object = None) -> RevancedConfig:
    """Build the minimum RevancedConfig-shaped object needed by Apkeep."""
    return cast(
        "RevancedConfig",
        SimpleNamespace(env=env or _Env(), temp_folder=temp_folder, temp_folder_name=str(temp_folder)),
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
        # Verify Java 26 (>= 21) successfully passes version check.
        _check_version('openjdk version "26.0.1" 2026-04-21\nOpenJDK Runtime Environment')

    def test_java_version_parser_rejects_unsupported_major_versions(self: Self) -> None:
        """Java versions below 21 cannot run the current patching toolchain."""
        # Verify Java 17 (< 21) raises CalledProcessError because Java 21 is now the required minimum.
        with self.assertRaises(subprocess.CalledProcessError):
            _check_version('openjdk version "17.0.12" 2024-07-16\nOpenJDK Runtime Environment')

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
                app = cast("APP", SimpleNamespace(package_name="com.example", download_source="apkeep"))
                Apkeep(_apkeep_config(temp_folder)).latest_version(app)

        logged_text = "\n".join(str(call.args) for call in debug_log.call_args_list)
        self.assertNotIn("user@example.test", logged_text)
        self.assertNotIn("super-secret-token", logged_text)
        self.assertIn("<redacted-email>", logged_text)
        self.assertIn("<redacted-token>", logged_text)

    def test_apkeep_uses_provider_from_source_suffix(self: Self) -> None:
        """`apkeep:<provider>` should pass that provider straight through to apkeep's -d flag."""
        with TemporaryDirectory() as tmp_dir:
            temp_folder = Path(tmp_dir)
            process = _ApkeepProcess(temp_folder / "com.example.apk")

            with patch("src.downloader.apkeep.Popen", return_value=process) as popen:
                app = cast("APP", SimpleNamespace(package_name="com.example", download_source="apkeep:f-droid"))
                Apkeep(_apkeep_config(temp_folder)).latest_version(app)

        cmd = popen.call_args.args[0]
        self.assertIn("f-droid", cmd)
        self.assertNotIn("google-play", cmd)

    def test_apkeep_defaults_to_google_play_without_a_provider_suffix(self: Self) -> None:
        """A bare `apkeep` source (no `:provider`) should keep defaulting to google-play."""
        with TemporaryDirectory() as tmp_dir:
            temp_folder = Path(tmp_dir)
            process = _ApkeepProcess(temp_folder / "com.example.apk")

            with patch("src.downloader.apkeep.Popen", return_value=process) as popen:
                app = cast("APP", SimpleNamespace(package_name="com.example", download_source="apkeep"))
                Apkeep(_apkeep_config(temp_folder)).latest_version(app)

        cmd = popen.call_args.args[0]
        self.assertIn("google-play", cmd)

    def test_apkeep_specific_version_appends_at_version_to_the_package_arg(self: Self) -> None:
        """specific_version should use apkeep's `package@version` convention (unsupported on google-play)."""
        with TemporaryDirectory() as tmp_dir:
            temp_folder = Path(tmp_dir)
            process = _ApkeepProcess(temp_folder / "com.example.apk")

            with patch("src.downloader.apkeep.Popen", return_value=process) as popen:
                app = cast("APP", SimpleNamespace(package_name="com.example", download_source="apkeep:f-droid"))
                Apkeep(_apkeep_config(temp_folder)).specific_version(app, "1.2.3")

        cmd = popen.call_args.args[0]
        self.assertIn("com.example@1.2.3", cmd)

    def test_apkeep_omits_credential_flags_when_not_configured(self: Self) -> None:
        """A provider that doesn't need Google credentials shouldn't require APKEEP_EMAIL/TOKEN."""
        with TemporaryDirectory() as tmp_dir:
            temp_folder = Path(tmp_dir)
            process = _ApkeepProcess(temp_folder / "com.example.apk")
            config = _apkeep_config(temp_folder, env=_NoCredsEnv())

            with patch("src.downloader.apkeep.Popen", return_value=process) as popen:
                app = cast("APP", SimpleNamespace(package_name="com.example", download_source="apkeep:f-droid"))
                Apkeep(config).latest_version(app)

        cmd = popen.call_args.args[0]
        self.assertNotIn("-e", cmd)
        self.assertNotIn("-t", cmd)
