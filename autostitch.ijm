// Automatically stitch a directory of files containing a "TileConfiguration.txt" file.

#@ File (label = "Input directory", style = "directory") input
#@ File (label = "Output directory", style = "directory") output
#@ String (label = "TileConfiguration file name", value = "TileConfiguration.txt") tcfile

run("Grid/Collection stitching", "type=[Positions from file] order=[Defined by TileConfiguration] directory=" + input + " layout_file=" + tcfile + " fusion_method=[Linear Blending] regression_threshold=0.30 max/avg_displacement_threshold=2.50 absolute_displacement_threshold=3.50 computation_parameters=[Save memory (but be slower)] image_output=[Write to disk] output_directory=" + output);

print("Waiting 5");
waitForUser(1);
open(output + File.separator + "img_t1_z1_c1");
open(output + File.separator + "img_t1_z1_c2");
open(output + File.separator + "img_t1_z1_c3");
run("Merge Channels...", "c1=img_t1_z1_c1 c2=img_t1_z1_c2 c3=img_t1_z1_c3");
saveAs("Tiff", output + File.separator + "Composite.tif");
close;
