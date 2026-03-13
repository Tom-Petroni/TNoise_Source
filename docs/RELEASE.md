# Release

## Release checklist

1. Verify the product version exposed in `TNoise/_consts.py`.
2. Run the minimum local checks.
3. Compile the supported Nuke/OS targets.
4. Test manually in Nuke.
5. Publish the `TNoise` archive with the installation documentation.

## Recommended local checks

```powershell
cargo check -p xtask
python -m compileall TNoise
```

If a target Nuke SDK is already available locally, also run a full plugin build:

```powershell
cargo xtask --compile --nuke-versions 16.0 --target-platform windows --output-to-package --limit-threads
```

## GitHub Actions CI

The `.github/workflows/nuke-build.yml` workflow operates in two modes:

- `pull_request` and `push` on `main`: smoke checks only
- push of a `v*` tag and `workflow_dispatch`: full multi-version / multi-platform build

The release build:

- generates a Nuke/version/platform matrix
- compiles each target
- verifies the presence of the expected binary
- assembles a multi-platform zip
- automatically publishes this zip in a GitHub Release on a `v*` tag push

The final bundle includes:

- `TNoise/`
- `README.md`
- `docs/INSTALL.md`
- `docs/NODE_REFERENCE.md`

## Creating a public release

1. Verify that `main` is green on the smoke checks.
2. Create a semver tag, for example `v1.0.0`.
3. Push the tag.
4. Let GitHub Actions compile all binaries.
5. Retrieve the GitHub Release created automatically with the attached zip.

## Manual QA before sale/distribution

- load the node in each supported Nuke version
- verify the menu and icon
- test the main output modes
- validate the embedded Python UI
- verify the package in a clean Nuke session

## Non-code commercial prerequisites

These points remain to be defined before external commercialisation:

- licence or EULA
- support policy
- official versioning/release notes
- binary signing if required
- marketing material, screenshots, website or product page
