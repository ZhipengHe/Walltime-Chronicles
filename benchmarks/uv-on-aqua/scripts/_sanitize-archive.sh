#!/bin/bash
# Produce a redacted-for-public copy of a bench archive bundle.
#
# Inputs:  <archive-dir>/raw.tar.zst
# Outputs: <archive-dir>/redacted.tar.zst       (public, tracked)
#          <archive-dir>/manifest.sha256        (sha256 of redacted.tar.zst, tracked)
#          <archive-dir>/raw.manifest.sha256    (sha256 of raw.tar.zst, gitignored)
#
# raw.tar.zst is left untouched on disk and is gitignored — kept for forensic
# value when something in the redacted view needs cross-checking. Idempotent.
#
# Redaction policy
# ----------------
# Categories scrubbed (runtime values are extracted from THIS run's
# session-meta.txt or overridden via env vars below — no values are baked
# into this script):
#   - Username and personal `/home/`, `/scratch/`, `/mnt/.../home/` paths.
#   - Internal cluster IPs (any 4-octet IPv4 in the bundle; NID `@o2ib`
#     suffix preserved separately so the structure stays readable).
#   - CVE-matchable build strings: Linux kernel, vendor-patched Lustre
#     client, Weka client.
#   - Filesystem `Use%` column from `df -h` output.
#   - Live `qstat -Q` queue snapshot block in session-meta.txt.
#   - PBS run identifiers: PBS_JOBID, session seed, UTC start timestamp.
#
# Categories kept as-is:
#   - Hostnames (the bench README documents the cluster name openly).
#   - CPU SKU + total RAM (useful benchmark context).
#   - Package versions (already public via the committed lockfile).
#   - PyPI / external CDN URLs in verbose logs.
#   - uv cache content-addressed keys.
#   - `/usr/bin/time -v` resource counters per cell.
#
# Env-var overrides (optional; defaults auto-detected from session-meta.txt):
#   REDACT_USER             username to scrub
#   REDACT_KERNEL           kernel build string to scrub
#   REDACT_LUSTRE_CLIENT    Lustre client version string to scrub
#   REDACT_WEKA_CLIENT      Weka client version string to scrub

set -euo pipefail

USAGE="usage: $0 <archive-dir>
       <archive-dir> must contain raw.tar.zst.
       Example: $0 results-archive/2026-06-25-<host>/"

