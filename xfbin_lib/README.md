# xfbin_lib
 A python module (and script) for parsing CyberConnect2 games XFBIN files.

# Installation
For using as a script for unpacking XFBIN files, download the latest [release](https://github.com/SutandoTsukai181/xfbin_lib/releases/latest).

For using as a module for another project, just add it as a submodule and import the following:

```py
from xfbin_lib.xfbin import *
```

# Script Usage

```
usage: xfbin_parser.exe [-h] [-f] [-d] [-s] [-j] [-v] [input] [output]

Unpacks/Repacks nuccChunks from CyberConnect2 XFBIN container files.

positional arguments:
  input                 path to input XFBIN file OR path to folder to repack
  output                path to output folder to extract the chunks to (defaults to a new folder with the name of the
                        input XFBIN) OR path to output XFBIN file when repacking (defaults to folder name + ".xfbin")

optional arguments:
  -h, --help            show this help message and exit
  -f, --force-overwrite
                        overwrite old extracted files without prompting
  -d, --file-data-only  when possible, write each chunk's file data only (NTP3 for .nut, NDP3 for .nud) (will disable repacking)
  -s, --sort-types      sort nuccChunks by type instead of page (will disable repacking)
  -j, --no-json         do not write "_page.json" for extracted pages (will disable repacking)
  -v, --verbose         print info about each extracted chunk
```

# Module Usage
Reading XFBIN files
```py
# Using path to file
xfbin_obj = read_xfbin(path)

# Using a bytearray object
xfbin_obj = read_xfbin(buffer)
```

Accessing NuccChunk objects inside an Xfbin
```py
# Each Xfbin contains Page objects, which contain NuccChunk objects
for page in xfbin_obj.pages:
    for chunk in page.chunks:
        # Do stuff with each NuccChunk
        print(f'Chunk name: {chunk.name}')
        print(f'Chunk path: {chunk.filePath}')
        print(f'Chunk type: {NuccChunk.get_nucc_str_from_type(type(chunk)})')
```

Writing XFBIN files from an Xfbin object
```py
# Writes the Xfbin to a bytearray buffer
buffer = write_xfbin(xfbin_obj)

# Writes the Xfbin to a path
write_xfbin_to_path(xfbin_obj, path)
```

There is no real documentation for all supported nuccChunk types, so if you want to use the module for accessing/modifying NuccChunk objects, I suggest checking [nucc.py](/xfbin/structure/nucc.py), which contains the current implementation for all NuccChunk objects. The properties added inside each `init_data` method are the same properties you can access from a NuccChunk object.

# Credits
[Smash Forge](https://github.com/jam1garner/Smash-Forge) team for their NUD models and NUT textures implementation, which the NuccChunkModel and NuccChunkTexture classes use, respectively.

