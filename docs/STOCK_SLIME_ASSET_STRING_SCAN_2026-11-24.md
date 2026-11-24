# Stock slime asset scan — 2026-11-24

Target build: Slime Rancher Mobile 1.1.1103, Unity 6000.3.0f1, IL2CPP ARM64.

## Method

The uploaded `data.unity3d` was unpacked as UnityFS v8. Its 1,058 storage blocks were reconstructed (1,051 LZ4/LZ4HC blocks and 7 uncompressed blocks), producing a 138,602,004-byte stream. The directory contains `globalgamemanagers`, `globalgamemanagers.assets`, `sharedassets0.assets`, their resource streams, Unity built-ins, and `level0`.

This pass scans printable strings in the extracted serialized files. It does not yet decode the Unity SerializedFile object table or type trees.

## Confirmed string-level evidence

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
- additional Pink combinations such as `slimePinkCrystalBase`, `slimePinkDervish`, `slimePinkHunterBase`, `slimePinkPhosphorBase`, `slimePinkRadBase`, `slimePinkRockBase`, `slimePinkSaber`, `slimePinkSpikeball`, and `slimePinkTabbyBase`.

The `slimePinkBase` string occurs twice in this file near material-property data. Treat these as material/resource names, not as proof of a prefab or SlimeDefinition object.

The string `MainSlimeDefinitions` is also present in `sharedassets0.assets`. Its owning object and referenced collection have not yet been resolved.

## What is not established yet

This pass does **not** recover the Pink Slime's:
- concrete `SlimeDefinition` serialized instance or field values;
- `IdentifiableId` and collection membership;
- diet, food groups, or favorite food;
- prefab/GameObject reference or prefab hierarchy;
- appearance structure and icon reference;
- Slimepedia entry ID/content;
- spawn constraints or spawn-location data.

Do not create a mod manifest from these strings alone.

## Next analysis target

The next required input is the game's larger `datapack.unity3d` bundle. The current `data.unity3d` establishes that the game-side script types and Pink appearance resources are present, but it has not yielded the complete stock slime definition. After the datapack is available, decode its Unity SerializedFile object tables/type trees and follow object references for Pink Slime, then compare with a second stock slime to distinguish shared defaults from per-slime fields.

Keep all game-facing runtime capabilities disabled until the serialized definition, native type mapping, and safe initialization lifecycle are verified.
