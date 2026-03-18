#!/usr/bin/env python3
"""
Compute per-image summary statistics from thresholded .asc files and
produce boxplots grouped by date, sample, slide, or custom groupings.

Parses structured filenames of the form:
    {date}-S{slide}-{sample}_{position}_{...conditions...}_ar.th.asc
    {date}-S{slide}-{sample}_{position}_{...conditions...}_color coded value.th.asc

Examples:
    0302-S01-DKO_C8_001_..._ar.th.asc
    0305-S12-KPC_WT_002_..._color coded value.th.asc

Usage:
    # Per-image boxplots grouped by sample:
    python asc-stats-boxplot.py ../KPC_combined/t-ar/ --suffix "_ar.th.asc" --group-by sample

    # Color points by acquisition date:
    python asc-stats-boxplot.py ../KPC_combined/t-ar/ --suffix "_ar.th.asc" --group-by sample --color-by date

    # Generate annotation template for manual alive/dead scoring:
    python asc-stats-boxplot.py ../KPC_combined/t-ar/ --suffix "_ar.th.asc" --generate-annotation-template annotations.csv

    # Use annotations to color by alive/dead:
    python asc-stats-boxplot.py ../KPC_combined/t-ar/ --suffix "_ar.th.asc" --group-by sample --color-by alive_dead --annotations annotations.csv

    # Per-slide boxplots (median of image medians) grouped by sample:
    python asc-stats-boxplot.py ../KPC_combined/t-ar/ --suffix "_ar.th.asc" --group-by sample --aggregate-by slide

    # Check for date confounders:
    python asc-stats-boxplot.py ../KPC_combined/t-ar/ --suffix "_ar.th.asc" --group-by date

    # Save CSV for further analysis:
    python asc-stats-boxplot.py ../KPC_combined/t-ar/ --suffix "_ar.th.asc" --csv-output stats.csv

    # Mean lifetime instead of free-bound ratio:
    python asc-stats-boxplot.py ../KPC_combined/t-tm/ --suffix "_color coded value.th.asc" --group-by sample
"""

import argparse
import os
import sys
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


def parse_filename(basename):
    """
    Parse a structured filename into metadata fields.

    Expected format: {date}-S{slide}-{sample}_{position}_{...}_{datatype}.th.asc
    where sample may contain underscores (e.g., DKO_C8, KPC_WT, BKO_CO2).

    Returns a dict with keys: date, slide, sample, position, or None if parsing fails.
    """
    # Match: date-Sslide-sample_NNN_ (where sample can contain underscores,
    # and position is a 3-digit number)

    # Try hyphen-delimited format: 0305-S10-BKO_CO2_001_...
    m = re.match(r'^(\d{4})-S(\d+)-(.+?)_(\d{3})_', basename)
    
    # Fall back to underscore-delimited format: 0305_S10_BKO_CO2_001_...
    if not m:
        m = re.match(r'^(\d{4})_S(\d+)_(.+?)_(\d{3})_', basename)
        


    
    if m:
        return {
            'date': m.group(1),
            'slide': f"S{m.group(2)}",
            'sample': m.group(3),
            'position': m.group(4),
            'date_slide': f"{m.group(1)}-S{m.group(2)}",
        }

    # Fallback: try to extract what we can
    print(f"Warning: Could not parse filename: {basename}", file=sys.stderr)
    return {
        'date': 'unknown',
        'slide': 'unknown',
        'sample': 'unknown',
        'position': 'unknown',
        'date_slide': 'unknown',
    }


def load_asc_stats(filepath):
    """
    Load a thresholded .asc file and compute summary statistics,
    ignoring NaN values.

    Returns a dict with mean, median, std, n_valid, n_total, fraction_valid.
    """
    try:
        data = np.loadtxt(filepath)
    except Exception as e:
        print(f"Error loading {filepath}: {e}", file=sys.stderr)
        return None

    flat = data.ravel()
    valid = flat[np.isfinite(flat)]

    if len(valid) == 0:
        return {
            'mean': np.nan,
            'median': np.nan,
            'std': np.nan,
            'n_valid': 0,
            'n_total': len(flat),
            'fraction_valid': 0.0,
        }

    return {
        'mean': float(np.mean(valid)),
        'median': float(np.median(valid)),
        'std': float(np.std(valid)),
        'n_valid': len(valid),
        'n_total': len(flat),
        'fraction_valid': len(valid) / len(flat),
    }


