from pathlib import Path

# Add opt-in diagnostics to the pinned FusionCore 0.045 source.
# Native messages remain in Android Logcat and are additionally appended to
# /storage/emulated/0/FusionCore/<game-package>/fusioncore-native.log.

def replace_once(path: str, old: str, new: str) -> None:
    file = Path(path)
    source = file.read_text(encoding="utf-8")
    count = source.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one patch anchor, found {count}")
    file.write_text(source.replace(old, new), encoding="utf-8")


# Configure a per-game external log before the native bootstrap starts.
replace_once(
    "fusionApp/src/main/jni/fusion/src/fusion.cpp",
    """    fs::path gamePath = fs::path(config.bepInExDirectory).parent_path();

    fs::path libUnity;
""",
    """    fs::path gamePath = fs::path(config.bepInExDirectory).parent_path();
    fs::path nativeLogPath = gamePath / "fusioncore-native.log";
    setenv("FUSIONCORE_NATIVE_LOG", nativeLogPath.c_str(), 1);
    log_format(LogLevel::INFO, TAG, "Native diagnostic log: {}", nativeLogPath.string());

    fs::path libUnity;
"""
)

# Record the most important native initialization boundaries.
replace_once(
    "fusionApp/src/main/jni/fusion/src/fusion.cpp",
    """        fs::path libIl2Cpp = gameLibsPath / "libil2cpp.so";
        allocate_setup_injected(libIl2Cpp.c_str(), patchedLibIl2Cpp.c_str(), 1024 * 1024);
""",
    """        fs::path libIl2Cpp = gameLibsPath / "libil2cpp.so";
        log_format(LogLevel::INFO, TAG, "DIAG: preparing injected libil2cpp from {}", libIl2Cpp.string());
        void *injectedHandle = allocate_setup_injected(libIl2Cpp.c_str(), patchedLibIl2Cpp.c_str(), 1024 * 1024);
        log_format(LogLevel::INFO, TAG, "DIAG: injected libil2cpp preparation returned {}", injectedHandle != nullptr);
"""
)

replace_once(
    "fusionApp/src/main/jni/fusion/src/fusion.cpp",
    """    std::string libUnityPath = libUnity.string();
    try_hook_libunity(libUnityPath, (gameLibsPath / "libunity.so").string());

    std::string patchedPath = patchedLibIl2Cpp.string();
""",
    """    std::string libUnityPath = libUnity.string();
    log_format(LogLevel::INFO, TAG, "DIAG: hooking libunity at {}", libUnityPath);
    try_hook_libunity(libUnityPath, (gameLibsPath / "libunity.so").string());
    log_format(LogLevel::INFO, TAG, "DIAG: libunity hook setup returned; active path {}", libUnityPath);

    std::string patchedPath = patchedLibIl2Cpp.string();
"""
)

replace_once(
    "fusionApp/src/main/jni/fusion/src/fusion.cpp",
    """    if (!il2cpp_initialize(il2cpp_path))
    {
""",
    """    log_format(LogLevel::INFO, TAG, "DIAG: calling dlopen/dlsym for libil2cpp at {}", il2cpp_path);
    if (!il2cpp_initialize(il2cpp_path))
    {
"""
)

replace_once(
    "fusionApp/src/main/jni/fusion/src/fusion.cpp",
    """    if(runtime_config.isIl2Cpp2Mono){
""",
    """    log(LogLevel::INFO, TAG, "DIAG: libil2cpp handle initialized");
    if(runtime_config.isIl2Cpp2Mono){
"""
)

replace_once(
    "fusionApp/src/main/jni/fusion/src/fusion.cpp",
    """    log(LogLevel::INFO, TAG, "Installing il2cpp hooks...");
    il2cpp_install_init_hook(il2cpp_init_hook);
    log(LogLevel::INFO, TAG, "il2cpp hooks installed successfully!");
""",
    """    log(LogLevel::INFO, TAG, "Installing il2cpp hooks...");
    log(LogLevel::INFO, TAG, "DIAG: entering il2cpp_install_init_hook");
    il2cpp_install_init_hook(il2cpp_init_hook);
    log(LogLevel::INFO, TAG, "DIAG: returned from il2cpp_install_init_hook");
    log(LogLevel::INFO, TAG, "il2cpp hooks installed successfully!");
"""
)

replace_once(
    "fusionApp/src/main/jni/fusion/src/fusion.cpp",
    """    // call the original il2cpp_init function
    int result = il2cpp_init(domain_name);

    if (runtime_config.initialized)
""",
    """    // call the original il2cpp_init function
    log(LogLevel::INFO, TAG, "DIAG: entering original il2cpp_init");
    int result = il2cpp_init(domain_name);
    log_format(LogLevel::INFO, TAG, "DIAG: original il2cpp_init returned {}", result);

    if (runtime_config.initialized)
"""
)

replace_once(
    "fusionApp/src/main/jni/fusion/src/fusion.cpp",
    """        dotnet_execute_assembly(dotNetConfig, &list);
""",
    """        log(LogLevel::INFO, TAG, "DIAG: entering BepInEx .NET entry point");
        dotnet_execute_assembly(dotNetConfig, &list);
        log(LogLevel::INFO, TAG, "DIAG: BepInEx .NET entry point returned");
"""
)

# Append native messages to the configured file while retaining Android Logcat.
replace_once(
    "fusionApp/src/main/jni/fusion/src/logger.cpp",
    """#include <android/log.h>

void log(LogLevel level, const char *tag, const char *message)
{
    __android_log_write(static_cast<int>(level), tag, message);
}
""",
    """#include <android/log.h>
#include <cstdlib>
#include <fstream>
#include <mutex>

static std::mutex native_log_mutex;

void log(LogLevel level, const char *tag, const char *message)
{
    __android_log_write(static_cast<int>(level), tag, message);

    const char *path = std::getenv("FUSIONCORE_NATIVE_LOG");
    if (path == nullptr || path[0] == '\\0') return;

    std::lock_guard<std::mutex> guard(native_log_mutex);
    std::ofstream output(path, std::ios::out | std::ios::app);
    if (output) {
        output << static_cast<int>(level) << " ["
               << (tag ? tag : "FusionCore") << "] "
               << (message ? message : "") << '\\n';
    }
}
"""
)

print("Applied FusionCore native file logging and IL2CPP phase diagnostics.")
