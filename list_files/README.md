# ShowFiles
This is a Bio-Formats based tool. Intended usage is mainly for Screen/Plate/Well image file formats.

This tool returns the `Filepaths` and the `Series` (in the Bio-Formats sense) and `Well` information. This enables processing of such information for associating of the original files with annotations (which might be available in a CSV or other textfile types). 

If possible, point the tool to a master file (e.g. `Index.xml` for PerkinElmer Operetta format).

Build from source:

```
cd list_files
conda create -n gradle-682 -c conda-forge gradle=6.8.2
conda activate gradle-682
gradle build fatJar
cd build/libs
```


Basic Usage:

```
java -jar showfiles-1.0.0-with-deps.jar <PATH-TO-MASTERFILE>
```

Basic Usage Example:

```
java -jar showfiles-1.0.0-with-deps.jar "/uod/npsc/data/Operetta/Collaborative/ML/ML-BE001/ML-BE001-01__2025-02-04T13_27_31-Measurement 1/Images/Index.xml"
```

CSV output option usage:

```
java -jar showfiles-1.0.0-with-deps.jar <PATH-TO-MASTERFILE> <NAME-OF-YOUR-CSV-OUTPUT-FILE>
```

CSV output option example: (the stdout is supressed by `> /dev/null`):

```
java -jar showfiles-1.0.0-with-deps.jar "/uod/npsc/data/Operetta/Collaborative/ML/ML-BE001/ML-BE001-01__2025-02-04T13_27_31-Measurement 1/Images/Index.xml" showfiles.csv > /dev/null
```

Suggested further workflow:
Use outputs from this tool for e.g. a Python-based tool to digest `showfiles.output` and your metadata textfiles (e.g. as CSV, where each line corresponds to a metadata of a particular `Well`) to associate the metadata with the images.
Pseudocode example:

```
python my_metadata_parser.py showfiles.csv metadata.csv # returns output based on the 2 CSV files containing metadata and filepaths
```
