#!/usr/bin/env python3
# Crop and clobber a directory of files from SPCImage exports.
# ChatGPT5 2025.09.20ish, modified by hand 2026.03.11

import os
from PIL import Image
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Crop a directory of files from SPCImage exports. Clobber if no output directory specified.")
    parser.add_argument("input_directory", type=str, help="directory containing input .tiff files.")
    parser.add_argument("output_directory", nargs="?", default=None, help="(optional) output directory.")
    
    args = parser.parse_args()

    input_directory = args.input_directory
    output_directory = args.output_directory

    if output_directory is None:
        output_directory = input_directory
    else:    
        # Make sure that output directory exists
        os.makedirs(output_directory, exist_ok=True)
    
    # Loop over the files in the directory
    for filename in os.listdir(input_directory):
        if filename.endswith(".tif"):
            # Construct full file path
            file_path = os.path.join(input_directory, filename)
        
            # Open the image using PIL
            with Image.open(file_path) as img:
                # Crop the image to 256x256 from the upper-left corner (0,0)
                cropped_img = img.crop((0, 0, 256, 256))
            
            # Create the new filename with "-crop" appended before the ".tif"
            new_filename = filename # filename.replace(".tif", "-crop.tif")
            new_file_path = os.path.join(output_directory, new_filename)
            
            # Save the cropped image
            cropped_img.save(new_file_path)
            print(f"Saved cropped image: {new_file_path}")

        
