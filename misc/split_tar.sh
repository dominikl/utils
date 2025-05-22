#!/bin/bash

# Usage: ./split_tar.sh /path/to/source [CHUNK_SIZE]
# Generate tar archive of a directory, split into multiple files with
# specified chunk size (default: 10G)

COMPRESSION="" # If you want to compress archive use z (gzip), j (bzip), etc.
CHECKSUM_CMD=shasum  # Might have to be adjusted, usually OSX: shasum, Linux: sha1sum
CHECKSUM_EXT=sha1

SOURCE_DIR="${1%/}"
SOURCE_NAME="$(basename "$SOURCE_DIR")"
ARCHIVE_NAME="${SOURCE_NAME}.tar"
case "$COMPRESSION" in
    "z") ARCHIVE_NAME="${ARCHIVE_NAME}.gz" ;;
    "j") ARCHIVE_NAME="${ARCHIVE_NAME}.bz2" ;;
    "J") ARCHIVE_NAME="${ARCHIVE_NAME}.xz" ;;
    "lzma") ARCHIVE_NAME="${ARCHIVE_NAME}.lzma" ;;
esac

CHUNK_SIZE="${2:-10G}"    # Optional: default to 10G
PART_PREFIX="${ARCHIVE_NAME}.part"

# Input validation
if [[ -z "$SOURCE_DIR" ]]; then
    echo "Usage: $0 /path/to/source [CHUNK_SIZE]"
    exit 1
fi

if [ ! -d "$SOURCE_DIR" ]; then
    echo "[✗] Source directory '$SOURCE_DIR' does not exist."
    exit 1
fi

# Step 1: Create and split tar archive
echo "[+] Creating multi-part archive from '$SOURCE_DIR' into '$ARCHIVE_NAME' with chunk size '$CHUNK_SIZE'..."
if [ "$COMPRESSION" = "lzma" ]; then
    tar --lzma -cf - "$SOURCE_DIR" | split -b "$CHUNK_SIZE" -d - "$PART_PREFIX-"
else
    tar -c${COMPRESSION}f - "$SOURCE_DIR" | split -b "$CHUNK_SIZE" -d - "$PART_PREFIX-"
fi

# Step 2: Generate checksums
echo "[+] Generating checksums..."
$CHECKSUM_CMD ${PART_PREFIX}-* > "${ARCHIVE_NAME}.$CHECKSUM_EXT"

echo "[✓] Done! Archive split and checksums saved to '${ARCHIVE_NAME}.$CHECKSUM_EXT'"

