"""CLI argument profiles and override parsing helpers."""

from __future__ import annotations

import shlex
from copy import deepcopy
from typing import Final

from loguru import logger

# This sentinel makes it explicit that the value is positional and should not be prefixed with any flag.
POSITIONAL_ARG: Final[str] = "__POSITIONAL__"
# This profile keeps current behavior and remains the default until the project intentionally switches versions.
DEFAULT_CLI_PROFILE: Final[str] = "revanced-cli-v6"
# This constant centralizes legacy old-key alias behavior shared across profiles.
KEYSTORE_ALIAS_ARG: Final[str] = "--keystore-entry-alias=alias"
# This constant centralizes legacy old-key entry password behavior shared across profiles.
KEYSTORE_ENTRY_PASSWORD_ARG: Final[str] = "--keystore-entry-password=ReVanced"  # noqa: S105
# This constant centralizes legacy old-key keystore password behavior shared across profiles.
KEYSTORE_PASSWORD_ARG: Final[str] = "--keystore-password=ReVanced"  # noqa: S105

# These keys define the supported and validated map for `list-patches` command generation.
LIST_PATCHES_KEYS: Final[set[str]] = {
    "CMD",
    "DESCRIPTIONS",
    "FILTER_PACKAGE_NAME",
    "INDEX",
    "OPTIONS",
    "PACKAGES",
    "PATCHES",
    "PATCHES_POST",
    "UNIVERSAL",
    "VERSIONS",
}

# These keys define the supported and validated map for `patch` command generation.
PATCH_KEYS: Final[set[str]] = {
    "APK",
    "CMD",
    "DISABLED",
    "ENABLED",
    "EXCLUSIVE",
    "FORCE",
    "KEYSTORE",
    "KEYSTORE_OLD",
    "OPTIONS",
    "OUTPUT",
    "PATCHES",
    "PATCHES_POST",
    "PURGE",
    "RIP_LIB",
    "STRIPLIBS",
}

# These defaults intentionally match the existing builder behavior for current stable users.
DEFAULT_LIST_PATCHES_ARGS: Final[dict[str, list[str]]] = {
    "CMD": ["list-patches"],
    "DESCRIPTIONS": [""],
    "FILTER_PACKAGE_NAME": [""],
    "INDEX": ["-i"],
    "OPTIONS": ["-o"],
    "PACKAGES": ["-p"],
    "PATCHES": [POSITIONAL_ARG],
    "PATCHES_POST": [""],
    "UNIVERSAL": ["-u"],
    "VERSIONS": ["-v"],
}

# These defaults intentionally match the existing patch invocation and keep old-key signing behavior compatible.
DEFAULT_PATCH_ARGS: Final[dict[str, list[str]]] = {
    "APK": [POSITIONAL_ARG],
    "CMD": ["patch"],
    "DISABLED": ["-d"],
    "ENABLED": ["-e"],
    "EXCLUSIVE": ["--exclusive"],
    "FORCE": ["--force"],
    "KEYSTORE": ["--keystore"],
    "KEYSTORE_OLD": [
        KEYSTORE_ALIAS_ARG,
        KEYSTORE_ENTRY_PASSWORD_ARG,
        KEYSTORE_PASSWORD_ARG,
    ],
    "OPTIONS": ["-O"],
    "OUTPUT": ["-o"],
    "PATCHES": ["-p"],
    "PATCHES_POST": [""],
    "PURGE": ["--purge"],
    "RIP_LIB": ["--rip-lib"],
    "STRIPLIBS": [""],
}

