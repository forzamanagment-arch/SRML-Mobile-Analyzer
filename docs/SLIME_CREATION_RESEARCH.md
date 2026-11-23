# Custom Slime Feasibility Research

Target sample: Slime Rancher Mobile 1.1.1103, Unity 6000.3.0f1, IL2CPP metadata v39.
Source examined locally: the user's original `global-metadata.dat` (10,657,216 bytes). The game binary itself is not stored in this repository.

## Executive conclusion

The metadata exposes game-side systems for slime definitions, diets, appearances, world spawning, and Slimepedia. This makes a custom-slime feature a plausible research target, but metadata alone does not prove that a new slime can be registered at runtime. The next required evidence is the serialized game data in Unity asset bundles and the native IL2CPP type/method mappings from the matching `libil2cpp.so`.

Do not start by building a visual editor. First prove a minimal runtime path that registers one cloned/test slime definition without corrupting a save or preventing the game from starting.

## Verified class/member evidence

All names below were decoded from the target metadata sample. Type-definition indices are sample-specific.

### Definition and diet

- `SlimeDefinition` (type definition 1137)
  - Fields: `Name`, `IdentifiableId`, `BaseSlimes`, `IsLargo`, `CanLargofy`, `PrefabScale`, `AppearancesDefault`, `AppearancesDynamic`, `Sounds`, `Diet`, `FavoriteToys`, `BaseModule`, `SlimeModules`.
  - Methods: `get_Appearances`, `LoadDietFromBaseSlimes`, `LoadFavoriteToysFromBaseSlimes`, `RegisterDynamicAppearance`, `GetAppearanceForSet`, constructor.
- `SlimeDiet` (1140)
  - Fields: `MajorFoodGroups`, `Favorites`, `AdditionalFoods`, `Produces`, `FavoriteProductionCount`, `EatMap`.
  - Methods include `Combine`, `RefreshEatMap`, `AddEatMapEntries`, `ProducePlorts`, and food-category message helpers.
- `SlimeDefinitions` (1146)
  - Fields: `Slimes`, `slimeDefinitionsByIdentifiable`, `largoDefinitionByBasePlorts`, `largoDefinitionByBaseDefinitions`.
  - Methods: `RefreshIndexes`, `RefreshDefinitions`, `GetSlimeByIdentifiableId`, and largo lookup methods.
- `SlimeVarietyModules` (1198) has `baseModule`, `slimeModules`, `addedComponents`; methods `Assemble` and `MergeGeneralComponents`.

### Appearance and assets

- `SlimeAppearance` (1112) fields include `NameXlateKey`, `Icon`, `AnimatorOverride`, `Structures`, `Face`, `QubitAppearance`, `ColorPalette`, and several special-effect appearance references.
- `SlimeAppearanceStructure` (1113): `DefaultMaterials`, `Element`, `ElementMaterials`, `SupportsFaces`, `FaceRules`.
- `SlimeAppearanceElement` (1124): `Name`, `Prefabs`.
- `SlimeAppearanceApplicator` (1123) includes `ApplyAppearance`, `ApplyAppearanceStructure`, `ApplyAppearanceObject`, and fields for the active definition, appearance, bones, and render objects.
- The icon is an explicit field on `SlimeAppearance`; it is not the same thing as the body texture or prefab.

### World spawning

- `DirectedActorSpawner` (1850) fields include `radius`, `constraints`, `spawnLocs`, `allowDirectedSpawns`, `directedSpawnWeight`, `timeDir`, and `region`. Methods include `Register`, `CanSpawn`, `Spawn`, and `GetEligibleConstraints`.
- `DirectedSlimeSpawner` (1856) has `slimeSpawnFX`, `modDir`, `lookupDir`, and `oasis`; methods include `Register`, `CanSpawn`, and `MaybeReplacePrefab`.
- `SpawnConstraint` (1848) fields: `slimeset`, `weight`, `window`, `feral`, `maxAgitation`.
- `SlimeSet` (2019) has a `members` field.
- The `Zone` enum (121) contains `QUARRY`, `MOSS`, `DESERT`, `RUINS`, `WILDS`, ranch zones, and additional zones. A second enum also named `Zone` exists at type definition 2094, so future tooling must qualify types by their full identity, not name alone.

### Slimepedia

- `PediaDirector` (1953) fields include `entries`, `identMapEntries`, `identDict`, `entryDict`, `pediaPopupPrefab`, `pediaPanelPrefab`, and `pediaModel`.
  - Methods include `Unlock`, `Get`, `GetPediaId`, `IsUnlocked`, and popup methods.
- `IdEntry` (1949): `id`, `icon`.
- `IdentMapEntry` (1950): `identId`, `pediaId`.
- `PediaUI` (1581) has UI fields for `titleText`, `introText`, `image`, `longDescText`, `dietText`, `favoriteText`, `biologyText`, `risksText`, and `plortText`. It also has `InitBundles`, `PopulateSlimesDesc`, `BuildListing`, and `CreateListing`.
- `MessageBundle` and `MessageDirector` provide message-bundle lookup and localization infrastructure.

## Important limits of the current evidence

1. The metadata decoder resolves names and table relationships, but the serialized `TypeIndex` values still need the matching native registration data from `libil2cpp.so`. Field types and method signatures are therefore not yet fully resolved.
2. Metadata does not contain the actual slime prefab, mesh, material, texture, icon image, or world spawn scene configuration.
3. The exact asset-bundle entries and Slimepedia message keys have not yet been inspected. Do not assume a guessed localization key format.
4. The `DirectedSlimeSpawner` and `DirectedActorSpawner` relationship, and the runtime registration order for all the registries, must be confirmed from resolved base types/methods or asset/runtime inspection.
5. No new slime has been instantiated in the game yet. This document is feasibility research, not a working mod implementation.

