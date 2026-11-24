# Slime spawn system research — 2026-11-24

Target: Slime Rancher Mobile 1.1.1103, Unity 6000.3.0f1, IL2CPP ARM64.

## Confirmed serialized component inventory

The UnityPy pass against `datapack.unity3d`, with the matching global manager assets loaded to resolve MonoScript references, identified these MonoBehaviour class counts:

| Class | Instances |
|---|---:|
| `DirectedSlimeSpawner` | 982 |
| `SpawnerTrigger` | 814 |
| `DirectedCrateSpawner` | 542 |
| `SpawnResource` | 422 |
| `DirectedAuxItemSpawner` | 260 |
| `GlitchSlimeSpawner` | 202 |
| `DirectedAnimalSpawner` | 194 |
| `PhasingSpawnResource` | 3 |

These are component instance counts in the parsed asset environment, not counts of unique visible pipes or active runtime spawn points. A component may belong to a prefab, inactive object, pooled object, or scene object.

## Relevant metadata types

The target IL2CPP metadata contains:

- `DirectedActorSpawner`: fields `constraints`, `spawnLocs`, `directedSpawnWeight`, `timeDir`, and `region`; methods include `Register`, `CanSpawn`, `Spawn`, and `GetEligibleConstraints`.
- `DirectedSlimeSpawner`: fields `slimeSpawnFX`, `modDir`, `lookupDir`, and `oasis`; methods include `Register`, `CanSpawn`, and `MaybeReplacePrefab`.
- `SpawnConstraint`: fields `slimeset`, `weight`, `window`, `feral`, and `maxAgitation`.
- `SlimeSet`: field `members`.

This establishes that the game has a data-driven spawn-selection layer with constraints and slime sets. It does not yet prove which component is attached to the visible pipe meshes or exactly when a location's spawn system activates.

## Working hypothesis

The visible tubes/pipes may be presentation objects associated with spawn triggers or directed spawners. The 814 `SpawnerTrigger` instances are a particularly relevant lead for investigating area-entry activation. The actual activation event, scene ownership, and tube-to-spawner relationship remain unverified.

## Next extraction pass

A dedicated UnityPy workflow has been added to the binary research repository:

`.github/workflows/analyze-spawn-network.yml`

It is designed to export:
- GameObject names and their component lists;
- resolved script class names for GameObject components;
- serialized field data for spawn-related MonoBehaviours;
- candidate GameObjects with names containing pipe/tube/spawn/slime/launcher/dispenser/joint/vent.

The workflow must be run manually from GitHub Actions. Its output must be inspected before identifying any visible tube or proposing a runtime hook.

## Safety / implementation boundary

No game state or save data is modified. Do not call spawn methods or mutate scene objects from plugin startup. First establish object identity, field references, scene lifecycle, and the correct main-thread initialization point. Keep runtime spawn registration disabled until those are verified.