# Profile map centralizes known CLI families so users can switch format with one env variable.
CLI_PROFILES: Final[dict[str, dict[str, dict[str, list[str]]]]] = {
    "revanced-cli": {
        "list_patches": deepcopy(DEFAULT_LIST_PATCHES_ARGS),
        "patch": deepcopy(DEFAULT_PATCH_ARGS),
    },
    "revanced-cli-v6": {
        # ReVanced v6 moved list flags to long names and made patches flag-based.
        "list_patches": {
            "CMD": ["list-patches"],
            "DESCRIPTIONS": ["--descriptions"],
            # Filter flag is optional and should not be emitted unless the user explicitly overrides it.
            "FILTER_PACKAGE_NAME": [""],
            "INDEX": ["--index"],
            "OPTIONS": ["--options"],
            "PACKAGES": ["--packages"],
            "PATCHES": ["-p"],
            # ReVanced v6 requires verification companion flags for every patches file group.
            "PATCHES_POST": ["-b"],
            "UNIVERSAL": ["--universal-patches"],
            "VERSIONS": ["--versions"],
        },
        # Patch command still supports most legacy short flags, but v6 removes rip-lib behavior.
        "patch": {
            "APK": [POSITIONAL_ARG],
            "CMD": ["patch"],
            "DISABLED": ["-d"],
            "ENABLED": ["-e"],
            "EXCLUSIVE": ["--exclusive"],
            "FORCE": ["--force"],
            "KEYSTORE": ["--keystore"],
            "KEYSTORE_OLD": [
                KEYSTORE_ALIAS_ARG,
                KEYSTORE_ENTRY_PASSWORD_ARG,
                KEYSTORE_PASSWORD_ARG,
            ],
            "OPTIONS": ["-O"],
            "OUTPUT": ["-o"],
            "PATCHES": ["-p"],
            # ReVanced v6 requires verification companion flags for every patches file group.
            "PATCHES_POST": ["-b"],
            "PURGE": ["--purge"],
            "RIP_LIB": [""],
            "STRIPLIBS": [""],
        },
    },
    "morphe-cli": {
        # Morphe list-patches requires explicit patch bundle flags instead of positional files.
        "list_patches": {
            "CMD": ["list-patches"],
            "DESCRIPTIONS": [""],
            # Filter flag is optional and should not be emitted unless the user explicitly overrides it.
            "FILTER_PACKAGE_NAME": [""],
            "INDEX": ["-i"],
            "OPTIONS": ["-o"],
            "PACKAGES": ["-p"],
            "PATCHES": ["--patches"],
            "PATCHES_POST": [""],
            "UNIVERSAL": ["-u"],
            "VERSIONS": ["-v"],
        },
        # Morphe patch supports striplibs and keeps most names aligned with revanced-cli.
        "patch": {
            "APK": [POSITIONAL_ARG],
            "CMD": ["patch"],
            "DISABLED": ["-d"],
            "ENABLED": ["-e"],
            "EXCLUSIVE": ["--exclusive"],
            "FORCE": ["--force"],
            "KEYSTORE": ["--keystore"],
            "KEYSTORE_OLD": [
                KEYSTORE_ALIAS_ARG,
                KEYSTORE_ENTRY_PASSWORD_ARG,
                KEYSTORE_PASSWORD_ARG,
            ],
            "OPTIONS": ["-O"],
            "OUTPUT": ["-o"],
            "PATCHES": ["-p"],
            "PATCHES_POST": [""],
            "PURGE": ["--purge"],
            "RIP_LIB": [""],
            "STRIPLIBS": ["--striplibs"],
        },
    },
}


def parse_arg_overrides(raw_overrides: str | None, allowed_keys: set[str]) -> dict[str, list[str]]:
    """Parse `KEY=value` override strings into a normalized dictionary."""
    # Empty values intentionally mean "no overrides", so we return quickly.
    if not raw_overrides:
        return {}

    parsed_overrides: dict[str, list[str]] = {}

    # We use shell tokenization so quoted values survive intact when users pass complex flags.
    for token in shlex.split(raw_overrides):
        # We skip malformed tokens to keep startup robust with partially wrong user input.
        if "=" not in token:
            logger.warning(f"Ignoring malformed CLI override token `{token}` (expected KEY=value).")
            continue

        key, value = token.split("=", maxsplit=1)
        normalized_key = key.strip().upper()

        # We ignore unsupported keys so users can pass experimental values without crashing builds.
        if normalized_key not in allowed_keys:
            logger.warning(f"Ignoring unsupported CLI override key `{normalized_key}`.")
            continue

        # We split the value to keep multiple flags/args for a key
        # Example: `FORCE='--force --continue-on-error'`
        parsed_overrides[normalized_key] = shlex.split(value.strip())

    return parsed_overrides


def resolve_cli_profile(profile_name: str | None) -> dict[str, dict[str, list[str]]]:
    """Resolve CLI profile by name and fallback to default profile when unknown."""
    # We normalize to lowercase so env values are case-insensitive for users.
    selected_profile = (profile_name or DEFAULT_CLI_PROFILE).strip().lower()

    # We fallback safely when profile is unknown to preserve existing working behavior.
    if selected_profile not in CLI_PROFILES:
        logger.warning(
            f"Unknown CLI argument profile `{selected_profile}`. Falling back to `{DEFAULT_CLI_PROFILE}`.",
        )
        selected_profile = DEFAULT_CLI_PROFILE

    # We return a deep copy so downstream merging cannot mutate shared constants.
    return deepcopy(CLI_PROFILES[selected_profile])


