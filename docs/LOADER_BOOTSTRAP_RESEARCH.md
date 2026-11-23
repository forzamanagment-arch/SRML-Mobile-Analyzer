# Loader and Manager Bootstrap Research

Date: 2026-11-24

Target:
- Game: Slime Rancher Mobile
- Package: `com.playdigious.slimerancher`
- Game version: `1.1.1103` (version code 609)
- Unity: `6000.3.0f1`
- Scripting backend: IL2CPP
- ABI: arm64-v8a
- User environment: Android 16, no root, no PC

## Executive decision

The next critical milestone is not the addon editor or slime factory. It is proving that a loader can start inside this exact game build and execute a harmless test plugin.

**Primary candidate for the first bootstrap experiment: NextBep / BepInEx Android Launcher.**

Do not yet declare it compatible with Slime Rancher Mobile. Its documented platform target (Android 9+, arm64-v8a, Unity IL2CPP) matches the broad platform category, but the exact target Unity 6000.3.0f1 game has not been tested.

The existing analyzer repository should remain focused on metadata/asset analysis. The eventual Manager/Runtime should be a separate application/repository unless the project structure is deliberately changed.

## Why an ordinary companion app is insufficient

Android application sandboxing isolates app processes and private files. A regular Manager APK can:
- import and validate addon archives;
- maintain an addon catalogue and enabled-state configuration;
- keep backups and logs it owns;
- launch an installed game Activity through Android's normal app-launch mechanisms.

A regular Manager APK cannot simply load a native library into another app's already-running process or call that game's IL2CPP objects. Shizuku is not a generic IL2CPP injection mechanism.

Therefore the architecture needs a launcher/bootstrap integration that causes loader code to be initialized as part of the game launch, or a separately installed game build that contains the bootstrap. The first option is the preferred research path.

## Candidate comparison

### 1. NextBep / BepInEx Android Launcher — primary candidate

Repositories:
- https://github.com/NextBep/BepInEx.Android.Launcher
- https://github.com/NextBep/BepInEx.Android

Documented features and design:
- Android launcher for Unity IL2CPP games, arm64-v8a, minimum Android API 28.
- One-tap launch through its launcher flow.
- Modpack management, enable/disable, config editing, logs, and crash diagnostics.
- Uses Android-side Java/Kotlin hooks (Pine) to intercept class loading, Instrumentation, native library loading, and UnityPlayer initialization.
- Uses native bootstrap libraries (`libmain.so` and `libnextbep.so`) to arrange library loading and CoreCLR startup.
- The native bootstrap installs an `il2cpp_init` hook and starts the managed BepInEx preloader.
- Per-game runtime data is documented under `/storage/emulated/0/BepInEx_Launcher/<game-package>/`; internal cache data is kept in launcher-private storage.

Why it is the best first test:
- It already solves the Android launch/bootstrap problem in a general Unity IL2CPP setting.
- It has a minimal test-plugin project.
- It separates Android launcher work from in-game managed plugin work.
- It gives us logs and crash diagnostics before we attempt game-specific registration.

Unproven risks:
- No evidence found that it has been tested with Slime Rancher Mobile 1.1.1103.
- No evidence found for Unity 6000.3.0f1 compatibility on this title.
- The launcher depends on Android framework behavior and package/activity details that may differ on the target device's Android 16 / OriginOS build.
- BepInEx/Il2CppInterop metadata and interop generation support for this exact Unity 6 metadata v39 build must be tested separately from the native bootstrap.
- Its documented general platform support is not a guarantee for every Unity IL2CPP title.

Licensing:
- The launcher/native integration is GPL-3.0.
- BepInEx is LGPL-2.1.
- Do not copy or fork launcher/native source into SRML Mobile without deciding to comply with the applicable GPL-3.0 obligations. Initial evaluation can use the public project as an external test harness without copying its implementation.

### 2. StArray.ModManager — secondary research reference

Repository:
- https://github.com/StArraySharp/StArray.ModManager

Its README describes:
- Android arm64 Unity IL2CPP support;
- native library loading into the game process;
- Dobby hooks;
- embedded CoreCLR;
- a UnityResolve-based reflection layer;
- mod scanning, dependency resolution, enable/disable, and an overlay.

This is architecturally relevant, especially for a future native/managed bridge and mod lifecycle. However, the README itself says much of the code was AI-generated, and the repository is a more ambitious combined mod manager/runtime. It is not a safer first proof than testing the more directly documented NextBep launcher.

