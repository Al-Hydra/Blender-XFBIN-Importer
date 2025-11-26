from ...xfbin_lib.xfbin.util import *
from enum import Enum
import numpy as np


# ─────────────────────────────
# TGA Data Type Constants
# ─────────────────────────────

class DataTypes(Enum):
    NO_IMAGE_DATA = 0
    UNCOMPRESSED_COLOR_MAPPED = 1
    UNCOMPRESSED_TRUE_COLOR = 2
    UNCOMPRESSED_BLACK_AND_WHITE = 3
    RUN_LENGTH_ENCODED_COLOR_MAPPED = 9
    RUN_LENGTH_ENCODED_TRUE_COLOR = 10
    RUN_LENGTH_ENCODED_BLACK_AND_WHITE = 11


# ─────────────────────────────
# TGA Structure
# ─────────────────────────────

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
        """Read TGA header only - image data is read separately based on format."""
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
        
        # Read color map if present
        if self.ColorMapType == 1:
            palette_entry_bytes = self.ColorMapDepth // 8
            self.PaletteData = br.read_bytes(self.ColorMapLength * palette_entry_bytes)

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

        if self.ColorMapType == 1:
            br.write_bytes(self.PaletteData)

        br.write_bytes(self.ImageData)

    def get_rgba(self):
        """
        Convenience method to get RGBA8888 pixel data from TGA.
        Similar to PNG.get_rgba() method.
        
        Returns:
            bytes: Image data in RGBA8888 format (always RGBA regardless of source format).
        """
        return convert_to_rgba8888(self)


# ─────────────────────────────
# Reading TGA Files
# ─────────────────────────────

def read_tga(tga_bytes):
    """
    Read a TGA file from bytes.
    
    Args:
        tga_bytes (bytes): The raw TGA file data.
    
    Returns:
        TGA: The TGA object with raw image data.
    """
    br = BinaryReader(tga_bytes, endianness=Endian.LITTLE, encoding="cp932")
    tga = br.read_struct(TGA)
    
    # Read image data based on compression type
    if tga.DataTypeCode in [DataTypes.RUN_LENGTH_ENCODED_TRUE_COLOR.value,
                            DataTypes.RUN_LENGTH_ENCODED_COLOR_MAPPED.value,
                            DataTypes.RUN_LENGTH_ENCODED_BLACK_AND_WHITE.value]:
        _read_rle_image_data(br, tga)
    elif tga.DataTypeCode in [DataTypes.UNCOMPRESSED_TRUE_COLOR.value,
                              DataTypes.UNCOMPRESSED_COLOR_MAPPED.value,
                              DataTypes.UNCOMPRESSED_BLACK_AND_WHITE.value]:
        _read_uncompressed_image_data(br, tga)
    elif tga.DataTypeCode == DataTypes.NO_IMAGE_DATA.value:
        tga.ImageData = b""
    else:
        raise ValueError(f"Unsupported TGA DataTypeCode: {tga.DataTypeCode}")
    
    return tga


def _read_rle_image_data(br: BinaryReader, tga: TGA):
    """
    Read RLE-compressed TGA image data.
    
    Args:
        br (BinaryReader): The binary reader positioned at image data.
        tga (TGA): The TGA object to populate with image data.
    """
    pixel_size = tga.BitsPerPixel // 8
    pixel_count = tga.Width * tga.Height
    pixels = bytearray()

    while len(pixels) < pixel_count * pixel_size:
        packet_header = br.read_uint8()
        if packet_header & 0x80:  # RLE packet
            run_length = (packet_header & 0x7F) + 1
            pixel_data = br.read_bytes(pixel_size)
            pixels.extend(pixel_data * run_length)
        else:  # Raw packet
            run_length = (packet_header & 0x7F) + 1
            pixels.extend(br.read_bytes(run_length * pixel_size))

    tga.ImageData = bytes(pixels)
    
    # Handle vertical flip if needed
    if not (tga.ImageDescriptor & 0x20):
        tga.ImageData = _flip_image_vertically(tga.ImageData, tga.Width, tga.Height, pixel_size)


