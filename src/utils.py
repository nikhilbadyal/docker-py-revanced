"""Utilities."""

import inspect
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import requests
from environs import Env
from loguru import logger
from pytz import timezone
from requests import Response, Session

if TYPE_CHECKING:
    from src.app import APP

from src.downloader.sources import APK_MIRROR_APK_CHECK
from src.exceptions import ScrapingError

default_build = [
    "youtube",
    "youtube_music",
]
possible_archs = ["armeabi-v7a", "x86", "x86_64", "arm64-v8a"]
request_header = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (HTML, like Gecko)"
    " Chrome/96.0.4664.93 Safari/537.36",
    "Authorization": "Basic YXBpLWFwa3VwZGF0ZXI6cm01cmNmcnVVakt5MDRzTXB5TVBKWFc4",
    "Content-Type": "application/json",
}
default_cli = "https://github.com/revanced/revanced-cli/releases/latest"
default_patches = "https://github.com/revanced/revanced-patches/releases/latest"
bs4_parser = "html.parser"
changelog_file = "changelog.md"
changelog_json_file = "changelog.json"
request_timeout = 60
session = Session()
session.headers["User-Agent"] = request_header["User-Agent"]
updates_file = "updates.json"
updates_file_url = "https://raw.githubusercontent.com/{github_repository}/{branch_name}/{updates_file}"
changelogs: dict[str, dict[str, str]] = {}
time_zone = "Asia/Kolkata"
app_version_key = "app_version"
patches_version_key = "patches_version"
cli_version_key = "cli_version"
implement_method = "Please implement the method"
status_code_200 = 200
resource_folder = "apks"
branch_name = "changelogs"
app_dump_key = "app_dump"
patches_dl_key = "patches_dl"


def update_changelog(name: str, response: dict[str, str]) -> None:
    """The function `update_changelog` updates the changelog file.

    Parameters
    ----------
    name : str
        A string representing the name of the change or update.
    response : Dict[str, str]
        The `response` parameter is a dictionary that contains information about the changes made. The keys
    in the dictionary represent the type of change (e.g., "bug fix", "feature", "documentation"), and
    the values represent the specific changes made for each type.
    """
    app_change_log = format_changelog(name, response)
    changelogs[name] = app_change_log


def format_changelog(name: str, response: dict[str, str]) -> dict[str, str]:
    """The `format_changelog` returns formatted changelog string.

    Parameters
    ----------
    name : str
        The `name` parameter is a string that represents the name of the changelog. It is used to create a
    collapsible section in the formatted changelog.
    response : Dict[str, str]
        The `response` parameter is a dictionary that contains information about a release. It has the
    following keys:

    Returns
    -------
        a formatted changelog as a dict.
    """
    final_name = f"[{name}]({response['html_url']})"
    return {
        "ResourceName": final_name,
        "Version": response["tag_name"],
        "Changelog": response["body"],
        "PublishedOn": response["published_at"],
    }


def write_changelog_to_file(updates_info: dict[str, Any]) -> None:
    """The function `write_changelog_to_file` writes a given changelog json to a file."""
    markdown_table = inspect.cleandoc(
        """
    | Resource Name | Version | Changelog | Published On | Build By|
    |---------------|---------|-----------|--------------|---------|
    """,
    )
    for app_data in changelogs.values():
        name_link = app_data["ResourceName"]
        version = app_data["Version"]
        changelog = app_data["Changelog"]
        published_at = app_data["PublishedOn"]
        built_by = get_parent_repo()

        # Clean up changelog for markdown
        changelog = changelog.replace("\r\n", "<br>")
        changelog = changelog.replace("\n", "<br>")
        changelog = changelog.replace("|", "\\|")

        # Add row to the Markdown table string
        markdown_table += f"\n| {name_link} | {version} | {changelog} | {published_at} | {built_by} |"
    with Path(changelog_file).open("w", encoding="utf_8") as file1:
        file1.write(markdown_table)
    Path(changelog_json_file).write_text(json.dumps(changelogs, indent=4) + "\n")
    Path(updates_file).write_text(json.dumps(updates_info, indent=4, default=str) + "\n")


def get_parent_repo() -> str:
    """The `get_parent_repo()` function returns the URL of the parent repository.

    Returns
    -------
        the URL of the parent repository, which is "https://github.com/nikhilbadyal/docker-py-revanced".
    """
    project_url = "https://github.com/nikhilbadyal/docker-py-revanced"
    return f"[Docker-py-revanced]({project_url})"


