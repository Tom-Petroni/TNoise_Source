"""Plugin creation script for user interface in Nuke."""

import logging

from _menu_creator import add_menu

logger = logging.getLogger(__name__)

try:
    add_menu()
except Exception:  # pragma: no cover - Nuke runtime dependency
    logger.exception("Unexpected failure while creating the TNoise menu.")
