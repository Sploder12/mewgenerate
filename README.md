# Mewgenerate

### About
This project aims to ease documentation of the Mewgenics game by parsing game files programatically rather than by hand. 

### Usage
To use this utility place the unpacked `resources.gpak` file into `./data/` and run `python main.py` with your arguments. The `./data/` folder should contain the following folders `audio/`, `data/`, `levels/`, `shaders/`, `swfs/`, and `textures/`. Ensure the python working directory is the same as the directory `main.py` is located in, otherwise, nothing will work.

```
python main.py [-h] [-v] [-o OUT_DIR] [--ffdec FFDEC] [--inkscape INKSCAPE] [--force-redump] [components ...]

A utility for parsing Mewgenics assets.
Unpacked .gpak files should be placed in ./data
Requires FFDec and Inkscape for full functionality

positional arguments:
  components            Components to export, blank for all. Valid values are "items", "furniture"

options:
  -h, --help            show this help message and exit
  -v, --verbose
  -o, --out-dir OUT_DIR
                        Output file location, please use an empty directory. (default: ./out)
  --ffdec FFDEC         Path to ffdec-cli executable, used for dumping assets from SWF files. (default: C:/Program Files (x86)/FFDec/ffdec-cli.exe)
  --inkscape INKSCAPE   Path to inkscape executable, used for cropping SVG assets. (default: C:/Program Files/Inkscape/bin/inkscape.com)
  --force-redump        Ignores asset cache.
```

### Developer Info

`src/parse_csv.py` contains the function `parse_csv(filepath)`, this is useful for translations found in `./data/data/text`.

`src/parse_gon.py` contains the function `parse_gon(filepath)`, this is useful for parsing `.gon` files into Python objects. Unlike a normal parser, comments are kept as a list of strings in the `"__COMMENTS__"` field of the object. Note that arrays are parsed as dictionaries so that `"__COMMENTS__"` can be present, they still use numeric indexes however.

`src/parse_swf.py` contains the function `parse_swf(filepath)`, this is useful for getting sprites and animations **WORK IN PROGRESS!!!**

Higher-level functionality is also provided in files named based off what they parse for Mewgenics. Ex. `src/keywords.py` handles strings for buffs and debuffs (keywords).
