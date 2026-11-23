# SRML Mobile Bootstrap Probe

A harmless first-stage BepInEx plugin used to verify that the Android loader reaches managed plugin execution inside Slime Rancher Mobile.

## What it does

When BepInEx loads the plugin, it writes a unique marker:

`[SRMLMOBILE_BOOTSTRAP_PROBE] Load() reached`

It also reports basic runtime information. It does not access game objects, change gameplay, modify saves, or register content.

## Build

The GitHub Actions workflow `.github/workflows/bootstrap-probe.yml` checks out the public NextBep launcher repository for its reference assemblies, builds this project with .NET 8, and packages the resulting DLL under:

`BepInEx/plugins/BootstrapProbe.dll`

The workflow artifact is named `SRMLMobile-BootstrapProbe`.

## Test boundary

A successful build proves only that the probe compiles against the referenced BepInEx API. It does not prove the target game can start NextBep, initialize CoreCLR, load BepInEx, or execute this plugin. Those require an on-device test through the NextBep launcher.
