# Target Slime Registration Research — metadata v39 pass

Date: 2026-11-24

Target:
- Package: `com.playdigious.slimerancher`
- Game version: `1.1.1103`, version code 609
- Unity: `6000.3.0f1`
- Backend / ABI: IL2CPP / arm64-v8a
- Metadata: `global-metadata.dat`, 10,657,216 bytes, magic `AF 1B B1 FA`, version 39

## Executive result

The original target metadata file was parsed directly in this research pass. The v39 header and all inspected fixed-record table sizes are internally consistent:

- Header size: 380 bytes.
- Type definitions: 14,452 records, 76 bytes each.
- Fields: 60,723 records, 10 bytes each.
- Methods: 94,414 records, 30 bytes each.
- Parameters: 95,059 records, 10 bytes each.
- Images / assemblies: 104 / 104 records.
- Properties / events: 15,084 / 232 records.
- Generic containers / parameters: 2,002 / 3,209 records.
- TypeIndex width: 2 bytes; TypeDefinitionIndex width: 2 bytes; GenericContainerIndex width: 2 bytes; ParameterDefinitionIndex width: 4 bytes.

All 31 non-empty section ranges were inside the file, no section overlaps were found, and the record-size checks passed for type definitions, fields, methods, parameters, images, assemblies, properties, events, generic containers, generic parameters, and interface offsets.

This is meaningful validation against the actual target file, not just synthetic fixtures. It still does **not** resolve TypeIndex values to managed types or native method addresses.

## Registration-related types found in the target metadata

Indices below are TypeDefinition indices from this exact metadata file. They are not stable across game builds.

| Type | TypeDefinition index | Relevant fields / methods |
|---|---:|---|
| `SlimeDefinition` | 1137 | `Name`, `IdentifiableId`, `BaseSlimes`, `IsLargo`, `CanLargofy`, `PrefabScale`, `AppearancesDefault`, `AppearancesDynamic`, `Sounds`, `Diet`, `FavoriteToys`, `BaseModule`, `SlimeModules` |
| `SlimeDiet` | 1140 | `MajorFoodGroups`, `Favorites`, `AdditionalFoods`, `Produces`, `FavoriteProductionCount`, `EatMap` |
| `SlimeDefinitions` | 1146 | `Slimes`, `slimeDefinitionsByIdentifiable`, `largoDefinitionByBasePlorts`, `largoDefinitionByBaseDefinitions` |
| `SlimeAppearance` | 1112 | `NameXlateKey`, `Icon`, `AnimatorOverride`, `Structures`, `Face`, `QubitAppearance`, `ColorPalette`, special appearance references |
| `SlimeAppearanceApplicator` | 1123 | active `SlimeDefinition` and `Appearance`, bones/render object state; methods include `ApplyAppearance`, `ApplyAppearanceStructure`, `ApplyAppearanceObject` |
| `SlimeAppearanceDirector` | 1241 | `SlimeDefinitions`, `appearancesByDependentAppearance`, `appearanceSelections` |
| `SlimeVarietyModules` | 1198 | `baseModule`, `slimeModules`, `addedComponents`; `Assemble`, `MergeGeneralComponents` |
| `DirectedActorSpawner` | 1850 | `constraints`, `spawnLocs`, `directedSpawnWeight`, `timeDir`, `region`; `Register`, `CanSpawn`, `Spawn`, `GetEligibleConstraints` |
| `DirectedSlimeSpawner` | 1856 | `slimeSpawnFX`, `modDir`, `lookupDir`, `oasis`; `Register`, `CanSpawn`, `MaybeReplacePrefab` |
| `SpawnConstraint` | 1848 | `slimeset`, `weight`, `window`, `feral`, `maxAgitation` |
| `SlimeSet` | 2019 | `members` |
| `PediaDirector` | 1953 | `entries`, `identMapEntries`, `identDict`, `entryDict`, `pediaModel`; `InitForLevel`, `Get`, `GetPediaId`, `Unlock`, `IsUnlocked` |
| `PediaUI` | 1581 | title, intro, image, long description, diet, favorite, biology, risks, and plort UI fields |

### Candidate metadata tokens

The following are ECMA-335 metadata tokens decoded from the target metadata. They are **not** native addresses, RVAs, or safe-to-call pointers.

