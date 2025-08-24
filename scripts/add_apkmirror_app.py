#!/usr/bin/env python3
r"""CLI to register a new APKMirror app in the repo.

This script automates the manual edits required when ReVanced adds support for a
new app that's available on APKMirror. It updates:
- src/downloader/sources.py: adds the APKMirror source mapping
- src/patches.py: maps package name -> app key
- README.md: appends the bullet link under the officially supported list

Usage examples:
  python scripts/add_apkmirror_app.py \
    --package com.facebook.katana \
    --name facebook \
    --apkmirror-path facebook-2/facebook

  python scripts/add_apkmirror_app.py \
    --package com.facebook.katana \
    --name facebook \
    --apkmirror-url https://www.apkmirror.com/apk/facebook-2/facebook/

Notes
-----
- APKMirror only. For other sources, extend the script accordingly.
- Idempotent: if entries already exist, it will skip updating that file.
"""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[1]
ORG_APP_PARTS = 2
APK_MIRROR_APP_EXISTS_URL = "https://www.apkmirror.com/wp-json/apkm/v1/app_exists/"
DEFAULT_USER_AGENT = os.getenv("APKMIRROR_USER_AGENT", "nikhil")
DEFAULT_BASIC_AUTH = os.getenv(
    "APKMIRROR_AUTH_BASIC",
    # base64("api-apkupdater:rm5rcfruUjKy04sMpyMPJXW8") as provided in the example
    "YXBpLWFwa3VwZGF0ZXI6cm01cmNmcnVVakt5MDRzTXB5TVBKWFc4",
)
DEFAULT_HTTP_TIMEOUT_SECS = 20


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for registering an APKMirror app."""
    parser = argparse.ArgumentParser(description="Register a new APKMirror app")
    parser.add_argument("--package", required=True, help="Android package name, e.g., com.facebook.katana")
    parser.add_argument("--name", required=True, help="Short app key/name used in configs, e.g., facebook")

    apkmirror = parser.add_mutually_exclusive_group(required=False)
    apkmirror.add_argument(
        "--apkmirror-path",
        help="APKMirror path '<org>/<app>' without leading /apk/, e.g., 'facebook-2/facebook'",
    )
    apkmirror.add_argument(
        "--apkmirror-url",
        help="Full APKMirror app URL, e.g., https://www.apkmirror.com/apk/facebook-2/facebook/",
    )

    parser.add_argument(
        "--apkmirror-auth",
        default=DEFAULT_BASIC_AUTH,
        help="Base64 for Basic Authorization header to APKMirror API (env: APKMIRROR_AUTH_BASIC)",
    )
    parser.add_argument(
        "--user-agent",
        default=DEFAULT_USER_AGENT,
        help="User-Agent value for APKMirror API (env: APKMIRROR_USER_AGENT)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show planned changes without writing files",
    )

    return parser.parse_args()


def extract_apkmirror_path(url_or_path: str) -> tuple[str, str]:
    """Return (org, app) from a full URL or 'org/app' path.

    Accepted examples:
      - facebook-2/facebook
      - https://www.apkmirror.com/apk/facebook-2/facebook/
      - https://www.apkmirror.com/apk/facebook-2/facebook
    """
    raw = url_or_path.strip()
    if raw.startswith("http"):
        # Keep only the path after '/apk/'
        m = re.search(r"/apk/([^/?#]+)/([^/?#]+)/?", raw)
        if not m:
            msg = "Unable to parse APKMirror URL. Expected .../apk/<org>/<app>/."
            raise ValueError(
                msg,
            )
        org, app = m.group(1), m.group(2)
    else:
        # org/app
        parts = raw.strip("/").split("/")
        if len(parts) != ORG_APP_PARTS:
            msg = "--apkmirror-path must be '<org>/<app>'"
            raise ValueError(msg)
        org, app = parts
    return org, app


def discover_apkmirror_path_via_api(package_name: str, auth_b64: str, user_agent: str) -> tuple[str, str]:
    """Query APKMirror app_exists API to discover the org/app path for a package.

    Tries `app.link` first, then falls back to `release.link`.
    Returns (org, app).
    """
    headers = {
        "Authorization": f"Basic {auth_b64}",
        "User-Agent": user_agent,
        "Content-Type": "application/json",
    }
    payload = {"pnames": [package_name]}
    resp = requests.post(
        APK_MIRROR_APP_EXISTS_URL,
        headers=headers,
        json=payload,
        timeout=DEFAULT_HTTP_TIMEOUT_SECS,
    )
    if resp.status_code != 200:  # noqa: PLR2004
        msg = f"APKMirror app_exists API error: HTTP {resp.status_code}"
        raise RuntimeError(msg)
    data = resp.json()
    items = data.get("data") or []
    if not items:
        msg = f"No data returned from APKMirror for {package_name}"
        raise RuntimeError(msg)

    item = items[0]
    app_link = ((item.get("app") or {}).get("link")) or ((item.get("release") or {}).get("link"))
    if not app_link:
        msg = "APKMirror response missing app/release link"
        raise RuntimeError(msg)

    # Expect a path like: /apk/<org>/<app>/...
    m = re.search(r"/apk/([^/]+)/([^/]+)/", app_link)
    if not m:
        msg = "Unable to parse org/app from APKMirror response link"
        raise RuntimeError(msg)
    return m.group(1), m.group(2)


def read_text(path: Path) -> str:
    """Read text from a file using UTF-8 encoding."""
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    """Write text to a file using UTF-8 encoding."""
    path.write_text(content, encoding="utf-8")


def insert_kv_into_dict(  # noqa: C901, PLR0912,PLR0915
    content: str,
    dict_var_pattern: str,
    key: str,
    value_code: str,
) -> tuple[str, bool]:
    r"""Insert a key/value into a Python dict literal for a variable.

    - dict_var_pattern: regex to match the variable assignment line that opens the dict
      e.g., r"revanced_package_names[\s\S]*?=\s*\{"
    - key: dictionary key to insert (without quotes)
    - value_code: full code for the value expression (already quoted/f-string as needed)

    Returns: (new_content, changed)
    """
    # Find dict opening
    open_match = re.search(dict_var_pattern, content)
    if not open_match:
        msg = "Could not locate dictionary with given pattern"
        raise RuntimeError(msg)

    # Find the '{' start index and walk to matching '}'
    brace_start = content.find("{", open_match.start())
    if brace_start == -1:
        msg = "Malformed dictionary start: missing '{'"
        raise RuntimeError(msg)

    i = brace_start
    depth = 0
    in_str: str | None = None
    esc = False
    while i < len(content):
        ch = content[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == in_str:
                in_str = None
        elif ch in ('"', "'"):
            in_str = ch
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                brace_end = i
                break
        i += 1
    else:
        msg = "Malformed dictionary: missing closing '}'"
        raise RuntimeError(msg)

    # The dictionary body
    body = content[brace_start + 1 : brace_end]

    # Check if key already exists
    key_re = re.compile(rf"^[ \t]*\"{re.escape(key)}\"\s*:\s*", re.MULTILINE)
    if key_re.search(body):
        return content, False

    # Determine indentation: look for first item, else fallback to 4 spaces more than dict line indent
    # Get indentation of first item (if any)
    item_match = re.search(r"^(?P<indent>[ \t]+)\"[^\n]+\"\s*:\s*", body, re.MULTILINE)
    if item_match:
        indent = item_match.group("indent")
    else:
        # Compute dictionary base indent from line start to '{'
        line_start = content.rfind("\n", 0, brace_start) + 1
        base_indent = content[line_start:brace_start].split("\n")[-1]
        # Count leading spaces/tabs of the line
        m_leading = re.match(r"^[ \t]*", base_indent)
        if not m_leading:
            msg = "Could not determine indentation for dictionary body"
            raise RuntimeError(msg)
        leading = m_leading.group(0)
        indent = leading + " " * 4

    new_entry = f'\n{indent}"{key}": {value_code},'

    # Insert before closing brace
    new_body = body + new_entry + "\n"
    new_content = content[: brace_start + 1] + new_body + content[brace_end:]
    return new_content, True


def update_sources_py(app_key: str, org: str, app: str, *, dry_run: bool) -> bool:
    """Update `src/downloader/sources.py` with the APKMirror mapping.

    Returns True if a change was made.
    """
    path = REPO_ROOT / "src" / "downloader" / "sources.py"
    content = read_text(path)
    value_code = f'f"{ '{' }APK_MIRROR_BASE_APK_URL{ '}' }/{org}/{app}/"'
    pattern = r"apk_sources\s*=\s*\{"
    new_content, changed = insert_kv_into_dict(content, pattern, app_key, value_code)
    if changed and not dry_run:
        write_text(path, new_content)
    return changed


def update_patches_py(package_name: str, app_key: str, *, dry_run: bool) -> bool:
    """Update `src/patches.py` with package -> app key mapping.

    Returns True if a change was made.
    """
    path = REPO_ROOT / "src" / "patches.py"
    content = read_text(path)
    value_code = f'"{app_key}"'
    # Match the dict assignment, accommodating type annotations
    pattern = r"revanced_package_names[\s\S]*?=\s*\{"
    new_content, changed = insert_kv_into_dict(content, pattern, package_name, value_code)
    if changed and not dry_run:
        write_text(path, new_content)
    return changed


def update_readme_md(app_key: str, org: str, app: str, *, dry_run: bool) -> bool:
    """Insert the README bullet link for the new app.

    Returns True if a change was made.
    """
    path = REPO_ROOT / "README.md"
    content = read_text(path)
    bullet = f"    - [{app_key}](https://www.apkmirror.com/apk/{org}/{app}/)"

    # Check if already present (exact label match, beginning of bullet)
    exists_pattern = re.compile(r"^\s*-\s*\[" + re.escape(app_key) + r"\]\(", flags=re.MULTILINE)
    if exists_pattern.search(content):
        return False

    # Locate the supported list block
    # Insert before the note that ends the list
    note = re.search(r"^\s*<br>`\*\*` - You can also patch any other app", content, re.MULTILINE)
    if note:
        insert_pos = note.start()
        new_content = content[:insert_pos] + bullet + "\n" + content[insert_pos:]
    else:
        # Fallback: append at end
        new_content = content.rstrip("\n") + "\n" + bullet + "\n"

    if not dry_run:
        write_text(path, new_content)
    return True


def main() -> None:
    """Entry point: parse args, perform updates, and report results."""
    args = parse_args()

    if args.apkmirror_path or args.apkmirror_url:
        org, app = extract_apkmirror_path(args.apkmirror_path or args.apkmirror_url)
    else:
        org, app = discover_apkmirror_path_via_api(args.package, args.apkmirror_auth, args.user_agent)

    changed_any = False
    changed_sources = update_sources_py(args.name, org, app, dry_run=args.dry_run)
    changed_any = changed_any or changed_sources

    changed_patches = update_patches_py(args.package, args.name, dry_run=args.dry_run)
    changed_any = changed_any or changed_patches

    changed_readme = update_readme_md(args.name, org, app, dry_run=args.dry_run)
    changed_any = changed_any or changed_readme

    if not changed_any:
        pass


if __name__ == "__main__":
    main()