Use it as a design/reference project, not as an assumed dependency.

### 3. BNM Android / native-only approaches — fallback research

A native IL2CPP hook library can avoid depending on a managed CoreCLR plugin runtime, but it would require us to implement more of the mod API, lifecycle, asset handling, and addon loading ourselves. Keep this as a fallback if the BepInEx/Il2CppInterop path cannot handle the target Unity build.

## Recommended architecture for SRML Mobile

Separate three responsibilities:

### A. SRML Mobile Manager

The Android app users interact with:
- imports `.SRMLmobileAddon` packages;
- validates manifest, hashes, paths, dependencies, game version, and Runtime API;
- manages enabled/disabled addons and profiles;
- keeps backups and diagnostics;
- starts the supported launch flow;
- displays the Runtime's actual load status.

The Manager must not display "running" merely because a package was imported or enabled.

### B. Bootstrap / launcher layer

Initial experiment: use NextBep as an external bootstrap test harness.

Longer-term options:
1. Integrate/adapt the launcher under a deliberate GPL-3.0 licensing decision.
2. Keep a separate launcher and define a documented Manager-to-launcher integration contract, if the launcher exposes a stable supported interface.
3. Build our own bootstrap only if neither route is practical.

Do not assume an arbitrary Android intent or file path is already supported by NextBep. Its actual exported activities, storage permissions, and inter-app integration contract must be inspected before designing that bridge.

### C. SRML Mobile Runtime

An in-process managed plugin, initially loaded by BepInEx:
- identifies the exact game package/version and Unity build;
- waits until IL2CPP and required game systems are ready;
- loads addon packages from a defined per-game directory;
- validates and resolves dependencies;
- provides a small stable API to data-driven content mods;
- reports structured status and errors to the Manager through a narrow IPC/logging channel.

The first Runtime should not execute arbitrary third-party scripts. The first addon format should be data-only. Optional managed code support can be added later with explicit compatibility and capability rules.

## Critical distinction: bootstrap success vs. modding success

These are separate gates:

1. **Game launch:** game starts through the launcher.
2. **Native bootstrap:** loader libraries initialize in the game process.
3. **IL2CPP readiness:** the loader observes successful IL2CPP initialization.
4. **Managed runtime:** CoreCLR starts successfully.
5. **Plugin execution:** a harmless test plugin logs a unique startup marker.
6. **Game interop:** required game classes and methods can be resolved.
7. **Game modification:** a reversible, harmless test change is visible in game.
8. **SRML functionality:** slime registration, Slimepedia, diet, spawning, and assets work.

Passing one gate does not prove the next. In particular, successful BepInEx startup does not prove that a new slime can be registered.

## First proof-of-concept plan

### Gate 0 — compatibility inventory

Before modifying or repackaging anything, record:
- exact game package/version/version code;
- target Activity and launchable Activity;
- installed APK split structure and native library locations;
- arm64 ABI;
- Unity and IL2CPP library names;
- available app storage locations and Android 16 restrictions.

Do not overwrite the user's original game installation or touch save data.

### Gate 1 — external launcher test

Use the upstream NextBep launcher as-is, without copying its source into this repository.

Expected evidence:
- launcher detects the installed target game;
- launcher can start it;
- game reaches its normal menu;
- launcher logs show the bootstrap stages;
- no unsupported-version assumptions are hidden as success.

If the launcher cannot detect or start this game, stop and document the exact failure before writing a custom injector.

### Gate 2 — minimal test plugin

Use the upstream test-plugin pattern, with a plugin that does no game modification. It should only emit a unique marker and report:
- plugin startup reached;
- process/package identity;
- Unity version if available;
- IL2CPP readiness;
- BepInEx/Il2CppInterop initialization state.

Success requires finding the marker in the expected log, not merely seeing the game launch.

### Gate 3 — game interop smoke test

Only after Gate 2:
- resolve a small number of harmless known game types;
- verify the target assembly/type identity and expected fields;
- compare results with the metadata v39 analysis;
- fail closed on unexpected game versions or missing members.

### Gate 4 — first reversible game-side proof

Only after the interop smoke test:
- make a minimal, reversible change that does not alter saves or persistent game data;
- confirm it is visible;
- confirm a clean launch without the loader restores normal behavior.

Then proceed to cloning an existing slime definition and appearance.

## Manager integration decision

Do not start by writing a custom native injector inside SRML Mobile Manager. That would duplicate the hardest and riskiest subsystem before we know whether the existing Android bootstrap works on the target game.

