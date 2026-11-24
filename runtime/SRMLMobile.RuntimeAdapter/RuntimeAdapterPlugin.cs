using System;
using System.Runtime.InteropServices;
using BepInEx;
using BepInEx.Unity.IL2CPP;
using SRMLMobile.API;

namespace SRMLMobile.RuntimeAdapter;

[BepInPlugin(PluginGuid, PluginName, PluginVersion)]
public sealed class RuntimeAdapterPlugin : BasePlugin
{
    public const string PluginGuid = "com.srmlmobile.runtimeadapter";
    public const string PluginName = "SRML Mobile Runtime Adapter";
    public const string PluginVersion = "0.1.0";

    public override void Load()
    {
        Log.LogInfo("================================================");
        Log.LogInfo("[SRMLMOBILE_RUNTIME_ADAPTER] BepInEx Load() reached");
        Log.LogInfo($"Adapter version: {PluginVersion}");
        Log.LogInfo($"Process architecture: {RuntimeInformation.ProcessArchitecture}");
        Log.LogInfo($"Runtime version: {Environment.Version}");

        try
        {
            var context = new ModContext(
                new ModIdentity(
                    "srmlmobile.runtime.smoke-test",
                    "SRML Mobile Runtime Smoke Test",
                    "0.1.0",
                    "SRML Mobile"),
                new BepInExLogger(Log),
                new RuntimeInfo("0.1.0", PluginVersion, "IL2CPP via BepInEx Fusion / Il2CppInterop"),
                new GameInfo(
                    "com.playdigious.slimerancher",
                    "1.1.1103",
                    "6000.3.0f1",
                    RuntimeInformation.ProcessArchitecture.ToString()),
                new NoGameplayFeatures());

            // This built-in test plugin exercises the public API contract without
            // loading external mod code or touching game objects.
            ISrmlMobilePlugin smokeTest = new RuntimeApiSmokeTest();
            smokeTest.OnLoad(context);

            Log.LogInfo("[SRMLMOBILE_RUNTIME_ADAPTER] API contract invocation succeeded");
            Log.LogInfo("Game-facing capabilities remain disabled in this build.");
        }
        catch (Exception exception)
        {
            Log.LogError("[SRMLMOBILE_RUNTIME_ADAPTER] API contract invocation failed: " + exception);
        }

        Log.LogInfo("================================================");
    }
}

internal sealed class RuntimeApiSmokeTest : ISrmlMobilePlugin
{
    public void OnLoad(IModContext context)
    {
        context.Logger.Info("ISrmlMobilePlugin.OnLoad invoked by the BepInEx adapter.");
        context.Logger.Info($"Mod identity: {context.Mod.Id} {context.Mod.Version}");
        context.Logger.Info($"Game: {context.Game.PackageName} {context.Game.GameVersion}");
        context.Logger.Info($"Unity: {context.Game.UnityVersion}");
        context.Logger.Info($"Runtime: {context.Runtime.RuntimeKind} / API {context.Runtime.ApiVersion}");

        foreach (ModCapability capability in Enum.GetValues<ModCapability>())
        {
            bool available = context.Features.IsAvailable(capability);
            string state = available ? "available" : "unavailable";
            context.Logger.Info($"Capability {capability}: {state}. {context.Features.GetUnavailableReason(capability)}");
        }
    }

    public void OnGameReady()
    {
        // Intentionally not invoked until a reliable game-ready signal is verified.
    }

    public void OnUnload()
    {
        // Unload is not supported by this first adapter.
    }
}

internal sealed class ModContext : IModContext
{
    public ModContext(ModIdentity mod, IModLogger logger, IRuntimeInfo runtime, IGameInfo game, IFeatureAvailability features)
    {
        Mod = mod;
        Logger = logger;
        Runtime = runtime;
        Game = game;
        Features = features;
    }

    public ModIdentity Mod { get; }
    public IModLogger Logger { get; }
    public IRuntimeInfo Runtime { get; }
    public IGameInfo Game { get; }
    public IFeatureAvailability Features { get; }
}

internal sealed class BepInExLogger : IModLogger
{
    private readonly BepInEx.Logging.ManualLogSource _log;

    public BepInExLogger(BepInEx.Logging.ManualLogSource log) => _log = log;

    public void Info(string message) => _log.LogInfo("[SRML Mobile API] " + message);
    public void Warning(string message) => _log.LogWarning("[SRML Mobile API] " + message);
    public void Error(string message, Exception? exception = null) =>
        _log.LogError("[SRML Mobile API] " + message + (exception is null ? string.Empty : Environment.NewLine + exception));
}

internal sealed record RuntimeInfo(string ApiVersion, string LoaderVersion, string RuntimeKind) : IRuntimeInfo;
internal sealed record GameInfo(string PackageName, string GameVersion, string UnityVersion, string Architecture) : IGameInfo;

internal sealed class NoGameplayFeatures : IFeatureAvailability
{
    public bool IsAvailable(ModCapability capability) => false;

    public string? GetUnavailableReason(ModCapability capability) =>
        "Not implemented yet. This capability stays disabled until its IL2CPP implementation is verified on-device.";
}
