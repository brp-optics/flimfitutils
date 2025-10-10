// Automatically stitch a directory of files containing a "TileConfiguration.txt" file.
// Usage: fiji --headless autostitch_headless.ijm "input_directory output_directory TileConfiguration_file_name.txt"
// 
//

print("Hello World!"); //For debugging headless.

// ---- argument parsing wrapper ----
args = getArgument();
if (args == "") {
    exit("ERROR: No arguments provided. Usage: fiji --headless -macro autostitch_headless.ijm 'input_directory output_directory TileConfiguration.txt'");
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
output = list[1];
tcfile = list[2];
print("Input: " + input);
print("tcfile:" + tcfile);

// The way I'm calling the script, output is a Unix relative path, but the script doesn't recognize a relative path when opening files.
// So we get the working directory as the directory the script is in.
//wd = getInfo("macro.filepath");
//wd = File.getParent(wd);
//print("Assuming working directory is " + wd);

run("Grid/Collection stitching", "type=[Positions from file] order=[Defined by TileConfiguration] directory=" + input + " layout_file=" + tcfile + " fusion_method=[Linear Blending] regression_threshold=0.30 max/avg_displacement_threshold=2.50 absolute_displacement_threshold=3.50 computation_parameters=[Save memory (but be slower)] image_output=[Write to disk] output_directory=" + output);

print("Done stitching.");