## Recommended implementation path

### Phase A — data and type mapping

1. Resolve the relevant class field types, inheritance, and method signatures using the matching native library's metadata/code registration structures.
2. Inspect the game's `data.unity3d` and `datapack.unity3d` bundles locally. Identify one existing ordinary slime's definition, appearance, prefab, icon, pedia entry, localization strings, and spawn references.
3. Compare at least two existing slimes with different diets and spawn zones to separate required fields from optional fields.

### Phase B — minimal runtime proof

1. Establish a reliable in-process loader/bootstrap for this exact Android/Unity build.
2. At the correct point in Unity initialization, locate the game's existing `SlimeDefinitions`, `SlimeAppearanceDirector`, `PediaDirector`, and spawn registration systems.
3. First clone/register a test definition based on an existing slime, reusing its prefab and appearance. Do not introduce custom geometry yet.
4. Verify that the test slime can be looked up by a unique ID, spawned, eaten/produce correctly, and displayed in Slimepedia.
5. Test on a backed-up save and keep an unmodified game installation as rollback.

### Phase C — creator and mod format

Only after Phase B works, define a portable mod package. Proposed fields:

- manifest: mod ID, schema version, display name, target game build;
- slime: unique identifiable ID, display name, optional description;
- diet: food groups, favorite food IDs, produced plort IDs and favorite yield;
- appearance: references to the user's icon, textures, materials, and prefab/mesh assets;
- Slimepedia: entry ID, icon, title/intro/long description, diet/favorite text;
- spawn: one or more zone/location references, weight, time window, feral/agitation settings.

The creator UI should export/import this package. It should not directly edit the game's original bundles. The runtime loader should validate IDs, assets, and references before registering anything.

## Android deployment assessment

A separate companion APK cannot simply read or modify another app's process memory under Android's normal application sandbox. Android's compatibility requirements explicitly preserve per-app UID/process isolation. Shizuku is not, by itself, a generic IL2CPP code-injection API.

A no-root route worth evaluating is an Android Unity IL2CPP launcher/loader that arranges for native loader code to run inside the game process. Existing open-source projects demonstrate this general architecture, but compatibility with this game's Unity 6000.3.0f1 build and Android 16 is unproven. Candidate research references:

- FusionCore: https://github.com/All-Of-Us-Mods/FusionCore
- BepInEx Android launcher: https://github.com/Tb1281/BepInEx-Android
- StArray.ModManager: https://github.com/StArraySharp/StArray.ModManager
- ByNameModding BNM Android: https://github.com/ByNameModding/BNM-Android

Do not assume any candidate works on this title until a minimal bootstrap test passes. The target game publisher's support page currently says mobile modding is not supported and is not planned; SRML Mobile is therefore an experimental, unsupported project.

## Preferred technical implementation hypothesis

The first loader to test should be **BepInEx-Android / NextBep**, not a custom injector written from scratch. Its documented architecture launches the game through a launcher, intercepts Android class loading and UnityPlayer initialization, loads native bootstrap libraries, hooks `il2cpp_init`, and starts CoreCLR plus the BepInEx preloader. Its stated target is Android 9+ on arm64 Unity IL2CPP games. This matches the broad platform shape of the target, but does not prove compatibility with Slime Rancher Mobile 1.1.1103, Unity 6000.3.0f1, or this Android 16 device.

Recommended separation of responsibilities:

1. **SRML Mobile Manager (Android app):** create/edit slime packages, import/export mods, validate manifests, manage backups, and show logs. It does not attempt to directly inject into another app.
2. **SRML Mobile Runtime (BepInEx plugin):** execute inside the game process, read installed mod packages, resolve IL2CPP classes, register slime definitions, diets, appearances, pedia entries, and spawn data.
3. **SRML Mod Package:** a versioned ZIP-like package containing a manifest, JSON configuration, icon, textures, and optional prefab/material assets. It contains data by default, not arbitrary executable code.
4. **Game adapter:** isolates game-build-specific class names, registration order, and asset loading. The first adapter targets only game 1.1.1103 / Unity 6000.3.0f1; other builds must fail closed until verified.

Use the BepInEx Android launcher as an external bootstrap test harness first. Do not copy its launcher/native injection source into this repository without an explicit licensing decision: its launcher and native injection components are GPL-3.0, while BepInEx itself is LGPL-2.1. The GPL-3.0 FusionCore project is a secondary reference/fallback, not an automatic dependency.

A separate manager APK cannot directly access the game's private process or memory under the normal Android sandbox. The runtime must be loaded into the game process by a supported launcher/integration path. Shizuku can help with certain device-side operations but should not be treated as the missing IL2CPP injection mechanism.

## First proof-of-concept sequence

1. Build or obtain a minimal BepInEx Android test plugin that logs a startup marker and reports Unity version, package identity, and IL2CPP runtime readiness.
2. Launch the exact game build through the launcher and verify the marker appears. Do not register content yet.
3. Resolve the target class/field types and inheritance using the matching native library.
4. Clone one stock slime definition and reuse its existing prefab/appearance. Add only a unique ID and a test Slimepedia mapping.
5. Verify the slime can be looked up and spawned in a disposable/backed-up save.
6. Add diet and spawn constraints, then custom appearance assets and user-created textures.
7. Build the visual slime creator only after the runtime proof works.

If the loader cannot start this Unity build, fall back to a controlled APK-patching experiment that embeds the loader into the game package. Keep the original installation and saves untouched until a reliable backup/restore path is proven. This fallback is more invasive and should not be the first experiment.

## Current next milestone

Produce a target-game asset inventory for one stock slime and one spawn location, then resolve the native type mappings. Only after those two evidence sets are available should implementation begin.
