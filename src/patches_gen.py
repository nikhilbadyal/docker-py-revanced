"""Generate patches using cli."""

import json
import re
import subprocess
from pathlib import Path
from typing import Any

from src.cli_args import DEFAULT_LIST_PATCHES_ARGS, append_cli_argument


def extract_name_from_section(section: str) -> str | None:
    """Extract the name from a section."""
    name_match = re.search(r"Name: (.*?)\n", section)
    return name_match.group(1).strip() if name_match else None


def extract_description_from_section(section: str) -> str:
    """Extract the description from a section."""
    description_match = re.search(r"Description: (.*?)\n", section)
    return description_match.group(1).strip() if description_match else ""


def extract_enabled_state_from_section(section: str) -> bool:
    """Extract the enabled state from a section."""
    enabled_match = re.search(r"Enabled: (true|false)", section, re.IGNORECASE)
    return enabled_match.group(1).lower() == "true" if enabled_match else False


def extract_package_info(package_section: str) -> dict[str, Any]:
    """Extract package name and versions from a package section."""
    package_name = package_section.split("\n", maxsplit=1)[0].strip()
    versions_match = re.search(r"Compatible versions:\s*((?:\d+\.\d+\.\d+\s*)+)", package_section)
    versions = versions_match.group(1).split() if versions_match else []
    return {"name": package_name, "versions": versions or None}


def extract_compatible_packages_from_section(section: str) -> list[dict[str, Any]]:
    """Extract compatible packages from a section."""
    if "Compatible packages:" not in section:
        return []

    package_sections = re.split(r"\s*Package name: ", section.split("Compatible packages:")[1])
    return [extract_package_info(package_section) for package_section in package_sections[1:]]


def parse_option_match(option_dict: dict[str, Any]) -> dict[str, Any]:
    """Parse a single option match into a dictionary."""
    title = option_dict.get("title", "").strip()
    # Use the title as the key if absent
    key = option_dict.get("key", "").strip()
    if not key:
        key = title

    possible_values = []
    if option_dict.get("possible_values"):
        raw_values = option_dict["possible_values"].strip().split("\n")
        option_dict["possible_values"] = [val.strip() for val in raw_values]

    return {
        "title": title,
        "description": option_dict.get("description", "").strip(),
        "required": option_dict.get("required", "").lower() == "true",
        "key": key,
        "default": option_dict.get("default", "").strip() if option_dict.get("default") else None,
        "possible_values": possible_values,
        "type": option_dict.get("type", "").strip(),
    }


def extract_options_from_section(options_section: str) -> list[dict[str, Any]]:
    """Extract options from an options section."""
    regex = re.compile(
        r"(?:Title|Name):\s*(?P<title>[^\n]+)\n"
        r"\s*Description:\s*(?P<description>[^\n]+)\n"
        r"\s*Required:\s*(?P<required>true|false)\n"
        r"(?:\s*Key:\s*(?P<key>[^\n]+)\n)?"
        r"(?:\s*Default:\s*(?P<default>[^\n]+)\n)?"
        r"(?:\s*Possible values:\n(?P<possible_values>[\s\S]*?))?"
        r"\s*Type:\s*(?P<type>[^\n]+)",
        re.VERBOSE,
    )
    return [parse_option_match(match.groupdict()) for match in regex.finditer(options_section)]


def split_section(section: str) -> tuple[str, str]:
    """Split a section into patch and options parts."""
    patch_section = section
    options_section = ""

    options_section_regex = re.compile(r"^Options:(?:\n(?!\w).*)*", re.MULTILINE)
    match = options_section_regex.search(section)
    if match:
        patch_section = (section[: match.start()] + section[match.end() :]).rstrip() + "\n\n"
        options_section = match.group(0)

    return patch_section, options_section


def parse_single_section(section: str) -> dict[str, Any]:
    """Parse a single section into a dictionary."""
    patch_section, options_section = split_section(section)
    name = extract_name_from_section(patch_section)
    description = extract_description_from_section(patch_section)
    enabled = extract_enabled_state_from_section(patch_section)
    compatible_packages = extract_compatible_packages_from_section(patch_section)
    options = extract_options_from_section(options_section)

    return {
        "name": name,
        "description": description,
        "compatiblePackages": compatible_packages or None,
        "use": enabled,
        "options": options,
    }


def run_command_and_capture_output(patches_command: list[str]) -> str:
    """Run command and capture its output."""
    result = subprocess.run(patches_command, capture_output=True, text=True, check=True)
    return result.stdout


def parse_text_to_json(text: str) -> list[dict[Any, Any]]:
    """Parse text output into JSON format."""
    sections = re.split(r"(?=^Name:)", text, flags=re.MULTILINE)
    return [parse_single_section(section) for section in sections]


def convert_command_output_to_json(
    jar_file_name: str,
    patches_file: str,
    cli_lp_args: dict[str, str] | None = None,
) -> list[dict[Any, Any]]:
    """
    Runs the ReVanced CLI command, processes the output, and saves it as a sorted JSON file.

    Args:
        jar_file_name (str): Name or path of the JAR file to run.
        patches_file (str): The patches file name or path to pass to the command.
    """
    # We start from defaults and then overlay resolved per-app profile/override values.
    list_patches_args = dict(DEFAULT_LIST_PATCHES_ARGS)
    if cli_lp_args:
        list_patches_args.update(cli_lp_args)

    # We construct the command from the configurable map to support multiple CLI syntaxes.
    command = ["java", "-jar", jar_file_name, list_patches_args["CMD"]]
    # These toggles reproduce existing behavior and remain configurable for future CLI changes.
    for key in ("INDEX", "PACKAGES", "UNIVERSAL", "VERSIONS", "OPTIONS", "DESCRIPTIONS"):
        append_cli_argument(command, list_patches_args.get(key, ""))
    # This optional flag slot is preserved for advanced users who embed a fixed filter in the template.
    append_cli_argument(command, list_patches_args.get("FILTER_PACKAGE_NAME", ""))
    # Patch bundle argument supports positional, split, or `--flag=value` formatting styles.
    append_cli_argument(command, list_patches_args["PATCHES"], patches_file)
    # Some CLI families require a companion flag per patches file group (e.g., v6 `-b` bypass verification).
    append_cli_argument(command, list_patches_args.get("PATCHES_POST", ""))

    output = run_command_and_capture_output(command)

    parsed_data = parse_text_to_json(output)

    # Filter out invalid entries where "name" is None
    parsed_data = [entry for entry in parsed_data if entry["name"] is not None]

    # Sort the data by the "name" field
    parsed_data.sort(key=lambda x: x["name"])

    with Path("patches.json").open("w") as file:
        json.dump(parsed_data, file, indent=2)

    return parsed_data
