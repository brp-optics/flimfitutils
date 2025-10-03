// Automatically merge files created by multichannel grid stitch
// Bjorn, 2025.10.02

print("Java:" + getVersion());
print(getInfo("java.version"));

#@ File (label = "Input directory", style = "directory") input
print("Input directory: " + input);
output = input;


// open each color channel
open(output + File.separator + "img_t1_z1_c1");
open(output + File.separator + "img_t1_z1_c2");
open(output + File.separator + "img_t1_z1_c3");

//merge color channels
run("Merge Channels...", "c1=[img_t1_z1_c1] c2=[img_t1_z1_c2] c3=[img_t1_z1_c3] create");
run("Set Scale...", "distance=1 known=0.733 unit=um");
selectImage("Composite");
run("Scale Bar...", "bold overlay");
saveAs("Tiff", output + File.separator + "Composite_supervised.tif");
print("Done merging.")