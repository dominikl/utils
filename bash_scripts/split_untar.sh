#!/bin/bash

# Usage: ./split_untar.sh outputname.tar

CHECKSUM_CMD=shasum
CHECKSUM_EXT=sha1

ARCHIVE_NAME="$1"
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
tar -xf "$ARCHIVE_NAME"

echo "[✓] Extraction complete."

rm "$ARCHIVE_NAME"

