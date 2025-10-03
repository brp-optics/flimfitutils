// Automatically merge files created by multichannel grid stitch
// Bjorn, 2025.10.02

print(getVersion());
print(getInfo("java.version"));

// ---- argument parsing wrapper ----
args = getArgument();
if (args == "") {
    exit("ERROR: No arguments provided. Usage: fiji --headless -macro autostitch_headless.ijm 'directory TileConfiguration.txt'");
}

// split on spaces
list = split(args, " ");

// check we got at least 1 args
expected = 1;
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
print("Input directory: " + input);
output = input;

open(output + File.separator + "img_t1_z1_c1");
open(output + File.separator + "img_t1_z1_c2");
open(output + File.separator + "img_t1_z1_c3");

run("Merge Channels...", "c1=[img_t1_z1_c1] c2=[img_t1_z1_c2] c3=[img_t1_z1_c3] create");
run("Set Scale...", "distance=1 known=0.733 unit=um");
selectImage("Composite");
//run("Scale Bar...", "width=500 height=100 thickness=100 font=400 bold overlay");
run("Scale Bar...", "bold overlay");
saveAs("Tiff", output + File.separator + "Composite_headless.tif");
print("Done merging.")