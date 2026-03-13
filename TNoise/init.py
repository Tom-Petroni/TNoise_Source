"""Main entry point for TNoise Nuke plugin."""

import logging

from _node_setup import setup_knob_changed
from _plugin_loader import add_plugin_path_safe

logger = logging.getLogger(__name__)

try:
    if add_plugin_path_safe():
        setup_knob_changed()
    else:
        logger.warning("Skipping TNoise node setup because plugin binary was not loaded.")
except Exception:  # pragma: no cover - Nuke runtime dependency
    logger.exception("Unexpected failure while initializing the TNoise plugin.")
