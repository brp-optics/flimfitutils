// ImageJ Script to open an image, export and apply the selected ROI number, and close the image again.
// Bjorn 2025.10.10.

#@ File (label = "Image", style = "file") input
#@ File (label = "Roi file", style = "file") roiFile
#@ Integer (label = "Roi Number", value = "0") roiNum
#@ File (label = "Output directory", style = "directory") outputDir

print(input);
print(roiFile);
print(roiNum);
print(outputDir);

inputName = File.getName(input);

open(input);
run("ROI Manager...");
roiManager("Open", roiFile);
roiManager("Select", roiNum);
run("Histogram", "bins=10000 use x_min=0 x_max=17097.80 y_max=Auto");
Table.showHistogramTable;
saveAs("Results", outputDir + File.separator + inputName + "-roi_" + toString(roiNum));
run("Close All");

open(input);
run("ROI Manager...");
roiManager("Open", roiFile);
roiManager("Select", roiNum);
run("Invert");
run("8-bit"); // I would save as bool if I could, but FIJI saves Masks as 8-bit, so I might as well keep some contrast...
saveAs("Tiff", outputDir +  File.separator + inputName + "-roi_" + toString(roiNum) + ".tif");
run("Close All");
