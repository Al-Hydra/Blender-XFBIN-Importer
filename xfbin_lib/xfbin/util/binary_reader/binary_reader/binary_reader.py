__author__ = "SutandoTsukai181"
__copyright__ = "Copyright 2021, SutandoTsukai181"
__license__ = "MIT"
__version__ = "1.4.3"

import struct
from contextlib import contextmanager
from enum import Flag, IntEnum
from typing import Tuple, Union
import numpy as np

FMT = {
    'b': 1, 'B': 1, 's': 1,
    'h': 2, 'H': 2, 'e': 2,
    'i': 4, 'I': 4, 'f': 4,
    'q': 8, 'Q': 8, 'd': 8,
}

_numpy_dtype_map = {
    "int8": "i1",
    "uint8": "u1",
    "int16": "i2",
    "uint16": "u2",
    "int32": "i4",
    "uint32": "u4",
    "int64": "i8",
    "uint64": "u8",
    "float16": "f2",
    "float32": "f4",
    "float64": "f8"
}

class Endian:
    LITTLE = 0
    BIG = 1


class Whence(IntEnum):
    BEGIN = 0
    CUR = 1
    END = 2


class BrStruct:
    """Base class for objects passed to BinaryReader's `read_struct` and `write_struct` methods.\n
    Any type passed to `read_struct` and any object passed to `write_struct` must inherit from this class.\n
    Override `__br_read__` and `__br_write__` methods from this class to set up BinaryReader to read your classes.\n"""

    def __init__(self) -> None:
        """If this class will be used with BinaryReader's `read_struct` method, then this method MUST receive zero arguments after `self`.\n
        """
        pass

    def __br_read__(self, br: 'BinaryReader', *args) -> None:
        """Called once when `BinaryReader.read_struct` is called on this class.\n
        This method must accept at least 1 parameter (other than `self`).\n
        The first parameter will be the BinaryReader instance which `read_struct` was called from.
        This parameter can be used to `read` the attributes of object.\n
        This method can take any number of parameters after the required first parameter.
        The additional arguments corresponding to these parameters should be passed to `BinaryReader.read_struct` after the `count` argument.\n
        """
        pass

    def __br_write__(self, br: 'BinaryReader', *args) -> None:
        """Called once when `BinaryReader.write_struct` is called on an instance of this class.\n
        This method must accept at least 1 parameter (other than `self`).\n
        The first parameter will be the BinaryReader instance which `write_struct` was called from.
        This parameter can be used to `write` the attributes of object.\n
        This method can take any number of parameters after the required first parameter.
        The additional arguments corresponding to these parameters should be passed to `BinaryReader.write_struct` after the `value` argument.\n
        """
        pass


