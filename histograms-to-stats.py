#!/usr/bin/env python3
# Claude Opus prompted by Bjorn, 2025.10.30.
"""
Histogram Analysis Script
Processes histogram data files to calculate mean and standard deviation,
plot histograms with Gaussian fits, and output statistics in CSV format.
"""

import argparse
import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


def load_histogram_data(filename):
    """
    Load histogram data from a file.
    Expects data in format: bin_center value (two columns)
    """
    try:
        # Load data expecting two columns: bin_center, value
        data = np.loadtxt(filename, delimiter=",", skiprows=1)
        if data.ndim == 1:
            print(f"Error: {filename} appears to have only one column. Expected format: bin_center value", file=sys.stderr)
            return None, None
        if data.shape[1] != 2:
            print(f"Error: {filename} has {data.shape[1]} columns. Expected format: bin_center value", file=sys.stderr)
            return None, None
        bin_centers = data[:, 0]
        values = data[:, 1]
        return bin_centers, values
    except Exception as e:
        print(f"Error loading {filename}: {e}", file=sys.stderr)
        return None, None


def threshold_histogram(bin_centers, values, lower_percentile=1, upper_percentile=99):
    """
    Remove outliers from histogram data using percentile thresholding.
    Percentiles are calculated on the expanded data (reconstructed from histogram).
    """
    # Reconstruct data points from histogram for percentile calculation
    expanded_data = np.repeat(bin_centers, values.astype(int))
    
    if len(expanded_data) == 0:
        return bin_centers, values
    
    lower_bound = np.percentile(expanded_data, lower_percentile)
    upper_bound = np.percentile(expanded_data, upper_percentile)
    
    # Filter the histogram based on bounds
    mask = (bin_centers >= lower_bound) & (bin_centers <= upper_bound)
    return bin_centers[mask], values[mask]

def parabolic_peak_x(x, y, i):
    """
    Sub-bin peak location using a 3-point quadratic fit around index i.
    Returns x_peak. Falls back to x[i] at edges or degenerate cases.
    """
    if i <= 0 or i >= len(y)-1:
        return x[i]
    y1, y2, y3 = y[i-1], y[i], y[i+1]
    denom = (y1 - 2*y2 + y3)
    if denom == 0:
        return x[i]
    # Offset (in bins) of the vertex relative to i
    delta = 0.5 * (y1 - y3) / denom
    # Convert that offset into x-units (assume quasi-uniform centers)
    if len(x) > 1:
        dx = 0.5*(x[min(i+1,len(x)-1)] - x[max(i-1,0)])
    else:
        dx = 0.0
    return x[i] + delta * dx

def mode_from_hist_smooth(bin_centers, values, bandwidth=None):
    """
    Smooth the histogram with a Gaussian kernel (in bin space),
    take the argmax, then refine with a local quadratic fit.
    """
    # Handle empty histogram
    if np.sum(values) == 0:
        return float('nan')

    # Estimate bin width (robust to minor jitter)
    if len(bin_centers) > 1:
        bin_width = np.median(np.diff(bin_centers))
    else:
        bin_width = 1.0

    # Choose a reasonable smoothing bandwidth if not provided
    # Rule of thumb: ~1–2 bin widths usually works well
    if bandwidth is None:
        bandwidth = 1.5 * bin_width

    # Convert bandwidth (x-units) to sigma in "bins"
    sigma_bins = max(bandwidth / bin_width, 1e-6)

    # Smooth counts via discrete Gaussian convolution
    # (no SciPy needed; this is a simple manual kernel)
    half = int(np.ceil(4 * sigma_bins))  # truncate at ~4 sigma
    kx = np.arange(-half, half+1)
    kernel = np.exp(-0.5 * (kx / sigma_bins)**2)
    kernel /= kernel.sum()

    y_smooth = np.convolve(values, kernel, mode='same')

    # Peak index
    i_max = int(np.argmax(y_smooth))

    # Sub-bin refinement
    return parabolic_peak_x(bin_centers, y_smooth, i_max)



def calculate_statistics(bin_centers, values):
    """
    Calculate mean and standard deviation from histogram data.
    """
    # Normalize values to get probabilities
    total = np.sum(values)
    if total == 0:
        return 0, 0
    probabilities = values / total
    
    # Calculate mean (expected value)
    mean = np.sum(bin_centers * probabilities)
    
    # Calculate variance and standard deviation
    variance = np.sum(probabilities * (bin_centers - mean)**2)
    stdev = np.sqrt(variance)
    
    return mean, stdev

