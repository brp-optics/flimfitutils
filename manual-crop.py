# Crop files from SPCImage exports. This one actually works,
# but it doesn't fit well into a bash script...

import os
from PIL import Image

# Set the directory containing the .tif files
input_directories = [#"s10-exet600-1400-0-500-fitet-sz-b2",
                     #"s2-exet600-1400-0-500-sz-b2",
                     #"s4-exet600-1400-0-500-fitet-sz-b2",
                     #"s56-exet600-1400-0-500-fitet-sz-b3",
                     #"s58-exet600-1400-0-500-fitet-sz-b3",
                     #"s6-exet600-1400-0-500-fitet-irfet-sz-b2",
                     "s76-exet600-1400-0-500-fitet-sz-b3", # <- file 0206 is corrupted.
                     #"s8-exet600-1400-0-500",
                     "s84-exet600-1400-0-500-fitet-sz-b3", #<- file 0149 is corrupted.
                     #"s86-exet600-1400-0-500-fitet-sz-b3",
                     #"s88-exet600-1400-0-500-fitet-sz-b3",
                     "s96-exet600-1400-0-500-fitet-sz-b3"]

for input_directory in input_directories:
    input_directory = os.path.join(r"C:\Users\lociuser\Desktop\panc-slides", input_directory)


    # Loop over the files in the directory
    for filename in os.listdir(input_directory):
        if filename.endswith("_color_image.tif"):
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
            try:
                cropped_img.save(new_file_path)
                #print(f"Saved cropped image: {new_file_path}")
            except Exception as e:
                print(f"Failed to save {new_file_path}: {e}")
