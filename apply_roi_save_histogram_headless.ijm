// ImageJ Headless script to open an image, export and apply the selected ROI number, and save
// Bjorn 2025.10.11.

print(getVersion());
print(getInfo("java.version"));

setBatchMode(true);
// ---- argument parsing wrapper ----
args = getArgument();
if (args == "") {
    exit("ERROR: No arguments provided. Usage: fiji --headless -macro autostitch_headless.ijm 'image_file roi_file roi_number output_dir'; all paths should be absolute.");
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

open(input);
open(roiFile);

getRawStatistics(nPix, mean, minv, maxv, std, hist);
print(d2s(mean,6) + "," + d2s(std,6) + "," + nPix);

// Rebin to desired histogram:
// target: 10k bins spanning [0, 20000]
// This code courtesy of ChatGPT 5.0; manually audited.
targetBins = 10000;
xMin = 0.0;
xMax = 20000;
range = xMax - xMin;
if (range <= 0) exit("Invalid histogram range.");

rebin=newArray(targetBins); // This one is my own. GPT hallucinated Array.resize.
Array.fill(rebin, 0);
binWidth = range / targetBins;

// Sum raw counts into target bins.
// Raw indices i represent intensity i (0..65535 for 16-bit).
rawLen = hist.length; // or is it length(hist)?
for (i = 0; i < rawLen; i++) {
    // Map intensity to target bin
    x = i; // intensity value == index
    if (x < xMin || x > xMax) continue;
    idx = floor((x - xMin) / binWidth);
    if (idx >= targetBins) idx = targetBins - 1; // clamp right edge
    rebin[idx] = rebin[idx] + hist[i];
}

// Write CSV: columns = bin_center, count
csvPath = outputDir + File.separator + inputName + "-" + File.getName(roiFile) + "-hist.csv";
f = File.open(csvPath);
print(f, "bin_center,value");
for (k = 0; k < targetBins; k++) {
    center = xMin + (k + 0.5) * binWidth;
    print(f, d2s(center, 6) + "," + rebin[k]);
}
File.close(f);
print("Saved hist.");

// Make a Thumbnail of the roi so I can rename it easily later.
run("Invert");
run("8-bit"); // I would save as bool if I could, but FIJI saves Masks as 8-bit, so I might as well keep some contrast...
w = getWidth(); h=getHeight();
w = round(w/10); h=round(h/10);
run("Scale...", "x=0.1 y=0.1 width=" + toString(w) + " height=" + toString(h) + " interpolation=Bicubic average create");
saveAs("Tiff", outputDir +  File.separator + inputName + "-" + File.getName(roiFile) + ".tif");
run("Close All");
print("Closed.");
