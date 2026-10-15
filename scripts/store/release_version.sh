#!/usr/bin/env bash
# Derive the store version numbers for a mobile build.
#
#   code       GITHUB_RUN_NUMBER (+ VERSION_CODE_OFFSET), so every CI build of
#              the Mobile release workflow gets a strictly larger Android
#              versionCode and iOS CURRENT_PROJECT_VERSION than the last one.
#   name       vMAJOR.MINOR.PATCH[-pre] tag without the "v" (Android
#              versionName); branch builds use APP_VERSION_DEFAULT.
#   marketing  MAJOR.MINOR.PATCH only (iOS MARKETING_VERSION must be
#              period-separated integers, so "-rc1" is dropped).
#
# Prints key=value lines; in GitHub Actions they are also appended to
# $GITHUB_OUTPUT. A v* tag that is not semver fails.
set -euo pipefail

DEFAULT="${APP_VERSION_DEFAULT:-1.0.0}"
OFFSET="${VERSION_CODE_OFFSET:-0}"
RUN="${GITHUB_RUN_NUMBER:-1}"
REF="${GITHUB_REF:-}"
REF_NAME="${GITHUB_REF_NAME:-}"

case "$RUN$OFFSET" in
  *[!0-9]*) echo "::error::GITHUB_RUN_NUMBER and VERSION_CODE_OFFSET must be integers" >&2; exit 1 ;;
esac
code=$((RUN + OFFSET))
# Play's ceiling for versionCode.
if [ "$code" -gt 2100000000 ]; then
  echo "::error::version code $code exceeds Play's limit" >&2; exit 1
fi

if [[ "$REF" == refs/tags/v* ]]; then
  if ! [[ "$REF_NAME" =~ ^v([0-9]+)\.([0-9]+)\.([0-9]+)(-[0-9A-Za-z.]+)?$ ]]; then
    echo "::error::release tag '$REF_NAME' is not vMAJOR.MINOR.PATCH[-prerelease]" >&2; exit 1
  fi
  name="${REF_NAME#v}"
  marketing="${BASH_REMATCH[1]}.${BASH_REMATCH[2]}.${BASH_REMATCH[3]}"
else
  name="$DEFAULT"
  marketing="${DEFAULT%%-*}"
fi

{
  echo "code=$code"
  echo "name=$name"
  echo "marketing=$marketing"
} | tee -a "${GITHUB_OUTPUT:-/dev/null}"
