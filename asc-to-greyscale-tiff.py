#!/usr/bin/env python3

"""

Convert 256x256 whitespace-delimited ASCII float grids to 32-bit grayscale TIFFs.



Deps: numpy, tifffile

    pip install numpy tifffile
    


Usage:

    python ascii_to_tiff32.py data/*.txt
    
    python ascii_to_tiff32.py data/*.dat --outdir out_tiffs --compression lzw
    
    python ascii_to_tiff32.py some_dir --shape 256x256 --suffix _f32.tiff
    
"""



import argparse

import os

from glob import glob

from typing import Iterable, List, Tuple



import numpy as np

import tifffile as tiff





def resolve_inputs(inputs: Iterable[str]) -> List[str]:
    
    seen = set()
    
    out = []
    
    for inp in inputs:
        
        if os.path.isdir(inp):
            
            for root, _, files in os.walk(inp):
                
                for fn in files:
                    
                    path = os.path.join(root, fn)
                    
                    if path not in seen:
                        
                        seen.add(path)
                        
                        out.append(path)
                        
        else:
            
            matches = glob(inp)
            
            if matches:
                
                for m in matches:
                    
                    if m not in seen:
                        
                        seen.add(m)
                        
                        out.append(m)
                        
            else:
                
                if os.path.exists(inp) and inp not in seen:
                    
                    seen.add(inp)
                    
                    out.append(inp)
                    
    return out





def load_ascii_floats(path: str, shape: Tuple[int, int]) -> np.ndarray:
    
    # For 256x256 this is fine; load as float64 then cast to float32.
    
    try:
        
        arr = np.loadtxt(path, dtype=np.float64)
        
    except Exception as e:
        
        raise RuntimeError(f"Failed to parse {path}: {e}")
    


    if arr.ndim == 1:
        
        expected = shape[0] * shape[1]
        
        if arr.size != expected:
            
            raise ValueError(f"{path}: expected {expected} values, got {arr.size}")
        
        arr = arr.reshape(shape)
        
    elif arr.ndim == 2:
        
        if arr.shape != shape:
            
            raise ValueError(f"{path}: expected shape {shape}, got {arr.shape}")
        
    else:
        
        raise ValueError(f"{path}: unexpected ndim={arr.ndim}")
    


    return arr.astype(np.float32, copy=False)





def save_tiff_float32(out_path: str, img: np.ndarray, compression: str) -> None:
    
    comp_map = {
        
        "none": None,
        
        "deflate": "deflate",
        
        "lzw": "lzw",
        
        "packbits": "packbits",
        
        "zstd": "zstd",
        
    }
    
    comp = comp_map[compression]
    
    # Single-image, single-channel float32 TIFF
    
    tiff.imwrite(out_path, img, dtype=np.float32, compression=comp)
    




def main():
    
    ap = argparse.ArgumentParser(
        
        description="Convert 256x256 ASCII float grids to 32-bit grayscale TIFFs (tifffile only)."
        
    )
    
    ap.add_argument("inputs", nargs="+", help="Files, directories, or globs to ASCII float files")
    
    ap.add_argument("--shape", type=str, default="256x256", help="Expected shape HxW (default 256x256)")
    
    ap.add_argument("--outdir", type=str, default="tiff32_out", help="Output directory")
    
    ap.add_argument("--suffix", type=str, default="_f32.tif", help="Output filename suffix")
    
    ap.add_argument(
        
        "--compression",
        
        type=str,
        
        default="zstd",
        
        choices=["none", "deflate", "lzw", "packbits", "zstd"],
        
        help="TIFF compression (float32-safe). Default: lzw.",
        
    )
    
    ap.add_argument("--fail-fast", action="store_true", help="Stop on first error")
    
    args = ap.parse_args()
    


    try:
        
        h, w = map(int, args.shape.lower().split("x"))
        
    except Exception:
        
        raise SystemExit("--shape must look like HxW, e.g., 256x256")
    
    shape = (h, w)
    


    os.makedirs(args.outdir, exist_ok=True)
    
    paths = resolve_inputs(args.inputs)
    
    if not paths:
        
        raise SystemExit("No input files found.")
    


    ok, failed = 0, 0
    
    for p in paths:
        
        try:
            
            img = load_ascii_floats(p, shape)
            
            base = os.path.basename(p)
            
            name, _sep, _ext = base.partition(".")
            
            out_path = os.path.join(args.outdir, name + args.suffix)
            
            save_tiff_float32(out_path, img, args.compression)
            print(".")
            #print(f"[OK] {p} -> {out_path} (float32, {img.shape})")
            
            ok += 1
            
        except Exception as e:
            
            print(f"[ERR] {p}: {e}")
            
            failed += 1
            
            if args.fail_fast:
                
                raise
            


    print(f"Done. Converted: {ok}, Failed: {failed}, Outdir: {args.outdir}")
    




if __name__ == "__main__":
    
    main()
    
