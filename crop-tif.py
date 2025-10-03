#!/usr/bin/env python3
# Crop and clobber a directory of files from SPCImage exports.
# ChatGPT5 2025.09.20ish
# Argparse and functionalization added manually.
# Bjorn 2025.10.01

import argparse
import os
from PIL import Image

def file_crop(file_path, suffix=None, out_suffix=None,
             size_x=256, size_y=256, corner="upper-left", verbose=False, dry_run=False):
    """
        file_crop(input_dir, suffix, out_suffix, size_x=256, size_y=256, corner, verbose):
        crop file of type suffix in input_dir to size_x x size_y.
        do nothing to files of other suffixes.
        input files are clobbered if out_suffix is '' or None.
    """

    if not suffix:
        suffix = '.tif'
    if out_suffix == '':
        out_suffix = None

    print(file_path)
    # Loop over the files in the directory
    if file_path.endswith(suffix):
        
        # Open the image using PIL
        with Image.open(file_path) as img:
            if verbose:
                print(f"Loading {file_path}")
            img.load() # Force PIL to read file into memory and release it.
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
        
        # Create the new filename with out_suffix
        if out_suffix:
            new_file_path =  file_path.replace(suffix, out_suffix)
        else:
            new_file_path = file_path
        
        # Save the cropped image
        if not dry_run:
            cropped_img.save(new_file_path)
        if verbose:
            print(f"Saved cropped image: {new_file_path}")

def main():   
    parser = argparse.ArgumentParser(description="Crop single TIFF file to a fixed size.")
    parser.add_argument("input_file", help="TIFF file to crop.")
    parser.add_argument("suffix", help="File suffix to match (e.g. '.tif').")
    parser.add_argument("size", type=int, help="Final edge length to crop to, in pixels (square crop).")
    parser.add_argument("corner", choices=["upper-left", "upper-right", "lower-left", "lower-right"], default="upper-left", help="Corner from which to crop.")
    parser.add_argument("--out-suffix", default="", help="Suffix to append to output files. Leave empty to overwrite originals.")
    parser.add_argument("--verbose", action="store_true", help="Print progress messages.", default=False)
    parser.add_argument("--dry-run", action="store_true", help="Don't save.", default=False)
    args = parser.parse_args()

    file_crop(args.input_file, args.suffix, args.out_suffix, args.size, args.size, args.corner, args.verbose, args.dry_run)
    
    if args.verbose:
        print("Done.")

        
if __name__ == "__main__":
    main()
    # tested with the following line:
    #python crop-tif-dir.py "C:\Users\lociuser\Desktop\panc-slides\s2-exet600-1400-0-500-sz-b2" ".tif" 256 --verbose
    
