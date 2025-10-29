#!/bin/python3
""" Program to read in a set of related lifetime text files and save them to a new location with invalid pixels marked as NaN.
""" 
# Bjorn 2025.10.27; debugged with help from Claude Sonnet 4.5

import numpy as np
import numpy.ma as ma
import os
import argparse
import sys
from fileutils import asc_load, asc_export
from typing import Dict, List


def _asc_get_related_stem(path) -> str:
    """ Given the name of one file in an asc file set, return a tem that can be easily used to construct related files."""
    
    export_suffixes = ['a1', 'a2', 't1', 't2', 'a1[%]', 'a2[%]', 'chi', 'phasor_G', 'phasor_S', 'scatter', 'color coded value', 'photons',  'offset', 'shift', 'color_image'] # 'statistic_all', 'phasor',  # These two have odd dimensions, and the phasor has almost but not quite one line per pixel. wtf.
    
    name, ext = os.path.splitext(path)
    for pattern in export_suffixes:
        if name.endswith('_'+pattern):
            return name.replace('_' + pattern, "")

    # If didn't find any matches, it is probably an img file:
    if ext == '.img':
        return name
    else:
        print(f"Warning: In asc_load_related: No related suffix found for {path}.", file=sys.stderr)
        print("Assuming no extension was indended and adding suffix to match.", file=sys.stderr)
    return name

def asc_load_related(path, suffix, verbose=False) -> np.ndarray:
    """ Given the name of one file in an asc file set, load the related asc file ending in suffix."""
    
    if not suffix.endswith('.asc') and not suffix.endswith('.tif') and not suffix.endswith('.txt'):
        suffix = suffix + ".asc"
    if not suffix.startswith('_'):
        suffix = '_' + suffix
    
    name = _asc_get_related_stem(path)
    return asc_load(name + suffix, verbose)
        
    # If all else fails, ValueError
    # raise ValueError("Path doesn't match known BH export endings.")

def asc_load_all_related(path, verbose) -> Dict:
    """ Given the name of one file in an asc file set, load all the related asc files that exist."""
    
    import_suffixes = ['a1', 'a2', 't1', 't2', 'a1[%]', 'a2[%]', 'chi', 'phasor_G', 'phasor_S', 'scatter', 'color coded value', 'photons', 'offset', 'shift'] # 'statistic_all', 'phasor', # These two have odd dimensions, and the phasor has almost but not quite one line per pixel. wtf.

    name = _asc_get_related_stem(path)

    # Loop through all possible data suffixes and add any that exist to dataset dict.
    dataset = {}
    for s in import_suffixes:
        fn_s = '_' + s + '.asc'
        if os.path.isfile(name + fn_s):
            dataset[s] = asc_load(name + fn_s, verbose)
    dataset.pop('statistic_all', None) # This one has a different shape
    return dataset

def threshold_mask(data, threshold_variable, min_thresh, max_thresh):
    threshold_failed = (np.array(min_thresh) > threshold_variable) | (threshold_variable > np.array(max_thresh))
    data = ma.masked_array(data, threshold_failed)
    return data

def threshold_reasonably(dataset, thresholds):
    """Apply all threshold masks to all data in a dataset."""
    first_key = list(dataset.keys())[0]
    combined_mask = np.zeros_like(dataset[first_key], dtype=bool)
    
    for tkey in thresholds:
        if tkey not in dataset:
            continue
        (min_thresh, max_thresh) = thresholds[tkey]
        threshold_failed = (np.array(min_thresh) > dataset[tkey]) | (dataset[tkey] > np.array(max_thresh))
        combined_mask = combined_mask | threshold_failed

    new_dataset = {}
    for key, data in dataset.items():
        print(key, data)
        new_dataset[key] = ma.masked_array(data, mask=combined_mask)
    return new_dataset

from scipy.signal import convolve2d
def add_binned_photons(dataset: Dict, BHbin) -> Dict:
    dataset['binned_photons'] = convolve2d(dataset['photons'],
                                           np.ones((2*BHbin+1, 2*BHbin+1)),
                                           boundary='fill',
                                           mode='same',
                                           fillvalue=0)
    return dataset

#def add_ar(dataset: Dict) -> dataset:

