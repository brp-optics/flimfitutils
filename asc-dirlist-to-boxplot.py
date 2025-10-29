#!/usr/bin/env python3
"""
Convert a series of directories containing ascii or tif files to box plots, one for each directory.

Deps: numpy, tifffile
    pip install numpy tifffile
  

Usage:
    python asc-dirlist-to-boxplot dir_list.txt suffix  # Show output interactively
    python asc-dirlist-to-boxplot dir_list.txt suffix --output=plot.png # 
    """

import subprocess # for building my dataset directory list
import argparse
import os, sys
from typing import Iterable, List, Tuple
import numpy as np
# import tifffile as tiff
import matplotlib.pyplot as plt


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


def resolve_inputs(inputs: Iterable[str], suffixes=None, recursive=False, verbose=False) -> List[str]:
    """Take in a list of directories; return a list of list of actual file paths.
    Note that suffix limitations are only applied to files in directories."""
    seen = set()
    out = []
    if type(inputs) == type("string"):
        inputs = [inputs]
                
    for inp in inputs:
        if os.path.isdir(inp):
            if recursive:
                out.append(list(files_recursively(inp, suffixes)))
            else:
                out.append(list(files_non_recursively(inp, suffixes)))
        else:
            if suffixes is not None:
                print("Warning: resolve_inputs: non-empty suffixes are not applied to non-directories.",
                      f"Suffix {suffixes} not applied to {inp}.")
            else:
                if os.path.exists(inp) and inp not in seen:
                    seen.add(inp)
                    out.append([inp])
    return out

def load_ascii_floats(path: str, shape: Tuple[int, int], verbose: bool) -> np.ndarray:
    # For 256x256 this is fine; load as float64 then cast to float32.
    try:
        if verbose:
            print(f"Loading {path} with shape {shape} ... ", end="")
        arr = np.loadtxt(path, dtype=np.float32)
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

def random_points(data, ratio):
    """ Given a numpy array, return ratio*size random points from the array.
    Designed to reduce footprint in creating boxplot visualization. """

    N = data.size
    rng = np.random.default_rng()
    c = rng.choice(np.ravel(data), size=round(ratio*N), replace=False)
    return c




def main():
    ap = argparse.ArgumentParser(
        description="Plot directories of 256x256 ASCII float grids in boxplot form."
    )
    ap.add_argument("input", nargs="+", help="File containing list of directories, or list of directories.")
    
    ap.add_argument("--output", type=str, help="Single file for output. Only used if single file for input.")
    ap.add_argument("--suffix", type=str, help="Limit input from directories to files matching this sufffix. Ignored if type specified.")
    ap.add_argument("--shape", type=str, default="256x256", help="Shape of data input files.")
    ap.add_argument("--type", type=str, help="Either 'ar' or 'tm'.")
    ap.add_argument("--dry-run", action="store_true", default=False, help="Don't write to disk.")
    ap.add_argument("--fail-fast", action="store_true", help="Stop on first error")
    args = ap.parse_args()

    try:
        h, w = map(int, args.shape.lower().split("x"))
    except Exception:
        raise SystemExit("--shape must look like HxW, e.g., 256x256")
    shape = (h, w)

    if os.isfile(args.inputs):
        inputs = readlines(args.inputs)
        print(inputs) ## Otherwise untested.
    else:
        inputs = args.inputs

    if args.type == "ar":
        suffix = "_ar.asc"
        path_prefix = lambda x: "data/processed/calculated_ars/" + x
    elif args.type == "tm":
        suffix = "_color coded value.asc"
        path_prefix = lambda x:



        
        path_prefix
    else:
        suffix = args.suffix
        path_prefix = ""

    paths = resolve_inputs(inputs, args.recursive, args.verbose, args.suffix)
    if not paths:
        raise SystemExit("No input files found.")
    if len(paths) > 1: # Need output dir.
        os.makedirs(args.outdir, exist_ok=True)
    
        ok, failed = 0, 0
        for p in paths:
            try:
                img = load_ascii_floats(p, shape, args.verbose)
                base = os.path.basename(p)
                name, _sep, _ext = base.partition(".")
                out_path = os.path.join(args.outdir, name + args.outsuffix)
                save_tiff_float32(out_path, img, args.compression, args.dry_run, args.verbose)
                if not args.verbose:
                    print(".")
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
                save_tiff_float32(args.outfile, img, args.compression, args.dry_run, args.verbose)
                if args.verbose:
                    print(f"[OK] {p} -> {args.outfile} (float32, {img.shape})")
            except Exception as e:
                print(f"[ERR] {p}: {e}")
                if args.fail_fast:
                    raise
        