| Owner | Member | Metadata token |
|---|---|---:|
| `SlimeDefinitions` | `RefreshIndexes` | `0x06001605` |
| `SlimeDefinitions` | `RefreshDefinitions` | `0x06001606` |
| `SlimeDefinitions` | `GetSlimeByIdentifiableId` | `0x06001609` |
| `SlimeDefinition` | `LoadDietFromBaseSlimes` | `0x060015E8` |
| `SlimeDefinition` | `RegisterDynamicAppearance` | `0x060015EA` |
| `SlimeDiet` | `RefreshEatMap` | `0x060015F1` |
| `SlimeDiet` | `ProducePlorts` | `0x060015F3` |
| `SlimeAppearanceDirector` | `RegisterDependentAppearances` | `0x0600185A` |
| `SlimeAppearanceDirector` | `RefreshDefaultChosenSlimes` | `0x0600185B` |
| `SlimeAppearanceDirector` | `GetChosenSlimeAppearance` overloads | `0x0600185C`, `0x0600185D` |
| `PediaDirector` | `InitForLevel` | `0x060026DF` |
| `PediaDirector` | `Get` | `0x060026E3` |
| `PediaDirector` | `GetPediaId` | `0x060026EA` |
| `DirectedActorSpawner` | `Register` | `0x060024B3` |
| `DirectedActorSpawner` | `Spawn` | `0x060024B8` |
| `DirectedSlimeSpawner` | `Register` | `0x060024E4` |
| `DirectedSlimeSpawner` | `MaybeReplacePrefab` | `0x060024E5` |

The presence of these methods identifies useful investigation targets. It does not establish their call order, visibility, static/instance status, or that directly invoking them is valid.

## Important type-identity traps

- The metadata contains two distinct enum TypeDefinitions named `Zone`: indices 121 and 2094. They have different members. Never identify a type by short name alone.
- There are two distinct TypeDefinitions named `IdEntry`: indices 1949 and 2059, with different fields. The correct Slimepedia entry type must be established from resolved field types and owning image/assembly.
- Namespace strings are empty for many game types in this build. Use image/assembly identity plus TypeDefinition index and metadata token rather than assuming a namespace-qualified C# name is unique.
- The serialized TypeIndex values are compact indices into IL2CPP's runtime type table. They are **not** TypeDefinition indices. The current metadata pass preserves these indices but does not guess their target type names.

## What this suggests about a minimal custom-slime proof

The most promising registry candidate is the `SlimeDefinitions` object and its `Slimes` collection, with `RefreshIndexes` / `RefreshDefinitions` as methods to investigate. The appearance path is separate and involves `SlimeAppearanceDirector`; Slimepedia uses a separate `PediaDirector` model with entry and identifiable-to-pedia mappings. World spawning has its own spawner/constraint structures.

A future test should therefore be staged, not implemented as one giant "register slime" call:

1. Resolve the actual managed types for the fields above from the native IL2CPP registration data.
2. Inspect the game's existing serialized slime definitions and identify one stock slime whose prefab, appearance, diet, and pedia references can be reused.
3. Establish when the game's registries are initialized. Do not call refresh/registration methods at arbitrary plugin startup.
4. In a disposable test profile, make a reversible in-memory clone with a unique ID and reused stock assets.
5. Confirm lookup first; only then test appearance, Slimepedia mapping, diet, and spawn integration separately.

No save modification or live gameplay mutation is part of this research pass.

## Asset-bundle observation

The available `data.unity3d` file is a UnityFS bundle. Its header reports bundle format version 8 and engine version `6000.3.0f1`, matching the target game's Unity version. This pass only verified the bundle header; it did not enumerate or extract serialized assets. The larger `datapack.unity3d` and resource files still need inspection.

## Blocking item for the next native-mapping pass

The matching `libil2cpp.so` is required to reconstruct the native metadata registration tables, resolve TypeIndex values, and map method tokens to native method pointers/RVAs. The native library must match this exact game build. Do not infer native addresses from metadata tokens.

After that, asset-bundle inspection is needed to map a stock slime's actual prefab, icon, appearance, materials, diet data, and Slimepedia records. The game-facing capabilities in Runtime Adapter 0.1.0 must remain disabled until both the native mapping and a safe in-game lifecycle point are verified.
