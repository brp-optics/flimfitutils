#!/usr/bin/env python3
# Crop and clobber a single tif file from SPCImage exports.
# ChatGPT5 2025.09.20ish
# Argparse and functionalization added manually.
# Bjorn 2025.10.01
# Converted to single file for snakemake use 2025.10.10.

import tempfile
import shutil
import argparse
import os
from PIL import Image

def file_crop(input_path, output_path,
              size_x=256, size_y=256, corner="upper-left", verbose=False, dry_run=False):
    """
        file_crop(input_path, output_path, size_x=256, size_y=256, corner, verbose, dry_run):
        crop file of type suffix in input_dir to size_x x size_y.
        input files are clobbered if output path is same as input path or None.
    """

    if not output_path:
        output_path = input_path
        
    # Open the image using PIL
    with Image.open(input_path) as img:
        if verbose:
            print(f"Opening: {input_path}")
        img.load() # Force PIL to read file into memory for GC reasons.
        width, height = img.size

        if corner=="upper-left":
            cropped_img = img.crop((0, 0, size_x, size_y))
        elif corner == "lower-right":
            cropped_img = img.crop((width - size_x, height - size_y, width, height))
        elif corner=="upper-right":
            cropped_img = img.crop((width - size_x, 0, width, size_y))
        elif corner=="lower-left":
            cropped_img = img.crop((0, height - size_y, size_x, height))
        else:
            raise ValueError(f"invalid corner: {corner}")
        
    # Save the cropped image
    if not dry_run:
        if output_path == input_path:
            print(f"Overwriting original: {input_path} ... ", end='')
        elif verbose:
            print(f"Saving {output_path} ... ", end='')
        cropped_img.save(output_path)
        if verbose:
            print("Done.")
    else: # dry run
        if output_path == input_path:
            print(f"Would overwrite original: {input_path} ... ", end='')
        elif verbose:
            print(f"Would save to {output_path} ... ", end='')
        if verbose:
            print("Done.")

def main():   
    parser = argparse.ArgumentParser(description="Crop single TIFF file to a fixed size.")
    parser.add_argument("input_file", help="TIFF file to crop.")
    parser.add_argument("output_file", help="File suffix to match (e.g. '.tif').")
    parser.add_argument("size", type=int, default=256, help="Final edge length to crop to, in pixels (square crop).")
    parser.add_argument("corner", choices=["upper-left", "upper-right", "lower-left", "lower-right"], default="upper-left", help="Corner from which to crop.")
    parser.add_argument("--verbose", action="store_true", help="Print progress messages.", default=False)
    parser.add_argument("--dry-run", action="store_true", help="Don't save.", default=False)
    args = parser.parse_args()
 
    file_crop(args.input_file, args.output_file, args.size, args.size, args.corner, args.verbose, args.dry_run)
    
    if args.verbose:
        print("All Done.")

if __name__ == "__main__":
    main()
    # tested with the following line:
    #dt=../data/raw/20250910_Panc_on_SLIM/20250910_3_S2/
    #python crop-tif.py "$dt"/pos_0000_color_image.tif ./pos_0000_color_image.tif 256 --verbose --dry-run
    #python crop-tif.py "$dt"/pos_0000_color_image.tif ./pos_0000_color_image.tif 256 --verbose
    #open ./pos_0000_color_image.tif
