# Stock slime asset scan — 2026-11-24

Target build: Slime Rancher Mobile 1.1.1103, Unity 6000.3.0f1, IL2CPP ARM64.

## Method

The uploaded `data.unity3d` was unpacked as UnityFS v8. Its 1,058 storage blocks were reconstructed (1,051 compressed blocks and 7 uncompressed blocks), producing a 138,602,004-byte stream. The directory contains `globalgamemanagers`, `globalgamemanagers.assets`, `sharedassets0.assets`, their resource streams, Unity built-ins, and `level0`.

The current analysis includes a string scan and a focused read of the serialized bytes around the `MainSlimeDefinitions` name. The complete Unity SerializedFile object table and type trees are still not decoded.

## Confirmed evidence

### `globalgamemanagers`

Contains display strings including:
- `Pink Slime`
- `Pink Plort`
- `Green Slime`
- `Blue Slime`
- `Black Slime`

These establish that the stock names are present in the bundle's global data, but their localization IDs/table schema have not yet been decoded.

### `globalgamemanagers.assets`

Contains serialized script/type records including:
- `SlimeDefinitions`
- `PinkSlimeFoodTypeTracker`
- `PediaUI`
- `SlimeAppearanceCarousel`
- `DirectedSlimeSpawner`

Nearby records include `Assembly-CSharp` and game namespaces such as `MonomiPark.SlimeRancher.DataModel` and `MonomiPark.SlimeRancher.Persist`.

This proves these script/type names are present in the asset metadata. It does not yet identify concrete MonoBehaviour instances or decode their field values.

### `sharedassets0.assets`

Contains appearance/material asset-name leads:
- `slimePinkBase`
- `slimePinkBoomBase`
- `slimePinkTabbyBase`
- additional Pink combinations such as `slimePinkCrystalBase`, `slimePinkDervish`, `slimePinkHunterBase`, `slimePinkPhosphorBase`, `slimePinkRadBase`, `slimePinkRockBase`, `slimePinkSaber`, and `slimePinkSpikeball`.

The `slimePinkBase` string occurs twice near material-property data. Treat these as material/resource names, not as proof of a prefab or SlimeDefinition object.

### `MainSlimeDefinitions` serialized payload

A focused byte-level inspection at offset `0x1F7AB70` in `sharedassets0.assets` found:

- A length-prefixed object name, `MainSlimeDefinitions` (20 bytes).
- Immediately after the name, a little-endian 32-bit count of `113`.
- Following the count, 113 repeated 12-byte reference-shaped records.
- Each record has file ID `0`; the 64-bit path IDs run sequentially from `0xE99` (3737) through `0xF09` (3849).

This is strong evidence that the named serialized payload contains a collection of 113 local object references. The shape is consistent with Unity PPtr records, but the owning object's exact class/type and the target objects' types/names are not yet established. In particular, do not yet assume every referenced object is a SlimeDefinition; the object table and type tree must confirm that.

This is the first concrete serialized collection lead in the available bundle and a much better target than the earlier isolated string hit.

## What is not established yet

This pass does **not** recover the Pink Slime's:
- concrete `SlimeDefinition` instance or field values;
- `IdentifiableId` and confirmed membership in the 113-reference collection;
- diet, food groups, or favorite food;
- prefab/GameObject reference or prefab hierarchy;
- appearance structure and icon reference;
- Slimepedia entry ID/content;
- spawn constraints or spawn-location data.

Do not create a mod manifest from the string scan or collection count alone.

## Datapack + global manager script-reference analysis — 2026-11-24

The target `datapack.unity3d` (UnityFS v8, Unity 6000.3.0f1) was successfully unpacked and parsed with UnityPy. The companion `globalgamemanagers`, `globalgamemanagers.assets`, and `globalgamemanagers.assets.resS` were loaded into the same UnityPy environment so MonoBehaviour script PPtrs could be resolved.

### Confirmed serialized inventory

- 546,788 parsed objects across the loaded environment.
- 38,046 MonoBehaviour objects.
- 38,046 / 38,046 MonoBehaviour script references resolved.
- 0 unresolved MonoBehaviour script references.
- 3,343 MonoScript objects.
- 1,781 Texture2D objects, 1,005 Sprite objects, 1,625 Mesh objects, 1,773 Material objects, and 184 TextAsset objects.
- One non-fatal parser warning remains for PlayerSettings: expected 932 bytes, read 928. It does not affect the completed MonoBehaviour reference map.

The report artifact is `datapack-unity-analysis-report-v3`, produced by workflow run 8 (success).

### Confirmed game component classes present in the datapack

Resolved `Assembly-CSharp` MonoBehaviour classes include:

| Class | Instances |
|---|---:|
| DirectedSlimeSpawner | 982 |
| Identifiable | 712 |
| SlimeAppearance | 345 |
| SlimeAppearanceApplicator | 159 |
| SlimeVarietyModules | 158 |
| SlimeEat | 158 |
| SlimeEatTrigger | 158 |
| SlimeEmotions | 158 |
| SlimeHealth | 158 |
| SlimeFaceAnimator | 158 |
| SlimeFeral | 156 |
| SlimeRandomMove | 155 |
| PediaDirector | 2 |
| PediaUI | 1 |

The script registry also contains `SlimeDefinition` (MonoScript path ID 3264) and `DirectedActorSpawner` (path ID 3276). Their presence in the script registry is confirmed, but this MonoBehaviour-only instance map does not establish that they occur as scene components. In particular, SlimeDefinition data is expected to be represented by serialized asset objects rather than ordinary GameObject components; those objects and their fields still need a dedicated pass.

### What this unlocks

We can now associate many prefab/scene component instances with real game class names instead of treating every MonoBehaviour as anonymous. The 158-instance family around `SlimeEat`, `SlimeEmotions`, `SlimeHealth`, `SlimeVarietyModules`, and `SlimeAppearanceApplicator` is a useful lead for reconstructing the stock slime prefab composition. The 982 `DirectedSlimeSpawner` instances provide a second concrete lead for spawn-system analysis.

### Remaining unknowns

This pass does **not** yet decode serialized field values or prove the 113 references in `MainSlimeDefinitions` point to specific SlimeDefinition objects. It also does not yet recover:
- the object-table types and names for the 113 references;
- each slime's IdentifiableId, diet, favorite food, and produced plorts;
- prefab references and full component hierarchy for each slime;
- appearance-to-icon/texture/sprite links;
- Slimepedia IDs and localized text;
- spawn constraints, region membership, and spawn-location values.

### Next analysis target

Extend the UnityPy pass beyond MonoBehaviour components: enumerate every serialized object in the relevant SerializedFiles, identify ScriptableObject/custom class objects through their MonoScript PPtrs, and decode the `MainSlimeDefinitions` collection. Resolve its 113 path IDs against the correct file's object table, then extract the Pink Slime definition and one comparison slime with their referenced diet, appearance, prefab, and Slimepedia data.

Keep all game-facing runtime capabilities disabled until the serialized definitions, native type mapping, and safe initialization lifecycle are verified.