def find_files(directory, suffix, include=None, exclude=None):
    """Find files in directory matching suffix, with optional include/exclude filters."""
    files = []
    for f in sorted(os.listdir(directory)):
        if not f.endswith(suffix):
            continue
        if include and not any(pat in f for pat in include):
            continue
        if exclude and any(pat in f for pat in exclude):
            continue
        files.append(os.path.join(directory, f))
    return files


def build_dataframe(directory, suffix, include=None, exclude=None, verbose=False):
    """
    Scan directory for matching files, compute per-image stats,
    parse filenames, and return a DataFrame.
    """
    files = find_files(directory, suffix, include=include, exclude=exclude)
    if not files:
        print(f"No files found in {directory} matching suffix '{suffix}'", file=sys.stderr)
        sys.exit(1)

    rows = []
    for filepath in files:
        basename = os.path.basename(filepath)
        if verbose:
            print(f"  Processing: {basename}", file=sys.stderr)

        meta = parse_filename(basename)
        stats = load_asc_stats(filepath)
        if stats is None:
            continue

        row = {'filename': basename, **meta, **stats}
        rows.append(row)

    df = pd.DataFrame(rows)
    print(f"Loaded {len(df)} images from {directory}", file=sys.stderr)
    return df


def make_boxplot(df, group_col, value_col='median', color_col=None,
                 title=None, ylabel=None,
                 aggregate_by=None, save_fig=None, dpi=150):
    """
    Create a boxplot of value_col grouped by group_col, optionally
    coloring scatter points by color_col.

    If aggregate_by is specified, first compute the median of value_col
    within each (group_col, aggregate_by) combination, then boxplot
    those aggregated values. E.g., aggregate_by='date_slide' gives
    per-slide medians boxplotted by sample.
    """
    plot_df = df.copy()

    if aggregate_by:
        # When aggregating, preserve the color column if possible
        # (take the most common value within each group)
        agg_dict = {value_col: 'median'}
        if color_col and color_col in plot_df.columns:
            agg_dict[color_col] = 'first'
        plot_df = (plot_df.groupby([group_col, aggregate_by])
                   .agg(agg_dict)
                   .reset_index())
        agg_label = f" (per-{aggregate_by} median)"
    else:
        agg_label = " (per-image)"

    # Sort groups for consistent ordering
    group_order = sorted(plot_df[group_col].unique())

    fig, ax = plt.subplots(figsize=(max(8, len(group_order) * 1.5), 6))

    # Violin + box (no fill, just outlines for structure)
    sns.violinplot(data=plot_df, x=group_col, y=value_col,
                   order=group_order, ax=ax, inner=None,
                   color='lightgray', alpha=0.3, linewidth=0.5)
    sns.boxplot(data=plot_df, x=group_col, y=value_col,
                order=group_order, ax=ax,
                boxprops=dict(facecolor='none', edgecolor='black'),
                whiskerprops=dict(color='black'),
                medianprops=dict(color='red', linewidth=1.5),
                capprops=dict(color='black'),
                showfliers=False, width=0.3)

    # Scatter points, colored by color_col if provided
    if color_col and color_col in plot_df.columns:
        color_values = sorted(plot_df[color_col].dropna().unique())
        palette = sns.color_palette('tab10', n_colors=len(color_values))
        color_map = dict(zip(color_values, palette))

        for i, group in enumerate(group_order):
            group_data = plot_df[plot_df[group_col] == group]
            # Jitter x positions
            jitter = np.random.default_rng(42).uniform(-0.15, 0.15, size=len(group_data))
            colors = [color_map.get(v, 'gray') for v in group_data[color_col]]
            ax.scatter(i + jitter, group_data[value_col],
                       c=colors, s=20, alpha=0.7, edgecolors='none', zorder=5)

        # Legend for colors
        from matplotlib.patches import Patch
        legend_handles = [Patch(facecolor=color_map[v], label=str(v))
                          for v in color_values]
        ax.legend(handles=legend_handles, title=color_col.replace('_', ' ').title(),
                  loc='best', fontsize=9)
    else:
        sns.swarmplot(data=plot_df, x=group_col, y=value_col,
                      order=group_order, ax=ax, color='black', alpha=0.5, size=4)

    # Sample counts
    counts = plot_df.groupby(group_col)[value_col].count()
    labels = [f'{g}\n(n={counts.get(g, 0)})' for g in group_order]
    ax.set_xticks(range(len(group_order)))
    ax.set_xticklabels(labels)

    if title:
        ax.set_title(title + agg_label, fontsize=13, fontweight='bold')
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=12)
    ax.set_xlabel(group_col.replace('_', ' ').title(), fontsize=12)
    ax.yaxis.grid(True, linestyle='--', alpha=0.7)
    ax.set_axisbelow(True)

    plt.tight_layout()

    # Print summary
    print(f"\nSummary ({group_col}{agg_label}):", file=sys.stderr)
    print("-" * 50, file=sys.stderr)
    for g in group_order:
        gdata = plot_df[plot_df[group_col] == g][value_col]
        print(f"  {g}: n={len(gdata)}, "
              f"median={gdata.median():.4f}, "
              f"mean={gdata.mean():.4f}, "
              f"std={gdata.std():.4f}", file=sys.stderr)

    if save_fig:
        fig.savefig(save_fig, dpi=dpi, bbox_inches='tight')
        print(f"Plot saved: {save_fig}", file=sys.stderr)

    return fig, ax


