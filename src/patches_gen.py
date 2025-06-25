"""Generate patches using cli."""

import json
import re
import subprocess
from pathlib import Path
from typing import Any


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

    def run_command_and_capture_output(patches_command: list[str]) -> Any:
        result = subprocess.run(patches_command, capture_output=True, text=True, check=True)
        return result.stdout

    def parse_text_to_json(text: str) -> list[dict[Any, Any]]:
        # Split the data into individual sections based on "Name:"
        sections = re.split(r"(?=Name:)", text)
        result = []

        for section in sections:
            # Extract the name
            name_match = re.search(r"Name: (.*?)\n", section)
            name = name_match.group(1).strip() if name_match else None

            # Extract the description
            description_match = re.search(r"Description: (.*?)\n", section)
            description = description_match.group(1).strip() if description_match else ""

            # Extract the enabled state
            enabled_match = re.search(r"Enabled: (true|false)", section, re.IGNORECASE)
            enabled = enabled_match.group(1).lower() == "true" if enabled_match else False

            # Extract compatible packages
            compatible_packages = []
            if "Compatible packages:" in section:
                package_sections = re.split(r"\s*Package name: ", section.split("Compatible packages:")[1])
                for package_section in package_sections[1:]:  # Skip the initial split
                    package_name = package_section.split("\n")[0].strip()
                    versions_match = re.search(r"Compatible versions:\s*((?:\d+\.\d+\.\d+\s*)+)", package_section)
                    versions = versions_match.group(1).split() if versions_match else []
                    compatible_packages.append({"name": package_name, "versions": versions if versions else None})

            # Extract options
            options = []
            if "Options:" in section:
                options_section = section.split("Options:")[1]
                option_matches = re.findall(
                    r"Title: (.*?)\n\s*Description: (.*?)\n\s*Required: (true|false)\n\s*Key: (.*?)\n\s*Default: (.*?)\n(?:\s*Possible values:\s*(.*?))?\s*Type: (.*?)\n",  # noqa: E501
                    options_section,
                    re.DOTALL,
                )
                for match in option_matches:
                    option = {
                        "title": match[0].strip(),
                        "description": match[1].strip(),
                        "required": match[2].lower() == "true",
                        "key": match[3].strip(),
                        "default": match[4].strip(),
                        "possible_values": [v.strip() for v in match[5].split() if v.strip()] if match[5] else [],
                        "type": match[6].strip(),
                    }
                    options.append(option)

            # Append the parsed data
            result.append(
                {
                    "name": name,
                    "description": description,
                    "compatiblePackages": compatible_packages if compatible_packages else None,
                    "use": enabled,
                    "options": options,
                },
            )

        return result

    # Run the command
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
