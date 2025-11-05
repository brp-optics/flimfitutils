#!/usr/bin/env python3
# Claude Opus prompted by Bjorn, 2025.11.03.
"""
Generate boxplots from CSV data with customizable file groupings.
Groups files by filename patterns and creates boxplots of median values.
"""

import os
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re
import sys
from pathlib import Path


def parse_grouping(grouping_str):
    """
    Parse a grouping string in the format 'pattern1,pattern2:group_name'
    
    Examples:
        's2-,s4-,s6-:CTRL' -> (['s2-', 's4-', 's6-'], 'CTRL')
        's42-s80:1KO' -> (range(42, 81), '1KO')
    """
    parts = grouping_str.split(':')
    if len(parts) != 2:
        raise ValueError(f"Invalid grouping format: {grouping_str}. Expected 'patterns:group_name'")
    
    patterns_part, group_name = parts
    
    # Check if it's a range (e.g., 's42-s80')
    range_match = re.match(r's(\d+)-s(\d+)', patterns_part)
    if range_match:
        start, end = map(int, range_match.groups())
        patterns = [f's{i}-' for i in range(start, end + 1)]
        # Also include exact matches without dash (e.g., 's42' for single sample files)
        patterns.extend([f's{i}' for i in range(start, end + 1)])
    else:
        # Split by comma for individual patterns
        patterns = [p.strip() for p in patterns_part.split(',')]
        
    return patterns, group_name


def assign_group(filename, groupings):
    """
    Assign a filename to a group based on the grouping rules.
    
    Args:
        filename: The filename to classify
        groupings: List of (patterns, group_name) tuples
    
    Returns:
        The group name or 'Other' if no match found
    """
    # Extract the name without extension
    name = os.path.splitext(filename)[0]

    for patterns, group_name in groupings:
        for pattern in patterns:
            # Check if the name starts with the pattern
            if name.startswith(pattern):
                print(f"Assigned group {group_name} to {name} because it started with {pattern}. Other patterns: {patterns}; other groups: {groupings}")
                return group_name
    print(f"Assigned other for {name}.")
    return 'Other'


