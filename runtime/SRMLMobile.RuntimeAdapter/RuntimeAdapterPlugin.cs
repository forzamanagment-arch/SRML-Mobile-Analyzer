using System;
using System.IO;
using System.Linq;
using System.Reflection;
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

        var context = new ModContext(
            new ModIdentity(
                "srmlmobile.runtime.external-test",
                "SRML Mobile External Add-on Test",
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

        RunBuiltInContractProbe(context);
        LoadExternalSampleAddOn(context);
        ProbeUnityInteropSurface();

        Log.LogInfo("[SRMLMOBILE_RUNTIME_ADAPTER] Adapter initialization finished");
        Log.LogInfo("Game-facing capabilities remain disabled in this build.");
        Log.LogInfo("================================================");
    }


    private void ProbeUnityInteropSurface()
    {
        try
        {
            string? bepinexDirectory = Directory.GetParent(Paths.PluginPath)?.FullName;
            string interopDirectory = Path.Combine(bepinexDirectory ?? string.Empty, "interop");

            Log.LogInfo("[LOGOSWAP_PROBE] BepInEx interop directory: " + interopDirectory);
            if (!Directory.Exists(interopDirectory))
            {
                Log.LogWarning("[LOGOSWAP_PROBE] Interop directory does not exist yet.");
                return;
            }

            string[] unityAssemblies = Directory.GetFiles(interopDirectory, "UnityEngine*.dll");
            Log.LogInfo("[LOGOSWAP_PROBE] UnityEngine interop DLL count: " + unityAssemblies.Length);
            foreach (string file in unityAssemblies.OrderBy(Path.GetFileName))
                Log.LogInfo("[LOGOSWAP_PROBE] Assembly file: " + Path.GetFileName(file));

            string[] loadCandidates =
            {
                "UnityEngine.CoreModule.dll",
                "UnityEngine.UIModule.dll",
                "UnityEngine.UI.dll",
                "UnityEngine.ImageConversionModule.dll"
            };

            foreach (string candidate in loadCandidates)
            {
                string path = Path.Combine(interopDirectory, candidate);
                if (!File.Exists(path))
                    continue;

                try
                {
                    Assembly.LoadFrom(path);
                    Log.LogInfo("[LOGOSWAP_PROBE] Loaded interop assembly: " + candidate);
                }
                catch (Exception exception)
                {
                    Log.LogWarning("[LOGOSWAP_PROBE] Could not load " + candidate + ": " + exception.GetType().Name + ": " + exception.Message);
                }
            }

            string[] targetTypes =
            {
                "UnityEngine.GameObject",
                "UnityEngine.Texture2D",
                "UnityEngine.Rect",
                "UnityEngine.Vector2",
                "UnityEngine.Sprite",
                "UnityEngine.ImageConversion",
                "UnityEngine.UI.Image"
            };

            Assembly[] loadedAssemblies = AppDomain.CurrentDomain.GetAssemblies();
            foreach (string typeName in targetTypes)
            {
                Type? type = loadedAssemblies
                    .Select(assembly => assembly.GetType(typeName, throwOnError: false))
                    .FirstOrDefault(found => found is not null);

                Log.LogInfo(type is null
                    ? "[LOGOSWAP_PROBE] TYPE_MISSING: " + typeName
                    : "[LOGOSWAP_PROBE] TYPE_FOUND: " + typeName + " in " + type.Assembly.GetName().Name);

                if (type is null)
                    continue;

                if (typeName == "UnityEngine.UI.Image")
                {
                    foreach (MethodInfo method in type.GetMethods(BindingFlags.Public | BindingFlags.Instance)
                                 .Where(method => method.Name is "get_sprite" or "set_sprite"))
                        Log.LogInfo("[LOGOSWAP_PROBE] Image API: " + method);
                }
                else if (typeName == "UnityEngine.GameObject")
                {
                    foreach (MethodInfo method in type.GetMethods(BindingFlags.Public | BindingFlags.Static)
                                 .Where(method => method.Name == "Find"))
                        Log.LogInfo("[LOGOSWAP_PROBE] GameObject API: " + method);
                }
                else if (typeName == "UnityEngine.Sprite")
                {
                    foreach (MethodInfo method in type.GetMethods(BindingFlags.Public | BindingFlags.Static)
                                 .Where(method => method.Name == "Create"))
                        Log.LogInfo("[LOGOSWAP_PROBE] Sprite API: " + method);
                }
                else if (typeName == "UnityEngine.ImageConversion")
                {
                    foreach (MethodInfo method in type.GetMethods(BindingFlags.Public | BindingFlags.Static)
                                 .Where(method => method.Name == "LoadImage"))
                        Log.LogInfo("[LOGOSWAP_PROBE] ImageConversion API: " + method);
                }
            }
        }
        catch (Exception exception)
        {
            Log.LogError("[LOGOSWAP_PROBE] Interop inspection failed: " + exception);
        }
    }

    private void RunBuiltInContractProbe(IModContext context)
    {
        try
        {
            ISrmlMobilePlugin probe = new RuntimeApiSmokeTest();
            probe.OnLoad(context);
            Log.LogInfo("[SRMLMOBILE_RUNTIME_ADAPTER] Built-in API contract probe succeeded");
        }
        catch (Exception exception)
        {
            Log.LogError("[SRMLMOBILE_RUNTIME_ADAPTER] Built-in API contract probe failed: " + exception);
        }
    }

    private void LoadExternalSampleAddOn(IModContext context)
    {
        string modsDirectory = Path.Combine(Paths.PluginPath, "SRMLMobile", "Mods");
        string assemblyPath = Path.Combine(modsDirectory, "SRMLMobile.SamplePlugin.dll");

        try
        {
            if (!File.Exists(assemblyPath))
            {
                Log.LogWarning("[SRMLMOBILE_RUNTIME_ADAPTER] External sample add-on not found: " + assemblyPath);
                return;
            }

            Assembly assembly = Assembly.LoadFrom(assemblyPath);
            Type[] pluginTypes = assembly.GetTypes()
                .Where(type =>
                    !type.IsAbstract &&
                    !type.IsInterface &&
                    typeof(ISrmlMobilePlugin).IsAssignableFrom(type) &&
                    type.GetConstructor(Type.EmptyTypes) is not null)
                .ToArray();

            if (pluginTypes.Length == 0)
            {
                Log.LogWarning("[SRMLMOBILE_RUNTIME_ADAPTER] No public parameterless ISrmlMobilePlugin entry point found.");
                return;
            }

            foreach (Type pluginType in pluginTypes)
            {
                try
                {
                    if (Activator.CreateInstance(pluginType) is not ISrmlMobilePlugin plugin)
                        continue;

                    Log.LogInfo("[SRMLMOBILE_RUNTIME_ADAPTER] Invoking external add-on: " + pluginType.FullName);
                    plugin.OnLoad(context);
                    Log.LogInfo("[SRMLMOBILE_RUNTIME_ADAPTER] External add-on OnLoad completed: " + pluginType.FullName);
                }
                catch (Exception exception)
                {
                    Log.LogError("[SRMLMOBILE_RUNTIME_ADAPTER] External add-on entry point failed: " + pluginType.FullName + Environment.NewLine + exception);
                }
            }
        }
        catch (Exception exception)
        {
            Log.LogError("[SRMLMOBILE_RUNTIME_ADAPTER] External sample add-on load failed: " + exception);
        }
    }
}

internal sealed class RuntimeApiSmokeTest : ISrmlMobilePlugin
{
    public void OnLoad(IModContext context)
    {
        context.Logger.Info("Built-in ISrmlMobilePlugin.OnLoad invoked.");
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

    public void OnGameReady() { }
    public void OnUnload() { }
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
