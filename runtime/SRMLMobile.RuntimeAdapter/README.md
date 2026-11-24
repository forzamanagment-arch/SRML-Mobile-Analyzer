# SRML Mobile Runtime Adapter 0.1.0

This is the first bridge between BepInEx Fusion and the contract-only `SRMLMobile.API`.

## What it does

- Registers as a BepInEx IL2CPP plugin.
- Creates an `IModContext` backed by the BepInEx logger and the known target game/runtime identity.
- Instantiates an in-assembly smoke-test implementation of `ISrmlMobilePlugin`.
- Invokes `OnLoad` and logs API/game/runtime information.
- Reports all gameplay capabilities as unavailable.

## What it does not do

- It does not load arbitrary external add-on DLLs yet.
- It does not touch Unity game objects or modify gameplay.
- It does not call `OnGameReady` because a reliable game-ready callback has not yet been verified.
- It does not support plugin unloading.
- It does not claim that the game successfully reaches this plugin. That must be verified on the device.

## Package

The CI artifact contains:
- `BepInEx/plugins/SRMLMobile.RuntimeAdapter.dll`
- `BepInEx/plugins/SRMLMobile.API.dll`

Both are built against the exact BepInEx Fusion assemblies embedded in FusionCore 0.045.
