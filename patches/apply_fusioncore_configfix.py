from pathlib import Path

# Patch target is pinned to FusionCore commit bf4c69d9d4724e4eff058664a5be0a1d9cfd4e61.

runtime = Path("fusionApp/src/main/java/dev/allofus/fusioncore/hooks/GameRuntime.java")
source = runtime.read_text(encoding="utf-8")

anchor = """        private ActivityResult start(Class<?> targetType, Context who, IBinder contextThread,
                                     IBinder token, Object target, Intent intent, int requestCode,
                                     Bundle options, UserHandle user) {
            try {
"""
replacement = """        /**
         * The game's launcher wrapper may create a fresh Intent and drop all extras.
         * Preserve only FusionCore's own config when that wrapper launches another
         * Activity inside the game package.
         */
        private Intent carryFusionConfigFromCaller(Object caller, Intent intent) {
            if (!(caller instanceof Activity) || intent == null || intent.getComponent() == null) {
                return intent;
            }
            if (!gameContext.getPackageName().equals(intent.getComponent().getPackageName())) {
                return intent;
            }

            Intent callerIntent = ((Activity) caller).getIntent();
            if (callerIntent == null) return intent;

            try {
                callerIntent.setExtrasClassLoader(GameRuntime.class.getClassLoader());
                if (!callerIntent.hasExtra(InstrumentationHooks.EXTRA_FUSION_CONFIG)) {
                    return intent;
                }

                android.os.Parcelable config = callerIntent.getParcelableExtra(
                        InstrumentationHooks.EXTRA_FUSION_CONFIG);
                if (config == null) return intent;

                Intent forwarded = new Intent(intent);
                forwarded.putExtra(InstrumentationHooks.EXTRA_FUSION_CONFIG, config);
                Log.i("GameRuntime", "Forwarded FusionCore config from "
                        + caller.getClass().getName() + " to "
                        + intent.getComponent().getClassName());
                return forwarded;
            } catch (RuntimeException error) {
                Log.e("GameRuntime", "Could not forward FusionCore config", error);
                return intent;
            }
        }

        private ActivityResult start(Class<?> targetType, Context who, IBinder contextThread,
                                     IBinder token, Object target, Intent intent, int requestCode,
                                     Bundle options, UserHandle user) {
            intent = carryFusionConfigFromCaller(target, intent);
            try {
"""
if source.count(anchor) != 1:
    raise SystemExit(f"Expected exactly one Instrumentation.start anchor, found {source.count(anchor)}")
runtime.write_text(source.replace(anchor, replacement), encoding="utf-8")

settings = Path("settings.gradle.kts")
settings_text = settings.read_text(encoding="utf-8")
foojay_block = """plugins {
    id("org.gradle.toolchains.foojay-resolver-convention") version "1.0.0"
}

"""
if settings_text.count(foojay_block) != 1:
    raise SystemExit("Expected exactly one optional Foojay resolver plugin block")
settings.write_text(settings_text.replace(foojay_block, ""), encoding="utf-8")

gradle = Path("fusionApp/build.gradle.kts")
build = gradle.read_text(encoding="utf-8")

# Keep the upstream app on API 36 in this reproducible build environment.
# AndroidX Core 1.19.0 requires API 37, which is not yet available from sdkmanager here.
# 1.17.0 is the preceding stable Core line and supports API 36.
for old, new in [
    ('androidx.core:core:1.19.0', 'androidx.core:core:1.17.0'),
    ('androidx.core:core-ktx:1.19.0', 'androidx.core:core-ktx:1.17.0'),
]:
    if build.count(old) != 1:
        raise SystemExit(f"Expected exactly one {old} dependency")
    build = build.replace(old, new)

sdk_anchor = "    compileSdk = 37\n"
if build.count(sdk_anchor) != 1:
    raise SystemExit(f"Expected exactly one compileSdk 37 setting, found {build.count(sdk_anchor)}")
build = build.replace(sdk_anchor, "    compileSdk = 36\n")

anchor = """    buildTypes {
        release {
"""
replacement = """    buildTypes {
        // Keep the patched test build side-by-side with the official FusionCore APK.
        debug {
            applicationIdSuffix = ".configfix"
            versionNameSuffix = "-configfix"
        }
        release {
"""
if build.count(anchor) != 1:
    raise SystemExit(f"Expected exactly one buildTypes anchor, found {build.count(anchor)}")
gradle.write_text(build.replace(anchor, replacement), encoding="utf-8")

print("Applied FusionCore config forwarding patch.")
