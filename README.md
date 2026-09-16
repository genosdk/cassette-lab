# Marantz PMD221 Plugin

Production workspace for a VST3/AU effect interface based on the photographed Marantz PMD221.

## Current assets

- `pmd221-skin-4k-exact.png`: 3840×2880 perspective-corrected photographic master; exact wear and dust retained.
- `pmd221-skin-concept.png`: photoreal orthographic reconstruction for art direction/reference.
- `pmd221-bottom.jpg`, `pmd221-io-side.jpg`, `pmd221-edge.jpg`: source textures for the rotatable presentation model.

The web viewer is intentionally dependency-free and uses CSS 3D so it can deploy directly on Railway.

## Run

```sh
npm start
```

Open `http://localhost:3000`.

## Fidelity note

The photographed unit does not yet include straight-on rear-edge or opposite-side captures. Those faces in the viewer are provisional and must not be used as manufacturing references.

## Native cassette plugin

See [plugin/README.md](plugin/README.md) for JUCE VST3/AU/Standalone builds.
See [docs/measurement-session.md](docs/measurement-session.md) for the hardware capture protocol.
Generate reproducible 24-bit test WAVs with `python3 tools/generate_stimuli.py`.
The current native engine is a transparent gain/mix scaffold, not yet a calibrated tape simulation.
