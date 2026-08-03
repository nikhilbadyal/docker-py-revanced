"""Utilities."""

import html
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
from urllib.parse import quote
from zoneinfo import ZoneInfo

import cloudscraper
import requests
from environs import Env
from loguru import logger
from requests import Response, Session

if TYPE_CHECKING:
    from src.app import APP
    from src.config import RevancedConfig

from src.downloader.sources import APK_MIRROR_APK_CHECK
from src.exceptions import ScrapingError

default_build = [
    "youtube",
    "youtube_music",
]
possible_archs = ["armeabi-v7a", "x86", "x86_64", "arm64-v8a"]
# Set Java 21 as the minimum required major version for running ReVanced patching toolchain.
minimum_java_major_version = 21
# Use a syntactically valid desktop Chrome identity because APKMirror and artifact hosts may reject impossible browsers.
request_header = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko)"
    " Chrome/96.0.4664.93 Safari/537.36",
    "Authorization": "Basic YXBpLWFwa3VwZGF0ZXI6cm01cmNmcnVVakt5MDRzTXB5TVBKWFc4",
    "Content-Type": "application/json",
}
default_cli = "https://github.com/revanced/revanced-cli/releases/latest"
# Prefer ReVanced's API-hosted patch bundle because it exposes the `.rvp` file directly without relying on
# release pages whose asset metadata may be unavailable or may only contain source archives.
default_patches = "https://api.revanced.app/v5/patches.rvp"
bs4_parser = "html.parser"
changelog_file = "changelog.md"
changelog_json_file = "changelog.json"
request_timeout = 60
session = Session()
session.headers["User-Agent"] = request_header["User-Agent"]

# Singleton cloudscraper session used for all APKMirror requests.
# APKMirror is protected by Cloudflare, which blocks plain requests with a 403
# "Just a moment..." challenge page. cloudscraper transparently solves those
# JS/cookie challenges and returns the real HTML response.
apkmirror_scraper = cloudscraper.create_scraper()
apkmirror_scraper.headers.update({"User-Agent": request_header["User-Agent"]})
updates_file = "updates.json"
updates_file_url = "https://raw.githubusercontent.com/{github_repository}/{branch_name}/{updates_file}"
obtainium_source_url = "https://raw.githubusercontent.com/{github_repository}/{branch_name}/obtainium_sources/{file_name}"
changelogs: dict[str, dict[str, str]] = {}
time_zone = "Asia/Kolkata"
app_version_key = "app_version"
patches_versions_key = "patches_versions"
cli_version_key = "cli_version"
implement_method = "Please implement the method"
status_code_200 = 200
resource_folder = "apks"
branch_name = "changelogs"
app_dump_key = "app_dump"
patches_dl_list_key = "patches_dl_list"


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

    # Collapse separator runs
    modified_string = re.sub(r"-+", ".", modified_string)
    modified_string = re.sub(r"\.+", ".", modified_string)

    # Remove leading and trailing dashes
    return modified_string.strip(".")


def _check_version(output: str) -> None:
    """Check version."""
    # Java version output differs by distribution, so parse the quoted version instead of matching vendor text.
    version_match = re.search(r'version "(?P<major>\d+)(?:\.(?P<minor>\d+))?', output)
    if not version_match:
        raise subprocess.CalledProcessError(-1, "java -version")
    major_version = int(version_match.group("major"))
    # Old Java reports versions as 1.x, so Java 8 appears as 1.8 and needs minor-version normalization.
    if major_version == 1 and version_match.group("minor"):
        major_version = int(version_match.group("minor"))
    if major_version < minimum_java_major_version:
        raise subprocess.CalledProcessError(-1, "java -version")


def check_java() -> None:
    """The function `check_java` checks if Java version 21 or higher is installed.

    Returns
    -------
        The function `check_java` does not return any value.
    """
    try:
        # Retrieve installed Java runtime version details from shell output.
        jd = subprocess.check_output(["java", "-version"], stderr=subprocess.STDOUT).decode("utf-8")
        jd = jd[1:-1]
        # Validate that installed Java version meets minimum required Java 21.
        _check_version(jd)
        logger.debug("Cool!! Java is available")
    except subprocess.CalledProcessError:
        # Log error indicating Java 21+ requirement was not satisfied before exiting.
        logger.error("Java>= 21 must be installed")
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
    return round(microseconds / float(1000))


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
        patches_versions_key: app.get_patch_bundles_versions(),
        cli_version_key: app.resource["cli"]["version"],
        "ms_epoch_since_patched": datetime_to_ms_epoch(datetime.now(ZoneInfo(time_zone))),
        "date_patched": datetime.now(ZoneInfo(time_zone)),
        "app_dump": app.for_dump(),
        "output_file_name": app.get_output_file_name(),
    }
    return updates_info


