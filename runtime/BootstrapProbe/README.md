# SRML Mobile Bootstrap Probe

A harmless first-stage BepInEx Fusion plugin used to verify that FusionCore reaches managed plugin execution inside Slime Rancher Mobile.

## What it does

When BepInEx Fusion loads the plugin, it writes a unique marker:

`[SRMLMOBILE_BOOTSTRAP_PROBE] Load() reached`

It also reports basic runtime information. It does not access game objects, change gameplay, modify saves, or register content.

## Build

The probe targets .NET 10 and compiles against the exact BepInEx Fusion assemblies embedded in the official FusionCore 0.045 APK's source tag:

- `BepInEx.Core.dll`
- `BepInEx.Unity.Common.dll`
- `BepInEx.Unity.IL2CPP.dll`
- `Il2CppInterop.Common.dll`
- `Il2CppInterop.Runtime.dll`
- `MonoMod.RuntimeDetour.dll`

The workflow checks out FusionCore tag `0.045`, extracts its embedded `BepInEx-arm64.zip`, builds the probe, and packages the DLL under:

`BepInEx/plugins/BootstrapProbe.dll`

The artifact is named `SRMLMobile-BootstrapProbe-FusionCore`.

## Test boundary

A successful build proves only that the probe compiles against the assemblies bundled with FusionCore 0.045. It does not prove Slime Rancher Mobile can launch through FusionCore, initialize IL2CPP, or execute this plugin. Those remain separate on-device proof gates.
