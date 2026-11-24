using System;
using System.Runtime.InteropServices;
using BepInEx.Logging;
using Il2CppInterop.Runtime.Runtime;
using Il2CppInterop.Runtime.Startup;

namespace SRMLMobile.RuntimeAdapter;

internal static class InteropStartupProbe
{
    public static IntPtr ObjectGetVirtualMethodExport { get; private set; }
    public static void Run(ManualLogSource log)
    {
        log.LogInfo("[INTEROP_STARTUP_PROBE] ===== BEGIN SAFE STARTUP PROBE 0.1.3 =====");
        try
        {
            Version unityVersion = Il2CppInteropRuntime.Instance.UnityVersion;
            log.LogInfo("[INTEROP_STARTUP_PROBE] Il2CppInterop UnityVersion: " + unityVersion);
            log.LogInfo("[INTEROP_STARTUP_PROBE] Unity major >= 6000: " + (unityVersion.Major >= 6000));
            log.LogInfo("[INTEROP_STARTUP_PROBE] HasShimForGetMethod: " + UnityVersionHandler.HasShimForGetMethod);
            log.LogInfo("[INTEROP_STARTUP_PROBE] HasGetMethodFromReflection: " + UnityVersionHandler.HasGetMethodFromReflection);
            log.LogInfo("[INTEROP_STARTUP_PROBE] IsMetadataV29OrHigher: " + UnityVersionHandler.IsMetadataV29OrHigher);
            log.LogInfo("[INTEROP_STARTUP_PROBE] Selected GenericMethod hook: " +
                (unityVersion.Major >= 6000
                    ? "GenericMethod_GetMethod_Unity6_Hook"
                    : "GenericMethod_GetMethod_Hook"));

            ProbeExports(log);
        }
        catch (Exception exception)
        {
            log.LogError("[INTEROP_STARTUP_PROBE] Probe failed: " + exception);
        }
        log.LogInfo("[INTEROP_STARTUP_PROBE] NOTE: export resolution only; no Xref scan, native memory read, pointer traversal, or hook installation performed.");
        log.LogInfo("[INTEROP_STARTUP_PROBE] ===== END SAFE STARTUP PROBE 0.1.3 =====");
    }

    private static void ProbeExports(ManualLogSource log)
    {
        IntPtr handle = IntPtr.Zero;
        try
        {
            if (!NativeLibrary.TryLoad("libil2cpp.so", typeof(InteropStartupProbe).Assembly, null, out handle))
            {
                log.LogWarning("[INTEROP_STARTUP_PROBE] Could not load libil2cpp.so for export inspection.");
                return;
            }

            foreach (string name in new[]
                     {
                         "il2cpp_object_get_virtual_method",
                         "il2cpp_array_new_specific",
                         "il2cpp_class_get_methods",
                         "il2cpp_class_get_method_from_name"
                     })
            {
                bool found = NativeLibrary.TryGetExport(handle, name, out IntPtr address);
                if (name == "il2cpp_object_get_virtual_method" && found)
                    ObjectGetVirtualMethodExport = address;
                log.LogInfo("[INTEROP_STARTUP_PROBE] EXPORT " + name + ": " +
                    (found ? "FOUND at 0x" + address.ToInt64().ToString("X") : "MISSING"));
            }
        }
        catch (Exception exception)
        {
            log.LogWarning("[INTEROP_STARTUP_PROBE] Export inspection failed: " +
                exception.GetType().Name + ": " + exception.Message);
        }
        finally
        {
            if (handle != IntPtr.Zero)
                NativeLibrary.Free(handle);
        }
    }
}
