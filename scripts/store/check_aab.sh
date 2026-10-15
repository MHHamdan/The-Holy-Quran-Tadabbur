#!/usr/bin/env bash
# Check the merged manifest of a release App Bundle with bundletool:
#   - versionCode / versionName are the ones CI stamped (Play rejects reuse)
#   - no SCHEDULE_EXACT_ALARM (the daily reminder is inexact)
#   - Auto Backup rules are wired (WebView storage stays on the device)
#   - the release build never allows cleartext traffic
#
#   AAB          path to the .aab (default: the Gradle release output)
#   EXPECT_CODE  expected versionCode (optional)
#   EXPECT_NAME  expected versionName (optional)
#   BUNDLETOOL_JAR  existing bundletool jar (downloaded and checksum-verified otherwise)
set -euo pipefail

AAB="${AAB:-android/app/build/outputs/bundle/release/app-release.aab}"
BT_VERSION="1.18.3"
BT_SHA256="a099cfa1543f55593bc2ed16a70a7c67fe54b1747bb7301f37fdfd6d91028e29"

test -f "$AAB" || { echo "::error::bundle not found: $AAB"; exit 1; }

jar="${BUNDLETOOL_JAR:-}"
if [ -z "$jar" ]; then
  jar="${RUNNER_TEMP:-/tmp}/bundletool-$BT_VERSION.jar"
  if [ ! -f "$jar" ]; then
    curl -fsSL -o "$jar" "https://github.com/google/bundletool/releases/download/$BT_VERSION/bundletool-all-$BT_VERSION.jar"
  fi
  echo "$BT_SHA256  $jar" | sha256sum -c - >/dev/null || { echo "::error::bundletool checksum mismatch"; exit 1; }
fi

bt() { java -jar "$jar" "$@"; }
manifest="$(bt dump manifest --bundle "$AAB")"
code="$(bt dump manifest --bundle "$AAB" --xpath /manifest/@android:versionCode)"
name="$(bt dump manifest --bundle "$AAB" --xpath /manifest/@android:versionName)"
echo "versionCode=$code versionName=$name"

fail=0
err() { echo "::error::$*"; fail=1; }

if [ -n "${EXPECT_CODE:-}" ] && [ "$code" != "$EXPECT_CODE" ]; then
  err "versionCode is $code, expected $EXPECT_CODE"
fi
if [ -n "${EXPECT_NAME:-}" ] && [ "$name" != "$EXPECT_NAME" ]; then
  err "versionName is $name, expected $EXPECT_NAME"
fi
if grep -q 'SCHEDULE_EXACT_ALARM' <<<"$manifest"; then
  err "the bundle declares SCHEDULE_EXACT_ALARM (the reminder must stay inexact)"
fi
if ! grep -q 'android:dataExtractionRules=' <<<"$manifest"; then
  err "android:dataExtractionRules is missing (WebView storage would be backed up)"
fi
if ! grep -q 'android:fullBackupContent=' <<<"$manifest"; then
  err "android:fullBackupContent is missing (WebView storage would be backed up on Android 11-)"
fi
if grep -q 'android:usesCleartextTraffic="true"' <<<"$manifest"; then
  err "the release manifest allows cleartext traffic"
fi

echo "Permissions:"
grep -oE 'android:name="android\.permission\.[A-Z_]+"' <<<"$manifest" | sort -u || true
exit "$fail"
