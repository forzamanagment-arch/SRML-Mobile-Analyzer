using System;
using System.Diagnostics;
using System.Linq;
using System.Runtime.InteropServices;
using BepInEx.Logging;
using Il2CppInterop.Common.XrefScans;

namespace SRMLMobile.RuntimeAdapter;

/// <summary>
/// Read-only trace of the exact ARM64 jump-chain used by Il2CppInterop's Unity 6
/// GenericMethod hook. It does not install hooks or write native memory.
/// </summary>
internal static class GenericMethodXrefProbe
{
    public static void Run(ManualLogSource log, IntPtr getVirtualMethodExport)
    {
        log.LogInfo("[GENERICMETHOD_XREF_TRACE] ===== BEGIN READ-ONLY TRACE 0.1.4 =====");
        try
        {
            if (getVirtualMethodExport == IntPtr.Zero)
            {
                log.LogWarning("[GENERICMETHOD_XREF_TRACE] EXPORT_POINTER_MISSING: startup export probe did not provide il2cpp_object_get_virtual_method.");
                return;
            }

            IntPtr moduleBase = FindIl2CppBase();
            log.LogInfo("[GENERICMETHOD_XREF_TRACE] Reusing verified export: " + Format(getVirtualMethodExport, moduleBase));

            IntPtr[] apiTargets = TraceJumpTargets(log, "STEP1 export -> Object::GetVirtualMethod", getVirtualMethodExport, moduleBase);
            if (apiTargets.Length != 1)
            {
                log.LogWarning("[GENERICMETHOD_XREF_TRACE] STOP_STEP1: expected exactly 1 jump target, got " + apiTargets.Length);
                return;
            }

            IntPtr getVirtualMethod = apiTargets[0];
            IntPtr[] getVirtualMethodXrefs = TraceJumpTargets(
                log, "STEP2 Object::GetVirtualMethod -> xrefs", getVirtualMethod, moduleBase);

            if (getVirtualMethodXrefs.Length == 0)
            {
                log.LogWarning("[GENERICMETHOD_XREF_TRACE] STOP_STEP2: no jump/call targets found inside Object::GetVirtualMethod.");
                return;
            }

            IntPtr getGenericVirtualMethod = getVirtualMethodXrefs[^1];
            log.LogInfo("[GENERICMETHOD_XREF_TRACE] Selected last STEP2 target (GetGenericVirtualMethod candidate): " +
                Format(getGenericVirtualMethod, moduleBase));

            IntPtr[] shimTargets = TraceJumpTargets(
                log, "STEP3 GetGenericVirtualMethod -> GetMethod shim", getGenericVirtualMethod, moduleBase);

            if (shimTargets.Length == 0)
            {
                log.LogWarning("[GENERICMETHOD_XREF_TRACE] STOP_STEP3: no tail-jump targets found in selected candidate.");
                return;
            }

            IntPtr selected = shimTargets.Take(2).Last();
            log.LogInfo("[GENERICMETHOD_XREF_TRACE] CURRENT_FORK_SELECTION: " + Format(selected, moduleBase));
            log.LogInfo("[GENERICMETHOD_XREF_TRACE] Candidate address only; no detour was installed.");
        }
        catch (Exception exception)
        {
            log.LogError("[GENERICMETHOD_XREF_TRACE] READ_ONLY_TRACE_EXCEPTION: " + exception);
        }
        finally
        {
            log.LogInfo("[GENERICMETHOD_XREF_TRACE] ===== END READ-ONLY TRACE 0.1.4 =====");
        }
    }

    private static IntPtr[] TraceJumpTargets(ManualLogSource log, string stage, IntPtr start, IntPtr moduleBase)
    {
        IntPtr[] targets = XrefScannerLowLevel.JumpTargets(start).ToArray();
        log.LogInfo("[GENERICMETHOD_XREF_TRACE] " + stage + ": count=" + targets.Length);
        for (int i = 0; i < targets.Length; i++)
            log.LogInfo("[GENERICMETHOD_XREF_TRACE] " + stage + " [" + i + "] = " + Format(targets[i], moduleBase));
        return targets;
    }

    private static IntPtr FindIl2CppBase()
    {
        try
        {
            return Process.GetCurrentProcess().Modules
                .OfType<ProcessModule>()
                .FirstOrDefault(module => string.Equals(module.ModuleName, "libil2cpp.so", StringComparison.OrdinalIgnoreCase))
                ?.BaseAddress ?? IntPtr.Zero;
        }
        catch
        {
            return IntPtr.Zero;
        }
    }

    private static string Format(IntPtr address, IntPtr moduleBase)
    {
        string absolute = "0x" + address.ToInt64().ToString("X");
        if (moduleBase == IntPtr.Zero)
            return absolute;
        long offset = address.ToInt64() - moduleBase.ToInt64();
        return absolute + " (libil2cpp.so+0x" + offset.ToString("X") + ")";
    }
}
