#!/usr/bin/env python3
# Bjorn 2025.10.27
# Written unassisted.
"""Load and plot multiple BH IRF files.

Depends: matplotlib, numpy

Usage:
    python compare-irfs irf1.irf irf2.irf ... --suffix "don't show suffix plot legends.irf"
"""

import matplotlib.pyplot as plt
import numpy as np
import os, sys
import argparse
from typing import List, Tuple
from itertools import combinations
from scipy import signal


def load_irf_file(path) -> Tuple[np.ndarray, np.ndarray]:
    try:
        data = np.loadtxt(path, dtype=float)
        # Load string metadata separately. It does not have type float.
        with open(path) as f:
            temp = f.readlines()
            meta = temp[-3:]
    except:
        raise
    return (data, meta)

def load_irf_files(paths:List[str]) -> Tuple[List[np.ndarray], List[np.ndarray], List[str]]:
    dataset = []
    metadataset = []
    filenames = []
    for path in paths:
        data, metadata = load_irf_file(path)
        dataset.append(data)
        metadataset.append(metadata)
        filenames.append(os.path.basename(path))
    return (dataset, metadataset, filenames)

def check_metadata(metadataset, filenames) -> None:
    """ Compare metadata between files. 
    Only warns on mismatch, because AFAIK the metadata is mostly about SPCImage version?
    """
    for (m1, f1), (m2, f2) in combinations(zip(metadataset, filenames), 2):
        if m1 != m2:
            print(f"Warning: metadata for {f1} and {f2} don't match.", file=sys.stderr)
    
def print_best_shifts(dataset, filenames, suffix=None):

    if suffix is None:
        suffix = ""
        
    # Indexed by file pair
    peakshifts = {}
    xcorrs = {}
    peak_xcorrs = {}
    weight_xcorrs = {}

    # Saving relative to the first file in filenames
    shift_dict = {}
    shift_dict['peak shift'] = []
    shift_dict['xcorr optimal shift'] = []
    shift_dict['peak only xcorr shift'] = []
    shift_dict['weighted xcorr shift'] = []

    ps = []
    xc = []
    px = []
    wx = []
    fs = []
    
    # Calculate relative shift using correlation on values exceeding 5% of maximum
    # The 5% threshold was chosen to eliminate sidebands.
    # for (d1, f1), (d2, f2) in combinations(zip(dataset, filenames), 2):
    d1 = dataset[0]
    f1 = filenames[0]
    
    for i, (d2, f2) in enumerate(zip(dataset[1:], filenames[1:]), 1):
    
        d2 /= np.max(d2)

        d3 = d1.copy()
        d4 = d2.copy()
        d3[d3 <= 0.05] = 0
        d4[d4 <= 0.05] = 0 

        weight = np.sqrt(np.abs(d1 * d2))
        d1w = d1.copy() * weight
        d2w = d2.copy() * weight
        
        # Cross-correlate; try a few methods see if they return similar results:

        bins_to_ns = 12.5/256
        
        peakshift = (np.argmax(d1) - np.argmax(d2)) * bins_to_ns

        xcorr = signal.correlate(d2, d1, mode="full")
        xcorr_lags = signal.correlation_lags(len(d2), len(d1), mode="full")
        xcorr_optimal_shift = xcorr_lags[np.argmax(xcorr)] * bins_to_ns
    
        peak_xcorr = signal.correlate(d4, d3, mode="full")
        peak_xcorr_lags = signal.correlation_lags(len(d4), len(d3), mode="full")
        peak_xcorr_optimal_shift = peak_xcorr_lags[np.argmax(peak_xcorr)] * bins_to_ns
        
        weight_xcorr = signal.correlate(d2w, d1w, mode="full")
        weight_xcorr_lags = signal.correlation_lags(len(d2w), len(d1w), mode="full")
        weight_xcorr_optimal_shift = weight_xcorr_lags[np.argmax(weight_xcorr)] * bins_to_ns
        
        print(f"# Comparing files {f1} and {f2}")
        print(f"Peak shift: {peakshift} ns")
        print(f"XCorr: {xcorr_optimal_shift} ns")
        print(f"XCorr Peak Only: {peak_xcorr_optimal_shift} ns")
        print(f"XCorr Weighted: {weight_xcorr_optimal_shift} ns")
        
        # Save values
        peakshifts[(f1, f2)] = peakshift
        xcorrs[(f1, f2)] = xcorr_optimal_shift
        peak_xcorrs[(f1, f2)] = peak_xcorr_optimal_shift
        weight_xcorrs[(f1, f2)] = weight_xcorr_optimal_shift

        shift_dict['peak shift'].append(peakshift)
        shift_dict['xcorr optimal shift'].append(xcorr_optimal_shift)
        shift_dict['peak only xcorr shift'].append(peak_xcorr_optimal_shift)
        shift_dict['weighted xcorr shift'].append(weight_xcorr_optimal_shift)

        fs.append(f2.replace(suffix, ""))
        ps.append(peakshift)
        xc.append(xcorr_optimal_shift)
        px.append(peak_xcorr_optimal_shift)
        wx.append(weight_xcorr_optimal_shift)
            
    # Print and graph the values relative to f1
    print(f"Shifts relative to {filenames[0]}:")
    for s, x, p, w, f in zip(ps, xc, px, wx, fs):
        # Why does this just print 
        print(f"{f}: {s:2f} {x:2f} {p:2f} {w:2f}")

    x_pos = list(range(len(fs)))
        
    plt.figure()
    plt.title(f"Shift relative to {filenames[0].replace(suffix, '')}")
    for i, (label, values) in enumerate(shift_dict.items()):
        plt.plot(x_pos, values, 'o-', label=label, markersize=3, alpha=0.7)
    
    plt.xlabel("Measurement date range")
    plt.ylabel("Shift (ns)")
    plt.xticks(x_pos, fs, rotation=45, ha='right')
    plt.legend()
    #plt.tight_layout()
    plt.show()


    
