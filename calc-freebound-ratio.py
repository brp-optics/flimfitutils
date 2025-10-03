#!/bin/python3

# Program to read in a free lifetime file and its matching bound file and return a text file containing free-bound ratios.
# Bjorn 2025.10.03

import numpy as np
import os
import argparse
import sys

def flimload(asciifile, verbose):
    if verbose:
        print(f"Loading {asciifile}...", end="")
    try:
        data = np.loadtxt(asciifile)
    except Exception as e:
        print(f"loadtxt: couldn't load {asciifile}: {e}")
    if verbose:
        print("success.")
    return data

def filesrecursively(path, suffixes):
    """ Returns an lazy generator over files matching suffixes in path.
    path: the root directory
    Suffixes: a string or iterator of strings.

    Result: Yields the path to the matching files.
    """
    for dirpath, __, files in os.walk(path):
        for file in files:
            if file.endswith(suffixes):
                filepath = os.path.join(dirpath, file)
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

def free_bound_ratio(m1, m2, invalid=-1, file=None):
    """ Calculate the free-bound ratio given to coefficient matrices.
    Replaces output with _invalid_ where there would be division by zero.
    """

    m2[m2==0] = invalid # Avoid division by zero, and free_bound_ratio should never go negative.
    try:
        ratio = m1/m2
    except Exception as e:
        print(f"free_bound_ratio: processing {file}: {e}", file=sys.stderr) 
    ratio[m2==invalid] = invalid
    return ratio

def flim_export(asc_filepath, matrix, verbose=True, dry_run=True):
    """ Export a matrix as a BH-compatible .asc file. """
    try:
        if dry_run:
            if verbose:
                print(f"Would save {matrix.shape} to {asc_filepath}.")
        else:
            if verbose:
                print(f"Saving {matrix.shape} to {asc_filepath}...", end="")
            np.savetxt(asc_filepath, matrix, fmt='%.7g', delimiter=' ', newline='\n')
            if verbose:
                print("success.")
    except Exception as e:
        print(f"flim_export: Error saving {asc_filepath}: {e}", file=sys.stderr)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Calculate and export free-bound ratios for BH exported FLIM data.")
    parser.add_argument("--free", type=str, help="Path to free coefficients ASC file, or suffix of free files if --in specified.")
    parser.add_argument("--bound", type=str, help="Path to bound coefficients ASC file, or suffix of bound files if --in specified.")
    parser.add_argument("--indir", type=str, help="Path to directory containing paired free and bound files.")
    parser.add_argument("--out", type=str, help="Path to output file or directory.")
    parser.add_argument("--suffix", type=str, help="Suffix for output files if --out is a directory.")
    parser.add_argument("--invalid", type=float, help="Optional value to use for invalid outputs.")
    parser.add_argument("--verbose", action="store_true", help="Print details of file operations.")
    parser.add_argument("--dry-run", action="store_true", help="Don't write to output files.")

    args = parser.parse_args()

    if args.suffix:
        suffix = args.suffix
    else:
        suffix = "-nr.asc" # for "NADH ratio"

    if args.indir:
        indir = os.path.expanduser(args.indir)
    else:
        indir = None
    free = os.path.expanduser(args.free)
    bound = os.path.expanduser(args.bound)
    out = os.path.expanduser(args.out)

    if indir and os.path.isdir(indir):
        free_files = list(files_non_recursively(indir, free))
        bound_files = list(files_non_recursively(indir, bound))

        assert(len(free_files) == len(bound_files))
        assert(os.path.isdir(out))
        for ff, bf in zip(free_files, bound_files):
            free = flimload(ff, args.verbose)
            bound = flimload(bf, args.verbose)
            ratio = free_bound_ratio(free, bound, args.invalid, ff)
            
            common_stem = os.path.commonprefix((os.path.basename(ff), os.path.basename(bf)))
            if common_stem[-2:] == '_a':
                common_stem = common_stem[:-2]
            out_fn = common_stem + suffix
            flim_export(os.path.join(out, out_fn), ratio, args.verbose, args.dry_run)

    else: # InDir not a directory.
        fd = flimload(free, args.verbose)
        bd = flimload(bound, args.verbose)
        ratio = free_bound_ratio(fd, bd, args.invalid, free)

        if os.path.isdir(out):
            common_stem = os.path.commonprefix((os.path.basename(free), os.path.basename(bound)))
            if common_stem[-2:] == '_a':
                common_stem = common_stem[:-2]
            out_fn = common_stem + suffix
            flim_export(os.path.join(out, out_fn), ratio, args.verbose, args.dry_run)

        else: # args.out is file or doesn't exist
            flim_export(args.out, ratio, args.verbose, args.dry_run)

# Tests:
# python calc-freebound-ratio.py --free=~/Desktop/panc-slides/s2-exet-fitet-sz-b2/pos_0000_a1.asc --bound=~/Desktop/panc-slides/s2-exet-fitet-sz-b2/pos_0000_a2.asc --out=./pos_0000_nr.asc --verbose --dry-run
# python calc-freebound-ratio.py --free=~/Desktop/panc-slides/s2-exet-fitet-sz-b2/pos_0000_a1.asc --bound=~/Desktop/panc-slides/s2-exet-fitet-sz-b2/pos_0000_a2.asc --out=./pos_0000_nr.asc --verbose
# wc -l ./pos_0000_nr.asc
# wc -w ./pos_0000_nr.asc
# cat ./pos_0000_nr.asc  # look at format.
# python calc-freebound-ratio.py --free=a1.asc --bound=a2.asc --indir=~/Desktop/panc-slides/s2-exet-fitet-sz-b2/ --out=./ --verbose
# python calc-freebound-ratio.py --free=a1.asc --bound=a1.asc --indir=~/Desktop/panc-slides/s2-exet-fitet-sz-b2/ --out=./ --verbose
# cat *.asc # (should return 1 everywhere)

