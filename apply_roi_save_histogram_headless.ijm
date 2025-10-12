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
expected = 4;
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
roiNum = list[2];
outputDir = list[3];

print("Input image: " + input);
print("ROI file: " + roiFile);
print("ROI number:" + roiNum);
print("Output dir:" + outputDir);

inputName = File.getName(input);

open(input);
print("opening roimanager");
roiManager("Open", roiFile);
print("selecting in roimanager");
roiManager("Select", roiNum);
print("Getting stats...");
getRawStatistics(nPix, mean, minv, maxv, std, hist);
print(toString(mean) +  toString(std) + toString(nPix));
print("Got stats.");
run("Histogram", "bins=10000 use x_min=0 x_max=17097.80 y_max=Auto");
Table.showHistogramTable;
saveAs("Results", outputDir + File.separator + inputName + "-roi_" + toString(roiNum) +"-hist.csv");
run("Close All");
print("Saved hist and cleaned up.");

// Make a Thumbnail of the roi so I can rename it easily later.
open(input);
roiManager("Select", roiNum);
run("Invert");
run("8-bit"); // I would save as bool if I could, but FIJI saves Masks as 8-bit, so I might as well keep some contrast...
w = getWidth(); h=getHeight();
w = round(w/10); h=round(h/10);
run("Scale...", "x=0.1 y=0.1 width=" + toString(w) + " height=" + toString(h) + " interpolation=Bicubic average create");
saveAs("Tiff", outputDir +  File.separator + inputName + "-roi_" + toString(roiNum) + ".tif");
print("Saved Tiff");
run("Close All");
print("Closed.");
