namespace SRMLMobile.API;

/// <summary>
/// Entry point implemented by a managed SRML Mobile plugin.
/// This contract is intentionally small until game-facing APIs are verified
/// against the target IL2CPP build.
/// </summary>
public interface ISrmlMobilePlugin
{
    /// <summary>Called once after the runtime has created the mod context.</summary>
    void OnLoad(IModContext context);

    /// <summary>
    /// Called only after the game-specific adapter reports that its supported
    /// game services are ready. It may never be called if initialization fails.
    /// </summary>
    void OnGameReady();

    /// <summary>
    /// Reserved for a future controlled unload path. Runtime implementations
    /// must document whether and when this callback is actually supported.
    /// </summary>
    void OnUnload();
}

/// <summary>Services provided to a plugin by SRML Mobile Runtime.</summary>
public interface IModContext
{
    ModIdentity Mod { get; }
    IModLogger Logger { get; }
    IRuntimeInfo Runtime { get; }
    IGameInfo Game { get; }
    IFeatureAvailability Features { get; }
}

/// <summary>Immutable identity and version information for the current add-on.</summary>
public sealed record ModIdentity(
    string Id,
    string Name,
    string Version,
    string Author);

/// <summary>Minimal logging surface; implementation routes messages to the runtime log.</summary>
public interface IModLogger
{
    void Info(string message);
    void Warning(string message);
    void Error(string message, Exception? exception = null);
}

/// <summary>Information about the loaded SRML Mobile runtime.</summary>
public interface IRuntimeInfo
{
    string ApiVersion { get; }
    string LoaderVersion { get; }
    string RuntimeKind { get; }
}

/// <summary>Read-only information about the current game process.</summary>
public interface IGameInfo
{
    string PackageName { get; }
    string GameVersion { get; }
    string UnityVersion { get; }
    string Architecture { get; }
}

/// <summary>
/// Reports capabilities actually implemented by the active game adapter.
/// A declared capability is not a promise that every game version supports it.
/// </summary>
public interface IFeatureAvailability
{
    bool IsAvailable(ModCapability capability);
    string? GetUnavailableReason(ModCapability capability);
}

/// <summary>
/// Reserved capability identifiers. Availability is controlled by the runtime;
/// values in this enum do not imply that the feature is already implemented.
/// </summary>
public enum ModCapability
{
    TextureReplacement = 1,
    CustomSlimeDefinition = 2,
    CustomSlimeAppearance = 3,
    CustomSlimeDiet = 4,
    CustomSpawnRules = 5,
    SlimepediaEntries = 6,
    GameplayPatches = 7,
    CustomItems = 8
}