def _obtainium_deep_link(
    *,
    package_name: str,
    app_name: str,
    author: str,
    source_url: str,
    config: "RevancedConfig",
) -> str:
    """Build an obtainium://app/... link that pre-fills an HTML source, so adding it is one tap."""
    additional_settings = {
        "trackOnly": False,
        "versionExtractionRegEx": config.obtainium_version_extraction_regex,
        "matchGroupToUse": config.obtainium_version_match_group,
        "versionDetection": bool(config.obtainium_version_extraction_regex),
        "apkFilterRegEx": "",
        "invertAPKFilter": False,
        "autoApkFilterByArch": True,
        "appName": app_name,
        "appAuthor": author,
        "about": "",
    }
    app_config = {
        "id": package_name,
        "url": source_url,
        "author": author,
        "name": app_name,
        "preferredApkIndex": 0,
        "additionalSettings": json.dumps(additional_settings, separators=(",", ":")),
        "overrideSource": "HTML",
    }
    # Compact separators keep the link shorter, matching what Obtainium itself produces.
    # quote(..., safe="") never leaves a literal `"` in the output, so this is safe to drop straight into an href.
    return "obtainium://app/" + quote(json.dumps(app_config, separators=(",", ":")), safe="")


def _write_obtainium_index(cards: list[dict[str, str]]) -> None:
    """Write a styled index page of one-click Obtainium "Add app" links.

    Written to the repo root (not obtainium_sources/) because GitHub Pages' branch-deploy mode can only
    serve from a branch's root or its /docs folder - never an arbitrary subfolder.
    """
    rows = "\n".join(
        f"""        <li class="app-card">
            <div class="app-header">
                <span class="app-name">{card["name"]}</span>
                <code class="package-name">{card["package_name"]}</code>
            </div>
            <div class="app-meta">
                <span class="meta-chip">App {card["app_version"]}</span>
                <span class="meta-chip">Patch {card["patch_version"]}</span>
            </div>
            <div class="app-actions">
                <a class="add-button" href="{card["deep_link"]}">Add to Obtainium</a>
                <a class="source-link" href="{card["source_url"]}">View source</a>
            </div>
        </li>"""
        for card in cards
    )
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Obtainium Sources</title>
    <style>
        :root {{
            color-scheme: light dark;
            --bg: #f5f6f8;
            --card-bg: #ffffff;
            --text: #1a1a1a;
            --muted: #5f6368;
            --accent: #2f6fed;
            --accent-text: #ffffff;
            --border: #e2e4e8;
        }}
        @media (prefers-color-scheme: dark) {{
            :root {{
                --bg: #16171a;
                --card-bg: #212226;
                --text: #f1f2f4;
                --muted: #9aa0a6;
                --accent: #6f9dff;
                --accent-text: #0b0d10;
                --border: #33353a;
            }}
        }}
        * {{ box-sizing: border-box; }}
        body {{
            margin: 0;
            padding: 2rem 1rem 3rem;
            background: var(--bg);
            color: var(--text);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }}
        main {{ max-width: 640px; margin: 0 auto; }}
        h1 {{ font-size: 1.5rem; margin-bottom: 0.25rem; }}
        p.intro {{ color: var(--muted); line-height: 1.5; margin-top: 0; }}
        p.intro a {{ color: var(--accent); text-decoration: none; }}
        p.intro a:hover {{ text-decoration: underline; }}
        ul {{ list-style: none; padding: 0; margin: 1.5rem 0 0; display: flex; flex-direction: column; gap: 0.75rem; }}
        .app-card {{
            display: flex;
            flex-direction: column;
            gap: 0.6rem;
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 0.9rem 1.1rem;
        }}
        .app-header {{
            display: flex;
            align-items: baseline;
            flex-wrap: wrap;
            gap: 0.5rem;
        }}
        .app-name {{ font-weight: 600; overflow-wrap: anywhere; }}
        .package-name {{
            font-size: 0.8rem;
            color: var(--muted);
            font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
            overflow-wrap: anywhere;
        }}
        .app-meta {{ display: flex; flex-wrap: wrap; gap: 0.4rem; }}
        .meta-chip {{
            font-size: 0.78rem;
            color: var(--muted);
            background: var(--bg);
            border: 1px solid var(--border);
            border-radius: 999px;
            padding: 0.15rem 0.6rem;
            font-variant-numeric: tabular-nums;
        }}
        .app-actions {{ display: flex; align-items: center; flex-wrap: wrap; gap: 0.75rem; margin-top: 0.2rem; }}
        .add-button {{
            flex-shrink: 0;
            display: inline-block;
            background: var(--accent);
            color: var(--accent-text);
            text-decoration: none;
            font-weight: 600;
            font-size: 0.9rem;
            padding: 0.5rem 0.9rem;
            border-radius: 8px;
            white-space: nowrap;
        }}
        .add-button:hover {{ opacity: 0.9; }}
        .source-link {{
            font-size: 0.85rem;
            color: var(--muted);
            text-decoration: none;
        }}
        .source-link:hover {{ color: var(--accent); text-decoration: underline; }}
    </style>
