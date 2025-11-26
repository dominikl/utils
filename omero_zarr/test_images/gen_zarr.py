#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# dependencies = ["ome-zarr"]
# ///

import argparse
import os
import shutil
import subprocess
import sys
import numpy as np
import zarr
from ome_zarr.io import parse_url
from ome_zarr.writer import write_image
from ome_zarr.format import FormatV04, FormatV05

x = 512
y = 256
c = 3
z = 4
t = 5

def get_format(args):
    if args.version == "0.4":
        return FormatV04()
    elif args.version == "0.5":
        return FormatV05()
    else:
        raise ValueError(f"Unsupported version: {args.version}")


def create_zarr(args):
    # Remove existing destination, if any, so we can recreate it cleanly
    if os.path.exists(args.dest):
        reply = input(f"Destination '{args.dest}' exists. Overwrite? [y/N]: ").strip().lower()
        if reply not in {"y", "yes"}:
            print("Aborting without overwriting existing destination.")
            sys.exit(1)
        shutil.rmtree(args.dest)

    store = parse_url(args.dest, mode="w", fmt=get_format(args)).store
    root = zarr.group(store=store)
    # Create dummy data for the image
    data = np.fromfunction(
        lambda t, c, z, y, x: x + 1 + 1000 * (y+1) +  1000000 * (c+1) + 10000000 * (z+1) + 100000000 * (t+1),
        (t, c, z, y, x),
        dtype=np.uint32,
    ).astype(np.uint32)
    chunks=(1, 1, 1, y, x)
    write_image(image=data, group=root, axes="tczyx",
                storage_options=dict(chunks=chunks))
    print(f"Created zarr with at {args.dest}")
    print(f"Version: {args.version}")
    print(f"Shape (TCZYX): {data.shape}")
    print(f"Chunks: {chunks}")
    print(f"Pixel values: x + 1 + 1000 * (y+1) +  1000000 * (c+1) + 10000000 * (z+1) + 100000000 * (t+1)")


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser for gen_zarr."""
    parser = argparse.ArgumentParser(
        description="Generate a zarr test image dataset.",
    )

    # Required arguments
    parser.add_argument(
        "dest",
        type=str,
        help="Destination path for the generated zarr.",
    )

    parser.add_argument(
        "--cols",
        type=int,
        default=None,
        help="Number of columns, for plate layout (default: None)",
    )

    parser.add_argument(
        "--rows",
        type=int,
        default=None,
        help="Number of rows, for plate layout (default: None)",
    )

    parser.add_argument(
        "--fields",
        type=int,
        default=3,
        help="Number of fields, for plate layout (default: 3)",
    )

    parser.add_argument(
        "--version",
        type=str,
        default="0.5",
        help="Dataset version string (default: '0.5')",
    )

    parser.add_argument(
        "--view",
        action="store_true",
        help="If set, view the generated data in validator",
    )


    return parser


def main(argv=None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    create_zarr(args)
    if args.view:
        # Launch the ome-zarr NGFF viewer/validator, equivalent to:
        #   ome_zarr view <dest>
        subprocess.run(["ome_zarr", "view", args.dest], check=False)


if __name__ == "__main__":
    main()

