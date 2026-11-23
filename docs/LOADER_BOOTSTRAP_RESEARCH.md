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
