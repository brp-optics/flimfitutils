#!/usr/bin/env python3
# Crop and clobber a directory of files from SPCImage exports.
# ChatGPT5 2025.09.20ish

import os
from PIL import Image

# Set the directory containing the .tif files
input_directory = r'\your\directory\here' 

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
        new_file_path = os.path.join(input_directory, new_filename)
            
        # Save the cropped image
        cropped_img.save(new_file_path)
        print(f"Saved cropped image: {new_file_path}")
