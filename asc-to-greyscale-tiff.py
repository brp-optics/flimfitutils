#!/usr/bin/env python3
"""
Convert 256x256 whitespace-delimited ASCII float grids to 32-bit grayscale TIFFs.


Deps: numpy, tifffile
    pip install numpy tifffile
  

Usage:
    python ascii_to_tiff32.py data/*.txt
    python ascii_to_tiff32.py data/*.dat --outdir out_tiffs --compression lzw
    python ascii_to_tiff32.py some_dir --shape 256x256 --suffix _f32.tiff
    """

import argparse
import os
from glob import glob
from typing import Iterable, List, Tuple
import numpy as np
import tifffile as tiff


def files_recursively(path, suffixes=""):
    """ Returns an lazy generator over files matching suffixes in path.
    path: the root directory
    Suffixes: a string or iterator of strings.

    Result: Yields the path to the matching files.
    """
    seen = set()
    for dirpath, __, files in os.walk(path):
        for file in files:
            if file.endswith(suffixes):
                filepath = os.path.join(dirpath, file)
                if filepath not in seen:
                    seen.add(filepath)
                    yield filepath

def files_non_recursively(dirpath, suffixes):
    """ A lazy generator over files matching suffixes in dirpath.
    dirpath: the directory
    suffixes: a string or iterator of strings.

    Result: Yields the path to the matching files.
    """
    for file in os.listdir(dirpath):
        if file.endswith(suffixes):
            yield os.path.join(dirpath, file)

def resolve_inputs(inputs: Iterable[str], recursive, verbose, suffixes=None) -> List[str]:
    """Take in a list of files or directories; return a list of actual file paths.
    Note that suffix limitations are only applied to directories."""
    seen = set()
    out = []
    if type(inputs) == type("string"):
        inputs = [inputs]
                
    for inp in inputs:
        if os.path.isdir(inp):
            if recursive:
                out.extend(list(files_recursively(inp, suffixes)))
            else:
                out.extend(list(files_non_recursively(inp, suffixes)))
        else:
            if suffixes is not None:
                print("Warning: resolve_inputs: non-empty suffixes are not applied to non-directories.",
                      f"Suffix {suffixes} not applied to {inp}.")
            matches = glob(inp)
            if matches:
                for m in matches:
                    if m not in seen:
                        seen.add(m)
                        out.append(m)
                        
            else:
                if os.path.exists(inp) and inp not in seen:
                    seen.add(inp)
                    out.append(inp)
    return out


def load_ascii_floats(path: str, shape: Tuple[int, int], verbose: bool) -> np.ndarray:
    # For 256x256 this is fine; load as float64 then cast to float32.
    try:
        if verbose:
            print(f"Loading {path} with shape {shape} ... ", end="")
        arr = np.loadtxt(path, dtype=np.float64)
        if verbose:
            print("success.")

    except Exception as e:
        raise RuntimeError(f"Failed to parse {path}: {e}")
    
    if arr.ndim == 1:
        expected = shape[0] * shape[1]
        if arr.size != expected:
            raise ValueError(f"{path}: expected {expected} values, got {arr.size}")
        arr = arr.reshape(shape)
    elif arr.ndim == 2:
        if arr.shape != shape:
            raise ValueError(f"{path}: expected shape {shape}, got {arr.shape}")
    else:
        raise ValueError(f"{path}: unexpected ndim={arr.ndim}")
    return arr.astype(np.float32, copy=False)

def save_tiff_float32(out_path: str, img: np.ndarray, compression: str, dry_run: bool, verbose: bool) -> None:
    comp_map = {
        "none": None,
        "deflate": "deflate",
        "lzw": "lzw",
        "packbits": "packbits",
        "zstd": "zstd",
    }
    comp = comp_map[compression]

    # Single-image, single-channel float32 TIFF
    if dry_run:
        if verbose:
            print(f"Would save {img.shape} image to {out_path}.")
    else:
        if verbose:
            print(f"Saving new {img.shape} image to {out_path} ... ", end="")
        tiff.imwrite(out_path, img, compression=comp)
        if verbose:
            print("success.")
    # No try...except block in this function because success counting is one level up.
        