</head>
<body>
    <main>
        <h1>Obtainium Sources</h1>
        <p class="intro">
            Tap a button below on an Android device with
            <a href="https://github.com/ImranR98/Obtainium">Obtainium</a> installed to add that app as an update
            source. Don't have it yet? Get it from the link above first.
        </p>
        <ul>
{rows}
        </ul>
    </main>
</body>
</html>
"""
    index_path = Path("index.html")
    index_path.write_text(html_content.strip(), encoding="utf_8")
    logger.info(f"Generated Obtainium site index: {index_path}")


def generate_obtainium_export(updates_info: dict[str, Any], config: "RevancedConfig") -> None:
    """Generate HTML files for Obtainium."""
    if not config.obtainium_export:
        return

    obtainium_sources_path = Path("obtainium_sources")
    obtainium_sources_path.mkdir(exist_ok=True)

    github_repository = config.env.str("GITHUB_REPOSITORY", "")
    obtainium_github_tag = config.obtainium_github_tag
    repo_owner = github_repository.split("/")[0] if github_repository else ""

    if not github_repository:
        logger.warning("GITHUB_REPOSITORY not set. Skipping Obtainium export.")
        return

    site_cards: list[dict[str, str]] = []

    for app_name, app_data in updates_info.items():
        if "output_file_name" not in app_data:
            continue

        # Release asset names are URL path segments, so encode them without allowing slash traversal.
        output_file_name = str(app_data["output_file_name"])
        encoded_output_file_name = quote(output_file_name, safe="")
        # Tags are also path segments, and custom tags may contain characters that need encoding.
        encoded_obtainium_github_tag = quote(obtainium_github_tag, safe="")

        # Construct the same public release URL shape GitHub serves for release assets.
        if obtainium_github_tag == "latest":
            # Latest release URLs let the generated HTML survive timestamp-based release tags.
            download_url = f"https://github.com/{github_repository}/releases/latest/download/{encoded_output_file_name}"
        else:
            # Fixed tag URLs are available for users who keep a stable release tag outside the default workflow.
            download_url = (
                f"https://github.com/{github_repository}/releases/download/"
                f"{encoded_obtainium_github_tag}/{encoded_output_file_name}"
            )

        # The HTML source hashes the APK link by default, so this label is informational for users.
        display_version = html.escape(str(app_data.get(app_version_key, "unknown")))
        # App names may come from env configuration, so escape text and slug filenames before writing HTML.
        display_app_name = html.escape(str(app_name))
        html_file_name = f"{slugify(str(app_name)) or 'app'}.html"
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{display_app_name}</title>
</head>
<body>
    <h1>{display_app_name}</h1>
    <p>Latest version: {display_version}</p>
    <a href="{download_url}">Download APK</a>
</body>
</html>
"""
        # Each app gets one HTML source page so users can subscribe to only the apps they patch.
        html_file_path = obtainium_sources_path / html_file_name
        html_file_path.write_text(html_content.strip(), encoding="utf_8")
        logger.info(f"Generated Obtainium export for {app_name}: {html_file_path}")

        if config.obtainium_site_export:
            package_name = str(app_data["app_dump"].get("package_name", ""))
            if not package_name:
                logger.warning(f"No package_name for {app_name}. Skipping its Obtainium deep link.")
            else:
                source_url = obtainium_source_url.format(
                    github_repository=github_repository, branch_name=branch_name, file_name=html_file_name,
                )
                deep_link = _obtainium_deep_link(
                    package_name=package_name,
                    app_name=str(app_name),
                    author=repo_owner,
                    source_url=source_url,
                    config=config,
                )
                patch_versions = ", ".join(str(v) for v in app_data.get(patches_versions_key, [])) or "unknown"
                site_cards.append(
                    {
                        "name": display_app_name,
                        "package_name": html.escape(package_name),
                        "app_version": display_version,
                        "patch_version": html.escape(patch_versions),
                        "deep_link": deep_link,
                        "source_url": html.escape(source_url),
                    },
                )

    if config.obtainium_site_export and site_cards:
        _write_obtainium_index(site_cards)
