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


## Findings from desktop SRML source study (2026-11-24)

Sources inspected:
- Official `SlimeRancherModding/SRML` repository, `SampleMod/Main.cs` and `SampleMod/modinfo.json`.
- `SRML/SR/SlimeRegistry.cs`.
- `SRML/SR/Templates/Identifiables/SlimeTemplate.cs`.
- `SRML/SR/RegionSetRegistry.cs`.
- Official SRML Getting Started / Project Setup wiki.

### What a real desktop mod looks like

The official sample is a compiled C# class library plus `modinfo.json`. Its entry class derives from `ModEntryPoint` and uses lifecycle methods:
- `PreLoad()`: early registration and Harmony patches; sample also subscribes to save-loaded callback and spawns an existing Mosaic Boom Largo.
- `Load()`: registration requiring the game context.
- `PostLoad()`: work that needs initialized game prefabs and other runtime resources.

The sample does not create a new slime. It demonstrates the lifecycle and spawning an existing prefab.

The wiki's project setup describes a .NET Framework class library and references to the desktop game's `Assembly-CSharp`, `SRML.dll`, Harmony, and UnityEngine assemblies. That is a desktop Mono mod build pipeline, not a binary format that can be loaded unchanged by the Android IL2CPP game.

### How desktop SRML actually creates slimes

The inspected `SlimeTemplate` is much more important than the minimal sample. It constructs a slime at runtime:
- creates/builds a `SlimeDefinition`;
- registers it through `SlimeRegistry.RegisterSlimeDefinition`;
- constructs a `GameObject` prefab and attaches the required components, including `SlimeAppearanceApplicator`, `Identifiable`, `SlimeEat`, `SlimeVarietyModules`, movement, health, emotions, audio, face, and interaction components;
- builds bone/appearance hierarchy and configures the appearance applicator;
- can generate largo variants and register their prefabs.

This proves that in desktop SRML, a custom slime is not just a texture and a JSON record. It is a coordinated runtime definition plus prefab/component graph and appearance resources.

### Registration behavior

`SlimeRegistry.RegisterSlimeDefinition`:
- tracks which mod owns the definition;
- selects the correct `SlimeDefinitions` instance based on SRML's loading step;
- inserts the definition into the ID lookup and slime list;
- updates largo lookup dictionaries where applicable;
- refreshes diet EatMaps for the new definition and its base slimes when requested.

`RegisterAppearance` registers dependent appearances and updates the chosen appearance through `SlimeAppearanceDirector`.

`RegionSetRegistry` separately registers region trees and maps zones to region-set IDs. This is a useful architectural precedent for keeping slime registration and habitat/region registration as distinct services.

### What transfers to SRML Mobile

Transferable concepts (not desktop binaries):
- a staged lifecycle with early registration, game-ready registration, and post-load asset work;
- registries for slime definitions, appearances, prefabs, and habitat/region data;
- explicit registration of the slime definition into lookup collections and diet-map refresh;
- a prefab factory that assembles the required components;
- package metadata separated from executable behavior;
- stable mod IDs and dependency declarations.

Not directly transferable:
- desktop `.NET Framework` DLLs and their references;
- desktop `Assembly-CSharp` types and Mono runtime assumptions;
- desktop Harmony patches;
- desktop `Identifiable.Id` enum extension mechanics;
- the exact component construction code, until equivalent IL2CPP runtime APIs and object creation paths are proven on mobile.

### Architecture decision updated

Keep `.SRMLmobileAddon` as a ZIP-compatible package, but do not assume its contents map one-to-one to desktop SRML files.

Recommended package model:
1. `manifest.json`: identity, version, target game build, Runtime API compatibility, dependencies, capabilities.
2. `Content/`: declarative slime/diet/Slimepedia/habitat definitions.
3. `Assets/`: icons, textures, and Unity asset bundles.
4. `Scripts/`: optional mobile-specific managed plugin assemblies only after IL2CPP loading and API compatibility are proven.
5. Desktop SRML DLLs are not accepted as mobile plugins.

The mobile Runtime should implement a staged API inspired by desktop SRML lifecycle, and a mobile-specific slime factory/registry. JSON definitions are an authoring format; the Runtime must translate them into actual IL2CPP objects, components, lookup registrations, and asset references. This translation is not implemented or proven yet.

### Critical caveat

Desktop SRML source is valuable evidence for game concepts and registration responsibilities, but it is not evidence that desktop mods can run on Android or that the mobile game's internal registration path is identical. The target mobile game's own metadata and serialized assets remain authoritative.
