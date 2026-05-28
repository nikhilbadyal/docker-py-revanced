"""Generate patches using cli."""

import json
import subprocess
from pathlib import Path
from typing import Any

from src.cli_args import DEFAULT_LIST_PATCHES_ARGS, append_cli_argument

# Patch fields are only section delimiters when they are emitted at column zero.
PATCH_DESCRIPTION_STOP_LABELS = ("Enabled:", "Options:", "Compatible packages:")

# Option fields are indented by the CLIs, so option parsing intentionally ignores indentation.
OPTION_TITLE_LABELS = ("Title:", "Name:")
OPTION_FIELD_LABELS = (
    *OPTION_TITLE_LABELS,
    "Description:",
    "Required:",
    "Key:",
    "Default:",
    "Possible values:",
    "Type:",
)

# Java logging can prefix the first data line, but the actual patch payload remains unchanged.
LOG_PREFIXES = ("INFO: ",)


def _normalise_cli_line(line: str) -> str:
    """Remove wrapper logging noise while preserving indentation that signals parser scope."""
    stripped = line.lstrip()
    for prefix in LOG_PREFIXES:
        if stripped.startswith(prefix):
            return stripped.removeprefix(prefix).rstrip()
    return line.rstrip()


def _has_label(line: str, label: str, *, top_level_only: bool) -> bool:
    """Check field labels with scope awareness so option labels do not split patches."""
    candidate = line if top_level_only else line.lstrip()
    return candidate.startswith(label)


def _field_value(line: str, label: str) -> str:
    """Extract a field value after the CLI label without preserving formatting indentation."""
    return line.lstrip().removeprefix(label).strip()


def _has_any_label(line: str, labels: tuple[str, ...], *, top_level_only: bool) -> bool:
    """Share label-boundary checks between patch fields and option fields."""
    return any(_has_label(line, label, top_level_only=top_level_only) for label in labels)


def _section_lines(section: str) -> list[str]:
    """Normalise each line once per section to keep parsing decisions consistent."""
    return [_normalise_cli_line(line) for line in section.splitlines()]


def _collect_multiline_field(
    lines: list[str],
    start_index: int,
    label: str,
    stop_labels: tuple[str, ...],
    *,
    stop_at_top_level: bool,
) -> tuple[str, int]:
    """Collect CLI field continuations until the next scoped field boundary."""
    values = [_field_value(lines[start_index], label)]
    index = start_index + 1

    while index < len(lines):
        line = lines[index]
        if _has_any_label(line, stop_labels, top_level_only=stop_at_top_level):
            break

        # Continuation lines are stored without CLI indentation but keep intentional blank lines.
        values.append(line.strip())
        index += 1

    return "\n".join(values).strip(), index


def _split_patch_sections(text: str) -> list[str]:
    """Split only on top-level patch names so indented option names remain inside a patch."""
    sections: list[str] = []
    current_section: list[str] = []

    for raw_line in text.splitlines():
        line = _normalise_cli_line(raw_line)
        if _has_label(line, "Name:", top_level_only=True):
            if current_section:
                sections.append("\n".join(current_section))
            current_section = [line]
            continue

        # Lines before the first patch are command noise and should not become empty patches.
        if current_section:
            current_section.append(line)

    if current_section:
        sections.append("\n".join(current_section))

    return sections


def _starts_option_block(line: str) -> bool:
    """Recognise both Morphe/Anddea option titles and ReVanced v6 option names."""
    return _has_any_label(line, OPTION_TITLE_LABELS, top_level_only=False)


def _split_option_blocks(option_lines: list[str]) -> list[list[str]]:
    """Split options by their first title/name field while keeping multiline bodies attached."""
    option_blocks: list[list[str]] = []
    current_block: list[str] = []

    for line in option_lines:
        if _starts_option_block(line):
            if current_block:
                option_blocks.append(current_block)
            current_block = [line]
            continue

        # Ignore leading spacer lines, but keep spacers once an option block has started.
        if current_block:
            current_block.append(line)

    if current_block:
        option_blocks.append(current_block)

    return option_blocks


def extract_name_from_section(section: str) -> str | None:
    """Extract the patch name from a top-level section header."""
    for line in _section_lines(section):
        if _has_label(line, "Name:", top_level_only=True):
            return _field_value(line, "Name:")
    return None


def extract_description_from_section(section: str) -> str:
    """Extract the patch description without consuming later patch fields."""
    lines = _section_lines(section)
    for index, line in enumerate(lines):
        if _has_label(line, "Description:", top_level_only=True):
            description, _ = _collect_multiline_field(
                lines,
                index,
                "Description:",
                PATCH_DESCRIPTION_STOP_LABELS,
                stop_at_top_level=True,
            )
            return description
    return ""


def extract_enabled_state_from_section(section: str) -> bool:
    """Extract the patch enabled flag from the top-level metadata."""
    for line in _section_lines(section):
        if _has_label(line, "Enabled:", top_level_only=True):
            return _field_value(line, "Enabled:").lower() == "true"
    return False


def extract_package_info(package_section: str) -> dict[str, Any]:
    """Extract one compatible package entry from CLI package text."""
    lines = [line for line in _section_lines(package_section) if line.strip()]
    if not lines:
        return {"name": "", "versions": None}

    # The helper accepts both raw split text and a full `Package name:` line for compatibility.
    first_line = lines[0]
    package_name = (
        _field_value(first_line, "Package name:")
        if _has_label(first_line, "Package name:", top_level_only=False)
        else first_line.strip()
    )
    versions: list[str] = []
    collecting_versions = False

    for line in lines[1:]:
        if _has_label(line, "Compatible versions:", top_level_only=False):
            inline_versions = _field_value(line, "Compatible versions:")
            if inline_versions:
                versions.extend(inline_versions.split())
            collecting_versions = True
            continue

        if collecting_versions:
            versions.extend(line.strip().split())

    return {"name": package_name, "versions": versions or None}


