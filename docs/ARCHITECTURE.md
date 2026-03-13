# Architecture

## Overview

The project is a Rust workspace centred on a native Nuke plugin, accompanied by a Python Nuke package and an `xtask` toolchain.

## Components

- `crates/tnoise-nuke`
  - compiles `src/tnoise_base.cpp`
  - exposes a `cdylib` loadable by Nuke
  - depends on `DDImage` headers/libs extracted from Nuke installers

- `xtask`
  - downloads supported Nuke installers
  - extracts the relevant headers and libraries
  - compiles the plugin for a given target
  - copies the result into `TNoise`

- `TNoise`
  - package loaded by Nuke via `.nuke/init.py`
  - selects the correct binary based on the current session
  - creates the `Nodes > TNoise` menu
  - hosts auxiliary Python UI scripts

## Execution flow

1. Nuke loads `~/.nuke/init.py`, which calls `nuke.pluginAddPath("./TNoise")`.
2. `TNoise/init.py` is executed as the plugin entry point: it detects the Nuke version, OS, and architecture, then adds the appropriate binary directory.
3. `TNoise/menu.py` creates the menu and the node creation commands.
4. The native binary `TNoise.<ext>` is then resolved by Nuke.

## Build flow

1. `cargo xtask --fetch-nuke` downloads or reuses Nuke installers.
2. `xtask` extracts `include/`, `DDImage.dll/.lib`, or equivalents.
3. `cargo build` compiles `crates/tnoise-nuke` with the expected environment variables.
4. `xtask` moves the binary into `target/nuke/builds`.
5. `xtask --output-to-package` populates `TNoise/bin`.

## Boundaries to keep clean

- `target/` is local build output only.
- `TNoise/bin/` must contain only the shipped binaries.
- Local runtime presets for the color ramp editor must not be versioned.
