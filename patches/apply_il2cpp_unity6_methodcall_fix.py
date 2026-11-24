#!/usr/bin/env python3
"""Patch the Unity 6 GenericMethod resolver to prefer ARM64 call targets.

The stock heuristic counts local B instructions as method targets. In the
Slime Rancher Mobile Unity 6000.3.0f1 binary, this selects a basic-block
address instead of the BL target for GenericMethod::GetMethod.
"""
from pathlib import Path
import re

path = Path("Il2CppInterop.Runtime/Injection/Hooks/GenericMethod_GetMethod_Unity6_Hook.cs")
source = path.read_text(encoding="utf-8")

if "XrefScannerLowLevel.MethodCalls" in source:
    raise SystemExit("Unity 6 GenericMethod resolver already uses MethodCalls")

pattern = re.compile(
    r"        public override IntPtr FindTargetMethod\(\)\n"
    r"        \{.*?\n        \}",
    re.S,
)

replacement = """        public override IntPtr FindTargetMethod()
        {
            var getVirtualMethodAPI = InjectorHelpers.GetIl2CppExport(nameof(IL2CPP.il2cpp_object_get_virtual_method));
            if (getVirtualMethodAPI == IntPtr.Zero)
                return IntPtr.Zero;

            // Prefer BL/BLR targets. JumpTargets also returns local B edges,
            // which are basic-block branches rather than method entrypoints.
            var apiCalls = XrefScannerLowLevel.MethodCalls(getVirtualMethodAPI).ToArray();
            if (apiCalls.Length == 0)
                apiCalls = XrefScannerLowLevel.JumpTargets(getVirtualMethodAPI).ToArray();
            if (apiCalls.Length == 0)
                return IntPtr.Zero;

            var getVirtualMethod = apiCalls[0];

            var getVirtualMethodCalls = XrefScannerLowLevel.MethodCalls(getVirtualMethod).ToArray();
            if (getVirtualMethodCalls.Length == 0)
                getVirtualMethodCalls = XrefScannerLowLevel.JumpTargets(getVirtualMethod).ToArray();
            if (getVirtualMethodCalls.Length == 0)
                return IntPtr.Zero;

            // The final call in Object::GetVirtualMethod resolves the generic virtual method.
            var getGenericVirtualMethod = getVirtualMethodCalls.Last();

            var genericMethodCalls = XrefScannerLowLevel.MethodCalls(getGenericVirtualMethod).ToArray();
            if (genericMethodCalls.Length == 0)
                genericMethodCalls = XrefScannerLowLevel.JumpTargets(getGenericVirtualMethod).ToArray();
            if (genericMethodCalls.Length == 0)
                return IntPtr.Zero;

            var target = genericMethodCalls.Last();
            Logger.Instance.LogTrace(
                "Unity 6 GenericMethod::GetMethod resolved: 0x{Address}",
                target.ToInt64().ToString("X"));
            return target;
        }"""

source, count = pattern.subn(replacement, source, count=1)
if count != 1:
    raise SystemExit(f"Expected one FindTargetMethod method, replaced {count}")

path.write_text(source, encoding="utf-8")
print(f"Patched {path}")
