"""Create APKMirror support pull requests for missing ReVanced-compatible packages."""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from loguru import logger

from scripts.add_apkmirror_app import (
    DEFAULT_BASIC_AUTH,
    DEFAULT_USER_AGENT,
    APKMirrorApp,
    derive_app_key,
    discover_apkmirror_app_via_api,
    slugify_app_key,
    update_patches_py,
    update_readme_md,
    update_sources_py,
)
from scripts.status_check import missing_apps_file
from src.downloader.sources import apk_sources
from src.patches import Patches


@dataclass(frozen=True)
class APKMirrorPRCandidate:
    """Resolved APKMirror package metadata plus the repo-specific PR identity."""

    metadata: APKMirrorApp
    app_key: str
    branch: str

    @property
    def title(self) -> str:
        """Return the PR and commit title that matches historical APKMirror support PRs."""
        return f"🎨 Added {self.metadata.display_name}"


def parse_args() -> argparse.Namespace:
    """Parse automation inputs from the GitHub Actions job."""
    parser = argparse.ArgumentParser(description="Create APKMirror support PRs for missing apps")
    parser.add_argument(
        "--missing-apps-json",
        default=missing_apps_file,
        help="Path to the JSON array produced by scripts.status_check",
    )
    parser.add_argument(
        "--base-branch",
        default="main",
        help="Pull request base branch name",
    )
    parser.add_argument(
        "--base-ref",
        default="origin/main",
        help="Git ref used to reset each generated branch before editing files",
    )
    parser.add_argument(
        "--branch-prefix",
        default="new-app/apkmirror-",
        help="Prefix for deterministic generated branches",
    )
    parser.add_argument(
        "--label",
        default="apkmirror⬇️",
        help="Label applied to generated APKMirror pull requests",
    )
    parser.add_argument(
        "--apkmirror-auth",
        default=DEFAULT_BASIC_AUTH,
        help="Base64 for Basic Authorization header to APKMirror API",
    )
    parser.add_argument(
        "--user-agent",
        default=DEFAULT_USER_AGENT,
        help="User-Agent value for APKMirror API",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Resolve candidates without pushing branches or creating PRs",
    )
    return parser.parse_args()


def load_missing_packages(path: Path) -> list[str]:
    """Load the package list from status-check JSON and reject malformed workflow handoff data."""
    data = json.loads(path.read_text(encoding="utf_8"))
    if not isinstance(data, list) or not all(isinstance(item, str) for item in data):
        msg = f"{path} must contain a JSON array of package-name strings"
        raise ValueError(msg)
    return data


def reserved_app_keys() -> set[str]:
    """Return app keys already claimed by source mappings or package mappings."""
    # Both dictionaries define user-facing app keys, so a generated key must avoid both surfaces.
    return set(apk_sources).union(Patches.support_app().values())


def resolve_candidate(
    package_name: str,
    reserved_keys: set[str],
    branch_prefix: str,
    auth_b64: str,
    user_agent: str,
) -> APKMirrorPRCandidate | None:
    """Resolve one missing package into a PR candidate when APKMirror has a matching app."""
    if package_name in Patches.support_app():
        logger.info(f"Skipping {package_name}; it is already supported in src/patches.py.")
        return None

    try:
        metadata = discover_apkmirror_app_via_api(package_name, auth_b64, user_agent)
    except (RuntimeError, TypeError) as exc:
        logger.info(f"Skipping {package_name}; APKMirror lookup did not produce a usable app: {exc}")
        return None

    app_key = derive_app_key(metadata, reserved_keys)
    reserved_keys.add(app_key)
    branch = f"{branch_prefix}{slugify_app_key(package_name)}"
    return APKMirrorPRCandidate(metadata=metadata, app_key=app_key, branch=branch)


def resolve_candidates(
    packages: list[str],
    branch_prefix: str,
    auth_b64: str,
    user_agent: str,
) -> list[APKMirrorPRCandidate]:
    """Resolve the next APKMirror-backed package so app-support PRs queue behind one base branch."""
    keys = reserved_app_keys()
    candidates = []
    for package_name in packages:
        candidate = resolve_candidate(package_name, keys, branch_prefix, auth_b64, user_agent)
        if not candidate:
            continue
        candidates.append(candidate)
        # Every generated app PR edits the same README list and source dictionaries, so stop after one
        # candidate to avoid creating sibling branches that immediately conflict after the first merge.
        break
    return candidates


