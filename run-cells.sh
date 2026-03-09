#!/bin/bash

# Sample fitting routine for metabolic FLIM data from fixed cells.
# brp-optics with Claude Opus 4.6, 2026.03.09

for dir in *PCK_on_SLIM
do

    for subdir in "$dir/*exet-fitet-sz-b*"
    do

	# Calculate Free-bound ratios. this step includes thresholding on data quality iirc.
	# Ideal binned photon counts are above 10,000 for biexponential fitting, free NADH lifetimes should be reasonable, and 
	# Results are saved in $dir/t-ar-$subdir


	# Generate histogram of the entire t-ar- directory
	# Do not include files with "chroma", "urea", or "pollen" in the name (control slide biexponentials aren't meaningful.)
	# Histogram files containing 535 in the name and 457 in the name separately (NADH vs FAD)
	# Display histograms and proposed thresholds for display


	# Threshold "-color-coded-value.asc" files (these contain mean lifetime t_m), in the same way that the Free-bound ratios were thresholded.
	# Results are saved in $dir/t-tm-$subdir

	# Generate histogram of the entire t-tm- directory
	# Do not include files with "chroma", "urea", or "pollen" in the name (control slide biexponentials aren't meaningful.)
	# Histogram files containing 535 in the name and 457 in the name separately (NADH vs FAD)
	# Display histograms and proposed thresholds for display
	
    done
done

# Generate histogram of all the *PCK_on_SLIM/t-ar-$subdir free-bound ratio files, combined
# Do not include files with "chroma", "urea", or "pollen" in the name (control slide biexponentials aren't meaningful.)
# Histogram files containing 535 in the name and 457 in the name separately (NADH vs FAD)
# Display histogram with proposed thresholds

# Generate histogram of all the *PCK_on_SLIM/t-tm-$subdir mean lifetime files, combnied
# Same as above


for subdir in *PCK_on_SLIM/t-ar-*
do
    # Using the selected thresholds,
    # Generate Free-bound greyscale tiff files using best histogram values from previous step
    # Results are saved in $dir/gs-t-ar-...

    # Manual inspection:
    open $subdir
done

for subdir in *PCK_on_SLIM/t-tm-*
do
    
    # Generate tm greyscale tiff files using the best histogram values
    # Save them in $dir/gs-t-tm...
	

    # Manual inspection:
    open $subdir

	
done
    
for subdir in "$dir/*exet600-1400-0-500-fitet-sz-b*"
do
    # Generate cropped tif files from SPCImage's exported .tif files (goal is to crop to 256x256; the bottom bar is a scalebar which we don't need 
    # Save cropped outputs to $dir/cropped-$subdir
    mkdir $dir/cropped-$subdir # Do we need to strip off the dir name from $subdir first?
    
    # manual inspection
    open $subdir & open cropped-$subdir & open t-tm-$subdir

    
done

    
