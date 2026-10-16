#!/usr/bin/env bash
# Release guard for store builds (v* tags): the apps must be compiled against
# the real HTTPS API, and the privacy policy must name a contact point (Play's
# User Data policy and App Store review both expect one).
#
#   API_URL   the PRODUCTION_API_URL repository variable
#   PRIVACY   the PRIVACY_CONTACT repository variable (an e-mail address)
set -euo pipefail

fail=0
if [ -z "${API_URL:-}" ]; then
  echo "::error::Set the PRODUCTION_API_URL repository variable before tagging a release."
  fail=1
elif [[ "$API_URL" != https://* ]]; then
  echo "::error::PRODUCTION_API_URL must be an https:// origin (got '$API_URL')."
  fail=1
fi

if [ -z "${PRIVACY:-}" ]; then
  echo "::error::Set the PRIVACY_CONTACT repository variable (privacy contact e-mail shown on /privacy) before tagging a release."
  fail=1
elif ! [[ "$PRIVACY" =~ ^[^@[:space:]]+@[^@[:space:]]+\.[^@[:space:]]+$ ]]; then
  echo "::error::PRIVACY_CONTACT must be an e-mail address (got '$PRIVACY')."
  fail=1
fi

# Store metadata must not ship placeholders (e.g. fastlane privacy_url.txt).
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
if grep -rq 'REPLACE_WITH' "$ROOT/fastlane/metadata" 2>/dev/null; then
  echo "::error::fastlane/metadata still holds REPLACE_WITH placeholders ($(grep -rl 'REPLACE_WITH' "$ROOT/fastlane/metadata" | sed "s#$ROOT/##" | tr '\n' ' ')): set the public web host before tagging a release."
  fail=1
fi

exit "$fail"
