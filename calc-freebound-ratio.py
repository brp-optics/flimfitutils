#!/bin/python3

# Program to read in a free lifetime file and its matching bound file and return a text file containing free-bound ratios.
# Bjorn 2025.10.03

import numpy as np
import os
import argparse
import sys

def flimload(asciifile, verbose):
    if verbose:
        print(f"Loading {asciifile} ... ", end="")
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

#    if np.any(m2 < 0):
#        print(f"free_bound_ratio: file {file} a2 goes negative.", file=sys.stderr)
#    if np.any(m1 < 0):
#        print(f"free_bound_ratio: file {file} a1 goes negative.", file=sys.stderr)
    # Surprise, surprise, out of 2208 test files, a1 goes negative in 37 of them and a2 goes negative in 2 of them.

    m2[m1<=0] = invalid
    m2[m2<=0] = invalid # Avoid division by zero, and free_bound_ratio should never go negative.
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
                print(f"Saving {matrix.shape} to {asc_filepath} ... ", end="")
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
        suffix = "_ar.asc" # for "a1/a2 ratio"

    if args.indir:
        indir = os.path.expanduser(args.indir)
    else:
        indir = None
    free = os.path.expanduser(args.free)
    bound = os.path.expanduser(args.bound)
    out = os.path.expanduser(args.out)

    if indir and os.path.isdir(indir):
        free_files = sorted(list(files_non_recursively(indir, free)))
        bound_files = sorted(list(files_non_recursively(indir, bound)))

        assert(len(free_files) == len(bound_files))
        assert(os.path.isdir(out))
        for ff, bf in zip(free_files, bound_files):
            free = flimload(ff, args.verbose)
            bound = flimload(bf, args.verbose)
            ratio = free_bound_ratio(free, bound, args.invalid, ff)
            
            common_stem = os.path.commonprefix((os.path.basename(ff), os.path.basename(bf)))
            if common_stem[-2:] == '_a':
                common_stem = common_stem[:-2]
            else:
                print(f"Unexpected filenames: {ff}, {bf}, {common_stem}", file=sys.stderr)
            out_fn = common_stem + suffix
            flim_export(os.path.join(out, out_fn), ratio, args.verbose, args.dry_run)

    else: # InDir not a directory.
        fd = flimload(free, args.verbose)
        bd = flimload(bound, args.verbose)
        ratio = free_bound_ratio(fd, bd, args.invalid, free)

        if os.path.isdir(out):
            common_stem = os.path.commonprefix((os.path.basename(free), os.path.basename(bound)))
            # By default, BH exports a1 and a2 ratios as pos_XXXX_a1.asc
            # and pos_XXXX_a2.asc. The common stem will end in "_a",
            # which I don't consider part of the desired suffix. 
            if common_stem[-2:] == '_a':
                common_stem = common_stem[:-2]
            out_fn = common_stem + suffix
            flim_export(os.path.join(out, out_fn), ratio, args.verbose, args.dry_run)

        else: # args.out is file or doesn't exist
            flim_export(args.out, ratio, args.verbose, args.dry_run)

# Tests, currently done manually:
# dt=../data/raw/20250910_Panc_on_SLIM/20250910_3_S2/s2-exet-fitet-sz-b2/
# python calc-freebound-ratio.py --free="$dt"/pos_0000_a1.asc --bound="$dt"/pos_0000_a2.asc --out=./pos_0000_nr.asc --verbose --dry-run # Should say "Would save (256,256) to ./pos_0000_nr.asc."
# python calc-freebound-ratio.py --free="$dt"/pos_0000_a1.asc --bound="$dt"/pos_0000_a2.asc --out=./pos_0000_nr.asc --verbose
# wc -l ./pos_0000_nr.asc # should be 256
# wc -w ./pos_0000_nr.asc # should be 256*256 = 65536
# cat ./pos_0000_nr.asc  # look at format. Last number should be 1.288815.
# cat ./pos_0000_nr.asc | fmt -1 | uniq | sort -un | head # Should be "nan" then 0.2222754
# cat ./pos_0000_nr.asc | fmt -1 | uniq | sort -un # Should end with 29.94402
# rm *_nr.asc
# python calc-freebound-ratio.py --free=a1.asc --bound=a2.asc --indir="$dt" --out=./ --invalid=-1 # Might take a while.
# ls "$dt"/*_a1.asc # 1104.
# ls "$dt"/*_a2.asc # 1104.
# ls *_ar.asc | wc -l # 1104.
# cat *_ar.asc | fmt -1 | uniq | sort -un > sort.temp
# head sort.temp # Should be -1, then almost 0.
# tail sort.temp # Should be big. For my dataset the biggest values are 87, then 208.
# rm *_ar.asc
# python calc-freebound-ratio.py --free=a1.asc --bound=a1.asc --indir="$dt"/ --out=./ --verbose --invalid=-1 # Should print a bunch of warnings about unexpected filenames. 
# cat *_ar.asc | fmt -1 uniq | sort -un # (should return 1 or -1 everywhere)
# ls *_ar.asc | wc -l # 1104.
# cat *_ar.asc | fmt -1 | wc -l # 1104 * 256 * 256 = 72351744
# rm *_ar.asc