def fill_in_default_args(from_defaults: dict[str, list[str]], into_args: dict[str, list[str]]) -> dict[str, list[str]]:
    """Fill in missing keys from defaults to ensure all expected keys are present."""
    for key, default_value in from_defaults.items():
        if key not in into_args:
            into_args[key] = default_value
    return into_args


def merge_cli_arg_maps(
    profile_name: str | None,
    global_overrides: tuple[str | None, str | None],
    app_overrides: tuple[str | None, str | None] = (None, None),
    app_profile_name: str | None = None,
) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """Resolve and merge global/app CLI argument maps."""
    # We unpack override tuples explicitly so call sites stay compact and lint-friendly.
    global_lp_overrides, global_p_overrides = global_overrides
    # We unpack app overrides explicitly so app-level precedence handling remains straightforward.
    app_lp_overrides, app_p_overrides = app_overrides
    # We first resolve the global profile because it defines the base map all overrides build upon.
    profile_maps = resolve_cli_profile(profile_name)
    list_patches_args = profile_maps["list_patches"]
    patch_args = profile_maps["patch"]

    # When app profile is provided, we switch base maps first and still apply global/app overrides after that.
    if app_profile_name:
        app_profile_maps = resolve_cli_profile(app_profile_name)
        list_patches_args = app_profile_maps["list_patches"]
        patch_args = app_profile_maps["patch"]

    # Global overrides are applied first so app overrides can intentionally take precedence.
    list_patches_args.update(parse_arg_overrides(global_lp_overrides, LIST_PATCHES_KEYS))
    patch_args.update(parse_arg_overrides(global_p_overrides, PATCH_KEYS))

    # App overrides are applied last to honor app-level configuration precedence.
    list_patches_args.update(parse_arg_overrides(app_lp_overrides, LIST_PATCHES_KEYS))
    patch_args.update(parse_arg_overrides(app_p_overrides, PATCH_KEYS))

    return list_patches_args, patch_args


def _format_template_arg(template: str, value: str | None = None) -> list[str]:
    """Helper to evaluate template formatting with value."""
    if not value:
        return [template]

    # Consume value when POSIITONAL
    if template == POSITIONAL_ARG:
        return [value]

    # Consume value when PLACEHOLDER
    if "{value}" in template:
        return [template.format(value=value)]

    # Consume value when template -> '--flag='
    if template.endswith("="):
        return [f"{template}{value}"]

    # Default behavior
    return [template, value]


def build_template_with_values(args: list[str], templates: list[str], values: list[str]) -> None:
    """Extend the args with each template and use value if required.

    Value is consumed for every template that is either `POSITIONAL_ARG` or
    contains the PLACEHOLDER (--flag={value}) or
    ends with '=' (--flag=).

    If the values still remain, after extending the args with the templates,
    the last template is used for the rest of the values.
    """
    current_value_index = 0
    max_value_index = len(values) - 1 if values else -1
    missing_value_msg = f"Missing value required for the positional arg from list of args: {templates}"

    # Iterate till 2nd last template
    for template in templates[:-1]:
        if template == POSITIONAL_ARG or "{value}" in template or template.endswith("="):
            if current_value_index <= max_value_index:
                args.extend(_format_template_arg(template, values[current_value_index]))
            else:
                logger.warning(missing_value_msg)
            current_value_index += 1
        else:
            args.append(template)

    last_template = templates[-1]
    if current_value_index > max_value_index:
        args.append(last_template)
        return

    # Consume rest of the values with the last template
    while current_value_index <= max_value_index:
        args.extend(_format_template_arg(last_template, values[current_value_index]))
        current_value_index += 1


def append_cli_argument(args: list[str], arg_templates: list[str], values: list[str] | None = None) -> None:
    """Append CLI argument from a list of arg templates and an optional list of dynamic values."""
    # We strip whitespace so values from env files with extra spaces behave predictably.
    normalized_templates = [t.strip() for t in arg_templates if t.strip()]

    # Handle completely empty templates
    if not normalized_templates:
        if values:
            args.extend(values)
        return

    # Handle completely empty values
    if not values:
        if normalized_templates:
            args.extend(normalized_templates)
        return

    build_template_with_values(args, normalized_templates, values)
