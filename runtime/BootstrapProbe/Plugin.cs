using System;
using System.Runtime.InteropServices;
using BepInEx;
using BepInEx.Unity.IL2CPP;

namespace SRMLMobile.BootstrapProbe;

[BepInPlugin("com.srmlmobile.bootstrapprobe", "SRML Mobile Bootstrap Probe", "0.1.0")]
public sealed class BootstrapProbePlugin : BasePlugin
{
    public override void Load()
    {
        Log.LogInfo("================================================");
        Log.LogInfo("[SRMLMOBILE_BOOTSTRAP_PROBE] Load() reached");
        Log.LogInfo("SRML Mobile test plugin was loaded inside the game process.");
        Log.LogInfo($"Process architecture: {RuntimeInformation.ProcessArchitecture}");
        Log.LogInfo($"Runtime version: {Environment.Version}");
        Log.LogInfo($"Operating system: {Environment.OSVersion}");
        Log.LogInfo("This probe does not modify game objects, saves, or gameplay.");
        Log.LogInfo("================================================");
    }
}