def calculate_statistics_multi(bin_centers, values, *, smoothed_bandwidth=None, return_dict=False):
    """
    Calculate mean, stdev, median, mode (raw peak, sub-bin), and peak (smoothed, sub-bin)
    from histogram data given bin centers and counts/heights.

    Parameters
    ----------
    bin_centers : array-like
        Histogram bin centers (not edges).
    values : array-like
        Histogram counts or weights for each bin.
    smoothed_bandwidth : float or None
        Optional bandwidth (in x-units) forwarded to mode_from_hist_smooth.
        If None, that function's default heuristic is used.
    return_dict : bool
        If True, return a dict with named fields; otherwise return a tuple:
        (mean, stdev, median, mode, peak)

    Returns
    -------
    tuple or dict
        mean, stdev, median, mode (raw), peak (smoothed)

    This code courtesy of GPT-5 Thinking. Sanity checked manually.
    """
    x = np.asarray(bin_centers, dtype=float)
    y = np.asarray(values, dtype=float)

    # Clean NaNs and sort by x to ensure monotonic centers
    m = np.isfinite(x) & np.isfinite(y)
    x = x[m]
    y = y[m]
    if x.size == 0 or np.nansum(y) <= 0:
        out = (np.nan, np.nan, np.nan, np.nan, np.nan)
        if return_dict:
            return {"mean": np.nan, "stdev": np.nan, "median": np.nan,
                    "mode": np.nan, "peak": np.nan}
        return out

    order = np.argsort(x)
    x = x[order]
    y = y[order]
    total = np.sum(y)

    # Probabilities
    p = y / total

    # Mean & stdev (as you had)
    mean = np.sum(x * p)
    variance = np.sum(p * (x - mean) ** 2)
    stdev = np.sqrt(variance)

    # Median (weighted) via CDF interpolation on sorted x
    cdf = np.cumsum(y) / total
    # Drop flat CDF plateaus to keep interpolation well-defined
    keep = np.concatenate(([True], np.diff(cdf) > 0))
    if keep.sum() >= 2:
        median = np.interp(0.5, cdf[keep], x[keep])
    else:
        # Degenerate case: all mass in one bin
        median = x[np.argmax(y)]

    # Mode from RAW histogram (sub-bin refinement around the max)
    i_raw = int(np.argmax(y))
    try:
        mode_raw = parabolic_peak(x, y, i_raw)  # provided by you earlier
    except Exception:
        mode_raw = x[i_raw]

    # Peak from SMOOTHED histogram (Gaussian smoothed + sub-bin refinement)
    try:
        peak_smooth = mode_from_hist_smooth(x, y, bandwidth=25*smoothed_bandwidth)  # provided by you earlier
    except Exception:
        # Fallback to raw mode if smoothing helper isn't available
        peak_smooth = mode_raw

    if return_dict:
        return {
            "mean": float(mean),
            "stdev": float(stdev),
            "median": float(median),
            "mode": float(mode_raw),     # raw-hist peak (parabolic)
            "peak": float(peak_smooth),  # smoothed peak (parabolic)
        }
    else:
        return float(mean), float(stdev), float(median), float(mode_raw), float(peak_smooth)

def gaussian(x, mean, stdev):
    """
    Gaussian/Normal distribution function.
    """
    if stdev == 0:
        return np.zeros_like(x)
    return (1 / (stdev * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - mean) / stdev) ** 2)


