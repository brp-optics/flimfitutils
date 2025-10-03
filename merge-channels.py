import os
import sys
import numpy as np
from PIL import Image

def load_grayscale_image(path):
    try:
        img = Image.open(path).convert('L')  # Convert to 8-bit grayscale
        return np.array(img)
    except Exception as e:
        print(f"Error loading image '{path}': {e}")
        sys.exit(1)

def merge_channels(directory):
    # Define expected filenames
    red_path = os.path.join(directory, 'img_t1_z1_c1')
    green_path = os.path.join(directory, 'img_t1_z1_c2')
    blue_path = os.path.join(directory, 'img_t1_z1_c3')
    alpha_path = os.path.join(directory, 'img_t1_z1_c4')  # Optional

    # Check if required files exist
    for path in [red_path, green_path, blue_path]:
        if not os.path.isfile(path):
            print(f"Missing file: {path}")
            sys.exit(1)

    # Load grayscale channels
    red = load_grayscale_image(red_path)
    green = load_grayscale_image(green_path)
    blue = load_grayscale_image(blue_path)

    if red.shape != green.shape or red.shape != blue.shape:
        print("Error: Input images must have the same dimensions.")
        sys.exit(1)

    # Optional alpha channel
    if os.path.isfile(alpha_path):
        alpha = load_grayscale_image(alpha_path)
        if alpha.shape != red.shape:
            print("Error: Alpha image dimensions do not match other channels.")
            sys.exit(1)
        rgba = np.stack([red, green, blue, alpha], axis=-1)
        mode = 'RGBA'
    else:
        rgba = np.stack([red, green, blue], axis=-1)
        mode = 'RGB'

    # Convert to PIL image and save
    out_image = Image.fromarray(rgba, mode=mode)
    output_path = os.path.join(directory, 'Composite_py.tif')
    out_image.save(output_path)
    print(f"Saved merged image to: {output_path}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python merge-channels.py <directory>")
        sys.exit(1)

    directory = sys.argv[1]
    if not os.path.isdir(directory):
        print(f"Error: '{directory}' is not a valid directory.")
        sys.exit(1)

    merge_channels(directory)

if __name__ == '__main__':
    main()