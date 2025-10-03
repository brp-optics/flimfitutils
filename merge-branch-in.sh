#!/usr/bin/env bash
# Usage: ./merge-branch-in.sh /source/root /backup/root
set -euxo pipefail

IFS=$'\n\t'	# Remove space as internal string separator.

SRC="${1:-}"; DEST="${2:-}"; DAYS="${3:-3}"
# Normalize: strip any trailing slash on SRC so prefix removal is stable
SRC="${SRC%/}"

if [[ -z "${SRC}" || -z "${DEST}" ]]; then
  echo "Usage: $0 <branch_dir> <root_dir> [days]" >&2
  exit 1
fi

# Ensure source exists
if [[ ! -d "$SRC" ]]; then
  echo "ERROR: Source directory not found: $SRC" >&2
  exit 1
fi

# Ensure destination exists
mkdir -p "$DEST"

# Safety: make sure we don't overwrite.
if [[ "$(realpath -m "$SRC")" == "$(realpath -m "$DEST")" ]]; then
  echo "ERROR: Source and destination resolve to the same path." >&2
  exit 1
fi

# Find files younger than 3 days in source tree and copy to backup
if command -v rsync >/dev/null 2>&1; then
    echo "Using rsync..."
    # -a : preserve attrs, recurse
    # -u : skip files that are newer on DEST (good for root being ahead)
    # --files-from/--from0 : use the find-produced list (NUL-safe)
    # --itemize-changes : show what would/will change
    # Add --dry-run first if you want to preview
  
    find "$SRC" -type f -mtime -3 -print0 | rsync -au --files-from=- --from0 --itemize-changes "$SRC/" "$DEST/"
else
    echo "rsync not found, falling back to cp..."
    find "$SRC" -type f -mtime -3 -print0 |
while IFS= read -r -d '' f; do
  # Remove the "$SRC/" prefix to get a relative path
  rel="${f#"$SRC"/}"
  out="$DEST/$rel"
  mkdir -p "$(dirname "$out")"
  cp -u -p -- "$f" "$out"
done
fi