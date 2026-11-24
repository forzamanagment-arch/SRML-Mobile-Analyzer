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

## Next analysis target

The next required input is the game's larger `datapack.unity3d` bundle. The available `data.unity3d` has yielded a named collection with 113 local object references, but the target objects must be resolved through the serialized object table and type metadata. The datapack is not currently present in the accessible Library files for this session.

After receiving it, inspect its UnityFS directory and SerializedFile object tables, resolve the stock slime definition references, and compare Pink Slime with a second stock slime to distinguish shared defaults from per-slime fields.

Keep all game-facing runtime capabilities disabled until the serialized definition, native type mapping, and safe initialization lifecycle are verified.
