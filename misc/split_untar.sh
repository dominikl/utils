#!/bin/bash

# Usage: ./split_untar.sh outputname.tar.part-00
# Extract tar archives created with split_tar.sh

# Detect available checksum command
if command -v shasum >/dev/null 2>&1; then
    CHECKSUM_CMD=shasum
elif command -v sha1sum >/dev/null 2>&1; then
    CHECKSUM_CMD=sha1sum
else
    echo "[✗] Error: shasum or sha1sum required"
    exit 1
fi
CHECKSUM_EXT=sha1

ARCHIVE_NAME="${1%%.part-*}"

if [[ "$ARCHIVE_NAME" == *.tar.gz ]]; then
    COMPRESSION="z"
elif [[ "$ARCHIVE_NAME" == *.tar.bz2 ]]; then
    COMPRESSION="j"
elif [[ "$ARCHIVE_NAME" == *.tar.xz ]]; then
    COMPRESSION="J"
elif [[ "$ARCHIVE_NAME" == *.tar.lzma ]]; then
    COMPRESSION="lzma"
else
    COMPRESSION=""
fi

PART_PREFIX="${ARCHIVE_NAME}.part"
CHECKSUM_FILE="${ARCHIVE_NAME}.$CHECKSUM_EXT"

if [ -z "$ARCHIVE_NAME" ]; then
    echo "Usage: $0 outputname.tar"
    exit 1
fi

if [ ! -f "$CHECKSUM_FILE" ]; then
    echo "[✗] Checksum file '$CHECKSUM_FILE' not found."
    exit 1
fi

# Step 1: Verify checksums
echo "[+] Verifying checksums..."
$CHECKSUM_CMD -c "$CHECKSUM_FILE" || {
    echo "[✗] Checksum verification failed."
    exit 1
}

echo "[✓] Checksums verified."

# Step 2: Reassemble archive
echo "[+] Reassembling archive..."
cat ${PART_PREFIX}-* > "$ARCHIVE_NAME"

# Step 3: Extract
echo "[+] Extracting archive..."
if [ "$COMPRESSION" = "lzma" ]; then
    tar --lzma -xf "$ARCHIVE_NAME"
else
    tar -x${COMPRESSION}f "$ARCHIVE_NAME"
fi

echo "[✓] Extraction complete."

rm "$ARCHIVE_NAME"