def run_command(command: list[str], *, capture: bool = False, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run a local command with consistent text output handling for git and gh calls."""
    logger.debug("Running command: {}", " ".join(command))
    return subprocess.run(command, capture_output=capture, check=check, text=True)


def apply_repo_changes(candidate: APKMirrorPRCandidate, *, dry_run: bool) -> bool:
    """Apply the standard three-file APKMirror support update for one candidate."""
    changed_sources = update_sources_py(
        candidate.app_key,
        candidate.metadata.org,
        candidate.metadata.app,
        dry_run=dry_run,
    )
    changed_patches = update_patches_py(candidate.metadata.package_name, candidate.app_key, dry_run=dry_run)
    changed_readme = update_readme_md(
        candidate.app_key,
        candidate.metadata.org,
        candidate.metadata.app,
        dry_run=dry_run,
    )
    return changed_sources or changed_patches or changed_readme


def build_pr_body(candidate: APKMirrorPRCandidate) -> str:
    """Build a short PR body with enough source evidence for review."""
    return "\n".join(
        [
            f"Automated APKMirror support update for `{candidate.metadata.package_name}`.",
            "",
            f"- App key: `{candidate.app_key}`",
            f"- APKMirror: {candidate.metadata.url}",
        ],
    )


def existing_pr_url(branch: str) -> str:
    """Return the open PR URL for a generated branch, if one already exists."""
    result = run_command(
        ["gh", "pr", "list", "--state", "open", "--head", branch, "--json", "url", "--jq", '.[0].url // ""'],
        capture=True,
    )
    return result.stdout.strip()


def create_or_update_pr(candidate: APKMirrorPRCandidate, base_branch: str, label: str) -> None:
    """Create a new PR or refresh the existing generated PR for the same package branch."""
    body = build_pr_body(candidate)
    pr_url = existing_pr_url(candidate.branch)
    if pr_url:
        run_command(["gh", "pr", "edit", pr_url, "--title", candidate.title, "--body", body, "--add-label", label])
        logger.info(f"Updated existing APKMirror PR for {candidate.metadata.package_name}: {pr_url}")
        return

    run_command(
        [
            "gh",
            "pr",
            "create",
            "--base",
            base_branch,
            "--head",
            candidate.branch,
            "--title",
            candidate.title,
            "--body",
            body,
            "--label",
            label,
        ],
    )
    logger.info(f"Created APKMirror PR for {candidate.metadata.package_name}.")


def push_candidate_branch(candidate: APKMirrorPRCandidate, base_ref: str) -> bool:
    """Create a deterministic branch containing only one APKMirror app support change."""
    run_command(
        ["git", "fetch", "origin", f"+refs/heads/{candidate.branch}:refs/remotes/origin/{candidate.branch}"],
        capture=True,
        check=False,
    )
    run_command(["git", "checkout", "-B", candidate.branch, base_ref])

    if not apply_repo_changes(candidate, dry_run=False):
        logger.info(f"Skipping {candidate.metadata.package_name}; the repository already has the requested entries.")
        return False

    run_command(["git", "add", "README.md", "src/downloader/sources.py", "src/patches.py"])
    staged = run_command(["git", "diff", "--cached", "--quiet"], check=False)
    if staged.returncode == 0:
        logger.info(f"Skipping {candidate.metadata.package_name}; no staged change remained after applying updates.")
        return False

    run_command(["git", "commit", "-m", candidate.title])
    # Generated branches are owned by this automation, so refreshing stale bot PRs is intentional.
    run_command(["git", "push", "--force-with-lease", "origin", f"HEAD:{candidate.branch}"])
    return True


def process_candidate(candidate: APKMirrorPRCandidate, args: argparse.Namespace) -> None:
    """Handle one resolved candidate from file edits through PR creation."""
    if args.dry_run:
        if apply_repo_changes(candidate, dry_run=True):
            logger.info(f"Would create APKMirror PR for {candidate.metadata.package_name} as {candidate.app_key}.")
        return

    if push_candidate_branch(candidate, args.base_ref):
        create_or_update_pr(candidate, args.base_branch, args.label)


def main() -> None:
    """Resolve missing packages and open the next APKMirror support PR for a resolvable app."""
    args = parse_args()
    packages = load_missing_packages(Path(args.missing_apps_json))
    candidates = resolve_candidates(packages, args.branch_prefix, args.apkmirror_auth, args.user_agent)
    if not candidates:
        logger.info("No APKMirror-backed missing apps found.")
        return

    for candidate in candidates:
        process_candidate(candidate, args)


if __name__ == "__main__":
    main()