def create_boxplot(df, groupings, title="Boxplot of Median Values by Group", 
                   show_points=False, use_stdev=False):
    """
    Create boxplots from the dataframe grouped by the specified groupings.
    
    Args:
        df: DataFrame with columns including 'filename', 'median', and optionally 'stdev'
        groupings: List of (patterns, group_name) tuples
        title: Title for the plot
        show_points: Whether to overlay individual data points
        use_stdev: Whether to include stdev information (as error bars or annotations)
    """
    # Assign groups to each row
    df['group'] = df['filename'].apply(lambda x: assign_group(x, groupings))
    
    # Filter out 'Other' group if it exists and is empty
    grouped_df = df[df['group'] != 'Other'].copy()

    print(grouped_df)
    
    if grouped_df.empty:
        print("Warning: No files matched the specified groupings.")
        grouped_df = df.copy()
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Define the order of groups for consistent plotting
    group_order = [group_name for _, group_name in groupings]
    group_order = [g for g in group_order if g in grouped_df['group'].unique()]
    
    # Create boxplot
    grouped_df.head()
    box_plot = sns.boxplot(data=grouped_df, x='group', y='median', 
                           order=group_order, ax=ax, hue='group', 
                           palette='Set2', legend=False)
    swarmplot = sns.swarmplot(data=grouped_df, x='group', y='median',
                              order=group_order, ax=ax,
                              legend=False)
    
    # Optionally show individual points
    if show_points:
        sns.stripplot(data=grouped_df, x='group', y='median', 
                     order=group_order, ax=ax, color='black', 
                     alpha=0.5, size=4)
    
    # Add standard deviation information if requested
    if use_stdev and 'stdev' in df.columns:
        # Calculate mean and std for each group
        group_stats = grouped_df.groupby('group').agg({
            'median': 'mean',
            'stdev': 'mean'
        }).reset_index()
        
        # Add annotations
        for idx, row in group_stats.iterrows():
            group_pos = group_order.index(row['group'])
            ax.text(group_pos, ax.get_ylim()[1] * 0.95, 
                   f'Avg σ: {row["stdev"]:.2f}',
                   ha='center', va='top', fontsize=9, style='italic')
    
    # Customize the plot
    ax.set_xlabel('Group', fontsize=12, fontweight='bold')
    ax.set_ylabel('Median Values', fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold')
    
    # Add grid for better readability
    ax.yaxis.grid(True, linestyle='--', alpha=0.7)
    ax.set_axisbelow(True)
    
    # Add sample counts to x-axis labels
    sample_counts = grouped_df.groupby('group')['filename'].count()
    new_labels = [f'{group}\n(n={sample_counts.get(group, 0)})' 
                 for group in group_order]
    ax.set_xticks(range(len(group_order)))
    ax.set_xticklabels(new_labels)
    
    # Adjust layout and display
    plt.tight_layout()
    
    # Print summary statistics
    print("\nSummary Statistics by Group:")
    print("-" * 50)
    for group in group_order:
        group_data = grouped_df[grouped_df['group'] == group]['median']
        print(f"\n{group}:")
        print(f"  Count: {len(group_data)}")
        print(f"  Mean: {group_data.mean():.3f}")
        print(f"  Median: {group_data.median():.3f}")
        print(f"  Std: {group_data.std():.3f}")
        print(f"  Min: {group_data.min():.3f}")
        print(f"  Max: {group_data.max():.3f}")
    
    return fig, ax, grouped_df


def main():
    parser = argparse.ArgumentParser(
        description='Generate boxplots from CSV data with file groupings',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Default grouping (CTRL, 1KO, 2KO):
  %(prog)s data.csv
  
  # Custom groupings:
  %(prog)s data.csv -g "s2-,s4-,s6-:CTRL" "s42-s80:1KO" "s82-s120:2KO"
  
  # Using range notation:
  %(prog)s data.csv -g "s2-s40:CTRL" "s42-s80:1KO" "s82-s120:2KO"
  
  # Show individual points:
  %(prog)s data.csv --show-points
  
  # Include standard deviation info:
  %(prog)s data.csv --use-stdev
        '''
    )
    
    parser.add_argument('csv_file', type=str,
                       help='Path to the CSV file containing the data')

    parser.add_argument('--csv-output', type=str, help='Save grouped data to csv file.')
    
    parser.add_argument('-g', '--groupings', nargs='+', 
                       help='Grouping definitions in format "pattern1,pattern2:group_name" or "sX-sY:group_name" for ranges')
    
    parser.add_argument('--show-points', action='store_true',
                       help='Show individual data points on the boxplot')
    
    parser.add_argument('--use-stdev', action='store_true',
                       help='Include standard deviation information in the plot')
    
    parser.add_argument('--title', type=str, default='Boxplot of Median Values by Group',
                       help='Title for the plot')
    
    parser.add_argument('--save-fig', type=str, default=None,
                       help='Save plot to file instead of displaying (e.g., plot.png, plot.pdf)')

    parser.add_argument('--dpi', type=int, default=100,
                       help='DPI for saved figure (default: 100)')
    
    args = parser.parse_args()
    
    # Check if CSV file exists
    if not Path(args.csv_file).exists():
        print(f"Error: CSV file '{args.csv_file}' not found.")
        sys.exit(1)
    
    # Read the CSV file
    try:
        df = pd.read_csv(args.csv_file)
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        sys.exit(1)
    
    # Check for required columns
    required_columns = ['filename', 'median']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"Error: Missing required columns: {missing_columns}")
        print(f"Available columns: {list(df.columns)}")
        sys.exit(1)
    
    # Parse groupings or use defaults
    if args.groupings:
        try:
            groupings = [parse_grouping(g) for g in args.groupings]
        except ValueError as e:
            print(f"Error parsing groupings: {e}")
            sys.exit(1)
    else:
        # Default groupings based on your specifications
        print("Using default groupings: CTRL (s2-s40), 1KO (s42-s80), 2KO (s82-s120)")
        ctrl_patterns = [f's{i}-' for i in range(2, 41, 2)] + [f's{i}-' for i in range(2, 41, 2)]
        ko1_patterns = [f's{i}-' for i in range(42, 81, 2)] + [f's{i}-' for i in range(42, 81, 2)]
        ko2_patterns = [f's{i}-' for i in range(82, 121, 2)] + [f's{i}-' for i in range(82, 121, 2)]
        
        groupings = [
            (ctrl_patterns, 'CTRL'),
            (ko1_patterns, '1KO'),
            (ko2_patterns, '2KO')
        ]
    print(groupings)
    print(df['mean'].head())
    # Create the boxplot
    fig, ax, grouped_df = create_boxplot(
        df, groupings, 
        title=args.title,
        show_points=args.show_points,
        use_stdev=args.use_stdev
    )
    
    # Save or display the plot
    if args.save_fig:
        fig.savefig(args.save_fig, dpi=args.dpi, bbox_inches='tight')
        print(f"\nPlot saved to: {args.save_fig}")
    else:
        plt.show()
    
    # Optionally save the grouped data
    grouped_output = Path(args.csv_output).stem + '_grouped.csv'
    grouped_df.to_csv(grouped_output, index=False)
    print(f"\nGrouped data saved to: {grouped_output}")


if __name__ == "__main__":
    main()
