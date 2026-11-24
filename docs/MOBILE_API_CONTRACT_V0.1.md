# SRML Mobile API contract 0.1

Status: initial compile-only contract; not yet connected to the game runtime.

## Why this is the first implementation slice

The original PC SRML API assumes Mono/.NET Framework and desktop game assemblies. The mobile target is Unity 6000.3.0f1 with IL2CPP. We must not expose desktop types as if they were available on Android.

The first mobile API therefore provides only stable lifecycle, logging, runtime/game identification, and capability discovery. It intentionally contains no direct Unity or IL2CPP references.

## Contract

Assembly: `SRMLMobile.API.dll`  
Target: `.NET 10`  
API version: `0.1.0`

A plugin implements `ISrmlMobilePlugin`:
- `OnLoad(context)`: runtime has created the mod context.
- `OnGameReady()`: runtime's game adapter has reported readiness.
- `OnUnload()`: reserved; not guaranteed until a safe unload path is implemented.

The context exposes:
- mod identity;
- logger;
- runtime API/loader/runtime-kind information;
- game package, game version, Unity version, and process architecture;
- feature availability queries.

## Capability negotiation

A capability identifier describes what a plugin wants to use. The runtime must independently report whether that capability is available for the current game build. A listed capability is not proof of implementation.

The first adapter should return unavailable for every gameplay capability until each one has a tested implementation. This avoids mods assuming that placeholder interfaces are functional.

## Manifest contract

The companion JSON Schema is `schemas/manifest.schema.json`. The sample is `examples/MinimalPlugin/manifest.json`.

The manifest distinguishes:
- game version compatibility;
- SRML Mobile API compatibility;
- requested capabilities;
- optional managed entry assembly;
- portable resources and Android-target AssetBundles.

The Manager validates package metadata without executing any code. A package with an entry assembly is not loaded by the Manager.

## Explicit non-goals for 0.1

- Loading PC SRML DLLs unchanged.
- Providing Harmony compatibility with Mono patches.
- Arbitrary native library loading.
- Runtime injection or anti-tamper evasion.
- Claiming custom slime registration works.
- Live unloading of managed plugins.

## Integration plan

1. Compile this API assembly in CI.
2. Keep the existing BepInEx BootstrapProbe as the independent runtime bootstrap test.
3. Implement a BepInEx adapter that creates `IModContext` and invokes `ISrmlMobilePlugin`.
4. Validate the adapter using a no-game-API test plugin that only logs lifecycle callbacks.
5. Add game-facing interfaces only after the relevant IL2CPP type and registration paths have been verified on-device.
