#!/bin/bash
# Idempotent install of hyperfine v1.20.0 to ~/.local/bin/.
# Verifies sha256 against a pinned value; bails on mismatch.

set -euo pipefail

VERSION="v1.20.0"
EXPECTED_SHA256="a298729daf3b670198b6988a0489289e0044174c8734a172659495dd09d080b6"
TARGET_DIR="$HOME/.local/bin"
TARGET="$TARGET_DIR/hyperfine"
ARCH="x86_64-unknown-linux-musl"
TARBALL="hyperfine-${VERSION}-${ARCH}.tar.gz"
URL="https://github.com/sharkdp/hyperfine/releases/download/${VERSION}/${TARBALL}"

mkdir -p "$TARGET_DIR"

if [ -x "$TARGET" ]; then
  current_sha=$(sha256sum "$TARGET" | awk '{print $1}')
  if [ "$current_sha" = "$EXPECTED_SHA256" ]; then
    echo "hyperfine $VERSION already at $TARGET (sha256 verified)"
    "$TARGET" --version
    exit 0
  fi
  echo "hyperfine present but sha256 mismatch:"
  echo "  current:  $current_sha"
  echo "  expected: $EXPECTED_SHA256"
  echo "Reinstalling..."
fi

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
cd "$TMP"

echo "Downloading $URL"
curl -fL -o "$TARBALL" "$URL"
tar xzf "$TARBALL"
cp "hyperfine-${VERSION}-${ARCH}/hyperfine" "$TARGET"
chmod +x "$TARGET"

actual_sha=$(sha256sum "$TARGET" | awk '{print $1}')
if [ "$actual_sha" != "$EXPECTED_SHA256" ]; then
  echo "ERROR: sha256 mismatch after install"
  echo "  expected: $EXPECTED_SHA256"
  echo "  actual:   $actual_sha"
  rm -f "$TARGET"
  exit 1
fi

echo "hyperfine $VERSION installed at $TARGET"
"$TARGET" --version
