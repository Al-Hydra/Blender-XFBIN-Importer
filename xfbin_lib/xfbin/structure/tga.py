from ..util import *
from enum import Enum
from itertools import chain
import numpy as np


class TGA(BrStruct):
    def __init__(self):
        self.ColorMapType = 0
        self.DataTypeCode = 0
        self.ColorMapOrigin = 0
        self.ColorMapLength = 0
        self.ColorMapDepth = 0
        self.x_Origin = 0
        self.y_Origin = 0
        self.Width = 0
        self.Height = 0
        self.BitsPerPixel = 0
        self.ImageDescriptor = 0
        self.ImageID = ""
        self.ImageData = b""
        self.PaletteData = b""

    def __br_read__(self, br: BinaryReader):
        self.IdLength = br.read_uint8()
        self.ColorMapType = br.read_uint8()
        self.DataTypeCode = br.read_uint8()
        self.ColorMapOrigin = br.read_uint16()
        self.ColorMapLength = br.read_uint16()
        self.ColorMapDepth = br.read_uint8()
        self.x_Origin = br.read_uint16()
        self.y_Origin = br.read_uint16()
        self.Width = br.read_uint16()
        self.Height = br.read_uint16()
        self.BitsPerPixel = br.read_uint8()
        self.ImageDescriptor = br.read_uint8()
        self.ImageID = br.read_str(self.IdLength)
        self.ImageData = br.read_bytes(self.Width * self.Height * self.BitsPerPixel // 8)
    

    def __br_write__(self, br: BinaryReader):
        br.write_uint8(len(self.ImageID))
        br.write_uint8(self.ColorMapType)
        br.write_uint8(self.DataTypeCode)
        br.write_uint16(self.ColorMapOrigin)
        br.write_uint16(self.ColorMapLength)
        br.write_uint8(self.ColorMapDepth)
        br.write_uint16(self.x_Origin)
        br.write_uint16(self.y_Origin)
        br.write_uint16(self.Width)
        br.write_uint16(self.Height)
        br.write_uint8(self.BitsPerPixel)
        br.write_uint8(self.ImageDescriptor)
        br.write_str(self.ImageID)

        if self.DataTypeCode == 1 or 9:
            br.write_bytes(self.PaletteData)

        br.write_bytes(self.ImageData)



class DataTypes(Enum):
    NO_IMAGE_DATA = 0
    UNCOMPRESSED_COLOR_MAPPED = 1
    UNCOMPRESSED_TRUE_COLOR = 2
    UNCOMPRESSED_BLACK_AND_WHITE = 3
    RUN_LENGTH_ENCODED_COLOR_MAPPED = 9
    RUN_LENGTH_ENCODED_TRUE_COLOR = 10
    RUN_LENGTH_ENCODED_BLACK_AND_WHITE = 11


def BGRA_to_RGBA(data: bytes) -> bytes:
    new_data = bytearray(data)
    for i in range(0, len(new_data), 4):
        b = new_data[i]
        g = new_data[i + 1]
        r = new_data[i + 2]
        a = new_data[i + 3]
        new_data[i] = r
        new_data[i + 1] = g
        new_data[i + 2] = b
        new_data[i + 3] = a

    
    return bytes(new_data)

def BGRA_to_ARGB(data: bytes) -> bytes:
    new_data = bytearray(data)
    for i in range(0, len(new_data), 4):
        b = new_data[i]
        g = new_data[i + 1]
        r = new_data[i + 2]
        a = new_data[i + 3]
        new_data[i] = a
        new_data[i + 1] = r
        new_data[i + 2] = g
        new_data[i + 3] = b

    
    return bytes(new_data)


def rgbaToTGA(width,height,textureData):
    tga = TGA()

    tga.ImageID = ""
    tga.ColorMapType = 1
    tga.DataTypeCode = DataTypes.UNCOMPRESSED_TRUE_COLOR.value
    tga.ColorMapOrigin = 0
    tga.ColorMapLength = 0
    tga.ColorMapDepth = 0
    tga.x_Origin = 0
    tga.y_Origin = 0
    tga.Width = width
    tga.Height = height
    tga.BitsPerPixel = 32
    tga.ImageDescriptor = 0
    tga.PaletteData = []
    tga.ImageData = bytes(textureData)


def indexed8ToTGA(width, height, indices, colorPalette):
    tga = TGA()

    # Convert indices and colorPalette to NumPy arrays
    indices_array = np.array(indices, dtype=np.uint8)
    colorPalette_array = np.array(colorPalette, dtype=np.uint8)

    # Use indices_array as index to colorPalette_array
    pixels = colorPalette_array[indices_array]

    # Flatten pixels array and convert to bytes
    pixels_bytes = pixels.flatten().tobytes()

    tga.ImageID = ""
    tga.ColorMapType = 0
    tga.DataTypeCode = DataTypes.UNCOMPRESSED_TRUE_COLOR.value
    tga.ColorMapOrigin = 0
    tga.ColorMapLength = 0
    tga.ColorMapDepth = 0
    tga.x_Origin = 0
    tga.y_Origin = 0
    tga.Width = width
    tga.Height = height
    tga.BitsPerPixel = 32
    tga.ImageDescriptor = 0
    tga.ImageData = pixels_bytes

    with BinaryReader(bytearray(), Endian.LITTLE, 'cp932') as br:
        br.write_struct(tga)

        return br.buffer()


def indexed4ToTGA(width, height, indices, colorPalette):
    tga = TGA()

    indices  = np.array(indices, dtype=np.uint8)
    colorPalette = np.array(colorPalette, dtype=np.uint8)

    # Use bitwise operations to extract lower and upper nibbles
    lower_nibble = indices & 0xF
    upper_nibble = indices >> 4

    #Create pixels array using NumPy array operations
    pixels = np.concatenate((colorPalette[lower_nibble], colorPalette[upper_nibble]), axis=1)

    # Flatten pixels array and convert to bytes
    pixels_bytes = pixels.flatten().tobytes()


    tga.ImageID = ""
    tga.ColorMapType = 0
    tga.DataTypeCode = DataTypes.UNCOMPRESSED_TRUE_COLOR.value
    tga.ColorMapOrigin = 0
    tga.ColorMapLength = 0
    tga.ColorMapDepth = 0
    tga.x_Origin = 0
    tga.y_Origin = 0
    tga.Width = width
    tga.Height = height
    tga.BitsPerPixel = 32
    tga.ImageDescriptor = 0
    tga.ImageData = pixels_bytes

    with BinaryReader(bytearray(), Endian.LITTLE, 'cp932') as br:
        br.write_struct(tga)

        return br.buffer()


def read_tga(tga_bytes):
    br = BinaryReader(tga_bytes, endianness= Endian.LITTLE, encoding="cp932")
    tga = br.read_struct(TGA)
    return tga