def extract_compatible_packages_from_section(section: str) -> list[dict[str, Any]]:
    """Extract all compatible packages from a patch section."""
    lines = _section_lines(section)
    compatible_index = next(
        (index for index, line in enumerate(lines) if _has_label(line, "Compatible packages:", top_level_only=True)),
        None,
    )
    if compatible_index is None:
        return []

    packages: list[dict[str, Any]] = []
    current_name: str | None = None
    current_versions: list[str] = []
    collecting_versions = False

    def flush_package() -> None:
        """Commit the current package once its following package or section boundary appears."""
        if current_name is not None:
            packages.append({"name": current_name, "versions": current_versions or None})

    for line in lines[compatible_index + 1 :]:
        if _has_label(line, "Package name:", top_level_only=False):
            flush_package()
            current_name = _field_value(line, "Package name:")
            current_versions = []
            collecting_versions = False
            continue

        if current_name is None:
            continue

        if _has_label(line, "Compatible versions:", top_level_only=False):
            inline_versions = _field_value(line, "Compatible versions:")
            if inline_versions:
                current_versions.extend(inline_versions.split())
            collecting_versions = True
            continue

        if collecting_versions and line.strip():
            current_versions.extend(line.strip().split())

    flush_package()
    return packages


def parse_option_match(option_lines: list[str]) -> dict[str, Any]:
    """Parse one option block across ReVanced, Morphe, and Anddea CLI dialects."""
    # The public helper accepts raw blocks, while extractor callers already pass normalised lines.
    normalised_option_lines = [_normalise_cli_line(line) for line in option_lines]
    title = ""
    description = ""
    required = False
    key = ""
    default = ""
    possible_values: list[str] = []
    option_type = ""
    index = 0

    while index < len(normalised_option_lines):
        line = normalised_option_lines[index]

        if _has_label(line, "Title:", top_level_only=False):
            title, index = _collect_multiline_field(
                normalised_option_lines,
                index,
                "Title:",
                OPTION_FIELD_LABELS,
                stop_at_top_level=False,
            )
            continue

        if _has_label(line, "Name:", top_level_only=False):
            title, index = _collect_multiline_field(
                normalised_option_lines,
                index,
                "Name:",
                OPTION_FIELD_LABELS,
                stop_at_top_level=False,
            )
            continue

        if _has_label(line, "Description:", top_level_only=False):
            description, index = _collect_multiline_field(
                normalised_option_lines,
                index,
                "Description:",
                OPTION_FIELD_LABELS,
                stop_at_top_level=False,
            )
            continue

        if _has_label(line, "Required:", top_level_only=False):
            required = _field_value(line, "Required:").lower() == "true"
            index += 1
            continue

        if _has_label(line, "Key:", top_level_only=False):
            key, index = _collect_multiline_field(
                normalised_option_lines,
                index,
                "Key:",
                OPTION_FIELD_LABELS,
                stop_at_top_level=False,
            )
            continue

        if _has_label(line, "Default:", top_level_only=False):
            default, index = _collect_multiline_field(
                normalised_option_lines,
                index,
                "Default:",
                OPTION_FIELD_LABELS,
                stop_at_top_level=False,
            )
            continue

        if _has_label(line, "Possible values:", top_level_only=False):
            raw_values, index = _collect_multiline_field(
                normalised_option_lines,
                index,
                "Possible values:",
                OPTION_FIELD_LABELS,
                stop_at_top_level=False,
            )
            possible_values = [value.strip() for value in raw_values.splitlines() if value.strip()]
            continue

        if _has_label(line, "Type:", top_level_only=False):
            option_type, index = _collect_multiline_field(
                normalised_option_lines,
                index,
                "Type:",
                OPTION_FIELD_LABELS,
                stop_at_top_level=False,
            )
            continue

        # Unknown spacer or future metadata lines are skipped so one new field does not drop a patch.
        index += 1

    # ReVanced v6 omits `Key:`, so the option name is the only usable key exposed by list-patches.
    option_key = key or title
    return {
        "title": title,
        "description": description,
        "required": required,
        "key": option_key,
        "default": default,
        "possible_values": possible_values,
        "type": option_type,
    }


def extract_options_from_section(section: str) -> list[dict[str, Any]]:
    """Extract options from a patch section without reading compatible package metadata."""
    lines = _section_lines(section)
    options_index = next(
        (index for index, line in enumerate(lines) if _has_label(line, "Options:", top_level_only=True)),
        None,
    )
    if options_index is None:
        return []

    option_lines: list[str] = []
    for line in lines[options_index + 1 :]:
        if _has_label(line, "Compatible packages:", top_level_only=True):
            break
        option_lines.append(line)

    return [parse_option_match(option_block) for option_block in _split_option_blocks(option_lines)]


def parse_single_section(section: str) -> dict[str, Any]:
    """Parse a single patch section into a dictionary."""
    name = extract_name_from_section(section)
    description = extract_description_from_section(section)
    enabled = extract_enabled_state_from_section(section)
    compatible_packages = extract_compatible_packages_from_section(section)
    options = extract_options_from_section(section)

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
    sections = _split_patch_sections(text)
    return [parse_single_section(section) for section in sections]


def convert_command_output_to_json(
    jar_file_name: str,
    patches_file: str,
    cli_lp_args: dict[str, str] | None = None,
    temporary_files_path: str | None = None,
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
    # Morphe list-patches accepts a temp path, so parallel app scans should not share its default directory.
    append_cli_argument(command, list_patches_args.get("TEMPORARY_FILES_PATH", ""), temporary_files_path)
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