plt.figure()


                
#if __name__ == "__main__":
#    main()


def test():
# Testing:
    testarray = np.random.randint(low=0, high=100, size=[256, 256])
    assert(random_points(testarray, 0.001).size == 66)
    assert(random_points(testarray, 0.001).shape == (66,))
 

# test_paths = [ # Test directories for ar-sz
#     "s2-exet-fitet-sz-b2",
#     "data/processed/calculated_ars/s4-exet-fitet-sz-b2",
#     "data/processed/calculated_ars/s6-exet-fitet-irfet-sz-b2",
#     "data/processed/calculated_ars/s10-exet-fitet-sz-b2",
#     "data/processed/calculated_ars/s16-exet-fitet-sz-b3",
#     "data/processed/calculated_ars/s56-exet-fitet-sz-b3",
#     "data/processed/calculated_ars/s58-exet-fitet-sz-b3",
#     "data/processed/calculated_ars/s76-exet-fitet-sz-b3",
#     "data/processed/calculated_ars/s84-exet-fitet-sz-b3",
#     "data/processed/calculated_ars/s86-exet-fitet-sz-b3",
#     "data/processed/calculated_ars/s88-exet-fitet-sz-b3",
#     "data/processed/calculated_ars/s96-exet-fitet-sz-b3",
# ]
# axis_labels = ["s2", "s4", "s6", "s10", "s16", "s56", "s58", "s76", "s84", "s86", "s88", "s96"]

test_dirs = [ # Test directories for tm-sz
    "s2-exet-fitet-sz-b2",
    "s4-exet-fitet-sz-b2",
    "s6-exet-fitet-irfet-sz-b2",
    "s10-exet-fitet-sz-b2",
    "s16-exet-fitet-sz-b3",
    "s56-exet-fitet-sz-b3",
    "s58-exet-fitet-sz-b3",
    "s76-exet-fitet-sz-b3",
    "s84-exet-fitet-sz-b3",
    "s86-exet-fitet-sz-b3",
    "s88-exet-fitet-sz-b3",
    "s96-exet-fitet-sz-b3",
]
axis_labels = [ t.split('-')[0] for t in test_dirs ]

test_paths = []
for t in test_dirs:
    t = subprocess.check_output(f'find data/raw -type d -name {t}', shell=True)
    t = t.decode('utf-8').strip()
    test_paths.append(t)
    
test()




directory_data = []
for dir in resolve_inputs(test_paths, suffixes="_color coded value.asc", recursive=False, verbose=False):
    file_data = []
    for file in dir:
        file_data.append(random_points(load_ascii_floats(file, (256, 256), False), 0.001))
    all_file_data = np.concatenate(file_data)
    directory_data.append(all_file_data)

def safe_np_log(ndarr):
    ndarr[ndarr<=0]=1e-16
    return np.log(ndarr)
    
plt.boxplot(directory_data, tick_labels=axis_labels)
plt.title("Full-image random points")
plt.xlabel("Slide")
plt.ylabel(r"$\alpha_1/\alpha_2$")
plt.show()    

log_data = [ safe_np_log(d) for d in directory_data ]
plt.boxplot(log_data, tick_labels=axis_labels)
plt.title("Full-image random points")
plt.xlabel("Slide")
plt.ylabel(r"log($\alpha_1/\alpha_2$)")
plt.show()    



test()
