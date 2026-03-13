# TNoise — Source

Code source du node Nuke `TNoise` : plugin natif Rust/C++, package Python, pipeline build multi-version et CI GitHub Actions.

## Structure

- `crates/tnoise-nuke` : node natif Nuke (`tnoise_base.cpp`) et bridge Rust.
- `xtask` : recuperation des SDK Nuke, build natif et packaging.
- `TNoise/` : package Python deployable dans `.nuke`.
- `docs/` : documentation d'installation, build, architecture et release.

## Demarrage rapide

Build Windows pour une version Nuke :

```powershell
cargo xtask --compile --nuke-versions 16.0 --target-platform windows --output-to-package --limit-threads
```

Sortie attendue :

`TNoise/bin/16.0/windows/x86_64/TNoise.dll`

Installation dans Nuke :

1. Copier le dossier `TNoise/` et le fichier `init.py` dans le repertoire `.nuke` de l'utilisateur.
2. Relancer Nuke puis verifier le menu `Nodes > TNoise`.

## Documentation

- [Installation](docs/INSTALL.md)
- [Build](docs/BUILD.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Reference du node](docs/NODE_REFERENCE.md)
- [Release](docs/RELEASE.md)
