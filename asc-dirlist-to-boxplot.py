#!/usr/bin/env python3
"""
Convert a series of directories containing ascii or tif files to box plots, one for each directory.

Deps: numpy, tifffile
    pip install numpy tifffile
  
Usage:
    python asc-dirlist-to-boxplot --input dir_list.txt --labels label_list.txt --type tm --suffix "_color coded value.asc" # Show output interactively
    python asc-dirlist-to-boxplot dir_list.txt suffix --output=plot.png # Not yet implemented.
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


def safe_np_log10(ndarr):
    ndarr[ndarr<=0]=1e-16
    return np.log10(ndarr)



def main():
    ap = argparse.ArgumentParser(
        description="Plot directories of 256x256 ASCII float grids in boxplot form."
    )
    ap.add_argument("--input", nargs="+", help="File containing list of directories, or list of directories.")
    ap.add_argument("--labels", nargs="+", help="File containing list of matching axis labels.")
    ap.add_argument("--suffix", type=str, help="Limit input from directories to files matching this sufffix. Ignored if type specified.")
    ap.add_argument("--shape", type=str, default="256x256", help="Shape of data input files.")
    ap.add_argument("--type", type=str, help="Either 'ar' or 'tm'. Used for y-axis label.")
    #ap.add_argument("--dry-run", action="store_true", default=False, help="Don't write to disk.")
    args = ap.parse_args()


    try:
        h, w = map(int, args.shape.lower().split("x"))
    except Exception:
        raise SystemExit("--shape must look like HxW, e.g., 256x256")
    shape = (h, w)

    if type(args.input)==type([]) and len(args.input)==1 and os.path.isfile(args.input[0]):
        with open(args.input[0]) as f:
            inputs = f.readlines()
            inputs = [l.strip() for l in inputs]
        print(inputs) ## Otherwise untested.
    else:
        inputs = [s.strip() for s in args.input]
        print("inputs:", inputs)

    if type(args.labels)==type([]) and len(args.labels)==1 and os.path.isfile(args.labels[0]):
        with open(args.labels[0]) as f:
            labels = f.readlines()
            labels = [l.strip() for l in labels]
    else:
        labels = [l.strip() for l in args.labels]

    assert(len(labels) == len(inputs))
        
    if args.type == "ar":
        ylabel = r'$\alpha_1/\alpha_2$'
    elif args.type == "tm":
        ylabel = r'$\tau_{mean}$'
    else:
        ylabel = "Values"
        
    directory_data = []
    for dir in resolve_inputs(inputs, suffixes=args.suffix, recursive=False, verbose=True):
        file_data = []
        for file in dir:
            file_data.append(random_points(load_ascii_floats(file, (256, 256), False), 0.001))
        all_file_data = np.concatenate(file_data)
        all_file_data = all_file_data[np.isfinite(all_file_data)] # remove NaNs.
        directory_data.append(all_file_data)
    print("Filtered to remove nans")
    print([type(d) for d in directory_data])
    print([d.size for d in directory_data])
    print(labels)

    plt.boxplot(directory_data, tick_labels=labels)
    plt.title("Full-image random points")
    plt.xlabel("Slide")
    plt.ylabel(ylabel)
    plt.show()    

    log_data = [ safe_np_log10(d) for d in directory_data ]

    print(len(log_data))
    print(len(labels))

    plt.boxplot(log_data, tick_labels=labels)
    plt.title("Full-image random points")
    plt.xlabel("Slide")
    plt.ylabel((r"log$_{10}($" + ylabel + r"$)$").replace('$$', ''))
    plt.show()

if __name__ == "__main__":
    main()
elif __name__ == "__test__":
    test()

def test():
# Testing:
    testarray = np.random.randint(low=0, high=100, size=[256, 256])
    assert(random_points(testarray, 0.001).size == 66)
    assert(random_points(testarray, 0.001).shape == (66,))
 
    
