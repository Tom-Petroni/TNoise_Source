# Build

## Prerequisites

- Rust stable
- Functional Cargo workspace
- Nuke SDKs available locally under `target/nuke/deps`, or fetchable via `cargo xtask`

Depending on the platform:

- Windows: `7z` and `lessmsi`
- Linux: `p7zip`
- macOS: `p7zip`
- Optional: `cargo-zigbuild` for Zig cross-compilation

## Useful commands

Fetch the SDKs/sources for a given version:

```powershell
cargo xtask --fetch-nuke --nuke-versions 16.0 --target-platform windows --limit-threads
```

Compile and copy the result into the Nuke package:

```powershell
cargo xtask --compile --nuke-versions 16.0 --target-platform windows --output-to-package --limit-threads
```

Compile multiple versions:

```powershell
cargo xtask --compile --nuke-versions 15.2,16.0 --target-platform windows --output-to-package --limit-threads
```

Compile with Zig:

```powershell
cargo xtask --compile --use-zig --nuke-versions 16.0 --target-platform linux --output-to-package
```

## Outputs

- Extracted Nuke SDKs: `target/nuke/deps/<version>/`
- Intermediate binaries: `target/nuke/builds/<version>/<target>/`
- Final Nuke package: `TNoise/bin/<version>/<os>/<arch>/`

## Main flags

- `--fetch-nuke`: downloads and extracts the required Nuke SDKs.
- `--compile`: compiles the plugin.
- `--output-to-package`: copies the binary into `TNoise`.
- `--use-zig`: enables `cargo zigbuild`.
- `--limit-threads`: serialises downloads/extractions.

## Build tips

- Keep `target/nuke/deps` cached locally to avoid unnecessary network round-trips.
- Use `--limit-threads` on machines where MSI/archive extractors are unstable when run in parallel.
- Only ship `TNoise`, never `target/`.
