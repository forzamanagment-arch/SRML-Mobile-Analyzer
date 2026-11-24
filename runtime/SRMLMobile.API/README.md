# SRML Mobile API 0.1.0

This is the first **contract-only** API assembly for mobile plugins.

## What exists

- A plugin lifecycle contract: `OnLoad`, `OnGameReady`, and reserved `OnUnload`.
- Read-only game/runtime information.
- A small logger interface.
- Capability discovery so mods can check whether a feature is implemented by the active game adapter.

## What deliberately does not exist yet

There are no slime registration, prefab, diet, spawn, Slimepedia, Harmony, or raw IL2CPP APIs in this release. Those interfaces must be based on verified mobile game behavior, not copied from desktop SRML and guessed into existence.

The capability enum reserves names only. The runtime must report unsupported capabilities as unavailable. A plugin must not infer support from the enum existing.

## Runtime integration status

This project is not yet wired into BepInEx/FusionCore plugin discovery. It is a stable boundary proposal and compile target. The existing `BootstrapProbe` remains the separate proof that BepInEx can reach a plugin entry point. A later adapter will bridge BepInEx's `BasePlugin` lifecycle to `ISrmlMobilePlugin`.

Target framework: .NET 10, matching the current FusionCore/BepInEx runtime direction.

## Compatibility rules

- API versions use semantic versioning.
- Runtime implementations must expose the exact API version they provide.
- Add-ons declare an API compatibility range in `manifest.json`.
- New optional capabilities are additive. Breaking contract changes require a major API version.
- The game adapter, not a plugin, owns all game-version-specific IL2CPP mappings.
