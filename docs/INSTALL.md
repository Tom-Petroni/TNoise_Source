# Installation

## Content to deploy

The folder to copy to the end user's machine is `TNoise`.

Expected structure after copying into `.nuke`:

```text
.nuke/
  init.py
  TNoise/
    init.py
    menu.py
    *.py
    bin/
      <version>/<os>/<arch>/TNoise.<ext>
    resources/
```

## Local installation

1. Copy the `TNoise` folder into the user's `.nuke` directory.
2. Add the following loader to `~/.nuke/init.py`:

```python
import nuke

nuke.pluginAddPath("./TNoise")
```

3. Restart Nuke.
4. Verify that `Nodes > TNoise` appears.

## Installation from GitHub Releases

1. Download the release zip produced by the GitHub workflow.
2. Extract the `TNoise` folder into `.nuke`.
3. Keep `README.md` and `docs/INSTALL.md` alongside it for user reference.
4. Add or verify `nuke.pluginAddPath("./TNoise")` in `~/.nuke/init.py`.
5. Restart Nuke and confirm the menu loads.

## Package behaviour

- `~/.nuke/init.py` calls `nuke.pluginAddPath("./TNoise")`, which adds the plugin package to Nuke's search path.
- `TNoise/init.py` is the plugin entry point: it detects the Nuke version, OS, and architecture, then adds the correct binary directory.
- `TNoise/menu.py` creates the menu and exposes the node.

## Quick troubleshooting

- If the menu does not appear, verify that the correct binary exists under `TNoise/bin/<version>/<os>/<arch>/`.
- If Nuke starts but the node fails to load, check the Script Editor for `TNoise` log messages.
- On macOS Apple Silicon, ARM builds are loaded only for Nuke versions that support ARM.

## Client distribution

For a commercial delivery, provide at minimum:

- the zip containing `TNoise`
- an installation README
- a functional reference for the node and its parameters
- the supported Nuke/OS compatibility matrix
- any signing or security prerequisites if the binaries are signed