class BinaryReader:
    """A buffer reader/writer containing a mutable bytearray.\n
    Allows reading and writing various data types, while advancing the position of the buffer on each operation."""
    __buf: bytearray
    __idx: int
    __endianness: Endian
    __encoding: str

    def __init__(self, buffer: bytearray = bytearray(), endianness: Endian = Endian.LITTLE, encoding='utf-8'):
        """Constructs a BinaryReader with the given buffer, endianness, and encoding and sets its position to 0.\n
        If buffer is not given, a new bytearray() is created. If endianness is not given, it is set to little endian.\n
        Default encoding is UTF-8. Will throw an exception if encoding is unknown.
        """
        self.__buf = bytearray(buffer)
        self.__endianness = endianness
        self.__idx = 0
        self.set_encoding(encoding)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__buf.clear()

    def pos(self) -> int:
        """Returns the current position in the buffer."""
        return self.__idx

    def __past_eof(self, index: int) -> bool:
        return index > self.size()

    def past_eof(self) -> bool:
        """Returns True if the current position is after the end of file."""
        return self.__past_eof(self.pos())

    def eof(self) -> bool:
        """Returns True if the current position is at/after the end of file."""
        return self.__past_eof(self.pos() + 1)

    def size(self) -> int:
        """Returns the size of the buffer."""
        return len(self.__buf)

    def buffer(self) -> bytearray:
        """Returns the buffer as a bytearray."""
        return bytearray(self.__buf)

    def pad(self, size: int) -> None:
        """Pads the buffer by 0s with the given size and advances the buffer position.\n
        Will advance the buffer position only if the position was at the end of the buffer.
        """
        if self.__idx == self.size():
            self.__idx += size

        self.__buf.extend(bytearray(size))

    def align_pos(self, size: int) -> int:
        """Aligns the current position to the given size.\n
        Advances the current position by (size - (current_position % size)), but only if it is not aligned.\n
        Returns the number of bytes skipped.
        """
        skipped = 0

        if self.pos() % size:
            skipped = size - (self.pos() % size)
            self.seek(skipped, Whence.CUR)

        return skipped

    def align(self, size: int) -> int:
        """Aligns the buffer to the given size.\n
        Extends the buffer from its end by (size - (buffer_size % size)), but only if it is not aligned.\n
        Will advance the buffer position only if the position was at the end of the buffer.\n
        Returns the number of bytes padded.
        """
        pad = 0

        if self.size() % size:
            pad = size - (self.size() % size)
            self.pad(pad)

        return pad

    def extend(self, buffer: bytearray) -> None:
        """Extends the BinaryReader's buffer with the given buffer.\n
        Does not advance buffer position.
        """
        self.__buf.extend(buffer)

    def trim(self, size: int) -> int:
        """Trims the buffer to the given size.\n
        If size is greater than the buffer's length, no bytes will be removed.\n
        If the position of the buffer was in the trimmed range, it will be set to the end of the buffer.\n
        Returns the number of bytes removed.
        """
        trimmed = 0

        if size >= 0:
            trimmed = self.size() - size

        if (trimmed > 0):
            self.__buf = self.__buf[:size]
            if (self.__idx > size):
                self.__idx = self.size()
        else:
            trimmed = 0

        return trimmed

    def seek(self, offset: int, whence: Whence = Whence.BEGIN) -> None:
        """Changes the current position of the buffer by the given offset.\n
        The seek is determined relative to the whence:\n
        Whence.BEGIN will seek relative to the start.\n
        Whence.CUR will seek relative to the current position.\n
        Whence.END will seek relative to the end (offset should be positive).
        """
        new_offset = self.__idx

        if whence == Whence.BEGIN:
            new_offset = offset
        elif whence == Whence.CUR:
            new_offset = self.__idx + offset
        elif whence == Whence.END:
            new_offset = len(self.__buf) - offset
        else:
            raise Exception('BinaryReader Error: invalid whence value.')

        if self.__past_eof(new_offset) or new_offset < 0:
            raise Exception(
                'BinaryReader Error: cannot seek farther than buffer length.')

        self.__idx = new_offset

    @contextmanager
    def seek_to(self, offset: int, whence: Whence = Whence.BEGIN) -> 'BinaryReader':
        """Same as `seek(offset, whence)`, but can be used with the `with` statement in a new context.\n
        Upon returning to the old context, the original position of the buffer before the `with` statement will be restored.\n
        Will return a reference of the BinaryReader to be used for `as` in the `with` statement.\n
        The original BinaryReader that this was called from can still be used instead of the return value.
        """
        prev_pos = self.__idx
        self.seek(offset, whence)
        yield self

        self.__idx = prev_pos

    def set_endian(self, endianness: Endian) -> None:
        """Sets the endianness of the BinaryReader."""
        self.__endianness = endianness
    
    def get_endian(self) -> Endian:
        """Returns the endianness of the BinaryReader."""
        return self.__endianness

    def set_encoding(self, encoding: str) -> None:
        """Sets the default encoding of the BinaryReader when reading/writing strings.\n
        Will throw an exception if the encoding is unknown.
        """
        str.encode('', encoding)
        self.__encoding = encoding

    @staticmethod
    def is_iterable(x) -> bool:
        return hasattr(x, '__iter__') and not isinstance(x, (str, bytes))
        
    
    def __read_type(self, fmt: str, count=None):
        i = self.__idx
        n = 1 if count is None else count
        size = FMT[fmt] * n
        if i + size > len(self.__buf):
            raise ValueError("BinaryReader Error: cannot read beyond buffer length.")

        fmt_str = (">" if self.__endianness else "<") + str(n) + fmt
        self.__idx += size
        result = struct.unpack_from(fmt_str, self.__buf, i)
        return result[0] if count is None else result

    def read_int64(self, count=None): return self.__read_type("q", count)
    def read_uint64(self, count=None): return self.__read_type("Q", count)
    def read_int32(self, count=None): return self.__read_type("i", count)
    def read_uint32(self, count=None): return self.__read_type("I", count)
    def read_int16(self, count=None): return self.__read_type("h", count)
    def read_uint16(self, count=None): return self.__read_type("H", count)
    def read_int8(self, count=None): return self.__read_type("b", count)
    def read_uint8(self, count=None): return self.__read_type("B", count)
    def read_float16(self, count=None): return self.__read_type("e", count)
    def read_float32(self, count=None): return self.__read_type("f", count)
    def read_float64(self, count=None): return self.__read_type("d", count)
    
    def read_type(self, format: str, count=None) -> Union[Tuple, int]:
        """Reads a value of the given type from the current position.\n
        If count is given, will return a tuple of values instead of 1 value.
        """
        if count is not None:
            return self.__read_type(format, count)
        return self.__read_type(format)[0]

    def read_bytes(self, size=1) -> bytes:
        """Reads a bytes object with the given size from the current position."""
        if size < 0:
            raise ValueError("size cannot be negative")

        end = self.__idx + size
        if end > len(self.__buf):
            raise ValueError("BinaryReader Error: can't read beyond buffer length.")

        raw = self.__buf[self.__idx:end]
        self.__idx = end
        return raw

    def read_str(self, size=None, encoding=None) -> str:
        """Reads a UTF-8 or UTF-16 string from the current position.
        
        If `size` is None, reads until the first null terminator (1 byte for UTF-8, 2 bytes for UTF-16).
        If `size` is given, reads exactly that many characters (not bytes).
        Uses the BinaryReader's encoding if none is provided.
        """
        encode = encoding or self.__encoding
        buf = self.__buf
        idx = self.__idx

        is_utf16 = encode.lower().replace('-', '') in {"utf16", "utf16le", "utf16be"}
        unit_size = 2 if is_utf16 else 1

        if size is None:
            chars = bytearray()
            while idx + unit_size <= len(buf):
                unit = buf[idx:idx + unit_size]
                if unit == b'\x00' * unit_size:
                    idx += unit_size
                    break
                chars.extend(unit)
                idx += unit_size
            self.__idx = idx
            return chars.decode(encode)

        if size < 0:
            raise ValueError('size cannot be negative')

        byte_count = size * unit_size
        end = idx + byte_count
        raw = buf[idx:end]
        self.__idx = end

        # Trim null terminator if present
        null_unit = b'\x00' * unit_size
        null_pos = raw.find(null_unit)
        if null_pos != -1:
            raw = raw[:null_pos]

        return raw.decode(encode)

    
    def read_str_at_offset(self, offset: int, size=None, encoding=None, whence = Whence.BEGIN) -> str:
        """Reads a string from a specific offset without changing the current read position."""
        current = self.__idx
        try:
            self.seek(offset, whence)
            return self.read_str(size, encoding)
        finally:
            self.seek(current, Whence.BEGIN)

    def read_str_to_token(self, token: str, encoding=None) -> str:
        """Reads a string until a string token is found.\n
        If encoding is `None` (default), will use the BinaryReader's encoding.
        """
        encode = encoding or self.__encoding

        i = 0
        string = bytearray()
        token_bytes = token.encode(encode)
        token_size = len(token_bytes)
        while self.__idx < len(self.__buf):
            string.append(self.__buf[self.__idx])
            self.__idx += 1
            if token_bytes == string[i : i + token_size]:
                break
            if len(string) >= token_size:
                i += 1

        return string.split(b'\x00', 1)[0].decode(encode)

    
    def read_array(self, type_name: str, count: int) -> np.ndarray:
        """Reads an array of values as a NumPy array using the specified type name."""
        if type_name not in _numpy_dtype_map:
            raise ValueError(f"Unsupported type name '{type_name}' for array reading.")

        dtype_str = _numpy_dtype_map[type_name]
        dtype = np.dtype(dtype_str).newbyteorder('<' if self.__endianness == Endian.LITTLE else '>')
        size = dtype.itemsize * count

        if self.__idx + size > len(self.__buf):
            raise ValueError("BinaryReader Error: can't read beyond buffer length.")

        array = np.frombuffer(self.__buf, dtype=dtype, count=count, offset=self.__idx)
        self.__idx += size
        return array

    def read_structured_array(self, dtype: Union[str, np.dtype], count: int) -> np.ndarray:
        """Reads a structured NumPy array based on a given dtype and element count."""
        if isinstance(dtype, str):
            dtype = np.dtype(dtype)

        dtype = dtype.newbyteorder('<' if self.__endianness == Endian.LITTLE else '>')
        size = dtype.itemsize * count

        if self.__idx + size > len(self.__buf):
            raise ValueError("BinaryReader Error: can't read beyond buffer length.")

        array = np.frombuffer(self.__buf, dtype=dtype, count=count, offset=self.__idx)
        self.__idx += size
        return array


    def read_struct(self, cls: type, count=None, *args) -> BrStruct:
        """Creates and returns an instance of the given `cls` after calling its `__br_read__` method.\n
        `cls` must be a subclass of BrStruct.\n
        If count is given, will return a tuple of values instead of 1 value.\n
        Additional arguments given after `count` will be passed to the `__br_read__` method of `cls`.\n
        """
        if not (cls and issubclass(cls, BrStruct)):
            raise Exception(
                f'BinaryReader Error: {cls} is not a subclass of BrStruct.')

        if count is not None:
            result = []

            for _ in range(count):
                br_struct = cls()
                br_struct.__br_read__(self, *args)
                result.append(br_struct)

            return tuple(result)

        br_struct = cls()
        br_struct.__br_read__(self, *args)

        return br_struct

    def __write_type(self, format: str, value, is_iterable: bool) -> None:
        i = self.__idx

        end = ">" if self.__endianness else "<"

        count = 1
        if is_iterable or type(value) is bytes:
            count = len(value)

        if i + (FMT[format] * count) > len(self.__buf):
            self.pad(FMT[format] * count)
        else:
            self.__idx += FMT[format] * count

        if is_iterable:
            struct.pack_into(end + str(count) + format, self.__buf, i, *value)
        else:
            struct.pack_into(end + str(count) + format, self.__buf, i, value)
    
            
    def write_bytes(self, value: bytes) -> None:
        """Writes a bytes object to the buffer."""
        self.__write_type("s", value, is_iterable=False)

    def write_str(self, string: str, null=True, encoding=None) -> int:
        """Writes a whole string to the buffer.\n
        If null is `True`, will append a null byte (`0x00`) after the string.\n
        If encoding is `None` (default), will use the BinaryReader's encoding.\n
        Returns the number of bytes written (including the null byte if it was added).
        """
        bytes_obj = string.encode(encoding or self.__encoding) + (b'\x00' if null else b'')
        self.write_bytes(bytes_obj)
        return len(bytes_obj)

    def write_str_fixed(self, string: str, size: int, encoding=None) -> None:
        """Writes a whole string with the given size to the buffer.\n
        If the string's size after being encoded is less than size, the remaining size will be filled with null bytes.\n
        If it's more than size, the encoded bytes will be trimmed to size.\n
        If encoding is `None` (default), will use the BinaryReader's encoding.
        """

        if size < 0:
            raise ValueError('size cannot be negative')

        self.write_bytes(string.encode(encoding or self.__encoding)[:size].ljust(size, b'\x00'))

    def write_int64(self, value: int) -> None:
        """Writes a signed 64-bit integer.\n
        If value is iterable, will write all of the elements in the given iterable.
        """
        self.__write_type("q", value, self.is_iterable(value))

    def write_uint64(self, value: int) -> None:
        """Writes an unsigned 64-bit integer.\n
        If value is iterable, will write all of the elements in the given iterable.
        """
        self.__write_type("Q", value, self.is_iterable(value))

    def write_int32(self, value: int) -> None:
        """Writes a signed 32-bit integer.\n
        If value is iterable, will write all of the elements in the given iterable.
        """
        self.__write_type("i", value, self.is_iterable(value))

    def write_uint32(self, value: int) -> None:
        """Writes an unsigned 32-bit integer.\n
        If value is iterable, will write all of the elements in the given iterable.
        """
        self.__write_type("I", value, self.is_iterable(value))

    def write_int16(self, value: int) -> None:
        """Writes a signed 16-bit integer.\n
        If value is iterable, will write all of the elements in the given iterable.
        """
        self.__write_type("h", value, self.is_iterable(value))

    def write_uint16(self, value: int) -> None:
        """Writes an unsigned 16-bit integer.\n
        If value is iterable, will write all of the elements in the given iterable.
        """
        self.__write_type("H", value, self.is_iterable(value))

    def write_int8(self, value: int) -> None:
        """Writes a signed 8-bit integer.\n
        If value is iterable, will write all of the elements in the given iterable.
        """
        self.__write_type("b", value, self.is_iterable(value))

    def write_uint8(self, value: int) -> None:
        """Writes an unsigned 8-bit integer.\n
        If value is iterable, will write all of the elements in the given iterable.
        """
        self.__write_type("B", value, self.is_iterable(value))

    def write_float32(self, value: float) -> None:
        """Writes a 32-bit float.\n
        If value is iterable, will write all of the elements in the given iterable.
        """
        self.__write_type("f", value, self.is_iterable(value))

    def write_float16(self, value: float) -> None:
        """Writes a 16-bit float (half-float).\n
        If value is iterable, will write all of the elements in the given iterable.
        """
        self.__write_type("e", value, self.is_iterable(value))
    
    def write_float64(self, value: float) -> None:
        """Writes a 64-bit float.\n
        If value is iterable, will write all of the elements in the given iterable.
        """
        self.__write_type("d", value, self.is_iterable(value))

    def write_struct(self, value: BrStruct, *args) -> None:
        """Calls the given value's `__br_write__` method.\n
        `value` must be an instance of a class that inherits BrStruct.\n
        If value is iterable, will call the `__br_write__` method of all elements in the given iterable.\n
        Additional arguments given after `value` will be passed to the `__br_write__` method of `value`.\n
        """
        if not isinstance(value, BrStruct) and not (self.is_iterable(value) and all(isinstance(e, BrStruct) for e in value)):
            raise Exception(
                f'BinaryReader Error: {value} is not an instance of BrStruct.')

        if self.is_iterable(value):
            for s in value:
                s.__br_write__(self, *args)
        else:
            value.__br_write__(self, *args)