def _read_uncompressed_image_data(br: BinaryReader, tga: TGA):
    """
    Read uncompressed TGA image data.
    
    Args:
        br (BinaryReader): The binary reader positioned at image data.
        tga (TGA): The TGA object to populate with image data.
    """
    bytes_per_pixel = tga.BitsPerPixel // 8
    image_data_size = tga.Width * tga.Height * bytes_per_pixel
    tga.ImageData = br.read_bytes(image_data_size)
    
    # If the image is bottom-left origin, flip it to top-left
    if not (tga.ImageDescriptor & 0x20):
        tga.ImageData = _flip_image_vertically(tga.ImageData, tga.Width, tga.Height, bytes_per_pixel)


def _flip_image_vertically(image_data: bytes, width: int, height: int, bytes_per_pixel: int) -> bytes:
    """
    Flip image data vertically.
    
    Args:
        image_data (bytes): The raw image data.
        width (int): The width of the image.
        height (int): The height of the image.
        bytes_per_pixel (int): The number of bytes per pixel.
    
    Returns:
        bytes: The vertically flipped image data.
    """
    row_size = width * bytes_per_pixel
    flipped_data = bytearray()

    for row in range(height):
        start = (height - 1 - row) * row_size
        end = start + row_size
        flipped_data.extend(image_data[start:end])

    return bytes(flipped_data)


# ─────────────────────────────
# Converting to RGBA8888
# ─────────────────────────────

def convert_to_rgba8888(tga: TGA) -> bytes:
    """
    Convert TGA image data to RGBA8888 format regardless of source format.
    
    Args:
        tga (TGA): The TGA object to convert.
    
    Returns:
        bytes: The image data in RGBA8888 format.
    """
    data_type = tga.DataTypeCode
    bits_per_pixel = tga.BitsPerPixel
    
    # Handle color-mapped (indexed) images
    if data_type in [DataTypes.UNCOMPRESSED_COLOR_MAPPED.value, 
                     DataTypes.RUN_LENGTH_ENCODED_COLOR_MAPPED.value]:
        return _color_mapped_to_rgba8888(tga)
    
    # Handle true color images
    elif data_type in [DataTypes.UNCOMPRESSED_TRUE_COLOR.value,
                       DataTypes.RUN_LENGTH_ENCODED_TRUE_COLOR.value]:
        return _true_color_to_rgba8888(tga)
    
    # Handle grayscale images
    elif data_type in [DataTypes.UNCOMPRESSED_BLACK_AND_WHITE.value,
                       DataTypes.RUN_LENGTH_ENCODED_BLACK_AND_WHITE.value]:
        return _grayscale_to_rgba8888(tga)
    
    else:
        raise ValueError(f"Unsupported TGA format: DataTypeCode={data_type}, BitsPerPixel={bits_per_pixel}")


def _color_mapped_to_rgba8888(tga: TGA) -> bytes:
    """
    Convert color-mapped (indexed) TGA to RGBA8888.
    
    Args:
        tga (TGA): The TGA object with color-mapped data.
    
    Returns:
        bytes: RGBA8888 pixel data.
    """
    palette_entry_bytes = tga.ColorMapDepth // 8
    
    # Parse palette based on depth
    if palette_entry_bytes == 3:  # RGB888 palette
        palette_array = np.frombuffer(tga.PaletteData, dtype=np.uint8).reshape(-1, 3)
        # Convert BGR to RGB and add alpha
        palette_rgba = np.zeros((len(palette_array), 4), dtype=np.uint8)
        palette_rgba[:, 0] = palette_array[:, 2]  # R
        palette_rgba[:, 1] = palette_array[:, 1]  # G
        palette_rgba[:, 2] = palette_array[:, 0]  # B
        palette_rgba[:, 3] = 255  # A
    elif palette_entry_bytes == 4:  # BGRA8888 palette
        palette_array = np.frombuffer(tga.PaletteData, dtype=np.uint8).reshape(-1, 4)
        # Convert BGRA to RGBA
        palette_rgba = palette_array[:, [2, 1, 0, 3]]
    else:
        raise ValueError(f"Unsupported palette depth: {tga.ColorMapDepth} bits")
    
    # Map indices to colors
    indices = np.frombuffer(tga.ImageData, dtype=np.uint8)
    pixels = palette_rgba[indices]
    
    return pixels.tobytes()


