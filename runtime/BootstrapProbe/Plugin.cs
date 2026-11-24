using System;
using System.IO;
using System.Runtime.InteropServices;
using BepInEx;
using BepInEx.Unity.IL2CPP;

namespace SRMLMobile.BootstrapProbe;

[BepInPlugin("com.srmlmobile.bootstrapprobe", "SRML Mobile Bootstrap Probe", "0.2.0")]
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
        ProbeGameFilesDirectory();
        Log.LogInfo("This probe does not modify game objects, saves, or gameplay.");
        Log.LogInfo("================================================");
    }

    private void ProbeGameFilesDirectory()
    {
        const string relative = "SRMLMobile/Mods";
        string[] candidates =
        {
            Path.Combine("/storage/emulated/0/Android/data/com.playdigious.slimerancher/files", relative),
            Path.Combine("/sdcard/Android/data/com.playdigious.slimerancher/files", relative)
        };

        foreach (string directory in candidates)
        {
            try
            {
                bool existed = Directory.Exists(directory);
                Log.LogInfo($"[SRMLMOBILE_STORAGE_PROBE] Candidate: {directory}");
                Log.LogInfo($"[SRMLMOBILE_STORAGE_PROBE] Directory existed before probe: {existed}");
                Directory.CreateDirectory(directory);

                string marker = Path.Combine(directory, "fusioncore-write-test.txt");
                File.WriteAllText(marker,
                    "SRML Mobile storage probe succeeded." + Environment.NewLine +
                    "This file was created by BootstrapProbe 0.2.0 inside the game process." + Environment.NewLine);

                bool markerExists = File.Exists(marker);
                Log.LogInfo($"[SRMLMOBILE_STORAGE_PROBE] WRITE_OK={markerExists}");
                Log.LogInfo($"[SRMLMOBILE_STORAGE_PROBE] Marker: {marker}");
                return;
            }
            catch (Exception ex)
            {
                Log.LogWarning($"[SRMLMOBILE_STORAGE_PROBE] Candidate failed: {directory}");
                Log.LogWarning($"[SRMLMOBILE_STORAGE_PROBE] {ex.GetType().FullName}: {ex.Message}");
            }
        }

        Log.LogError("[SRMLMOBILE_STORAGE_PROBE] No candidate path could be written.");
    }
}