def handle_request_response(response: Response, url: str) -> None:
    """The function handles the response of a GET request and raises an exception if the response code is not 200.

    Parameters
    ----------
    response : Response
        The parameter `response` is of type `Response`, which is likely referring to a response object from
    an HTTP request. This object typically contains information about the response received from the
    server, such as the status code, headers, and response body.
    url: str
        The url on which request was made
    """
    response_code = response.status_code
    if response_code != status_code_200:
        msg = f"Unable to downloaded assets. Reason - {response.text}"
        raise ScrapingError(msg, url=url)


def slugify(string: str) -> str:
    """The `slugify` function converts a string to a slug format.

    Parameters
    ----------
    string : str
        The `string` parameter is a string that you want to convert to a slug format.

    Returns
    -------
        The function `slugify` returns a modified version of the input string in slug format.
    """
    # Convert to lowercase
    modified_string = string.lower()

    # Remove special characters
    modified_string = re.sub(r"[^\w\s-]", ".", modified_string)

    # Replace spaces with dashes
    modified_string = re.sub(r"\s+", ".", modified_string)

    # Remove consecutive dashes
    modified_string = re.sub(r"-+", ".", modified_string)

    # Remove leading and trailing dashes
    return modified_string.strip(".")


def _check_version(output: str) -> None:
    """Check version."""
    if "Runtime Environment" not in output:
        raise subprocess.CalledProcessError(-1, "java -version")
    if "17" not in output and "20" not in output:
        raise subprocess.CalledProcessError(-1, "java -version")


def check_java() -> None:
    """The function `check_java` checks if Java version 17 or higher is installed.

    Returns
    -------
        The function `check_java` does not return any value.
    """
    try:
        jd = subprocess.check_output(["java", "-version"], stderr=subprocess.STDOUT).decode("utf-8")
        jd = jd[1:-1]
        _check_version(jd)
        logger.debug("Cool!! Java is available")
    except subprocess.CalledProcessError:
        logger.error("Java>= 17 must be installed")
        sys.exit(-1)


def delete_old_changelog() -> None:
    """The function `delete_old_changelog` deleted old changelog file."""
    Path(changelog_file).unlink(missing_ok=True)


def apkmirror_status_check(package_name: str) -> Any:
    """The `apkmirror_status_check` function checks if an app exists on APKMirror.

    Parameters
    ----------
    package_name : str
        The `package_name` parameter is a string that represents the name of the app package to check on
    APKMirror.

    Returns
    -------
        the response from the APKMirror API as a JSON object.
    """
    body = {"pnames": [package_name]}
    response = requests.post(APK_MIRROR_APK_CHECK, json=body, headers=request_header, timeout=60)
    return response.json()


def contains_any_word(string: str, words: list[str]) -> bool:
    """Checks if a string contains any word."""
    return any(word in string for word in words)


def datetime_to_ms_epoch(dt: datetime) -> int:
    """Returns millis since epoch."""
    microseconds = time.mktime(dt.timetuple()) * 1000000 + dt.microsecond
    return int(round(microseconds / float(1000)))


def load_older_updates(env: Env) -> dict[str, Any]:
    """Load older updated from updates.json."""
    try:
        update_file_url = updates_file_url.format(
            github_repository=env.str("GITHUB_REPOSITORY"),
            branch_name=branch_name,
            updates_file=updates_file,
        )
        with urllib.request.urlopen(update_file_url) as url:
            return json.load(url)  # type: ignore[no-any-return]
    except Exception as e:  # noqa: BLE001
        logger.error(f"Failed to retrieve update file: {e}")
        return {}


def save_patch_info(app: "APP", updates_info: dict[str, Any]) -> dict[str, Any]:
    """Save version info a patching resources used to a file."""
    updates_info[app.app_name] = {
        app_version_key: app.app_version,
        patches_version_key: app.resource["patches"]["version"],
        cli_version_key: app.resource["cli"]["version"],
        "ms_epoch_since_patched": datetime_to_ms_epoch(datetime.now(timezone(time_zone))),
        "date_patched": datetime.now(timezone(time_zone)),
        "app_dump": app.for_dump(),
    }
    return updates_info