def main():
    ap = argparse.ArgumentParser(
        description="Convert 256x256 ASCII float grids to 32-bit grayscale TIFFs (tifffile only)."
    )
    ap.add_argument("inputs", nargs="+", help="Files, directories, or globs to ASCII float files")
    ap.add_argument("--shape", type=str, default="256x256", help="Expected shape HxW (default 256x256)")
    ap.add_argument("--outdir", type=str, help="Output directory.")
    ap.add_argument("--outfile", type=str, help="Single file for output. Only used if single file for input.")
    ap.add_argument("--insuffix", type=str, help="Limit input from directories to files matching this sufffix.")
    ap.add_argument("--outsuffix", type=str, default="_f32.tif", help="Output filename suffix, if output is directory.")
    ap.add_argument("--recursive", "-r", action="store_true", default=False, help="Recurse down subdirectories")
    ap.add_argument("--multiplyby", "-m", type=float,  help="Optional factor to multiply all values by before export. Useful when later processing doesn't handle non-integer values well (ImageJ!).")
    ap.add_argument("--verbose", "-v", action="store_true", default=False, help="Print detailed debugging data.")
    ap.add_argument("--dry-run", action="store_true", default=False, help="Don't write to disk.")
    ap.add_argument(
        "--compression",
        type=str,
        default="deflate",
        choices=["none", "deflate", "lzw", "packbits", "zstd"],
        help="TIFF compression (float32-safe). Default: lzw.",
    )
    ap.add_argument("--fail-fast", action="store_true", help="Stop on first error")
    args = ap.parse_args()

    try:
        h, w = map(int, args.shape.lower().split("x"))
    except Exception:
        raise SystemExit("--shape must look like HxW, e.g., 256x256")
    shape = (h, w)

    paths = resolve_inputs(args.inputs, args.recursive, args.verbose, args.insuffix)
    if not paths:
        raise SystemExit("No input files found.")
    if len(paths) > 1: # Need output dir.
        os.makedirs(args.outdir, exist_ok=True)
    
        ok, failed = 0, 0
        for p in paths:
            try:
                img = load_ascii_floats(p, shape, args.verbose)
                if args.multiplyby is not None:
                    img = img * args.multiplyby
                base = os.path.basename(p)
                name, _sep, _ext = base.partition(".")
                out_path = os.path.join(args.outdir, name + args.outsuffix)
                save_tiff_float32(out_path, img, args.compression, args.dry_run, args.verbose)
                if not args.verbose:
                    print(".", end="")
                if args.verbose:
                    print(f"[OK] {p} -> {out_path} (float32, {img.shape})")
                ok += 1
                        
            except Exception as e:
                print(f"[ERR] {p}: {e}")
                failed += 1
                if args.fail_fast:
                    raise

        print(f"Done. Converted: {ok}, Failed: {failed}, Outdir: {args.outdir}")
    else: # Single file output
        for p in paths:
            try:
                img = load_ascii_floats(p, shape, args.verbose)
                if args.multiplyby is not None:
                    img = img * args.multiplyby
                save_tiff_float32(args.outfile, img, args.compression, args.dry_run, args.verbose)
                if args.verbose:
                    print(f"[OK] {p} -> {args.outfile} (float32, {img.shape})")
            except Exception as e:
                print(f"[ERR] {p}: {e}")
                if args.fail_fast:
                    raise
        

if __name__ == "__main__":
    main()

## Testing, currently manually:

# dt=./
# uv run python asc-to-greyscale-tiff.py "$dt"/pos_0000_nr.asc --outfile="$dt"/pos_0000_nr_out.asc --dry-run --verbose
# open the image in fiji and inspect. min = 0.2222754
# uv run python asc-to-greyscale-tiff.py "$dt" --insuffix=_ar.asc --outsuffix="_f32.tiff" --outdir=./ --dry-run --verbose
#python3 asc-to-greyscale-tiff.py ./ --insuffix=_ar.asc --outsuffix="_f32.tiff" --outdir=./
# Open a random image in fiji and inspect, min=-1, max~30.