def plot_histogram_with_fit(bin_centers, values, mean, stdev, filename, median=None, mode=None, peak=None, save_plot=True, output_dir=None):
    """
    Plot histogram data with Gaussian fit overlay.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Calculate bin width (assuming uniform spacing)
    if len(bin_centers) > 1:
        bin_width = bin_centers[1] - bin_centers[0]
    else:
        bin_width = 1
    
    # Plot histogram as bar chart
    ax.plot(bin_centers, values, alpha=0.7, 
            color='black', label='Data')
    
    # Create Gaussian fit scaled to match histogram
    x_fit = np.linspace(bin_centers.min() - 2*stdev, bin_centers.max() + 2*stdev, 1000)
    # Scale Gaussian to match the histogram's total area
    total_area = np.sum(values) * bin_width
    y_fit = gaussian(x_fit, mean, stdev) * total_area
    ax.plot(x_fit, y_fit, 'r-', linewidth=2, label=f'Gaussian fit\nμ={mean:.3f}, σ={stdev:.3f}')

    max_y = np.max(values)
    if median: # Draw a vertical line at median.
        ax.vlines(median, 0, max_y*1.1, label="Median", color="red")
    if mode: # Draw a vertical line at identified mode.
        ax.vlines(mode, 0, max_y*1.1, label="Mode", color="orange")
    if peak: # Draw a vertical line at identified peak.
        ax.vlines(peak, 0, max_y*1.1, label="Peak", color="blue")
    
    # Formatting
    ax.set_xlabel('Value', fontsize=12)
    ax.set_ylabel('Count', fontsize=12)
    ax.set_title(f'Histogram: {os.path.basename(os.path.dirname(filename))}', fontsize=14)
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_plot:
        if output_dir:
            plot_filename = os.path.join(output_dir, 
                                        f"{os.path.splitext(os.path.basename(filename))[0]}_histogram.png")
        else:
            plot_filename = f"{os.path.splitext(filename)[0]}_histogram.png"
        plt.savefig(plot_filename, dpi=150, bbox_inches='tight')
        print(f"Plot saved: {plot_filename}", file=sys.stderr)
    
    return fig

def main():
    parser = argparse.ArgumentParser(description='Analyze histogram data from files')
    parser.add_argument('--input', '-i', nargs='+', required=True,
                       help='Input file(s) containing histogram data (format: bin_center value)')
    parser.add_argument('--threshold', '-t', action='store_true',
                       help='Apply threshold to remove outliers before calculating statistics')
    parser.add_argument('--lower-percentile', type=float, default=1,
                       help='Lower percentile for thresholding (default: 1)')
    parser.add_argument('--threshold-min', type=float, default=0,
                        help='Minimum absolute value for thresholding.')
    parser.add_argument('--upper-percentile', type=float, default=99,
                       help='Upper percentile for thresholding (default: 99)')
    parser.add_argument('--no-plot', action='store_true',
                       help='Disable plotting (only output statistics)')
    parser.add_argument('--output-dir', '-o', type=str,
                       help='Directory to save plots (default: same as input files)')
    parser.add_argument('--show-plots', action='store_true',
                       help='Display plots interactively')
    parser.add_argument('--save-plots', action='store_true',
                        help='Save plots.')
    parser.add_argument('--combine-pdf', action='store_true',
                        help='Save all plots in a single PDF file') # Never tested and I don't trust Claude.
#     parser.add_argument('--write-stats', type=str, help="CSV file to write summary statistics to. Currently of the format filename, mean, stdev.") Can get this output from stdout.
    
    args = parser.parse_args()
    
    # Prepare output directory if specified
    if args.output_dir and not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
    
    # Print CSV header
    print("filename,mean,stdev,median,mode,peak_smooth")
    
    # Prepare PDF if combining plots
    pdf_pages = None
    if not args.no_plot and args.combine_pdf:
        pdf_filename = os.path.join(args.output_dir if args.output_dir else '.', 
                                   'histogram_analysis.pdf')
        pdf_pages = PdfPages(pdf_filename)
        print(f"Creating combined PDF: {pdf_filename}", file=sys.stderr)
    
    # Process each input file
    results = []
    figures = []
    
    for input_file in args.input:
        if not os.path.exists(input_file):
            print(f"Warning: File {input_file} not found, skipping...", file=sys.stderr)
            continue
        
        # Load histogram data
        bin_centers, values = load_histogram_data(input_file)
        if bin_centers is None or values is None:
            continue
        
        # Apply thresholding if requested
        if args.threshold:
            original_sum = np.sum(values)
            bin_centers, values = threshold_histogram(bin_centers, values, 
                                                     args.lower_percentile, 
                                                     args.upper_percentile)
            removed_sum = original_sum - np.sum(values)
            if original_sum > 0:
                print(f"Thresholding {input_file}: removed {removed_sum/original_sum*100:.1f}% of data", 
                      file=sys.stderr)
        
        # Calculate statistics
        mean, stdev, median, mode, peak = calculate_statistics_multi(bin_centers, values)
        
        # Output results in CSV format
        print(f"{input_file},{mean:.6f},{stdev:.6f},{median:.6f},{mode:.6f},{peak:.6f}")
        results.append((input_file, mean, stdev, median, mode, peak))
        
        # Create plot if requested
        if not args.no_plot:
            fig = plot_histogram_with_fit(bin_centers, values, mean, stdev, input_file, median=median, mode=mode, peak=peak,
                                          save_plot=(args.save_plots or not args.combine_pdf),
                                          output_dir=args.output_dir)
            
            figures.append(fig)
            
            if pdf_pages:
                pdf_pages.savefig(fig, bbox_inches='tight')
    
    # Finalize PDF if combining
    if pdf_pages:
        pdf_pages.close()
        print(f"Combined PDF saved: {pdf_filename}", file=sys.stderr)
    
    # Show plots if requested
    if args.show_plots and not args.no_plot:
        plt.show()
    else:
        # Close all figures to free memory
        for fig in figures:
            plt.close(fig)
            
    # Summary statistics
    if len(results) > 1:
        means = [r[1] for r in results]
        stdevs = [r[2] for r in results]
        medians = [r[3] for r in results]
        modes = [r[4] for r in results]
        peaks = [r[5] for r in results]
        
        print(f"\nSummary statistics across all files:", file=sys.stderr)
        print(f"Mean of means: {np.mean(means):.6f}", file=sys.stderr)
        print(f"Std of means: {np.std(means):.6f}", file=sys.stderr)
        print(f"Mean of stdevs: {np.mean(stdevs):.6f}", file=sys.stderr)
        print(f"Mean of medians: {np.mean(medians):.6f}", file=sys.stderr)
        print(f"Std of medians: {np.mean(medians):.6f}", file=sys.stderr)
        print(f"Mean of modes: {np.mean(modes):.6f}", file=sys.stderr)
        print(f"Std of modes: {np.mean(modes):.6f}", file=sys.stderr)
        print(f"Mean of peaks: {np.mean(peaks):.6f}", file=sys.stderr)
        print(f"Std of peaks: {np.mean(peaks):.6f}", file=sys.stderr)
        
        
if __name__ == "__main__":
    main()


    