def _true_color_to_rgba8888(tga: TGA) -> bytes:
    """
    Convert true color TGA to RGBA8888.
    
    Args:
        tga (TGA): The TGA object with true color data.
    
    Returns:
        bytes: RGBA8888 pixel data.
    """
    if tga.BitsPerPixel == 32:
        # BGRA8888 -> RGBA8888
        color_array = np.frombuffer(tga.ImageData, dtype=np.uint8).reshape(-1, 4)
        rgba_array = color_array[:, [2, 1, 0, 3]]  # Swap B and R channels
        return rgba_array.tobytes()
    
    elif tga.BitsPerPixel == 24:
        # BGR888 -> RGBA8888
        color_array = np.frombuffer(tga.ImageData, dtype=np.uint8).reshape(-1, 3)
        rgba_array = np.zeros((len(color_array), 4), dtype=np.uint8)
        rgba_array[:, 0] = color_array[:, 2]  # R
        rgba_array[:, 1] = color_array[:, 1]  # G
        rgba_array[:, 2] = color_array[:, 0]  # B
        rgba_array[:, 3] = 255  # A
        return rgba_array.tobytes()
    
    elif tga.BitsPerPixel == 16:
        # RGB555 or ARGB1555 -> RGBA8888
        color_data = np.frombuffer(tga.ImageData, dtype=np.uint16)
        rgba_array = np.zeros((len(color_data), 4), dtype=np.uint8)
        
        # Extract RGB555 components (bits 0-14)
        rgba_array[:, 2] = ((color_data & 0x001F) << 3) | ((color_data & 0x001F) >> 2)  # B
        rgba_array[:, 1] = ((color_data & 0x03E0) >> 2) | ((color_data & 0x03E0) >> 7)  # G
        rgba_array[:, 0] = ((color_data & 0x7C00) >> 7) | ((color_data & 0x7C00) >> 12)  # R
        
        # Check if alpha bit is present (bit 15)
        rgba_array[:, 3] = np.where(color_data & 0x8000, 255, 0)  # A
        
        return rgba_array.tobytes()
    
    else:
        raise ValueError(f"Unsupported true color bit depth: {tga.BitsPerPixel}")


def _grayscale_to_rgba8888(tga: TGA) -> bytes:
    """
    Convert grayscale TGA to RGBA8888.
    
    Args:
        tga (TGA): The TGA object with grayscale data.
    
    Returns:
        bytes: RGBA8888 pixel data.
    """
    if tga.BitsPerPixel == 8:
        # L8 -> RGBA8888
        gray_array = np.frombuffer(tga.ImageData, dtype=np.uint8).reshape(-1, 1)
        rgba_array = np.concatenate([gray_array, gray_array, gray_array, 
                                     np.full((gray_array.shape[0], 1), 255, dtype=np.uint8)], axis=1)
        return rgba_array.tobytes()
    
    elif tga.BitsPerPixel == 16:
        # LA88 (Luminance + Alpha) -> RGBA8888
        data_array = np.frombuffer(tga.ImageData, dtype=np.uint8).reshape(-1, 2)
        luminance = data_array[:, 0:1]
        alpha = data_array[:, 1:2]
        rgba_array = np.concatenate([luminance, luminance, luminance, alpha], axis=1)
        return rgba_array.tobytes()
    
    else:
        raise ValueError(f"Unsupported grayscale bit depth: {tga.BitsPerPixel}")