[ $# -eq 1 ] || { echo "$USAGE" >&2; exit 2; }
[ -d "$1" ] || { echo "not a directory: $1" >&2; exit 1; }

ARCHIVE_DIR=$(cd "$1" && pwd)
RAW="$ARCHIVE_DIR/raw.tar.zst"
[ -f "$RAW" ] || { echo "missing: $RAW" >&2; exit 1; }
REDACTED="$ARCHIVE_DIR/redacted.tar.zst"

# Cross-platform sed -i (BSD on macOS needs the '' arg; GNU on Linux doesn't).
sed_inplace() {
  if [ "$(uname -s)" = "Darwin" ]; then
    sed -i '' "$@"
  else
    sed -i "$@"
  fi
}

# Escape a value for safe use in `s|VALUE|...|` substitutions.
sed_escape() {
  printf '%s\n' "$1" | sed 's|[][\\/.*^$]|\\&|g'
}

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
EXTRACTED="$TMP/extracted"
mkdir -p "$EXTRACTED"
tar --use-compress-program=unzstd -xf "$RAW" -C "$EXTRACTED"

cd "$EXTRACTED"
META="$EXTRACTED/session-meta.txt"

# Auto-detect runtime values (env overrides win)
USER_NAME="${REDACT_USER:-}"
if [ -z "$USER_NAME" ] && [ -f "$META" ]; then
  USER_NAME=$(grep -oE '/(home|scratch)/[a-zA-Z0-9_]+' "$META" 2>/dev/null \
              | head -1 | sed -E 's|/(home\|scratch)/||')
fi
USER_NAME="${USER_NAME:-$(whoami 2>/dev/null || true)}"

KERNEL_BUILD="${REDACT_KERNEL:-}"
if [ -z "$KERNEL_BUILD" ] && [ -f "$META" ]; then
  KERNEL_BUILD=$(awk '/^Linux / {print $3; exit}' "$META")
fi

LUSTRE_CLIENT="${REDACT_LUSTRE_CLIENT:-}"
if [ -z "$LUSTRE_CLIENT" ] && [ -f "$META" ]; then
  LUSTRE_CLIENT=$(awk '/^lustre kernel:/ {print $3; exit}' "$META")
fi

WEKA_CLIENT="${REDACT_WEKA_CLIENT:-}"
if [ -z "$WEKA_CLIENT" ] && [ -f "$META" ]; then
  WEKA_CLIENT=$(awk '/^\* [0-9]+\.[0-9]+\.[0-9]+$/ {print $2; exit}' "$META")
fi

# Username + paths
if [ -n "$USER_NAME" ]; then
  USER_ESC=$(sed_escape "$USER_NAME")
  find . -type f -print0 | while IFS= read -r -d '' f; do
    sed_inplace -E \
      -e "s|/mnt/[a-zA-Z0-9_]+/home/$USER_ESC|/mnt/<lustre-mount>/home/<user>|g" \
      -e "s|/home/$USER_ESC|/home/<user>|g" \
      -e "s|/scratch/$USER_ESC|/scratch/<user>|g" \
      -e "s|\\b$USER_ESC\\b|<user>|g" \
      "$f"
  done
fi

# CVE-matchable build strings BEFORE the IP regex — the Lustre/kernel build
# strings can themselves contain 4-octet patterns (e.g. a Lustre version like
# A.B.C.D_<vendor>_<rev>). If the IP regex ran first it would eat the leading
# A.B.C.D and leave the `_<vendor>_<rev>` suffix exposed.
if [ -n "$KERNEL_BUILD" ]; then
  KERNEL_ESC=$(sed_escape "$KERNEL_BUILD")
  find . -type f -print0 | while IFS= read -r -d '' f; do
    sed_inplace -e "s|$KERNEL_ESC|<kernel>|g" "$f"
  done
fi
if [ -n "$LUSTRE_CLIENT" ]; then
  LUSTRE_ESC=$(sed_escape "$LUSTRE_CLIENT")
  find . -type f -print0 | while IFS= read -r -d '' f; do
    sed_inplace -e "s|$LUSTRE_ESC|<lustre-client>|g" "$f"
  done
fi
if [ -n "$WEKA_CLIENT" ]; then
  WEKA_ESC=$(sed_escape "$WEKA_CLIENT")
  find . -type f -print0 | while IFS= read -r -d '' f; do
    sed_inplace -E -e "s|^\\* $WEKA_ESC\$|* <weka-client>|g" "$f"
  done
fi

# Internal cluster IPs (generic 4-octet match; preserves @o2ib suffix
# structure by tagging it first)
find . -type f -print0 | while IFS= read -r -d '' f; do
  sed_inplace -E \
    -e 's|[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}@o2ib|<lustre-nid>@o2ib|g' \
    "$f"
  sed_inplace -E \
    -e 's|[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}|<ip>|g' \
    "$f"
done

# Strip the FS `Use%` column from df -h output
find . -type f -print0 | while IFS= read -r -d '' f; do
  sed_inplace -E -e 's| [0-9]+%( +/)| <n%>\1|g' "$f"
done

# Strip the qstat -Q queue-snapshot block from session-meta.txt
if [ -f session-meta.txt ]; then
  sed_inplace -E '/^Queue +Max +Tot/,/^=== seed/{/^=== seed/!d;}' session-meta.txt
fi

# PBS run identifiers (generic patterns — no QUT-specific server name)
find . -type f -print0 | while IFS= read -r -d '' f; do
  sed_inplace -E \
    -e 's|PBS_JOBID:[ ]+[0-9]+\.[a-z]+|PBS_JOBID: <jobid>|g' \
    -e 's|session seed:[ ]+[0-9]+|session seed: <seed>|g' \
    -e 's|^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$|<utc>|g' \
    "$f"
done

# Re-bundle to an absolute path
NEW="$TMP/redacted.tar.zst"
tar --use-compress-program='zstd -19' -cf "$NEW" -C "$EXTRACTED" .
mv "$NEW" "$REDACTED"

(cd "$ARCHIVE_DIR" && sha256sum redacted.tar.zst > manifest.sha256)
(cd "$ARCHIVE_DIR" && sha256sum raw.tar.zst > raw.manifest.sha256)

# Self-verify against the redacted bundle (using the same runtime values;
# no QUT-specific literals in this verification path either)
VERIFY="$TMP/verify"
mkdir -p "$VERIFY"
tar --use-compress-program=unzstd -xf "$REDACTED" -C "$VERIFY"
cd "$VERIFY"

count_hits() {
  ( eval "$1" 2>/dev/null || true ) | wc -l | tr -d ' '
}

user_hits=0
if [ -n "$USER_NAME" ]; then
  USER_ESC_GREP=$(sed_escape "$USER_NAME")
  user_hits=$(count_hits "grep -rE '\\b$USER_ESC_GREP\\b' .")
fi
ip_hits=$(count_hits "grep -rE '\\b[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\b' .")
kernel_hits=0
if [ -n "$KERNEL_BUILD" ]; then
  kernel_hits=$(count_hits "grep -rF -- \"$KERNEL_BUILD\" .")
fi
lustre_hits=0
if [ -n "$LUSTRE_CLIENT" ]; then
  lustre_hits=$(count_hits "grep -rF -- \"$LUSTRE_CLIENT\" .")
fi
weka_hits=0
if [ -n "$WEKA_CLIENT" ]; then
  weka_hits=$(count_hits "grep -rE \"^\\* $(sed_escape "$WEKA_CLIENT")\$\" .")
fi
jobid_hits=$(count_hits "grep -rE 'PBS_JOBID:[ ]+[0-9]+\\.[a-z]+' .")

echo "=== sanitize verification (each must be 0) ==="
echo "  username occurrences:    $user_hits"
echo "  IP occurrences:          $ip_hits"
echo "  kernel-build hits:       $kernel_hits"
echo "  lustre-client hits:      $lustre_hits"
echo "  weka-client hits:        $weka_hits"
echo "  PBS jobid hits:          $jobid_hits"
echo
echo "Raw      (private):  $RAW ($(wc -c < "$RAW") bytes, gitignored)"
echo "Redacted (public):   $REDACTED ($(wc -c < "$REDACTED") bytes, tracked)"

if [ "$user_hits" != "0" ] || [ "$ip_hits" != "0" ] || [ "$kernel_hits" != "0" ] \
   || [ "$lustre_hits" != "0" ] || [ "$weka_hits" != "0" ] || [ "$jobid_hits" != "0" ]; then
  echo "ERROR: residual hits in redacted bundle — redaction did not fully scrub" >&2
  exit 3
fi
