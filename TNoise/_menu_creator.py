"""Functions that handle creation of the Nuke menu."""

import logging
import os

import nuke  # ty:ignore[unresolved-import]

from _consts import (
    ICON_FILENAME,
    MENU_NAME,
    NODE_CLASS_NAME,
    PLUGIN_LOADED_ENV_VAR,
    RESOURCE_PATH_ADDED_ENV_VAR,
    RESOURCES_PATH,
    normalized_path,
)

logger = logging.getLogger(__name__)


def _create_menu():
    """Create the Nuke menu and add the command."""
    toolbar = nuke.menu("Nodes")
    menu = toolbar.findItem(MENU_NAME)
    if menu is None:
        menu = toolbar.addMenu(MENU_NAME, ICON_FILENAME)

    if toolbar.findItem("{}/{}".format(MENU_NAME, NODE_CLASS_NAME)) is None:
        menu.addCommand(
            NODE_CLASS_NAME,
            "nuke.createNode('{}')".format(NODE_CLASS_NAME),
            None,
            ICON_FILENAME,
        )


def add_menu():
    """Add the Nuke menu if the plugin has been loaded."""
    if os.getenv(PLUGIN_LOADED_ENV_VAR) != "1":
        logger.warning("Skipping TNoise menu creation because plugin binary was not loaded.")
        return

    _add_menu_dependencies_to_plugin_path()
    _create_menu()


def _add_menu_dependencies_to_plugin_path():
    resources_path = normalized_path(RESOURCES_PATH)
    if os.getenv(RESOURCE_PATH_ADDED_ENV_VAR) == resources_path:
        return

    nuke.pluginAppendPath(resources_path)
    os.environ[RESOURCE_PATH_ADDED_ENV_VAR] = resources_path
