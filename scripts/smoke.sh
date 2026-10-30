#!/usr/bin/env bash
set -euo pipefail
remote-ios --backend mock workflow run "$(dirname "$0")/../examples/agent-workflows/smoke.json"
