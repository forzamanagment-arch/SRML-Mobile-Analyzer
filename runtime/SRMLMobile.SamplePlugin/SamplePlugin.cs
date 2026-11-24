using SRMLMobile.API;

namespace SRMLMobile.SamplePlugin;

/// <summary>
/// A separate add-on assembly used to verify the Runtime Adapter's external
/// plugin discovery and invocation path. It deliberately does not access Unity
/// or game internals.
/// </summary>
public sealed class SamplePlugin : ISrmlMobilePlugin
{
    public void OnLoad(IModContext context)
    {
        context.Logger.Info("================================================");
        context.Logger.Info("[SAMPLE_ADDON_LOADED] External sample add-on entry point invoked.");
        context.Logger.Info($"Mod: {context.Mod.Id}");
        context.Logger.Info($"Game: {context.Game.PackageName} {context.Game.GameVersion}");
        context.Logger.Info($"Runtime API: {context.Runtime.ApiVersion}");
        context.Logger.Info("This message originates from a separate DLL implementing ISrmlMobilePlugin.");
        context.Logger.Info("No game objects, saves, or gameplay were modified.");
        context.Logger.Info("================================================");
    }

    public void OnGameReady()
    {
        // Reserved until the Runtime Adapter exposes a verified game-ready event.
    }

    public void OnUnload()
    {
        // Live unloading is not supported in the first adapter.
    }
}
