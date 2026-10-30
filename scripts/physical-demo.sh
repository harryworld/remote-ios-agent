#!/usr/bin/env bash
# Requires explicit prepared inputs; stops at the first failure. Does not choose an app/device.
set -euo pipefail
: "${REMOTE_IOS_DEVICE:?Select a device}"
: "${REMOTE_IOS_TEST_IPA:?Supply a signed demo IPA}"
: "${REMOTE_IOS_TEST_BUNDLE:?Supply its bundle ID}"
: "${REMOTE_IOS_TEST_X:?Supply button X in screenshot pixels}"
: "${REMOTE_IOS_TEST_Y:?Supply button Y in screenshot pixels}"
remote-ios device status
remote-ios install "$REMOTE_IOS_TEST_IPA"
remote-ios launch "$REMOTE_IOS_TEST_BUNDLE"
remote-ios workflow interact-verify --x "$REMOTE_IOS_TEST_X" --y "$REMOTE_IOS_TEST_Y"
remote-ios logs "$REMOTE_IOS_TEST_BUNDLE" --seconds 5
