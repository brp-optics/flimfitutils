#!/usr/bin/env python3
# Claude Sonnet 4.5, 2025.10.29
# Fixed get_cmap, Bjorn, 2025.10.29

"""
Apply rainbow colormap to greyscale TIFF files.
"""

import argparse
import sys
import numpy as np
import tifffile
import matplotlib as mpl
import matplotlib.pyplot as plt # Fallback for get_cmaps in older matplotlib

def create_colormap_image(cmap_name='rainbow', height=256, width=1024):
    """
    Create a visual representation of the colormap.
    
    Args:
        cmap_name: Name of the matplotlib colormap
        height: Height of the colormap image
        width: Width of the colormap image
    
    Returns:
        RGB image array of the colormap
    """
    
    try:
        cmap = mpl.colormaps.get_cmap(cmap_name)
    except AttributeError:
        cmap = plt.get_cmap(cmap_name)
        
    gradient = np.linspace(0, 1, width)
    gradient_2d = np.tile(gradient, (height, 1))
    colormap_image = cmap(gradient_2d)[:, :, :3]  # Remove alpha channel
    return (colormap_image * 255).astype(np.uint8)


def apply_colormap(input_path, output_path, freeval, boundval, 
                   dry_run=False, verbose=False):
    """
    Apply rainbow colormap to a greyscale TIFF file.
    
    Args:
        input_path: Path to input TIFF file
        output_path: Path to output TIFF file
        freeval: Value to map to blue (low end of colormap)
        boundval: Value to map to red (high end of colormap)
        dry_run: If True, don't save output files
        verbose: If True, print progress information
    """
    
    if verbose:
        print(f"Reading input file: {input_path}")
    
    # Read the input TIFF file
    try:
        data = tifffile.imread(input_path)
    except Exception as e:
        print(f"Error reading input file: {e}", file=sys.stderr)
        sys.exit(1)
    
    if verbose:
        print(f"Input shape: {data.shape}")
        print(f"Input dtype: {data.dtype}")
        print(f"Data range: [{np.min(data):.6f}, {np.max(data):.6f}]")
    
    # Ensure data is float32
    if data.dtype != np.float32:
        if verbose:
            print(f"Converting from {data.dtype} to float32")
        data = data.astype(np.float32)
    
    if verbose:
        print(f"Normalizing data: freeval={freeval} (blue), boundval={boundval} (red)")
    
    # Normalize data to [0, 1] range based on freeval and boundval
    # freeval maps to 0 (blue), boundval maps to 1 (red)
    if boundval == freeval:
        print("Warning: freeval equals boundval, all values will map to the same color", 
              file=sys.stderr)
        normalized = np.zeros_like(data)
    else:
        normalized = (data - freeval) / (boundval - freeval)
        normalized = np.clip(normalized, 0, 1)
    
    if verbose:
        print(f"Normalized range: [{np.min(normalized):.6f}, {np.max(normalized):.6f}]")
    
    # Apply rainbow colormap
    if verbose:
        print("Applying rainbow colormap")
    # For older versions of matplotlib.
    try:
        cmap = mpl.colormaps.get_cmap('rainbow')
    except AttributeError:
        cmap = plt.get_cmap('rainbow')
        
    colored_data = cmap(normalized)
    
    # Convert to 8-bit RGB (remove alpha channel)
    rgb_data = (colored_data[:, :, :3] * 255).astype(np.uint8)
    
    if verbose:
        print(f"Output shape: {rgb_data.shape}")
        print(f"Output dtype: {rgb_data.dtype}")
    
    if dry_run:
        if verbose:
            print(f"Dry run mode: skipping {output_path} save")
        return
    
    # Save the colored TIFF
    if verbose:
        print(f"Saving output file: {output_path}")
    
    try:
        tifffile.imwrite(output_path, rgb_data, photometric='rgb')
    except Exception as e:
        print(f"Error writing output file: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Save the colormap
    colormap_path = output_path + ".colormap.tiff"
    if verbose:
        print(f"Saving colormap: {colormap_path}")
    
    try:
        colormap_image = create_colormap_image('rainbow')
        tifffile.imwrite(colormap_path, colormap_image, photometric='rgb')
    except Exception as e:
        print(f"Error writing colormap file: {e}", file=sys.stderr)
        sys.exit(1)
    
    if verbose:
        print("Done!")


def main():
    parser = argparse.ArgumentParser(
        description='Apply rainbow colormap to greyscale TIFF files.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  %(prog)s input.tif output.tif --freeval 0.0 --boundval 1.0 --verbose
        """
    )
    
    parser.add_argument('input', help='Input TIFF file path')
    parser.add_argument('output', help='Output TIFF file path')
    parser.add_argument('--freeval', '--blueval', type=float, required=True,
                       help='Value to map to blue (low end of colormap)')
    parser.add_argument('--boundval', '--redval', type=float, required=True,
                       help='Value to map to red (high end of colormap)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Process data but do not save output files')
    parser.add_argument('--verbose', action='store_true',
                       help='Print progress information')
    
    args = parser.parse_args()
    
    apply_colormap(
        args.input,
        args.output,
        args.freeval,
        args.boundval,
        dry_run=args.dry_run,
        verbose=args.verbose
    )


if __name__ == '__main__':
    main()