The most economical route is:
1. prove NextBep can launch this exact game;
2. prove a test plugin runs;
3. build SRML Mobile Runtime as a plugin;
4. only then decide whether the final Manager should integrate NextBep's GPL-3.0 launcher code or communicate with a separately installed launcher through a verified interface.

## Current status

| Area | Status |
|---|---|
| Target game is Unity IL2CPP arm64 | Confirmed from prior target inspection |
| Android launcher/bootstrap project exists | Confirmed |
| NextBep has a plugin test project | Confirmed from repository tree |
| NextBep supports Android IL2CPP generally | Project documentation claim |
| NextBep supports this exact game build | Not tested |
| Unity 6000.3.0f1 interop works | Not tested |
| Test plugin executes in Slime Rancher Mobile | Not tested |
| SRML Mobile Runtime exists | Not implemented |
| Manager-to-launcher integration contract | Not inspected/proven |

## Sources inspected

- NextBep launcher README: https://github.com/NextBep/BepInEx.Android.Launcher
- NextBep native bootstrap source: https://github.com/NextBep/BepInEx.Android.Launcher/blob/main/app/src/main/cpp/main/main.cpp
- NextBep Android BepInEx fork: https://github.com/NextBep/BepInEx.Android
- StArray.ModManager: https://github.com/StArraySharp/StArray.ModManager
- BepInEx IL2CPP install documentation: https://docs.bepinex.dev/v6.0.0-pre.1/articles/user_guide/installation/unity_il2cpp.html

This is a research and implementation plan, not a claim that the loader has already been run against Slime Rancher Mobile.


## Additional source-level inspection (not just README claims)

The following files were inspected in the NextBep launcher repository:

- `app/src/main/java/com/bepinex/android/GameDetector.kt`
- `app/src/main/java/com/bepinex/android/BootstrapActivity.kt`
- `app/src/main/java/com/bepinex/android/FileExtractor.kt`
- `app/src/main/cpp/main/main.cpp`
- `TestPlugin/Plugin.cs`

Confirmed from source:

1. **Game detection:** `GameDetector` queries launchable activities, checks the installed APK as a ZIP for `lib/<abi>/libil2cpp.so`, and records package/version information. It does not currently prove that the game is compatible; detection only identifies an IL2CPP-shaped target.
2. **Bootstrap launch:** `BootstrapActivity` obtains the target package context with code access, prepares a game classloader, resolves the target launch Activity, prepares per-game runtime state, installs Android-side hooks, initializes native library routing, then starts a stub Activity that is rewritten to the game's real launch Activity.
3. **Storage:** the launcher requests all-files access on Android 11+ for its documented external per-game runtime/mod data. The .NET runtime is extracted into launcher-private storage. This is an important integration and user-permission consideration for our Manager.
4. **Native stage:** `main.cpp` loads the NextBep/native runtime libraries, initializes the Fusion bootstrap, and routes Unity and IL2CPP library loading. This is a concrete native bootstrap implementation, not a normal Android app launch.
5. **Test plugin:** the sample plugin derives from BepInEx `BasePlugin` and writes a distinct startup marker from `Load()`. This is exactly the kind of harmless smoke test we should use before touching game objects.

### Implication for our Manager

NextBep already has its own launcher UI, storage model, and modpack manager. It is not enough for SRML Mobile Manager to write an addon into an arbitrary directory and launch the game's normal icon: the game must be started through the bootstrap flow.

For the first experiment, use NextBep's own UI and its sample plugin unchanged. If that works on the target, the next implementation decision is whether SRML Mobile Manager becomes a licensed integration/fork or whether NextBep exposes a stable external launch/import contract we can use. Do not invent an intent action or private API before verifying it in source.

### Evidence boundaries

The source inspection confirms how the launcher is designed. It does not confirm that:
- the target game passes its game-detection and bootstrap steps;
- Android 16 / OriginOS permits every required hook on this device;
- the target Unity 6000.3.0f1 build initializes BepInEx and Il2CppInterop successfully;
- a plugin can resolve Slime Rancher Mobile's game types;
- a custom slime can be registered.


---

## Addendum: FusionCore and Unity 6000 Android verification research

Date: 2026-11-24

This addendum supersedes the earlier candidate ranking above. The earlier section was written before inspecting FusionCore's release assets and the newer Tb1281 Android port.

### FusionCore: viable first installable bootstrap candidate

