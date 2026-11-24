using System;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using BepInEx.Logging;

namespace SRMLMobile.RuntimeAdapter;

internal static class InteropRuntimeInventory
{
    public static void Run(ManualLogSource log)
    {
        log.LogInfo("[INTEROP_INVENTORY] ===== BEGIN READ-ONLY RUNTIME INVENTORY 0.1.2 =====");
        log.LogInfo("[INTEROP_INVENTORY] Process architecture: " + RuntimeInformation.ProcessArchitecture);
        log.LogInfo("[INTEROP_INVENTORY] Framework: " + RuntimeInformation.FrameworkDescription);
        log.LogInfo("[INTEROP_INVENTORY] Runtime: " + Environment.Version);

        Assembly[] assemblies = AppDomain.CurrentDomain.GetAssemblies();
        foreach (Assembly assembly in assemblies
                     .Where(IsRelevantAssembly)
                     .OrderBy(a => a.GetName().Name, StringComparer.Ordinal))
        {
            ReportAssembly(log, assembly);
            ReportRelevantTypes(log, assembly);
        }

        bool hasDisarm = assemblies.Any(a =>
            (a.GetName().Name ?? string.Empty).Contains("Disarm", StringComparison.OrdinalIgnoreCase));
        bool hasIced = assemblies.Any(a =>
            (a.GetName().Name ?? string.Empty).Contains("Iced", StringComparison.OrdinalIgnoreCase));

        log.LogInfo("[INTEROP_INVENTORY] Disarm-like assembly loaded: " + hasDisarm);
        log.LogInfo("[INTEROP_INVENTORY] Iced-like assembly loaded: " + hasIced);
        log.LogInfo("[INTEROP_INVENTORY] NOTE: assembly presence alone does not prove which decoder a specific hook uses.");
        log.LogInfo("[INTEROP_INVENTORY] NOTE: this probe does not invoke Xref scanning, decode native memory, resolve pointers, or install hooks.");
        log.LogInfo("[INTEROP_INVENTORY] ===== END READ-ONLY RUNTIME INVENTORY 0.1.2 =====");
    }

    private static bool IsRelevantAssembly(Assembly assembly)
    {
        string name = assembly.GetName().Name ?? string.Empty;
        return name.Contains("Il2CppInterop", StringComparison.OrdinalIgnoreCase)
            || name.Contains("Disarm", StringComparison.OrdinalIgnoreCase)
            || name.Contains("Iced", StringComparison.OrdinalIgnoreCase)
            || name.Contains("BepInEx", StringComparison.OrdinalIgnoreCase);
    }

    private static void ReportAssembly(ManualLogSource log, Assembly assembly)
    {
        AssemblyName name = assembly.GetName();
        string location = SafeLocation(assembly);
        log.LogInfo("[INTEROP_INVENTORY] ASSEMBLY: " + name.FullName);
        log.LogInfo("[INTEROP_INVENTORY] LOCATION: " + location);

        try
        {
            string[] references = assembly.GetReferencedAssemblies()
                .Select(reference => reference.FullName ?? reference.Name ?? "?")
                .OrderBy(value => value, StringComparer.Ordinal)
                .ToArray();
            log.LogInfo("[INTEROP_INVENTORY] REFERENCES: " + string.Join(" | ", references));
        }
        catch (Exception exception)
        {
            log.LogWarning("[INTEROP_INVENTORY] REFERENCES_FAILED: " + exception.GetType().Name + ": " + exception.Message);
        }

        if (string.IsNullOrEmpty(location) || !File.Exists(location))
            return;

        try
        {
            using FileStream stream = File.OpenRead(location);
            using SHA256 sha = SHA256.Create();
            string hash = Convert.ToHexString(sha.ComputeHash(stream));
            log.LogInfo("[INTEROP_INVENTORY] SHA256: " + hash);
        }
        catch (Exception exception)
        {
            log.LogWarning("[INTEROP_INVENTORY] HASH_FAILED: " + exception.GetType().Name + ": " + exception.Message);
        }
    }

    private static void ReportRelevantTypes(ManualLogSource log, Assembly assembly)
    {
        Type[] types;
        try
        {
            types = assembly.GetTypes();
        }
        catch (ReflectionTypeLoadException exception)
        {
            types = exception.Types.Where(type => type is not null).Cast<Type>().ToArray();
            log.LogWarning("[INTEROP_INVENTORY] PARTIAL_TYPE_ENUMERATION: " +
                assembly.GetName().Name + " (" + exception.LoaderExceptions.Length + " loader errors)");
        }
        catch (Exception exception)
        {
            log.LogWarning("[INTEROP_INVENTORY] TYPE_ENUMERATION_FAILED: " +
                assembly.GetName().Name + ": " + exception.GetType().Name + ": " + exception.Message);
            return;
        }

        foreach (Type type in types
                     .Where(IsRelevantType)
                     .OrderBy(type => type.FullName, StringComparer.Ordinal))
        {
            log.LogInfo("[INTEROP_INVENTORY] TYPE: " + type.FullName);
            try
            {
                foreach (MethodInfo method in type.GetMethods(
                             BindingFlags.Public | BindingFlags.NonPublic |
                             BindingFlags.Static | BindingFlags.Instance |
                             BindingFlags.DeclaredOnly))
                {
                    string parameters = string.Join(", ",
                        method.GetParameters().Select(parameter =>
                            parameter.ParameterType.FullName ?? parameter.ParameterType.Name));
                    log.LogInfo("[INTEROP_INVENTORY] METHOD: " + method.Name +
                        "(" + parameters + ") -> " +
                        (method.ReturnType.FullName ?? method.ReturnType.Name));
                }
            }
            catch (Exception exception)
            {
                log.LogWarning("[INTEROP_INVENTORY] METHOD_ENUMERATION_FAILED: " +
                    type.FullName + ": " + exception.GetType().Name + ": " + exception.Message);
            }
        }
    }

    private static bool IsRelevantType(Type type)
    {
        string name = type.FullName ?? type.Name;
        return name.Contains("XrefScanner", StringComparison.OrdinalIgnoreCase)
            || name.Contains("GenericMethod", StringComparison.OrdinalIgnoreCase)
            || name.Contains("GetFieldDefaultValue", StringComparison.OrdinalIgnoreCase)
            || name.Contains("Arm64", StringComparison.OrdinalIgnoreCase)
            || name.Contains("Disarm", StringComparison.OrdinalIgnoreCase)
            || name.Contains("Decoder", StringComparison.OrdinalIgnoreCase);
    }

    private static string SafeLocation(Assembly assembly)
    {
        try { return assembly.Location; }
        catch (Exception exception) { return "<unavailable: " + exception.GetType().Name + ">"; }
    }
}
