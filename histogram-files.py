import matplotlib.pyplot as plt
import numpy as np
import os
import re
from scipy.stats import norm, entropy # for histstats

def flimhist(asciifile, minval=0, maxval=4000, binwidth=10):
    data = np.loadtxt(asciifile)
    bins = int(round((maxval-minval)/binwidth + 1,0))
    h, b = np.histogram(data, range=[minval, maxval], bins=bins)
    return (h, b, binwidth)

def showhist(hist, bin_edges, binwidth, title=None):
    plt.figure()
    bin_centers = (bin_edges[:-1]+bin_edges[1:])/2
    plt.bar(bin_centers, h, align='center')
    if title:
        plt.title(title)
    plt.show()

def histstats(hist, bin_edges, binwidth, title=None):
    # This function written by ChatGPT5.
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    total_counts = np.sum(hist)

    # Compute mean and standard deviation from histogram
    mean = np.sum(bin_centers * hist) / total_counts
    variance = np.sum(((bin_centers - mean) ** 2) * hist) / total_counts
    stddev = np.sqrt(variance)

    print(f"mean: {mean:.2f}")
    print(f"standard deviation: {stddev:.2f}")

    # Compute cumulative distribution
    cdf = np.cumsum(hist) / total_counts

    # Interpolate percentiles
    percentiles_to_compute = [1, 5, 95, 99]
    percentile_values = np.interp([p / 100 for p in percentiles_to_compute], cdf, bin_centers)

    for p, val in zip(percentiles_to_compute, percentile_values):
        print(f"{p}th percentile: {val:.2f}")

    # Create a Gaussian curve with the same mean and std
    gaussian = norm.pdf(bin_centers, mean, stddev)
    gaussian_scaled = gaussian * (total_counts * binwidth)  # scale to match histogram area

    # Compare similarity using KL divergence
    kl_div = entropy(hist + 1e-10, gaussian_scaled + 1e-10)
    print(f"KL divergence to Gaussian: {kl_div:.4f}")

    # Optional plot
    plt.figure()
    plt.bar(bin_centers, hist, align='center', width=binwidth, alpha=0.6, label='Histogram')
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

def accumulatehists(path, suffixes):
    """Combine histograms from multiple files into a single histogram."""
    master_h = None
    print(":", end="")
    for file in filesrecursively(path, suffixes):
        if master_h is None: # first loop
            master_h, control_b, control_binwidth = flimhist(file, 0, 4000)
        else:
            h, b, _ = flimhist(file, 0, 4000)
            if np.all(b==control_b):
                master_h += h
                print(".", end="")
    print(":")
    return (master_h, control_b, control_binwidth)


h, b, w = accumulatehists(r"C:\Users\lociuser\Desktop\s96-exet-fitet-sz-b3", "t2.asc")
showhist(h, b, w)
histstats(h[5:], b[5:], w)