# ─────────────────────────────
# Writing TGA Files
# ─────────────────────────────

def rgbaToTGA(width: int, height: int, textureData: bytes) -> bytes:
    """
    Create a TGA file from RGBA8888 pixel data.
    
    Args:
        width (int): Image width.
        height (int): Image height.
        textureData (bytes): RGBA8888 pixel data.
    
    Returns:
        bytes: TGA file data.
    """
    tga = TGA()
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
    tga.ImageDescriptor = 0x20  # Top-left origin
    
    # Convert RGBA to BGRA for TGA format
    rgba_array = np.frombuffer(textureData, dtype=np.uint8).reshape(-1, 4)
    bgra_array = rgba_array[:, [2, 1, 0, 3]]
    tga.ImageData = bgra_array.tobytes()

    with BinaryReader(bytearray(), Endian.LITTLE, 'cp932') as br:
        br.write_struct(tga)
        return br.buffer()


def indexed8ToTGA(width: int, height: int, indices: bytes, colorPalette: list) -> bytes:
    """
    Create a TGA file from 8-bit indexed data.
    
    Args:
        width (int): Image width.
        height (int): Image height.
        indices (bytes): Index data (one byte per pixel).
        colorPalette (list): RGBA color palette.
    
    Returns:
        bytes: TGA file data.
    """
    indices_array = np.frombuffer(indices, dtype=np.uint8) if isinstance(indices, bytes) else np.array(indices, dtype=np.uint8)
    colorPalette_array = np.array(colorPalette, dtype=np.uint8)
    
    # Map indices to colors
    pixels = colorPalette_array[indices_array]
    rgba8888_data = pixels.flatten().tobytes()
    
    return rgbaToTGA(width, height, rgba8888_data)


def indexed4ToTGA(width: int, height: int, indices: bytes, colorPalette: list) -> bytes:
    """
    Create a TGA file from 4-bit indexed data.
    
    Args:
        width (int): Image width.
        height (int): Image height.
        indices (bytes): Index data (two 4-bit indices per byte).
        colorPalette (list): RGBA color palette.
    
    Returns:
        bytes: TGA file data.
    """
    indices_array = np.frombuffer(indices, dtype=np.uint8) if isinstance(indices, bytes) else np.array(indices, dtype=np.uint8)
    colorPalette_array = np.array(colorPalette, dtype=np.uint8)
    
    # Extract lower and upper nibbles
    lower_nibble = indices_array & 0xF
    upper_nibble = indices_array >> 4
    
    # Map to colors
    pixels_lower = colorPalette_array[lower_nibble]
    pixels_upper = colorPalette_array[upper_nibble]
    
    # Interleave pixels
    pixels = np.empty((len(indices_array) * 2, 4), dtype=np.uint8)
    pixels[0::2] = pixels_lower
    pixels[1::2] = pixels_upper
    
    rgba8888_data = pixels.flatten().tobytes()
    
    return rgbaToTGA(width, height, rgba8888_data)


# ─────────────────────────────
# Color Conversion Utilities
# ─────────────────────────────

def BGRA_to_RGBA(data: bytes) -> bytes:
    """Convert BGRA to RGBA."""
    color_array = np.frombuffer(data, dtype=np.uint8).reshape(-1, 4)
    rgba_array = color_array[:, [2, 1, 0, 3]]
    return rgba_array.tobytes()


def BGRA_to_ARGB(data: bytes) -> bytes:
    """Convert BGRA to ARGB."""
    color_array = np.frombuffer(data, dtype=np.uint8).reshape(-1, 4)
    argb_array = color_array[:, [3, 2, 1, 0]]
    return argb_array.tobytes()