Repository: https://github.com/All-Of-Us-Mods/FusionCore

Source and release inspection confirms:
- Latest inspected release: `0.045`.
- Release assets include `fusionApp-release.apk` (57,222,476 bytes) and `fusionApp-debug.apk` (60,570,988 bytes).
- Release APK SHA-256 published by GitHub: `661ad5ebaef78c9ea395d7751f9c4f758b263008a4e012d1167cc6ae3aec3602`.
- App Gradle config: minSdk 24, targetSdk 36, arm64-v8a only.
- README says Android 7/API24 minimum, but actual testing is Android 11+; do not interpret minSdk as proof of Android 16 / OriginOS compatibility.
- The project is GPL-3.0. Treat it as an external test harness unless we deliberately accept the corresponding distribution/source obligations.

Relevant source behavior confirmed:
- Scans installed Unity IL2CPP apps; current README says a game-specific manifest entry is no longer required.
- Resolves the target launch Activity, creates a game package context/classloader, installs package/activity/notification/instrumentation hooks, and launches the game Activity through its stub Activity.
- Redirects native library lookup for Fusion, IL2CPP, Unity, and .NET runtime libraries.
- Detects the Unity version from copied Unity data files. Its version parser accepts release/final suffixes such as `6000.3.0f1`.
- Downloads unstripped `libunity.so` and symbols for the exact Unity version and ABI. If download fails, source falls back to the original game `libunity.so`.
- The FusionCore.UnityDependencies repository has a release tag `6000.3.0f1` with `libunity.so.arm64-v8a` (28,082,328 bytes), SHA-256 `04c73a41f1a8301fee54902e90fd198d536c3e8325b674f27bb383a1d050e846`, plus matching symbol library. This removes one major version-asset uncertainty for our exact Unity build.
- Its Unity managed-library resolver normalizes the game version to `6000.3.0`; the Unity BepInEx library repository lists that version.
- Its metadata-header check accepts IL2CPP metadata versions 16 through 64. Our observed metadata version 39 passes this preliminary header check. This is not proof that full interop generation or plugin loading succeeds.

Important unresolved risks:
- No test has been run against package `com.playdigious.slimerancher` or game version `1.1.1103`.
- No test has been run on the user's Android 16 / OriginOS device.
- Need determine whether this game's IL2CPP exports are obfuscated and whether FusionCore's automatic API mapping handles the exact binary.
- The launcher hosts the game Activity inside its process; game-specific SDKs, billing, Firebase, activity lifecycle, and package identity can cause failures even after initial Unity startup.
- FusionCore's APK release digest is known, but its APK signing certificate and exact installed behavior have not yet been independently checked. Do not install it solely on the basis of the release page.

### Tb1281/BepInEx-Android: stronger Unity 6000 engineering reference

Repository: https://github.com/Tb1281/BepInEx-Android

The README and project documentation describe a newer Android arm64 IL2CPP port with a multi-stage, provenance-pinned build pipeline. Its documented architecture uses a native bootstrap, CoreCLR hosting, BepInEx IL2CPP chainloader, and native hook engines. The repository explicitly credits FusionCore as a reference for injection-chain/native-loader architecture.

Its hardware verification matrix reports:
- Snapdragon 8 Gen 3, Android 15+, Unity 6000, The Tower: pass.
- Snapdragon 8 Gen 3, Android 15+, Unity 6000, Unlock!: pass.
- Snapdragon 8 Gen 2, Android 15+, Unity 2022.3, Revolution Idle: pass.
- A more detailed 2026-10-14 re-verification reports The Tower 29.0.6 on Unity 6000.3.15f1 reaching the menu, and Unlock! 19.0 on Unity 6000.0.68f1 reaching the menu.

This is meaningful evidence that a modern BepInEx/CoreCLR Android path can work on Unity 6000. It is still not evidence for Slime Rancher Mobile. The repository has no GitHub Releases at the time of inspection, and its build requires several pinned producer steps (native dependencies, .NET runtime, managed framework, then launcher APK). It is therefore a stronger technical fallback/reference, but not the simplest first phone-side experiment.

The repository's Unity 6000 case study also documents real launcher-hosting compatibility problems involving Firebase resource lookup/component discovery, Play Services identity, and billing retry loops. These are useful risk areas to watch if our target game reaches Unity startup but fails later.

### Updated decision

