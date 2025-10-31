// ImageJ Headless script to open an image, export and apply the selected ROI number, and save
// Bjorn 2025.10.11.

print(getVersion());
print(getInfo("java.version"));

setBatchMode(true);
// ---- argument parsing wrapper ----
args = getArgument();
if (args == "") {
    exit("ERROR: No arguments provided. Usage: fiji --headless -macro apply_roi_save_histogram_headless.ijm 'image_file roi_file output_dir'; all paths should be absolute.");
}

// split on spaces
list = split(args, " ");

// check we got at least 3 args
expected = 3;
if (list.length < expected) {
    msg = "ERROR: Expected at least " + expected + " arguments, but got " + list.length + ".";
    exit(msg);
}

// trim whitespace
for (i = 0; i < list.length; i++) {
    list[i] = trim(list[i]);
}

// assign to named variables for clarity
input  = list[0];
roiFile = list[1];
outputDir = list[2];

print("Input image: " + input);
print("ROI file: " + roiFile);
print("Output dir:" + outputDir);

inputName = File.getName(input);
inputNameNoExt = File.getNameWithoutExtension(input);

open(input);
open(roiFile);

getRawStatistics(nPix, mean, minv, maxv, std, hist);
print("mean: " + d2s(mean,6) + ", std: " + d2s(std,6) + ", nPix: " + nPix);

// Rebin to desired histogram:
// target: 10k bins spanning [0, 20000]
// This code courtesy of ChatGPT 5.0; manually audited.
nBins = 10000;
xMin = 0.0;
xMax = 10000.0;
range = xMax - xMin;
if (range <= 0) exit("Invalid histogram range.");

values=newArray(nBins);
counts = newArray(nBins);    // counts
getHistogram(values, counts, nBins, xMin, xMax);

//setOption("NaNBackground");

// Write CSV: columns = bin_center, count
csvPath = outputDir + File.separator + inputNameNoExt + "-" + File.getName(roiFile) + "-hist.csv";
f = File.open(csvPath);
print(f, "bin_center,value");
for (i=0; i<nBins; i++)
    print(f, d2s(values[i]/1000, 6) + "," + counts[i]);
File.close(f);
print("Saved hist.");

print("Pixel(3479,3468)=" + toString(getPixel(3479,3468)) + "  should be 1.5901"); // If this doesn't work, we will multiply pixel values by 1000 as a hack.

/*
Potential alternate histogramming procedure which works for float files, from ChatGPT 5.0:

// Manual histogram for floats within ROI
requires("1.53"); // selectionContains needs a reasonably recent build
getBoundingRect(x0, y0, w, h);
nBins   = 10000;
histMin = 0.0;
histMax = 20000.0;
range = histMax - histMin;
binW  = range / nBins;
counts = newArray(nBins);
Array.fill(counts, 0);

for (y = y0; y < y0 + h; y++) {
    for (x = x0; x < x0 + w; x++) {
        if (!selectionContains(x, y)) continue; // stay inside ROI
        v = getPixel(x, y); // float value on 32-bit images
        if (v != v) continue;        // skip NaN (NaN != NaN)
        if (v < histMin || v > histMax) continue; // ignore out-of-range
        idx = floor((v - histMin) / binW);
        if (idx >= nBins) idx = nBins - 1;
        counts[idx]++;
    }
}
// write CSV with centers
csvPath = outputDir + File.separator + inputNameNoExt + "-" + File.getName(roiFile) + "-hist.csv";
f = File.open(csvPath);
print(f, "bin_center,value");
for (k = 0; k < nBins; k++) {
    center = histMin + (k + 0.5) * binW;
    print(f, d2s(center, 6) + "," + counts[k]);
}
File.close(f);




 */ 



// Make a Thumbnail of the roi so I can rename it easily later.
run("Invert");
run("8-bit"); // I would save as bool if I could, but FIJI saves Masks as 8-bit, so I might as well keep some contrast...
w = getWidth(); h=getHeight();
w = round(w/10); h=round(h/10);
run("Scale...", "x=0.1 y=0.1 width=" + toString(w) + " height=" + toString(h) + " interpolation=Bicubic average create");
saveAs("Tiff", outputDir +  File.separator + inputNameNoExt + "-" + File.getName(roiFile) + ".tif");
run("Close All");
print("Closed.");
