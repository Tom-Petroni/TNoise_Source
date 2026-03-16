"""Plugin loader and lookup script."""

import logging
import os
import platform

import nuke  # ty:ignore[unresolved-import]

from _consts import (
    INSTALLATION_PATH,
    PLUGIN_BIN_DIRECTORY,
    PLUGIN_BINARY_PATH_ENV_VAR,
    PLUGIN_LOADED_ENV_VAR,
    normalized_path,
)

logger = logging.getLogger(__name__)

NUKE_ARM_VERSION = 15
"""First Nuke major version that has ARM support."""


class PluginNotFoundError(Exception):
    """Raised when the plugin path is not found."""


class UnsupportedSystemError(Exception):
    """Raised when the operating system is not supported."""


def _get_nuke_version():
    """Return the Nuke version in Major.Minor format."""
    return "{}.{}".format(nuke.NUKE_VERSION_MAJOR, nuke.NUKE_VERSION_MINOR)


def _machine_name():
    """Return a normalized machine identifier for the current host."""
    return (platform.machine() or platform.processor() or "").strip().lower()


def _get_operating_system_name():
    """Return the OS name matching package folders."""
    operating_system = platform.system().lower()

    if "linux" in operating_system:
        return "linux"
    if "windows" in operating_system:
        return "windows"
    if "darwin" in operating_system:
        return "macos"

    raise UnsupportedSystemError("System '{}' is not supported.".format(operating_system))


def _get_arch():
    """Return architecture folder name for current system."""
    architecture = _machine_name()
    operating_system = _get_operating_system_name()

    if architecture in {"amd64", "x64", "x86_64", "x86-64", "em64t"}:
        return "x86_64"

    if architecture in {"arm64", "aarch64"} and operating_system == "macos":
        if nuke.NUKE_VERSION_MAJOR >= NUKE_ARM_VERSION:
            return "aarch64"
        return "x86_64"

    raise UnsupportedSystemError(
        "Architecture '{}' is not supported.".format(architecture),
    )


def _build_plugin_path():
    """Build expected plugin path in installed package."""
    version_folder = _resolve_version_folder()
    return normalized_path(
        os.path.join(
            INSTALLATION_PATH,
            PLUGIN_BIN_DIRECTORY,
            version_folder,
            _get_operating_system_name(),
            _get_arch(),
        )
    )


def _is_minor_version_folder(name):
    """Return True for folders in Major.Minor format."""
    parts = name.split(".")
    return len(parts) == 2 and all(part.isdigit() for part in parts)


def _resolve_version_folder():
    """Resolve the best available version folder for the running Nuke."""
    requested = _get_nuke_version()
    plugin_bin_root = os.path.join(INSTALLATION_PATH, PLUGIN_BIN_DIRECTORY)

    if os.path.isdir(os.path.join(plugin_bin_root, requested)):
        return requested

    if not os.path.isdir(plugin_bin_root):
        return requested

    try:
        available = [
            entry
            for entry in os.listdir(plugin_bin_root)
            if _is_minor_version_folder(entry)
            and os.path.isdir(os.path.join(plugin_bin_root, entry))
        ]
    except OSError:
        return requested

    try:
        requested_major, requested_minor = (
            int(part) for part in requested.split(".", 1)
        )
    except ValueError:
        return requested

    same_major = []
    for entry in available:
        major, minor = (int(part) for part in entry.split(".", 1))
        if major == requested_major:
            same_major.append((minor, entry))

    if not same_major:
        return requested

    lower_or_equal = [entry for minor, entry in same_major if minor <= requested_minor]
    if lower_or_equal:
        selected = max(
            lower_or_equal,
            key=lambda version: int(version.split(".", 1)[1]),
        )
    else:
        selected = min(
            (entry for _, entry in same_major),
            key=lambda version: int(version.split(".", 1)[1]),
        )

    logger.warning(
        "TNoise binary folder '%s' not found, using '%s' fallback.",
        requested,
        selected,
    )
    return selected


def add_plugin_path():
    """Add plugin path to Nuke if found and return the resolved path."""
    plugin_path = _build_plugin_path()
    if not os.path.isdir(plugin_path):
        os.environ[PLUGIN_LOADED_ENV_VAR] = "0"
        os.environ.pop(PLUGIN_BINARY_PATH_ENV_VAR, None)
        raise PluginNotFoundError(
            (
                "TNoise is installed, but this Nuke version '{}' is not available "
                "in this package."
            ).format(nuke.NUKE_VERSION_STRING),
        )

    already_loaded = (
        os.getenv(PLUGIN_LOADED_ENV_VAR) == "1"
        and os.getenv(PLUGIN_BINARY_PATH_ENV_VAR) == plugin_path
    )
    if not already_loaded:
        nuke.pluginAppendPath(str(plugin_path))  # ty:ignore[unresolved-attribute]

    os.environ[PLUGIN_LOADED_ENV_VAR] = "1"
    os.environ[PLUGIN_BINARY_PATH_ENV_VAR] = plugin_path
    return plugin_path


def add_plugin_path_safe():
    """Add plugin path to Nuke if found, otherwise log failure."""
    try:
        plugin_path = add_plugin_path()
        logger.info("TNoise plugin loaded successfully from '%s'.", plugin_path)
        return True
    except (PluginNotFoundError, UnsupportedSystemError):
        logger.exception("TNoise plugin loading failed.")
        return False
