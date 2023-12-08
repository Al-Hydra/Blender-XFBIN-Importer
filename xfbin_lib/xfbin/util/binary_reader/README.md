# PyBinaryReader
A python module for basic binary file IO.

This is something I wrote to use in my personal projects, but feel free to use it if you like!

# Installation
`pip install binary-reader` (add `--upgrade` to update)

# Usage
```py
from binary_reader import BinaryReader
```

Here is some example usage on creating and using a BinaryReader to read a small part of the DDS header:

```py
f = open("example.dds", "rb")  # Open a file in binary mode

reader = BinaryReader(f.read())  # Create a new BinaryReader from the file buffer (we can close the file afterwards)

# Read the magic as a UTF-8 encoded string and compare it to the correct magic
if reader.read_str(4) != 'DDS ':
    raise Exception('Incorrect magic.')

size = reader.read_uint32()  # Read the next 4 bytes as an unsigned 32-bit integer
```

Another example on using BinaryReader features to navigate through a buffer:

```py
some_offset = reader.read_uint32()  # Read an offset that we want to move to

prev_pos = reader.pos()  # Store the current position so we can return back later
reader.seek(some_offset)  # Set the current position in the file to that offset

vector = reader.read_float(3)  # Read 3 consecutive 32-bit floats, return them as a tuple

reader.seek(prev_pos)  # Go back to the previous position

reader.seek(4, whence=1)  # In addition to absolute seeking, we can also seek relative to the current position...

reader.seek(0, whence=2)  # And relative to the end of the buffer. This will set the position to be the last index in the buffer

```

In addition to reading, you can also write to a new buffer:
```py
writer = BinaryReader()  # Create a new BinaryReader (bytearray buffer is initialized automatically)

writer.set_endian(is_big_endian=True)  # Set the endianness to big endian

writer.write_str('MGIC')
writer.write_uint32(20)

writer.align(0x10)  # Align the buffer to 0x10 (in this case, will append 8 bytes to the buffer)

writer.pad(0xF0)  # Add 0xF0 bytes of padding
print(writer.size())  # This should print 256 (0x100)

# Write the buffer to a new file
with open('examplefile', 'wb') as f:
    f.write(writer.buffer())
```

These are the types that can be used with BinaryReader. Just add `read_` or `write_` before the type to get the method name:
```
uint8, int8,
uint16, int16, half_float
uint32, int32, float
uint64, int64,
bytes, str
```

# License
This project uses the MIT License, so feel free to include it in whatever you want.
