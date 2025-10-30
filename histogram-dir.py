import matplotlib.pyplot as plt
import numpy as np
import os, sys
import re
import argparse
from scipy.stats import norm, entropy # for histstats
from concurrent.futures import ProcessPoolExecutor, as_completed # for parallelization

def flimhist(asciifile, minval=0, maxval=4000, binwidth=10):
    data = np.fromfile(asciifile, sep=' ', dtype="float32")
    bins = int(round((maxval-minval)/binwidth + 1,0))
    h, b = np.histogram(data, range=[minval, maxval], bins=bins)
    return (h, b, binwidth) # b is the bin edges array.

def ratiohist(asciifile, minval=0, maxval=4000, binwidth=0.01):
    """ Provides a logarithmic (base 10) histogram for free-bound ratios.
    Note that the bin array returned is an edges array."""
    data = np.fromfile(asciifile, sep=' ', dtype="float32")
    if minval is None:
        minval = np.min(np.min(data))
    if maxval is None:
        maxval = np.max(np.max(data))
    minval = np.log10(minval) if minval > 0 else np.log10(1e-16)
    maxval = np.log10(maxval) if maxval > 0 else np.log10(1e-16)
    data = np.log10(data)
    bins = int(round((maxval-minval)/binwidth + 1,0)) 
    h, b = np.histogram(data, range=[minval, maxval], bins=bins)
    return (h, b, binwidth) # b is the bin edges array.

def showhist(hist, bin_edges, binwidth, title=None, zero_cutoff=None):
    plt.figure()
    bin_centers = (bin_edges[:-1]+bin_edges[1:])/2
    bin_widths = np.diff(bin_edges) # We have actually calculate them given the potential for nonlinear bins.
    if zero_cutoff is not None:
            mask = bin_centers > zero_cutoff
            hist = hist[mask]
            bin_widths = bin_widths[mask]
            bin_centers = bin_centers[mask]
            
            left_edge = bin_centers[0] - bin_widths[0]/2
            right_edges = bin_centers + bin_widths/2
            bin_edges = np.concatenate([[left_edge], right_edges])
        
    plt.bar(bin_centers, hist, width=binwidth, align='center')
    plt.xlabel("Value")
    plt.ylabel("Frequency")
    if title:
        plt.title(title)
    plt.show()

def savehistplot(fn, hist, bin_edges, binwidth, title=None, zero_cutoff=None):
    print("Warning: savehistplot never tested.", file=sys.stderr)
    plt.figure()
    bin_centers = (bin_edges[:-1]+bin_edges[1:])/2
    bin_widths = np.diff(bin_edges) # We have actually calculate them given the potential for nonlinear bins.
    if zero_cutoff is not None:
            mask = bin_centers > zero_cutoff
            hist = hist[mask]
            bin_widths = bin_widths[mask]
            bin_centers = bin_centers[mask]
            
            left_edge = bin_centers[0] - bin_widths[0]/2
            right_edges = bin_centers + bin_widths/2
            bin_edges = np.concatenate([[left_edge], right_edges])
    plt.bar(bin_centers, hist, width=binwidth, align='center')
    if title:
        plt.title(title)
    plt.xlabel("Value")
    plt.ylabel("Frequency")
    plt.savefig(fn)

def exp10(ar: np.ndarray) -> np.ndarray:
    return np.exp(ar*np.log(10))
    
def histstats(hist, bin_edges, binwidth, title=None, zero_cutoff=None, log_repeat=False, saveas=None):
    if saveas is None:
        outfile=sys.stdout
        display_figures=True
    else:
        if os.path.exists(saveas):
            print(f"Warning: clobbering {saveas}", sys.stderr)
        display_figures=False
        try:
            outfile = open(saveas, 'w')
        except:
            raise

    try:
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        bin_widths = np.diff(bin_edges)
    
        if zero_cutoff is not None:
            mask = bin_centers > zero_cutoff
            hist = hist[mask]
            bin_widths = bin_widths[mask]
            bin_centers = bin_centers[mask]
            
            left_edge = bin_centers[0] - bin_widths[0]/2
            right_edges = bin_centers + bin_widths/2
            bin_edges = np.concatenate([[left_edge], right_edges])
        
        total_counts = np.sum(hist)

        # Compute mean and standard deviation from histogram
        mean = np.sum(bin_centers * hist) / total_counts
        variance = np.sum(((bin_centers - mean) ** 2) * hist) / total_counts
        stddev = np.sqrt(variance)

        print(f"mean: {mean:.2f}", file=outfile)
        print(f"standard deviation: {stddev:.2f}", file=outfile)

        # Compute cumulative distribution
        cdf = np.cumsum(hist) / total_counts

        # Interpolate percentiles
        percentiles_to_compute = [1, 5, 95, 99]
        percentile_values = np.interp([p / 100 for p in percentiles_to_compute], cdf, bin_centers)

        for p, val in zip(percentiles_to_compute, percentile_values):
            print(f"{p}th percentile: {val:.2f}", file=outfile)

        # Create a Gaussian curve with the same mean and std
        gaussian_scaled = norm.pdf(bin_centers, mean, stddev)
        gaussian_scaled *= np.sum(hist*bin_widths) / np.sum(gaussian_scaled * bin_widths) #Normalize by volume

        # Compare similarity using KL divergence
        kl_div = entropy(hist + 1e-10, gaussian_scaled + 1e-10)
        print(f"KL divergence to Gaussian: {kl_div:.4f}", file=outfile)

        # Optional plot
        if display_figures:
            plt.figure()
            plt.bar(bin_centers, hist, align='center', width=bin_widths, alpha=0.6, label='Histogram')
            plt.plot(bin_centers, gaussian_scaled, 'r-', label='Gaussian Fit')

            # Add vertical lines for percentiles
            for p, val in zip(percentiles_to_compute, percentile_values):
                plt.axvline(val, linestyle='--', label=f'{p}th percentile')

            plt.xlabel('Value')
            plt.ylabel('Frequency')
            if title:
                plt.title(title)
            plt.legend()
            plt.show()

        if log_repeat: #repeat everything with the exponential of the histogram
            print(f"exponential of mean: {exp10(mean):.2f}", file=outfile)
            print(f"exponential of standard deviation: {exp10(stddev):.2f}", file=outfile)
            for p, val in zip(percentiles_to_compute, percentile_values):
                print(f"exponential of {p}th percentile: {exp10(val):.2f}", file=outfile)

    except:
        raise
    finally:
        if outfile is not sys.stdout:
            outfile.close()
        