def asc_export_ma(path, data, invalid_value_fill, dry_run=False, verbose=False):
    try:
        if dry_run:
            print(f"Would save {data.shape} to {path}.")
        else:
            if verbose:
                print(f"Saving {data.shape} to {path} ...", end="")
            np.savetxt(path, data.filled(fill_value=invalid_value_fill))
            if verbose:
                print("Success.")
    except:
        raise
    
def asc_export_mas(pathstem, dataset, suffix, invalid_value_fill, dry_run=False, verbose=False):
    for key, data in dataset.items():
        asc_export_ma(pathstem + "_" + key + suffix, data, invalid_value_fill, dry_run, verbose)

if __name__ == "__main__":
    print("Hit main")
    parser = argparse.ArgumentParser(description="Threshold raw BH exports to limit to pixels which have sane fits.")
    parser.add_argument("input", type=str, help="Path to ASC or TIF file")
    parser.add_argument("out", type=str, help="Path to output file, or directory to output to with --suffix.")
    parser.add_argument("--bh-bin", type=int, help="BH bin size, for (re)binning photons")
    parser.add_argument("--suffix", type=str, default=".th.asc", help="Suffix for output files if --out is a directory. Default to '.th.asc'")
    parser.add_argument("--verbose", action="store_true", help="Print details of file operations.")
    parser.add_argument("--dry-run", action="store_true", help="Don't write to output files.")

    args = parser.parse_args()

    # indir = False
    # # The following top bit not written yet.
    # if indir and os.path.isdir(indir):
        
    #     free_files = sorted(list(files_non_recursively(indir, free)))
    #     bound_files = sorted(list(files_non_recursively(indir, bound)))

    #     assert(len(free_files) == len(bound_files))
    #     assert(os.path.isdir(out))
    #     for ff, bf in zip(free_files, bound_files):
    #         free = flimload(ff, args.verbose)
    #         bound = flimload(bf, args.verbose)
    #         ratio = free_bound_ratio(free, bound, args.invalid, ff)
            
    #         common_stem = os.path.commonprefix((os.path.basename(ff), os.path.basename(bf)))
    #         if common_stem[-2:] == '_a':
    #             common_stem = common_stem[:-2]
    #         else:
    #             print(f"Unexpected filenames: {ff}, {bf}, {common_stem}", file=sys.stderr)
    #         out_fn = common_stem + suffix
    #         flim_export(os.path.join(out, out_fn), ratio, args.verbose, args.dry_run)


    freq = 80 # MHz; Laser repetition frequency
    pix_dwell = 5 # us; Pixel dwell time
    frames_acc = 45 # Number of frames accumulated in this experiemnt
    min_phot_confident_fit = 3000 # Minimum number of photons for a confident fit.
    chisq_min = 0.75
    chisq_max = 1.5
    if args.bh_bin is not None:
        bin = args.bh_bin
    else:
        parser.error("--bh-bin is a required argument.")

    
    thresholds = { "a1": (0, np.inf),
                   "a2": (0, np.inf),
                   "t1": (0, np.inf),
                   "t2": (0, np.inf),
                   ## minimum for fitting is 3000 photons in binned_photons
                   ## max photons for TCSPC is 30% photon saturation at 80MHz and 5 us per pixel x 45 frames
                   "photons": (0, ((2*bin+1)**2)*0.3*freq*pix_dwell*frames_acc),
                   "chi": (chisq_min, chisq_max), # ChiSq
                   "binned_photons": (min_phot_confident_fit, np.inf)
              }

    dataset = asc_load_all_related(args.input, args.verbose)
    dataset = add_binned_photons(dataset, bin)
    dataset_th = threshold_reasonably(dataset, thresholds)

    if os.path.isdir(args.out):
        out_basename_stem = _asc_get_related_stem(os.path.basename(args.input))
        out_path_stem = os.path.join(args.out, out_basename_stem)
        asc_export_mas(out_path_stem,
                       dataset_th,
                       args.suffix,
                       np.nan,
                       args.dry_run,
                       args.verbose)
    else: 
        asc_export_mas(_asc_get_related_stem(args.out),
                       dataset_th,
                       args.suffix,
                       np.nan,
                       args.dry_run,
                       args.verbose)
