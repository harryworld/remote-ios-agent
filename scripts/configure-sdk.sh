#!/usr/bin/env bash
set -euo pipefail
if [[ $# != 2 ]]; then
  echo 'Usage: configure-sdk.sh /authorized/Xcode.xip /new/output-directory' >&2
  exit 2
fi
# User supplies authorized SDK source. No download, redistribution, or license acceptance.
command -v xtool >/dev/null
xtool sdk build "$1" "$2"
xtool sdk install "$2/darwin.xtoolsdk"
swift sdk list
