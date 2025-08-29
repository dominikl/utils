#!/usr/bin/env python3
"""
Generate companion ome.xml files.
"""

import argparse
import re
import sys
import string
from pathlib import Path
from typing import Generator, Dict, Set, Tuple
import tifffile
from ome_types.model import OME
from ome_types.model import Channel
from ome_types.model import Image
from ome_types.model import ImageRef
from ome_types.model import Pixels
from ome_types.model import Plane
from ome_types.model import Plate
from ome_types.model import TiffData
from ome_types.model import Well
from ome_types.model import WellSample
import uuid


def main():
    parser = argparse.ArgumentParser(
        description="Generate companion ome.xml files",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "name",
        type=str,
        help="Name of the plate"
    )

    parser.add_argument(
        "sample",
        type=Path,
        help="Sample tif file"
    )
    
    # Required arguments
    parser.add_argument(
        "input_file",
        type=Path,
        help="Input file containing the list of image filenames"
    )

    parser.add_argument(
        "regex",
        type=Path,
        help="File with regex for parsing the file names; has to contain named groups 'row', 'col', 'field', 'channel_index', 'channel_name', 'z', 't',\
        e.g. for matching file names like B12_2-z1-t2-ch1-DAPI.tiff use:\
        (?P<row>[a-zA-Z]+)(?P<col>\\d+)_(?P<field>\\d+)-z(?P<z>\\d+)-t(?P<t>\\d+)-ch(?P<channel_index>\\d+)-(?P<channel_name>.+)\\."
    )
    
    # Optional arguments    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--timepoints",
        action="store_true",
        help="If the sample file has several images they will be considered as timepoints, otherwise it is assumed they are z-planes."
    )

    parser.add_argument(
        "--order",
        type=str,
        default="XYCZT",
        help="Order"
    )

    parser.add_argument(
        "--row-num",
        action="store_true",
        help="Flag if rows are numbers (0, 1, ... instead of A, B, ...)"
    )

    parser.add_argument(
        "--row-zero",
        action="store_true",
        help="Flag if rows are zero-based (First -> 0, Second -> 1, ...); otherwise, they are one-indexed (First -> 1, Second -> 2, ...)"
    )

    parser.add_argument(
        "--col-zero",
        action="store_true",
        help="Flag if columns are zero-based (First -> 0, Second -> 1, ...); otherwise, they are one-indexed (First -> 1, Second -> 2, ...)"
    )

    parser.add_argument(
        "--field-zero",
        action="store_true",
        help="Flag if fields are zero-based (First -> 0, Second -> 1, ...); otherwise, they are one-indexed (First -> 1, Second -> 2, ...)"
    )

    parser.add_argument(
        "--c-zero",
        action="store_true",
        help="Flag if channel indices are zero-based; otherwise, they are one-indexed"
    )

    parser.add_argument(
        "--z-zero",
        action="store_true",
        help="Flag if z plane indices are zero-based; otherwise, they are one-indexed"
    )

    parser.add_argument(
        "--t-zero",
        action="store_true",
        help="Flag if t indices are zero-based; otherwise, they are one-indexed"
    )

    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Skip manual confirmation."
    )

    args = parser.parse_args()
    
    if not args.input_file.exists():
        print(f"Error: Input file '{args.input_file}' does not exist", file=sys.stderr)
        sys.exit(1)
    
    run(args)