def files_recursively(path, suffixes):
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
    """ Returns an lazy generator over files matching suffixes in path.
    path: the root directory
    Suffixes: a string or iterator of strings.

    Result: Yields the path to the matching files.
    """
    for file in os.listdir(dirpath):
        if file.endswith(suffixes):
            yield os.path.join(dirpath, file)

def accumulatehists(dirpath, suffixes):
    """Combine histograms from multiple files into a single histogram."""
    master_h = None
    print(":", end="")
    for file in files_recursively(dirpath, suffixes):
        if master_h is None: # first loop
            master_h, control_b, control_binwidth = flimhist(file, 0, 4000)
        else:
            h, b, _ = flimhist(file, 0, 4000)
            if np.all(b==control_b):
                master_h += h
                print(".", end="")
    print(":")
    if type(suffixes)==type("string"):
        writehists(dirpath, "combined_" + suffixes)
    return (master_h, control_b, control_binwidth)

def process_file(file):
    try:
        h, _, _ = flimhist(file, 0, 4000)
        return h
    except Exception as e:
        print(f"Error processing {file}: {e}")
        return None

def process_file_log(file):
    try:
        h, _, _ = ratiohist(file, 0, 4000)
        return h
    except Exception as e:
        print(f"Error processing {file}: {e}")
        return None
    
def accumulatehists_parallel(dirpath, suffixes, recursive, log):
    if recursive:
        print("We are recursive")
        files = list(files_recursively(dirpath, suffixes))
    else:
        print("We are not recursive")
        files = list(files_non_recursively(dirpath, suffixes))

    if len(files) == 0:
        raise ValueError("Empty files array in accumulatehists_parallel. Do any files match suffix?")

    if not log:
        _, bins, width = flimhist(files[0], 0, 4000)
    else: # log:
        _, bins, width = ratiohist(files[0], 0, 4000)
    total_hist = None

        
    with ProcessPoolExecutor() as executor:
        if not log:
            futures = {executor.submit(process_file, file): file for file in files}
        else: #log
            futures = {executor.submit(process_file_log, file): file for file in files}
        for future in as_completed(futures):
            result = future.result()
            if result is not None:
                if total_hist is None:
                    total_hist = result
                else:
                    total_hist += result
                print(".", end="")
    print(":")
    return total_hist, bins, width

def savehist(filepath, hist, bins, width, zero_cutoff=None):
    if zero_cutoff is not None:
        print("Warning: savehist doesn't take zero_cutoff yet. Full range is being saved.", file=sys.stderr)
    np.savetxt(filepath + ".hist", hist)
    np.savetxt(filepath + ".bins", bins)
    np.savetxt(filepath + ".width", width)
    
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge data from directory into a single histogram, (optionally) plot and save plot or binned data.")
    parser.add_argument("directory", help="Path from which to recursively search.")
    parser.add_argument("--recursive", "-r", action="store_true", help="Recurse into subdirectories, otherwise only process top level.")
    parser.add_argument("--suffix", type=str, help="Suffix to consider for input files.")
    parser.add_argument("--suffixes", type=str, help="Suffixes to consider for input files.")
    parser.add_argument("--saveplot", type=str, help="File for saving plot.")
    parser.add_argument("--savehist", type=str, help="File for saving histogram data.")
    parser.add_argument("--showplot", action="store_true", help="Interactively show histogram plot.")
    parser.add_argument("--log", action="store_true", help="Histogram log of values instead of values. Useful for free-bound ratios.")
    parser.add_argument("--zero_cutoff", type=float, help="Cutoff value for lower end of histogram (use to filter out zero values)")
    parser.add_argument("--text-output", type=str, help="Store statistical summary in the specified text file.")
    parser.add_argument("--title", type=str, help="Graph title")

    args = parser.parse_args()

    if args.suffixes:
        suffix = args.suffixes
        suffix = suffix.split(" ")
    elif args.suffix:
        suffix = args.suffix
    else:
        suffix = "_color coded value.asc"

    h, b, w = accumulatehists_parallel(args.directory, suffix, args.recursive, args.log)

    if args.showplot:
        showhist(h, b, w, title=args.title, zero_cutoff=args.zero_cutoff)
    if args.saveplot:
        try:
            savehistplot(args.saveplot, h, b, w, zero_cutoff=args.zero_cutoff)
        except:
            raise
        
    if args.savehist:
        try:
            savehist(args.savehist, h, b, w, zero_cutoff=args.zero_cutoff)
        except:
            raise

    if args.zero_cutoff:
        histstats(h, b, w, zero_cutoff=args.zero_cutoff, log_repeat=args.log, title=args.title, saveas=args.text_output)
    else:
        histstats(h, b, w, log_repeat=args.log, title=args.title, saveas=args.text_output)
