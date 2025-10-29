// Automatically add scale to files created by grid stitch
// Bjorn, 2025.10.02

print(getVersion());
print(getInfo("java.version"));

// ---- argument parsing wrapper ----
args = getArgument();
if (args == "") {
    exit("ERROR: No arguments provided. Usage: fiji --headless -macro add_scale_headless.ijm 'input output'");
}

// split on spaces
list = split(args, " ");

// check we got at least 1 args
expected = 2;
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
print("Input: " + input);
print("Output: " + output);

open(input);

run("Set Scale...", "distance=1 known=0.733 unit=um");
run("Scale Bar...", "width=500 height=100 thickness=100 font=400 bold overlay");
saveAs("Tiff", output);
print("Done scaling.")