def parse(input_file: Path) -> Generator[str, None, None]:
    """
    Parse input file and yield each line as a stripped string.
    
    Args:
        input_file: Path to the input file containing the list of image filenames
        
    Yields:
        str: Each line from the file with whitespace stripped
        
    Raises:
        FileNotFoundError: If the input file doesn't exist
        IOError: If there's an error reading the file
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            for line in f:
                yield line.strip()
    except FileNotFoundError:
        raise FileNotFoundError(f"Input file '{input_file}' not found")
    except IOError as e:
        raise IOError(f"Error reading file '{input_file}': {e}")


def safe_extract(match: re.Match[str], name: str) -> str | None:
    """
    Safely extract a named group from a regex match object.
    
    This function attempts to extract a named group from a regex match,
    handling cases where the group doesn't exist in the pattern or
    where the group exists but matched an empty string.
    
    Args:
        match: A regex match object from re.match() or re.search()
        name: Name of the regex group to extract
        
    Returns:
        str | None: The matched string if the group exists and is non-empty,
                   None if the group doesn't exist or is empty
    """
    try:
        group_value = match.group(name)
        if group_value:
            return group_value
        return None
    except IndexError:
        # Group doesn't exist in the regex pattern
        return None


class Specs:
    x = 0
    y = 0
    c = 1
    dtype = "uint8"
    order = "XYCZT"
    z = 1
    t = 1
    spp = 1
    channels = dict()
    planes_per_tiff = 1
    f = 1
    cols = 0
    rows = set()


def run(args):
    # Load regex from file
    with open(args.regex, 'r') as f:
        regex = f.read().strip()
    
    match = re.match(regex, args.sample.name)
    if match:
        if args.verbose:
            print("Regex matches:")
            for k, v in match.groupdict().items():
                print(f"  {k}: {v}")
    else:
        print("Regex does not match sample image name", file=sys.stderr)
        sys.exit(1)


    specs = Specs()
    specs.order = args.order

    # Get image specs from sample
    specs.x, specs.y, specs.spp, specs.dtype, n = check_sample(args)
    if n > 1:
        if args.timepoints:
            specs.t = n
        else:
            specs.z = n
        if specs.spp > 1:
            specs.planes_per_tiff = specs.spp * n
        else:
            specs.planes_per_tiff = n
    
    # Get plate specs from file list
    specs.cols, specs.rows, n_field, n_z, n_t, specs.channels, images = check_filenames(args, regex)
    if n_field:
        specs.f = n_field
    if n_z:
        if specs.z > 1:
            print(f"Error: Z planes specified in filenames, but sample image already has Z planes", file=sys.stderr)
            sys.exit(1)
        specs.z = n_z
    if n_t:
        if specs.t > 1:
            print(f"Error: Timepoints specified in filenames, but sample image already has timepoints", file=sys.stderr)
            sys.exit(1)
        specs.t = n_t
    if specs.channels:
        if specs.spp > 1:
            print(f"Error: Channels specified in filenames, but sample image already is multichannel", file=sys.stderr)
            sys.exit(1)
        else:
            specs.c = len(specs.channels)

    if not (specs.cols and specs.rows):
        print("Error: Columns and rows must be specified in filenames", file=sys.stderr)
        sys.exit(1)
    
    print(f"Summary:")
    print(f"  X: {specs.x}")
    print(f"  Y: {specs.y}")
    print(f"  Number of channels: {specs.c}")
    print(f"  Channels: {specs.channels}")
    print(f"  Samples per pixel: {specs.spp}")
    print(f"  Planes per tiff: {specs.planes_per_tiff}")
    print(f"  Z planes: {specs.z}")
    print(f"  Timepoints: {specs.t}")
    print(f"  Pixeltype: {specs.dtype}")
    print(f"  Dimension order: {specs.order}")
    print(f"  Columns: {specs.cols}")
    print(f"  Rows: {sorted(specs.rows)}")
    print(f"  Fields: {specs.f}")

    if not args.quiet:
        print("Is that correct? (y/n)")
        x = input()
        if x.lower() != "y":
            return

    ome = OME()
    plate = Plate(name=args.name, rows=len(specs.rows), columns=specs.cols)
    ome.plates.append(plate)

    wells = dict()
    for key, images in images.items():
        row, col, field = key.split("|")
        row = int(row)
        col = int(col)
        field = int(field)
        wells_key = f"{row}|{col}"
        if wells_key not in wells:
            wells[wells_key] = Well(row=row, column=col)
            for _ in range(specs.f):
                wells[wells_key].well_samples.append(None)
            plate.wells.append(wells[wells_key])
        img = gen_image(args, specs, regex, images, key)
        wells[wells_key].well_samples[field] = WellSample(index=field, image_ref=ImageRef(id=img.id))
        ome.images.append(img)

    out_file = f"{args.name}.ome.xml"
    with open(out_file, 'w') as f:
        f.write(ome.to_xml())
    print(f"Wrote OME-XML to {out_file}")


def check_sample(args):
    """
    Extract image dimensions and metadata from a sample TIFF file.
    
    This function reads a TIFF file and extracts key metadata including:
    - X and Y dimensions
    - Samples per pixel (channels)
    - Pixel data type
    - Number of images
    
    Args:
        sample_file (Path): Path to the sample TIFF file to analyze
        
    Returns:
        tuple: (x, y, c, dtype, n) where:
            - x (int): Width in pixels
            - y (int): Height in pixels  
            - spp (int): Samples per pixel (ie. channels)
            - dtype (str): Pixel data type (e.g., 'uint8', 'uint16')
            - n (int): Number of images
    """
    with tifffile.TiffFile(args.sample) as tif:
        if args.verbose:
            print(f"Tiffinfo:")
            print(f"Pages: {len(tif.pages)}")
            print(f"Shaped (1,1,y,x,s): {tif.pages[0].shaped}")
            print(f"Dtype: {tif.pages[0].dtype}")

        x = tif.pages[0].shaped[3]
        y = tif.pages[0].shaped[2]
        spp = tif.pages[0].shaped[4]
        n = len(tif.pages)
        return x, y, spp, str(tif.pages[0].dtype), n


def check_filenames(args: argparse.Namespace, regex: str) -> Tuple[int, Set[str], int, int, int, Dict[int, str], Dict[str, list[str]]]:
    """
    Parse image filenames and extract plate/image metadata using regex pattern.
    
    Analyzes a list of image filenames to extract plate layout information
    and image metadata. Uses a regex pattern to parse filenames and extract:
    - Row and column positions (essential for plate layout)
    - Field positions (optional, for multi-field imaging)
    - Z-plane, timepoint, and channel information (optional)
    - Channel names and indices
    
    Handles both zero-based and one-based indexing based on command-line
    arguments and validates channel naming consistency.
    
    Args:
        args: Parsed command-line arguments containing input_file path and indexing flags
        regex: Regular expression pattern with named groups for parsing filenames
        
    Returns:
        Tuple containing:
            - n_col (int): Maximum number of columns
            - rows (Set[str]): Set of row identifiers found
            - n_field (int): Maximum number of fields
            - n_z (int): Maximum number of z-planes
            - n_t (int): Maximum number of timepoints
            - channels (Dict[int, str]): Channel index to name mapping
            - images (Dict[str, list[str]]): Key to filename list mapping
    """
    n_col: int = 0
    rows: Set[str] = set()
    n_field: int = 0
    n_z: int = 0
    n_t: int = 0
    channels: Dict[int, str] = dict()
    channel_index: int = 0
    images: Dict[str, list[str]] = dict()

    for line in parse(args.input_file):
        match = re.match(regex, line)
        if match:
            # essential
            col = int(safe_extract(match, 'col'))
            if col is None:
                print(f"Warn: Skippking, no column info in line: {line}", file=sys.stderr)
                continue
            if not args.col_zero:
                col = col - 1
            n_col = max(col+1, n_col)

            # essential
            row = safe_extract(match, 'row')
            if row is None:
                print(f"Warn: Skippking, no row info in line: {line}", file=sys.stderr)
                continue
            if not args.row_num:
                row = string.ascii_lowercase.index(row.lower())
            else:
                row = int(row)
                if not args.row_zero:
                    row = row - 1
            rows.add(safe_extract(match, 'row'))

            # optional
            if safe_extract(match, 'field'):
                field = int(safe_extract(match, 'field'))
                if not args.field_zero:
                    field -= 1
                n_field = max(field+1, n_field)
            else:
                field = 0
            
            key = f"{row}|{col}|{field}"
            if key not in images:
                images[key] = []
            images[key].append(line)

            # optional
            if safe_extract(match, 'z'):
                z = int(safe_extract(match, 'z'))
                if not args.z_zero:
                    z = z - 1
                n_z = max(z+1, n_z)
            
            # optional
            if safe_extract(match, 't'):
                t = int(safe_extract(match, 't'))
                if not args.t_zero:
                    t = t - 1
                n_t = max(t+1, n_t)

            # optional  
            if safe_extract(match, 'channel_index'):
                c = int(safe_extract(match, 'channel_index'))
                if not args.c_zero:
                    c = c - 1
                if safe_extract(match, 'channel_name'):
                    if safe_extract(match, 'channel_name') in channels and c != channels[safe_extract(match, 'channel_name')]:
                        print(f"Error: Channel {safe_extract(match, 'channel_name')} has multiple indices: {c} and {channels[safe_extract(match, 'channel_name')]}")
                        sys.exit(1)
                    channels[c] = safe_extract(match, 'channel_name')
                else:
                    channels[c] = None
            else:
                if safe_extract(match, 'channel_name') and safe_extract(match, 'channel_name') not in channels:
                    channels[channel_index] = safe_extract(match, 'channel_name')
                    channel_index += 1
        else:
            print(f"Warn: Skippking, no match in line: {line}", file=sys.stderr)
            

    return n_col, rows, n_field, n_z, n_t, channels, images


def gen_image(args, specs, regex, images, name):
    if specs.spp > 1:
        pixels_c = specs.spp
    else:
        pixels_c = specs.c
    pixels = Pixels(
        type=specs.dtype,
        size_x=specs.x,
        size_y=specs.y,
        size_z=specs.z,
        size_c=pixels_c,
        size_t=specs.t,
        dimension_order=specs.order
    )
    # for c in range(pixels_c):
    #     for t in range(specs.t):
    #         for z in range(specs.z):
    #             pixels.planes.append(Plane(
    #                 the_c=c,
    #                 the_t=t,
    #                 the_z=z
    #             ))
    for _ in range(specs.c):
        pixels.channels.append(Channel(samples_per_pixel=specs.spp))
    if specs.channels:
        for index, ch_name in specs.channels.items():
            pixels.channels[index]= Channel(samples_per_pixel=1, name=ch_name)

    image = Image(
        name=name,
        pixels=pixels,
    )
    for filename in images:
        tiff_uuid = TiffData.UUID(
            value=f"urn:uuid:{uuid.uuid4()}",
            file_name=filename
        )
        match = re.match(regex, filename)
        if match:
            if safe_extract(match, 'z'):
                z = int(safe_extract(match, 'z'))
                if not args.z_zero:
                    z = z - 1
            else:
                z = 0
            
            if safe_extract(match, 't'):
                t = int(safe_extract(match, 't'))
                if not args.t_zero:
                    t = t - 1
            else:
                t = 0

            if safe_extract(match, 'channel_index'):
                c = int(safe_extract(match, 'channel_index'))
                if not args.c_zero:
                    c = c - 1
            elif safe_extract(match, 'channel_name'):
                c = channels[safe_extract(match, 'channel_name')]
            else:
                c = 0

            tiff = TiffData(
                first_c=c,
                first_t=t,
                first_z=z,
                plane_count=specs.planes_per_tiff,
                uuid=tiff_uuid)
            pixels.tiff_data_blocks.append(tiff)
            for p_i in range(specs.planes_per_tiff):
                for s_i in range(specs.spp):
                    if specs.spp > 1:
                        c_i = s_i
                    else:
                        c_i = c
                    if specs.planes_per_tiff > 1:
                        if args.timepoints:
                            t = p_i
                        else:
                            z = p_i
                    pixels.planes.append(Plane(
                            the_c=c_i,
                            the_t=t,
                            the_z=z
                ))
    return image


if __name__ == "__main__":
    main()