def main():
    parser = argparse.ArgumentParser(
        description='Compute per-image stats from thresholded .asc files and generate boxplots.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Boxplot of free-bound ratio by sample:
  %(prog)s ../KPC_combined/t-ar/ --suffix "_ar.th.asc" --group-by sample

  # Boxplot of mean lifetime by sample, aggregated per slide:
  %(prog)s ../KPC_combined/t-tm/ --suffix "_color coded value.th.asc" --group-by sample --aggregate-by date_slide

  # Check for date confounders:
  %(prog)s ../KPC_combined/t-ar/ --suffix "_ar.th.asc" --group-by date

  # NADH only:
  %(prog)s ../KPC_combined/t-ar/ --suffix "_ar.th.asc" --group-by sample --include 457

  # Save stats CSV:
  %(prog)s ../KPC_combined/t-ar/ --suffix "_ar.th.asc" --csv-output ar_stats.csv
        '''
    )

    parser.add_argument('directory', help='Directory containing thresholded .asc files')
    parser.add_argument('--suffix', required=True,
                        help='File suffix to match (e.g., "_ar.th.asc" or "_color coded value.th.asc")')
    parser.add_argument('--group-by', default='sample',
                        choices=['sample', 'date', 'slide', 'date_slide'],
                        help='Grouping variable for boxplot (default: sample)')
    parser.add_argument('--aggregate-by', default=None,
                        choices=['slide', 'date_slide', 'date'],
                        help='Aggregate images within this grouping before boxplotting. '
                             'E.g., --aggregate-by date_slide gives per-slide medians.')
    parser.add_argument('--value', default='median',
                        choices=['median', 'mean'],
                        help='Summary statistic to plot (default: median)')
    parser.add_argument('--include', nargs='+',
                        help='Only include files containing these substrings (e.g., 457 for NADH)')
    parser.add_argument('--exclude', nargs='+',
                        help='Exclude files containing these substrings')
    parser.add_argument('--csv-output', help='Save per-image stats to CSV')
    parser.add_argument('--save-fig', help='Save plot to file (e.g., boxplot.png)')
    parser.add_argument('--title', help='Plot title')
    parser.add_argument('--ylabel', help='Y-axis label')
    parser.add_argument('--dpi', type=int, default=150, help='DPI for saved figure')
    parser.add_argument('--show', action='store_true', help='Show plot interactively')
    parser.add_argument('--verbose', '-v', action='store_true', help='Print per-file progress')
    parser.add_argument('--min-valid-fraction', type=float, default=0.01,
                        help='Exclude images with fewer than this fraction of valid pixels (default: 0.01)')
    parser.add_argument('--color-by', default=None,
                        help='Color scatter points by this column (e.g., "date", "slide", '
                             'or any column from --annotations). Default: no coloring.')
    parser.add_argument('--annotations', type=str, default=None,
                        help='CSV file with manual annotations to merge. Must have a "filename" '
                             'column matching the .asc basenames, plus any additional columns '
                             '(e.g., "alive_dead"). Unmatched files keep NaN for annotation cols.')
    parser.add_argument('--generate-annotation-template', type=str, default=None, metavar='OUTPUT_CSV',
                        help='Generate a template CSV for manual annotation and exit. '
                             'Pre-fills filename, date, slide, sample, median. '
                             'Add your own columns (e.g., alive_dead) and fill them in.')

    args = parser.parse_args()

    # Build the dataframe
    df = build_dataframe(args.directory, args.suffix,
                         include=args.include, exclude=args.exclude,
                         verbose=args.verbose)

    # Filter out images with too few valid pixels
    before = len(df)
    df = df[df['fraction_valid'] >= args.min_valid_fraction]
    dropped = before - len(df)
    if dropped > 0:
        print(f"Dropped {dropped} images with <{args.min_valid_fraction*100:.0f}% valid pixels",
              file=sys.stderr)

    # Generate annotation template if requested
    if args.generate_annotation_template:
        template = df[['filename', 'date', 'slide', 'sample', 'position', 'median']].copy()
        template['alive_dead'] = ''  # placeholder column for manual annotation
        template['notes'] = ''
        template.to_csv(args.generate_annotation_template, index=False)
        print(f"Annotation template saved to: {args.generate_annotation_template}", file=sys.stderr)
        print(f"  {len(template)} rows. Fill in 'alive_dead' and/or add columns, then pass back with --annotations.",
              file=sys.stderr)
        sys.exit(0)

    # Merge annotations if provided
    if args.annotations:
        ann = pd.read_csv(args.annotations)
        if 'filename' not in ann.columns:
            print("Error: annotation CSV must have a 'filename' column.", file=sys.stderr)
            sys.exit(1)
        # Merge on filename, keeping all rows from df
        ann_cols = [c for c in ann.columns if c != 'filename' and c not in df.columns]
        if not ann_cols:
            print("Warning: no new columns found in annotation CSV.", file=sys.stderr)
        else:
            df = df.merge(ann[['filename'] + ann_cols], on='filename', how='left')
            n_annotated = df[ann_cols[0]].notna().sum()
            print(f"Merged annotations: {n_annotated}/{len(df)} images have annotations "
                  f"(columns: {ann_cols})", file=sys.stderr)

    # Save CSV if requested
    if args.csv_output:
        df.to_csv(args.csv_output, index=False)
        print(f"Stats saved to: {args.csv_output}", file=sys.stderr)

    # Determine labels
    suffix_short = args.suffix.replace('.th.asc', '').replace('_', ' ').strip()
    title = args.title or f"{suffix_short} by {args.group_by}"
    ylabel = args.ylabel or f"{args.value} {suffix_short}"

    # Validate color-by column exists
    color_col = args.color_by
    if color_col and color_col not in df.columns:
        available = ', '.join(df.columns)
        print(f"Error: --color-by '{color_col}' not found. Available: {available}", file=sys.stderr)
        sys.exit(1)

    # Make the boxplot
    fig, ax = make_boxplot(
        df,
        group_col=args.group_by,
        value_col=args.value,
        color_col=color_col,
        title=title,
        ylabel=ylabel,
        aggregate_by=args.aggregate_by,
        save_fig=args.save_fig,
        dpi=args.dpi,
    )

    if args.show:
        plt.show()
    else:
        plt.close(fig)


if __name__ == '__main__':
    main()
