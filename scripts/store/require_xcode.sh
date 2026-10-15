#!/usr/bin/env bash
# App Store Connect rejects uploads not built with Xcode 26+ / the iOS 26 SDK
# (Apple requirement effective 2026-04-28). Fail early on an older Xcode.
set -euo pipefail

MIN="${XCODE_MAJOR_MIN:-26}"
line="$(xcodebuild -version | head -1)"
echo "$line"
major="$(echo "$line" | sed -nE 's/^Xcode ([0-9]+).*/\1/p')"
if [ -z "$major" ] || [ "$major" -lt "$MIN" ]; then
  echo "::error::App Store uploads need Xcode $MIN or newer (found: $line)."
  exit 1
fi
xcodebuild -showsdks | grep -E 'iphoneos' || true
