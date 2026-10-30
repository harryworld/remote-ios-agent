#!/usr/bin/env bash
# Install a caller-selected official Linux toolchain archive, verified by SHA-256.
set -euo pipefail
: "${SWIFT_ARCHIVE_URL:?Set an official https://download.swift.org/ Linux archive URL}"
: "${SWIFT_ARCHIVE_SHA256:?Set its independently verified SHA-256}"
: "${SWIFT_INSTALL_DIR:?Set a new user-writable installation directory}"
case "$SWIFT_ARCHIVE_URL" in https://download.swift.org/*) ;; *) echo 'Use an official swift.org archive' >&2; exit 2;; esac
[[ ! -e "$SWIFT_INSTALL_DIR" ]] || { echo 'Destination must not already exist' >&2; exit 2; }
stage=$(mktemp -d)
trap 'rm -rf "$stage"' EXIT
curl --fail --location --proto '=https' --tlsv1.2 "$SWIFT_ARCHIVE_URL" -o "$stage/swift.tar.gz"
printf '%s  %s\n' "$SWIFT_ARCHIVE_SHA256" "$stage/swift.tar.gz" | sha256sum --check -
mkdir -p "$SWIFT_INSTALL_DIR"
tar -xzf "$stage/swift.tar.gz" --strip-components=1 -C "$SWIFT_INSTALL_DIR"
"$SWIFT_INSTALL_DIR/usr/bin/swift" --version
printf 'Add %s/usr/bin to PATH. Install distribution runtime libraries listed by swift.org.\n' "$SWIFT_INSTALL_DIR"
