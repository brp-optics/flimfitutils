# Import a csv, export a tileconfig.

import argparse
import os
import numpy as np

def load_xyz_coordinates(file_path, pixel_size_um=1, overlap=0):
    coords = np.loadtxt(file_path, delimiter=",") # Will be an N x 3 array.
    if overlap is not None and overlap > 0:
        print("Overlap not defined yet. Would need to calculate a grid and use that to get the spacing.")   
    else:
        return coords / -pixel_size_um

# 0.7 um / pixel -> 

def save_tiles(file_path, coords, prefix=None, suffix=None):
    if (prefix is None) or (not prefix):
        prefix = "pos_"
    if (suffix is None) or (not suffix):
        suffix = "_color_image"
    with open(file_path, mode='w') as f:
        print("""# Define the number of dimensions we are working on""", file=f)
        print("""dim = 2""", file=f)
        print("", file=f)
        print("# Define the image coordinates", file=f)
        for i in range(len(coords)):
            print(f"{prefix}{i:04d}{suffix}.tif ; ; ({coords[i,0]}, {coords[i,1]})", file=f)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert acquisition coordinate csv file to ImageJ TileCoordinates.txt")
    parser.add_argument("input_csv", help="Path to input CSV file (no headers, 3 columns: x y z)")
    parser.add_argument("output_tileconfig", help="Path to output TileConfig file.")
    parser.add_argument("--pixel_size_um", type=float, help="Optional size of a pixel in um.")
    parser.add_argument("--overlap", type=float, help="Optional overlap, in pct. Overrides pixel size.")
    parser.add_argument("--prefix", default='pos_', help="Optional prefix for files. Overrides 'pos_'.")
    parser.add_argument("--suffix", default="", help="Optional suffix for files. Overrides '_color_image'.")

    args = parser.parse_args()

    coords = load_xyz_coordinates(args.input_csv, pixel_size_um=args.pixel_size_um, overlap=args.overlap)
    save_tiles(args.output_tileconfig, coords, prefix=args.prefix, suffix=args.suffix)
else: # testing
    input = r"C:\Users\hyeonho\Desktop\Bjorn_Paulson\research\18_Circadian\20250918_stitching\s58-z-locations-short.csv"
    output = r"C:\Users\hyeonho\Desktop\Bjorn_Paulson\research\18_Circadian\20250918_stitching\TileConfig.txt"
    coords = load_xyz_coordinates(input)
    save_tiles(output, coords)
