#!/bin/python3
# Module of file utilities that I've been using frequently.
#
# To use within flimutils:
# import fileutils; fileutils.asc_load()
# OR
# from fileutils import asc_load
#
# To use from another project:
# import flimutils.fileutils
# OR
# from flimutils.fileutils import asc_load
#
# Changelog, 2025.10.28:
# - flimload renamed to asc_load, on the rationale that I may store flim data in tiff files.
# - underscore added to files_recursively, to match files_non_recursively
# - flimexport renamed to asc_export.
# Bjorn

import numpy as np
import os
import argparse
import sys

def asc_load(asciifile, verbose):
    if verbose:
        print(f"Loading {asciifile} ... ", end="")
    try:
        data = np.loadtxt(asciifile)
    except Exception as e:
        print(f"loadtxt: couldn't load {asciifile}: {e}")
    if verbose:
        print("success.")
    return data

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
            np.savetxt(asc_filepath, matrix, fmt='%.6g', delimiter=' ', newline='\n')
            if verbose:
                print("success.")
    except Exception as e:
        print(f"asc_export: Error saving {asc_filepath}: {e}", file=sys.stderr)