def plot_irfs(dataset: List[np.ndarray], filenames: List[str], suffix=None, no_legend=False):
    if suffix is None:
        suffix = ""

    plt.figure(figsize=(4,3))
    for (i, (d,f)) in enumerate(zip(dataset, filenames)):
        fn = f.replace(suffix, "")
        print(fn) # for testing only
        if np.max(d) > 0:
            d=d/np.max(d)
        else:
            continue
        plt.plot(d, label=fn, linewidth=2)
    plt.title("Normalized IRF values")
    plt.xlabel("time bin")
    if not no_legend:
        plt.legend()
    plt.xlim([0,255])
    ax1 = plt.gca()
    ax2 = plt.twiny()

    # Create a top scale in ns.
    new_scale_ticks = np.arange(0, 12.5, 0.05)
    original_scale_positions = new_scale_ticks * 256/12.5
    
    ax2.set_xlim(ax1.get_xlim())
    ax2.set_xticks(original_scale_positions)
    ax2.set_xticklabels(new_scale_ticks)
    ax2.set_xlabel("Time (ns)")
    
    plt.show()


def load_irf_file(path) -> Tuple[np.ndarray, np.ndarray]:
    try:
        data = np.loadtxt(path, dtype=float)
        # Load string metadata separately. It does not have type float.
        with open(path) as f:
            temp = f.readlines()
            meta = temp[-3:]
    except:
        raise
    return (data, meta)

def load_irf_files(paths:List[str]) -> Tuple[List[np.ndarray], List[np.ndarray], List[str]]:
    dataset = []
    metadataset = []
    filenames = []
    for path in paths:
        data, metadata = load_irf_file(path)
        dataset.append(data)
        metadataset.append(metadata)
        filenames.append(os.path.basename(path))
    return (dataset, metadataset, filenames)

    
def main():
    ap = argparse.ArgumentParser(
        description="Convert 256x256 ASCII float grids to 32-bit grayscale TIFFs (tifffile only)."
    )
    ap.add_argument("inputs", nargs="+", help="IRF files")
    ap.add_argument("--suffix", type=str, default=".irf", help="Suffix to remove from files when labelling plot.")
    ap.add_argument("--no-legend", action="store_true", help="Suppress legend. Useful when comparing >10 IRFs.")
    args = ap.parse_args()

    ds, ms, fs = load_irf_files(args.inputs)
    check_metadata(ms, fs)
    plot_irfs(ds, fs, args.suffix, args.no_legend)
    print_best_shifts(ds, fs, args.suffix)

if __name__ == "__main__":
    main()
