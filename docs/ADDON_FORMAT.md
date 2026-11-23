# SRML Mobile Add-on Format and Runtime Architecture

Status: proposal / pre-implementation design.

## Goals

- A user installs one `.SRMLmobileAddon` file through SRML Mobile Manager.
- The package contains metadata, data definitions, localization, and assets.
- Ordinary content mods should not need executable code.
- A separate in-process Runtime owns all interaction with Unity and IL2CPP.
- The format is versioned and validates compatibility before activation.

## Component boundaries

1. **Addon package**: passive ZIP container. It never injects itself into the game.
2. **SRML Mobile Manager**: imports, validates, lists, enables/disables, updates, and removes packages. It stores installed package files and metadata.
3. **SRML Mobile Runtime**: runs inside the game process, exposes a stable mod API, loads approved packages, and bridges to game-specific adapters.
4. **Game adapter**: version-specific mapping from stable SRML concepts to actual game classes and registration paths.
5. **Game**: Slime Rancher Mobile systems such as slime definitions, appearance, diet, spawning, and Slimepedia.

The Manager must not be treated as an injector. Android app sandboxing means a separate manager process cannot simply modify another app's memory. Runtime loading/integration is a separate engineering milestone and remains unproven for Unity 6000.3.0f1 / Android 16.

## Package layout (proposal)

```text
Example.SRMLmobileAddon
├── manifest.json
├── preview.png
├── Slime/
│   ├── slime.json
│   ├── icon.png
│   ├── textures/
│   └── models/
├── Localization/
│   ├── en.json
│   └── ru.json
├── Scripts/
│   └── Example.Mod.dll
└── Libraries/
```

The extension is a ZIP-compatible archive. The archive must contain relative paths only. The importer must reject path traversal, duplicate normalized paths, symlinks, oversized entries, unsupported compression methods, malformed manifests, and unexpected executable/native payloads.

## Manifest v1 sketch

```json
{
  "format": "SRMLmobileAddon",
  "formatVersion": 1,
  "id": "author.example.coolslime",
  "name": "Cool Slime",
  "author": "Author",
  "version": "1.0.0",
  "type": "slime",
  "targetGame": {
    "package": "com.playdigious.slimerancher",
    "version": "1.1.1103"
  },
  "runtimeApi": "1.0",
  "entryAssembly": null,
  "dependencies": [],
  "assets": {
    "slimeDefinition": "Slime/slime.json",
    "icon": "Slime/icon.png"
  }
}
```

This is a design sketch, not a finalized schema. Exact game-version policy, API compatibility ranges, signing, and dependency resolution need implementation decisions.

## Content-first slime definition

A first version should describe ordinary slimes declaratively, without requiring C# code:

- stable mod-owned identifier;
- display name and localization keys;
- favorite food / diet references;
- allowed habitat or spawn-region identifiers;
- Slimepedia entry, description, and icon;
- appearance asset references;
- optional spawn tuning, constrained by Runtime-supported fields.

The schema must not expose raw IL2CPP pointers, arbitrary memory offsets, or internal game addresses. The game adapter validates and translates the definition to the current game version.

The exact serialization fields and accepted habitat identifiers remain to be confirmed from Unity assets and runtime behavior. Metadata reveals relevant classes, but does not prove that a new definition can be registered successfully.

## Scripts

Scripts are optional. The initial package format reserves `Scripts/`, but script execution should remain disabled until the in-process Runtime and managed-code interoperability layer are proven on the target game.

When supported, scripts should be compiled managed assemblies targeting a documented SRML Mobile API. They should not be arbitrary source snippets executed by the Manager. Native `.so` plugins are excluded from the first format version. A future capability/permission model should restrict file access, network access, and game hooks.

## Install and activation flow

1. Manager reads the archive without executing its contents.
2. Validate manifest, package ID, version, file paths, sizes, hashes, game version, Runtime API, and dependencies.
3. Show the user the requested capabilities and compatibility result.
4. Extract into an app-private staging directory, then atomically promote to the installed-mod directory.
5. Runtime discovers enabled packages after it has initialized and the game adapter reports readiness.
6. Runtime loads content definitions and assets in dependency order, validates references, and registers supported content.
7. Runtime reports per-mod success/failure to Manager through a narrow local IPC/status channel.
8. Disabling a mod takes effect on the next game launch unless a specific feature is proven safe to unload live.

The Manager should never claim a mod is active merely because the package was imported.

## Initial proof milestones

1. Prove a Runtime bootstrap inside this exact game build; log package version, Unity version, IL2CPP readiness, and adapter status.
2. Resolve required game types and fields safely.
3. Clone/register one existing slime definition without custom assets.
4. Prove a unique identifier and Slimepedia entry.
5. Prove diet/favorite-food behavior.
6. Prove spawn-region integration.
7. Load a custom icon and appearance assets.
8. Add a documented content schema and a basic package validator in Manager.
9. Enable optional managed scripts only after the above path is stable.

## Uploaded Unity bundle inspection

The supplied `data.unity3d` is a UnityFS bundle (format 8), built with Unity 6000.3.0f1. Its bundle directory contains seven entries:

- `globalgamemanagers`
- `Resources/unity_builtin_extra`
- `globalgamemanagers.assets`
- `sharedassets0.assets`
- `globalgamemanagers.assets.resS`
- `sharedassets0.assets.resS`
- `level0`

The bundle directory alone does not identify slime prefabs or prove scene spawn configuration. The next asset-analysis step is to parse the serialized asset files and enumerate relevant object types/names, then inspect the larger `datapack.unity3d` if required. Do not commit original game asset bundles to this repository.

## Current limitations

- No compatible Runtime bootstrap has been proven for the target Unity/Android combination.
- The exact registration path for new slime definitions is not proven.
- The exact prefab, appearance, and scene spawn data are not yet mapped.
- The manifest and slime JSON are proposals, not stable public contracts.
- Package signing and a final permission model are not implemented.
