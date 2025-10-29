#!/bin/python3

# Program to read in a set of related lifetime text files and save them to a new location with invalid pixels marked as NaN.
# Bjorn with Claude Opus 4.1, 2025.10.27-28.

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

def asc_export(asc_filepath, matrix, verbose=True, dry_run=True):
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
        print(f"asc_export: Error saving {asc_filepath}: {e}", file=sys.stderr)

def threshold_mask(data, threshold_variable, min_thresh, max_thresh)
    threshold_failed = (np.array(min_thresh) > threshold_variable) | (threshold_variable > np.array(max_thresh))
    data = ma.masked_array(data, threshold_failed)
    return data

def threshold_reasonably(dataset, thresholds)
    for data in dataset:
        for variable, (min_thresh, max_thresh) in thresholds:
            data = threshold_mask(data, dataset[variable], min_thresh, max_thresh)
    return data

thresholds = { "a1": (0, 1e20),
               "a2": (0, 1e20),
               "photons": (3000/7/7/45, 0.005*3600), ## minimum for fitting; 30% photon count saturation.
               "chi": (0.75, 1.5), # ChiSq
               "binned_photons": (3000, __),
               


suffixes = set(
              
def load_and_threshold_related_files

              
              

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Calculate and export free-bound ratios for BH exported FLIM data.")
    parser.add_argument("--free", type=str, help="Path to free coefficients ASC file, or suffix of free files if --in specified.")
    parser.add_argument("--bound", type=str, help="Path to bound coefficients ASC file, or suffix of bound files if --in specified.")
    parser.add_argument("--photons", type=str, help="Path to photon count ASC file, or suffix of photon files.")
    parser.add_argument("--photonthresh", type=str, default="3000:1000000", help="Threshold for photons per pixel.")
    parser.add_argument("--bh-bin", type=int, help="BH bin size, for (re)binning photons")
    parser.add_argument("--chisq", type=str, help="Path to chi sq ASC file, or suffix of chi sq files.")
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
    photons = os.path.expanduser(args.photons)
    chisq = os.path.expanduser(args.chisq)
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