1. **First external bootstrap candidate:** FusionCore 0.045, because it has an installable upstream APK and a matching Unity 6000.3.0f1 arm64 native dependency release. This is a candidate for controlled evaluation, not a compatibility claim or an instruction to install immediately.
2. **Primary advanced technical reference / fallback:** Tb1281/BepInEx-Android, because its source documents and reports physical-device tests on Unity 6000, including 6000.3.15f1. Its lack of a published APK and heavier build pipeline make it less convenient for the first test.
3. **NextBep Launcher:** keep as historical reference only; its own README warns that it is not stable and recommends FusionCore.

### Revised proof gates

Before asking the user to install anything:
- Independently inspect the FusionCore release APK's package identity, signing certificate, manifest, and static contents; verify its SHA-256 against the published digest.
- Confirm the game can be detected without requiring unsupported storage permissions or changing the original game installation.
- Confirm the target game's Activity and native library layout are compatible with the launch path.
- Keep original game installation and save data untouched.

Only then conduct a controlled first launch. A successful launch is still only Gate 1; plugin marker, IL2CPP readiness, interop, and a harmless reversible game-side test remain separate gates.


---

## Addendum: FusionCore 0.045 APK verification and probe retarget

Date: 2026-11-24

### APK verification performed in GitHub Actions

A reproducible inspection workflow was added at `.github/workflows/inspect-fusioncore-apk.yml`. It downloads the official FusionCore release assets and checks the published GitHub SHA-256 values, APK manifest, signing certificate, native libraries, and embedded BepInEx archive.

The latest inspected APK (`0.045`) passed:
- Downloaded file SHA-256 matched the GitHub release asset digest: `661ad5ebaef78c9ea395d7751f9c4f758b263008a4e012d1167cc6ae3aec3602`.
- `apksigner verify` succeeded using APK Signature Scheme v2.
- The same signing certificate was present in both releases `0.0.4` and `0.045`; certificate SHA-256: `231eed8eb870813a2b820245b78775258af384bf1ae8be0d82abe5fe84c1d692`.
- Package ID: `dev.allofus.fusioncore`.
- Label: `Fusion Core`.
- minSdk 24, targetSdk 36, compileSdk 37, ABI `arm64-v8a`.
- Note: despite the release tag `0.045`, the APK manifest still reports `versionName=0.0.1` and `versionCode=1`.

This establishes that the downloaded APK matches the published release file and has a consistent signer across the two checked releases. It does not prove that the software is bug-free or compatible with Slime Rancher Mobile.

### Permission review

