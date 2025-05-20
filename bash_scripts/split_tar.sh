#!/bin/bash

# Usage: ./split_tar.sh /path/to/source outputname.tar [CHUNK_SIZE]

CHECKSUM_CMD=shasum
CHECKSUM_EXT=sha1

SOURCE_DIR="$1"
ARCHIVE_NAME="$2"
CHUNK_SIZE="${3:-1G}"    # Optional: default to 1G
PART_PREFIX="${ARCHIVE_NAME}.part"

# Input validation
if [[ -z "$SOURCE_DIR" || -z "$ARCHIVE_NAME" ]]; then
    echo "Usage: $0 /path/to/source outputname.tar [CHUNK_SIZE]"
    exit 1
fi

if [ ! -d "$SOURCE_DIR" ]; then
    echo "[✗] Source directory '$SOURCE_DIR' does not exist."
    exit 1
fi

# Step 1: Create and split tar archive
echo "[+] Creating multi-part archive from '$SOURCE_DIR' into '$ARCHIVE_NAME' with chunk size '$CHUNK_SIZE'..."
tar -cf - "$SOURCE_DIR" | split -b "$CHUNK_SIZE" -d - "$PART_PREFIX-"

# Step 2: Generate checksums
echo "[+] Generating checksums..."
$CHECKSUM_CMD ${PART_PREFIX}-* > "${ARCHIVE_NAME}.$CHECKSUM_EXT"

echo "[✓] Done! Archive split and checksums saved to '${ARCHIVE_NAME}.$CHECKSUM_EXT'"

