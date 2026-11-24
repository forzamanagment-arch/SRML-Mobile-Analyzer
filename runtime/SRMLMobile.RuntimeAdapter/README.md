# SRML Mobile Runtime Adapter 0.1.0

This is the first bridge between BepInEx Fusion and the contract-only `SRMLMobile.API`.

## What it does

- Registers as a BepInEx IL2CPP plugin.
- Creates an `IModContext` backed by the BepInEx logger and the known target game/runtime identity.
- Runs a built-in API contract probe.
- Loads the separate `SRMLMobile.SamplePlugin.dll` from `BepInEx/plugins/SRMLMobile/Mods/`.
- Finds public parameterless types implementing `ISrmlMobilePlugin` and invokes their `OnLoad` callback.
- Reports all gameplay capabilities as unavailable.

## What it does not do

- It does not yet parse add-on manifests or resolve dependencies.
- It does not touch Unity game objects or modify gameplay.
- It does not call `OnGameReady` because a reliable game-ready callback has not yet been verified.
- It does not support plugin unloading.
- It is not a security sandbox. Add-on DLLs execute managed code in the game process and should only be installed from sources the user trusts.
- It does not claim that the game successfully reaches this plugin. That must be verified on the device.

## Package

The CI artifact contains:
- `BepInEx/plugins/SRMLMobile.RuntimeAdapter.dll`
- `BepInEx/plugins/SRMLMobile.API.dll`
- `BepInEx/plugins/SRMLMobile/Mods/SRMLMobile.SamplePlugin.dll`

All assemblies are built against the exact BepInEx Fusion assemblies embedded in FusionCore 0.045.