The APK manifest declares:
- `MANAGE_EXTERNAL_STORAGE` (the app explicitly sends the user to Android's all-files access settings).
- `QUERY_ALL_PACKAGES` (used by the selector's installed-game scan).
- Legacy and media storage permissions, Internet/network permissions, and notification permission.
- Also `CAMERA`, `FOREGROUND_SERVICE_MICROPHONE`, and Play Billing permission.

In the reviewed FusionCore Java/Kotlin source, the all-files permission is explicitly checked and requested. The selector scans installed launcher apps, checks APK/split APK entries for `libil2cpp.so`, and copies game assets into `/sdcard/FusionCore/<package>`. It also reads the target game's declared permissions and may ask for missing ones before launch. No explicit camera or microphone API use was found in the reviewed launcher source; their manifest declarations remain a caution and are not a reason to grant those permissions if prompted without a clear need.

The original game APK is read and copied into FusionCore's external working directory; the inspected launch path does not patch the installed game APK in place. This is source-level evidence, not a guarantee against game crashes or save issues.

### Exact embedded runtime contents

The official `0.045` APK contains arm64 native libraries including:
- `libmain.so`
- `libfusion.so`
- `libdobby.so`
- `libcoreclr.so` and `libclrjit.so`
- CoreCLR support libraries.

It also bundles `BepInEx-arm64.zip`, `dotnet-arm64.zip`, and `il2cpp2mono-arm64.zip`. The embedded BepInEx archive contains:
- `core/BepInEx.Core.dll`
- `core/BepInEx.Unity.IL2CPP.dll`
- `core/BepInEx.Unity.Common.dll`
- `core/Il2CppInterop.*.dll`
- `core/MonoMod.*.dll`
- `config/BepInEx.cfg`
- `plugins/`

### BootstrapProbe retargeted and compiled

The existing harmless probe has been retargeted from NextBep's reference assemblies to the exact BepInEx Fusion assemblies embedded in FusionCore tag `0.045`. It now targets .NET 10, matching the runtime framework used by this BepInEx Fusion build.

GitHub Actions run `45276358708` completed successfully:
- Extracted the embedded runtime archive from FusionCore tag `0.045`.
- Verified all required reference assemblies exist.
- Built `BootstrapProbe.dll` against those assemblies.
- Build result: 0 warnings, 0 errors.
- Packaged the DLL at `BepInEx/plugins/BootstrapProbe.dll`.

Artifact: `SRMLMobile-BootstrapProbe-FusionCore`.

This is a compile/package verification only. The probe has not been executed inside Slime Rancher Mobile.

### Updated readiness decision

Static prerequisites now align unusually well:
- Target game is arm64 IL2CPP and contains `libil2cpp.so`.
- Its metadata header is valid magic/version 39; FusionCore's preliminary metadata check accepts versions 16 through 64.
- FusionCore has a matching unstripped Unity library release for Unity `6000.3.0f1`, arm64-v8a.
- The Unity base-library repository contains exact `6000.3.0.zip`.
- The probe compiles against the exact embedded FusionCore BepInEx assemblies.

Remaining unknowns are runtime-only: detection on the actual device, game Activity hosting, Unity initialization, IL2CPP API mapping for this exact `libil2cpp.so`, and actual plugin execution. Android 16 / OriginOS 16 and this specific game build remain untested.


---

## Addendum: FusionCore 0.045 JNI crash on Unity 6 / Android 16

Date: 2026-11-24

### Device observation

Slime Rancher Mobile is detected by FusionCore 0.045, but launching through FusionCore terminates at the early Unity loading screen. The game still launches normally when started directly. The device's Android exit report identifies a CheckJNI fatal error in the FusionCore native bootstrap:

```
JNI DETECTED ERROR IN APPLICATION: obj == null
in call to GetBooleanField
from boolean com.unity3d.player.NativeLoader.load(java.lang.String)
```

The report's native stack enters `fusion_parse_config()` during `fusion_bootstrap_from_libmain()`. BepInEx has no `LogOutput.log`, consistent with the failure occurring before the managed chainloader starts.

### Source-level failure path in FusionCore tag 0.045

Reviewed files:
- `fusionApp/src/main/jni/fusion/src/fusion.cpp`
- `fusionApp/src/main/jni/fusion/src/fusion_config.cpp`
- `fusionApp/src/main/jni/fusion/src/utilities/java.cpp`
- `fusionApp/src/main/jni/main/main.cpp`

The native `load(JNIEnv*, jobject, jstring)` entry point calls `fusion_bootstrap_from_libmain(env)`. That calls `get_fusion_config(env)`, then passes the returned object directly to `fusion_parse_config(env, javaConfig)`. There is no null check between these calls.

`get_fusion_config()` can return null if it cannot obtain the current Unity Activity, its Intent, or the `fusioncore.config` Parcelable extra. `fusion_parse_config()` immediately invokes `GetBooleanField(jFusionConfig, ...)` for `isIl2Cpp2Mono` and `useOriginalLibUnity`. A null config therefore reaches JNI `GetBooleanField` and matches the observed CheckJNI error.

### Strong Unity 6 compatibility hypothesis

The target game uses Unity `6000.3.0f1`. Unity's Unity 6 upgrade documentation states that the former Java `UnityPlayer` class was split into `UnityPlayerForActivityOrService` and `UnityPlayerForGameActivity`, both derived from the `UnityPlayer` base class. Unity also documents that the GameActivity entry point is `UnityPlayerGameActivity` and uses the `UnityPlayerForGameActivity` bridge.

FusionCore 0.045's `getUnityActivity()` searches these class names in this order:
1. `com/unity3d/player/UnityPlayer`
2. `com/unity3d/player/UnityPlayerForGameActivity`
3. `com/unity3d/player/UnityPlayerForActivityOrService`

It stops as soon as the first class is found, then looks for a static `currentActivity` field on that class. If Unity 6's base `UnityPlayer` is present but the field is declared on the concrete bridge class, FusionCore returns null without trying the bridge classes. This is a particularly plausible explanation for the null Activity -> null config -> `GetBooleanField(null, ...)` crash. It is not yet proven against this exact game's packaged Unity Java classes.

A second possible null path is that the Activity is found but its Intent does not contain the expected `fusioncore.config` extra. The current report alone cannot distinguish these two cases.

### Additional native parsing defect

The `GET_JBOOLEAN_FIELD` macro tests a `jboolean` value with `if (!value)` and logs it as "null". A Java boolean false is a valid value, not a null reference. This is a misleading diagnostic and the subsequent `ExceptionClear()` is inappropriate when no JNI exception is pending. It is not the cause of the observed null-object crash, but should be corrected in any maintained fork.

### Safe fix direction (not yet implemented)

1. Make `getUnityActivity()` test each candidate class independently: find the class, look up `currentActivity`, read the field, and continue to the next candidate if either the field ID or Activity object is null. Delete local references on every path.
2. Add explicit null checks after `getUnityActivity()`, `getIntent()`, and `getParcelableExtra()`; log which stage failed and return a controlled bootstrap failure.
3. Check `javaConfig` in `fusion_bootstrap_from_libmain()` before calling `fusion_parse_config()`.
4. Check `jFusionConfig` and each `GetFieldID()` result before any field read in `fusion_parse_config()`. Do not call `ExceptionClear()` merely because a boolean value is false.
5. If the Activity exists but the extra is absent, inspect Intent wrapping/Parcelable class-loader propagation separately. Do not mask that failure by guessing a config.

The first fix should prevent the fatal null dereference and expose a useful log; it may not by itself make the game launch. The Unity bridge-field hypothesis must be verified against the target APK's actual classes before treating it as the confirmed root cause.

### Related upstream evidence

- FusionCore source tag 0.045: https://github.com/All-Of-Us-Mods/FusionCore/tree/0.045
- FusionCore issue #34 reports a different JNI-related crash on Android 16 with Unity 2020.3.41f1; the maintainer attributed that report to the Unity 2020.X interop path. It is not the same stack or proven same defect: https://github.com/All-Of-Us-Mods/FusionCore/issues/34
- Unity 6 upgrade guide documents the UnityPlayer bridge-class split: https://docs.unity.cn/6000.2/Documentation/Manual/UpgradeGuideUnity6.html
- Unity 6000.3 AndroidApplication.currentActivity reference: https://docs.unity.com/en-us/engine/6000.3/script-reference/unityengine/android/androidapplication/currentactivity
- Unity 6 Android application entry documentation describes `UnityPlayerForGameActivity` and `UnityPlayerGameActivity`: https://docs.unity.com/en-us/engine/6000.7/manual/platform-specific/android/developing/unityasa-library

Status: source-level root-cause candidate identified; no FusionCore binary has been modified, and no device-side fix has been tested.


### Follow-up: exact null-dereference path confirmed in source

A line-by-line recheck of tag 0.045 confirms the path more precisely:

- `fusion_bootstrap_from_libmain()` at `fusion.cpp:161-164` obtains `javaConfig = get_fusion_config(env)`, immediately calls `fusion_parse_config(env, javaConfig)`, then deletes the local reference. There is no null check on `javaConfig`.
- `fusion_parse_config()` first resolves the FusionConfig class. If that class cannot be found, it returns early. If the class is found, it immediately executes `GET_JBOOLEAN_FIELD(isIl2Cpp2Mono)`.
- That macro calls `GetFieldID(configClass, ...)` and then `GetBooleanField(jFusionConfig, fieldId)` without checking whether `jFusionConfig` is null.

Therefore, the reported CheckJNI error is directly explained if `get_fusion_config()` returns null while the FusionConfig class remains loadable. This confirms the null-config dereference as the immediate defect. It does not yet identify which condition made `get_fusion_config()` return null.

The earlier Unity 6 bridge-class hypothesis remains plausible but unverified. Unity 6000.3 documentation confirms that the old concrete UnityPlayer Java API was split into `UnityPlayerForActivityOrService` and `UnityPlayerForGameActivity`, with both deriving from the UnityPlayer base class. The FusionCore helper stops at the first class it finds and expects a static `currentActivity` field on that class. We need inspect the target APK's actual DEX definitions and field ownership before selecting the exact fix.

### Diagnostic artifact needed from target APK

The smallest useful next artifact is the target game's DEX bytecode, not its large Unity asset bundles:
- `classes.dex`
- any additional `classes2.dex`, `classes3.dex`, etc. present in the same APK/split APKs.

We need determine whether `UnityPlayer`, `UnityPlayerForActivityOrService`, and `UnityPlayerForGameActivity` are present, which one declares `currentActivity`, and which Activity class is the manifest launcher. Do not infer this from Unity version alone.

No target APK DEX has been supplied or inspected yet. Do not claim the bridge-field mismatch is confirmed until that inspection is complete.


### Follow-up: target APK DEX inspection (2026-11-24)

The user supplied `classes.dex`, `classes2.dex`, and `classes3.dex` from the target game APK. All three have valid DEX magic/version headers and were successfully parsed.

Observed class counts:
- `classes.dex`: 8,068 class definitions.
- `classes2.dex`: 5,374 class definitions.
- `classes3.dex`: 17 class definitions.

Relevant findings in `classes2.dex`:
- `com.unity3d.player.UnityPlayer` is present.
- It declares a static field `currentActivity` of type `android.app.Activity`.
- `com.unity3d.player.UnityPlayerForActivityOrService` is present and extends `UnityPlayer`.
- `com.unity3d.player.UnityPlayerForGameActivity` is present and extends `UnityPlayer`.
- `com.unity3d.player.UnityPlayerActivity` is present and extends `android.app.Activity`.
- `com.google.firebase.MessagingUnityPlayerActivity` is present and extends `UnityPlayerActivity`.

This **falsifies the specific earlier suspicion** that the target's UnityPlayer base class necessarily lacks the `currentActivity` field. The field is explicitly declared on the base class in the supplied DEX, so FusionCore's first candidate class does have the field it looks up. This does not prove the field is populated at the moment FusionCore queries it, nor that the target launch Activity is one of the listed classes.

The supplied DEX files do not include the target APK's AndroidManifest.xml, so they do not establish which Activity is the actual launcher or whether the launch Intent contains FusionCore's expected `fusioncore.config` Parcelable. The immediate null-config dereference remains confirmed; the upstream cause is still unresolved.

Next diagnostic artifact: the target APK's decoded manifest or a screenshot/export of its application Activities and launcher Activity from MT Manager. Specifically verify the `MAIN` + `LAUNCHER` Activity and its fully-qualified class name. Do not infer the launcher from the presence of `UnityPlayerActivity` alone.

The obfuscated Activity in `classes3.dex` is not identified as the launcher from DEX structure alone; no conclusion is drawn about its purpose.


### Follow-up: target APK binary AndroidManifest.xml parsed (2026-11-24)

The user supplied the target APK's binary `AndroidManifest.xml`. It was parsed directly as Android binary XML; no re-export from MT Manager was necessary.

Manifest identity:
- Package: `com.playdigious.slimerancher`
- Version name: `1.1.1103`; version code: `609`
- minSdk: 29; targetSdk: 36; compileSdk: 36.
- Application class: `android.app.Application`.

**Actual `MAIN` + `LAUNCHER` Activity:**
- `com.m8bjh1b7.w1cn8q.F587w173`
- Exported: true
- launchMode: 2 (`singleTask`)
- screenOrientation: 6
- It is an obfuscated application Activity, not one of the standard Unity/Firebase Activity class names.

DEX cross-check:
- The class `com.m8bjh1b7.w1cn8q.F587w173` is present in `classes3.dex`.
- Its direct superclass is `android.app.Activity`, not `UnityPlayerActivity` and not `UnityPlayerForGameActivity`.
- Its DEX class-data lists methods `onCreate`, `startOriginalLauncher`, a constructor, and a synthetic lambda method.
- The manifest separately declares `com.google.firebase.MessagingUnityPlayerActivity` as an exported Activity with `unityplayer.UnityActivity=true` metadata, but it has no `MAIN` / `LAUNCHER` intent filter in this manifest.

Interpretation:
- The app's launcher entry point is a custom/obfuscated wrapper Activity. It is not the Firebase Unity Activity declared separately.
- This is a concrete new lead for FusionCore's failure: its launch/hook path may be assuming that the launcher Activity is the Unity Activity, or the wrapper may launch/delegate to the original Unity Activity in a way FusionCore's Activity/config propagation does not preserve.
- This does **not** yet prove the wrapper is the cause. Its method names show a `startOriginalLauncher` helper, but the method's full behavior has not yet been disassembled, and the manifest alone cannot establish which Activity is current when native Fusion bootstrap asks for `fusioncore.config`.
- The earlier hypothesis that `currentActivity` is absent from the UnityPlayer base class remains falsified by DEX inspection.

Next source-level diagnostic: inspect the bytecode of `F587w173.onCreate()` and `startOriginalLauncher()`, identify the actual target Activity class it starts, and compare that with FusionCore's Activity/Intent hooks. This should determine whether the wrapper is a simple trampoline, a protection/loader layer, or a custom Unity launch path. Do not patch the game or FusionCore until this flow is understood.
