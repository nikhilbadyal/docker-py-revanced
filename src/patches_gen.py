"""Generate patches using cli."""

import json
import re
import subprocess
from pathlib import Path
from typing import Any


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
    package_name = package_section.split("\n")[0].strip()
    versions_match = re.search(r"Compatible versions:\s*((?:\d+\.\d+\.\d+\s*)+)", package_section)
    versions = versions_match.group(1).split() if versions_match else []
    return {"name": package_name, "versions": versions if versions else None}


def extract_compatible_packages_from_section(section: str) -> list[dict[str, Any]]:
    """Extract compatible packages from a section."""
    if "Compatible packages:" not in section:
        return []

    package_sections = re.split(r"\s*Package name: ", section.split("Compatible packages:")[1])
    return [extract_package_info(package_section) for package_section in package_sections[1:]]


def parse_option_match(match: tuple[str, ...]) -> dict[str, Any]:
    """Parse a single option match into a dictionary."""
    return {
        "title": match[0].strip(),
        "description": match[1].strip(),
        "required": match[2].lower() == "true",
        "key": match[3].strip(),
        "default": match[4].strip(),
        "possible_values": [v.strip() for v in match[5].split() if v.strip()] if match[5] else [],
        "type": match[6].strip(),
    }


def extract_options_from_section(section: str) -> list[dict[str, Any]]:
    """Extract options from a section."""
    if "Options:" not in section:
        return []

    options_section = section.split("Options:")[1]
    option_matches = re.findall(
        r"Title: (.*?)\n\s*Description: (.*?)\n\s*Required: (true|false)\n\s*Key: (.*?)\n\s*Default: (.*?)\n(?:\s*Possible values:\s*(.*?))?\s*Type: (.*?)\n",  # noqa: E501
        options_section,
        re.DOTALL,
    )
    return [parse_option_match(match) for match in option_matches]


def parse_single_section(section: str) -> dict[str, Any]:
    """Parse a single section into a dictionary."""
    name = extract_name_from_section(section)
    description = extract_description_from_section(section)
    enabled = extract_enabled_state_from_section(section)
    compatible_packages = extract_compatible_packages_from_section(section)
    options = extract_options_from_section(section)

    return {
        "name": name,
        "description": description,
        "compatiblePackages": compatible_packages if compatible_packages else None,
        "use": enabled,
        "options": options,
    }


def run_command_and_capture_output(patches_command: list[str]) -> str:
    """Run command and capture its output."""
    result = subprocess.run(patches_command, capture_output=True, text=True, check=True)
    return result.stdout


def parse_text_to_json(text: str) -> list[dict[Any, Any]]:
    """Parse text output into JSON format."""
    sections = re.split(r"(?=Name:)", text)
    return [parse_single_section(section) for section in sections]


def convert_command_output_to_json(
    jar_file_name: str,
    patches_file: str,
) -> list[dict[Any, Any]]:
    """
    Runs the ReVanced CLI command, processes the output, and saves it as a sorted JSON file.

    Args:
        jar_file_name (str): Name or path of the JAR file to run.
        patches_file (str): The patches file name or path to pass to the command.
    """
    command = ["java", "-jar", jar_file_name, "list-patches", "-ipuvo", patches_file]
    output = run_command_and_capture_output(command)

    parsed_data = parse_text_to_json(output)

    # Filter out invalid entries where "name" is None
    parsed_data = [entry for entry in parsed_data if entry["name"] is not None]

    # Sort the data by the "name" field
    parsed_data.sort(key=lambda x: x["name"])

    with Path("patches.json").open("w") as file:
        json.dump(parsed_data, file, indent=2)

    return parsed_data
