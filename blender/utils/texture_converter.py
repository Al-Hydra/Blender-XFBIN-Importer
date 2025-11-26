from ...xfbin_lib.xfbin.structure.nut import *
from .tga import *
from ...xfbin_lib.xfbin.structure.dds import *
from .png.png import *
from .blockCompressor import blockCompressor
import numpy as np


pixel_formats_map = {
    "DXT1": 0,
    "DXT3": 1,
    "DXT5": 2,
    "B5G5R5A1": 6,
    "B4G4R4A4": 7,
    "B5G6R5": 8,
    "R8G8B8A8": 17,
}

test_path = r"G:\Dev\Blender-XFBIN-Importer\blender\utils"
def rgba8888_to_rgb565(rgba_data: bytearray, width, height, order=['r', 'g', 'b', 'a'], endianness='little'):
    """
    Convert RGBA8888 to a 16-bit RGB565 format with fixed bits:
    - R = 5 bits
    - G = 6 bits
    - B = 5 bits

    Parameters:
    - rgba_data: input bytes (R8G8B8A8)
    - width: width of the image
    - height: height of the image
    - order: list of channels in output order, e.g. ['r','g','b','a'] or ['a','r','g','b']
    - endianness: 'little' or 'big'

    Returns:
    - packed 16-bit bytes
    """
    if set(order) != {'r', 'g', 'b', 'a'}:
        raise ValueError("order must contain exactly ['r','g','b','a'] in some permutation")

    rgba_array = np.frombuffer(rgba_data, dtype=np.uint8).reshape(height, width, 4)
    channel_map = {'r': rgba_array[:, :, 0],
                   'g': rgba_array[:, :, 1],
                   'b': rgba_array[:, :, 2],
                   'a': rgba_array[:, :, 3]}

    # fixed bit widths
    bit_width = {'r': 5, 'g': 6, 'b': 5}
    packed = np.zeros((height, width), dtype=np.uint16)
    shift = 16
    for ch in ['r', 'g', 'b']:
        shift -= bit_width[ch]
        val = channel_map[ch] >> (8 - bit_width[ch])
        packed |= (val.astype(np.uint16) << shift)

    if endianness == 'big':
        packed = packed.byteswap()

    return packed.tobytes()

def rgba8888_to_rgba5551(rgba_data: bytearray, width, height, order=['r', 'g', 'b', 'a'], endianness='little'):
    """
    Convert RGBA8888 to a 16-bit 5551 format with fixed bits:
    - R, G, B = 5 bits each
    - A = 1 bit

    Parameters:
    - rgba_data: input bytes (R8G8B8A8)
    - width: width of the image
    - height: height of the image
    - order: list of channels in output order, e.g. ['r','g','b','a'] or ['a','r','g','b']
    - endianness: 'little' or 'big'
    
    Returns:
    - packed 16-bit bytes
    """
    if set(order) != {'r','g','b','a'}:
        raise ValueError("order must contain exactly ['r','g','b','a'] in some permutation")

    rgba_array = np.frombuffer(rgba_data, dtype=np.uint8).reshape(height, width, 4)
    channel_map = {'r': rgba_array[:, :, 0],
                   'g': rgba_array[:, :, 1],
                   'b': rgba_array[:, :, 2],
                   'a': rgba_array[:, :, 3]}

    # fixed bit widths
    bit_width = {'r':5, 'g':5, 'b':5, 'a':1}
    packed = np.zeros((height, width), dtype=np.uint16)
    shift = 16
    for ch in order:
        shift -= bit_width[ch]
        val = channel_map[ch] >> (8 - bit_width[ch])
        packed |= (val.astype(np.uint16) << shift)

    if endianness == 'big':
        packed = packed.byteswap()

    return packed.tobytes()

def rgba8888_to_rgba4444(rgba_data: bytearray, width, height, order=['r', 'g', 'b', 'a'], endianness='little'):
    """
    Converts RGBA8888 data to RGBA4444 format.

    Args:
        rgba_data (bytearray): Input RGBA8888 data.
        width (int): Width of the image.
        height (int): Height of the image.
        order (list): Channel order, default is ['r', 'g', 'b', 'a'].
        endianness (str): Byte order, 'little' or 'big'.

    Returns:
        bytearray: Converted RGBA4444 data.
    """
    if set(order) != {'r', 'g', 'b', 'a'}:
        raise ValueError("order must contain exactly ['r','g','b','a'] in some permutation")

    rgba_array = np.frombuffer(rgba_data, dtype=np.uint8).reshape(height, width, 4)
    channel_map = {'r': rgba_array[:, :, 0],
                   'g': rgba_array[:, :, 1],
                   'b': rgba_array[:, :, 2],
                   'a': rgba_array[:, :, 3]}

    # fixed bit widths
    bit_width = {'r': 4, 'g': 4, 'b': 4, 'a': 4}
    packed = np.zeros((height, width), dtype=np.uint16)
    shift = 16
    for ch in order:
        shift -= bit_width[ch]
        val = channel_map[ch] >> (8 - bit_width[ch])
        packed |= (val.astype(np.uint16) << shift)

    if endianness == 'big':
        packed = packed.byteswap()

    return packed.tobytes()


def rgba8888_to_dxt1(rgba_data: bytearray, width: int, height: int, order=[], endianness='little') -> bytes:
    dxt1_data = blockCompressor.compress_bc1_intel(rgba_data, width, height)
    return dxt1_data

def rgba8888_to_dxt3(rgba_data: bytearray, width: int, height: int, order=[], endianness='little') -> bytes:
    dxt3_data = blockCompressor.compress_dxt3(rgba_data, width, height)
    return dxt3_data

def rgba8888_to_dxt5(rgba_data: bytearray, width: int, height: int, order=[], endianness='little') -> bytes:
    dxt5_data = blockCompressor.compress_bc3_intel(rgba_data, width, height)
    return dxt5_data
    


def rgb565_to_rgba8888(rgb565_data: bytearray, width, height):
    rgb565_array = np.frombuffer(rgb565_data, dtype=np.uint16).reshape(height, width)
    channel_map = {
        'r': ((rgb565_array >> 11) & 0x1F) << 3,
        'g': ((rgb565_array >> 5) & 0x3F) << 2,
        'b': (rgb565_array & 0x1F) << 3,
        'a': np.full((height, width), 255, dtype=np.uint8)
    }
    rgba8888 = np.stack((channel_map['r'], channel_map['g'], channel_map['b'], channel_map['a']), axis=-1).astype(np.uint8)

    return rgba8888.tobytes()


def rgba5551_to_rgba8888(rgba5551_data: bytearray, width, height):
    rgba5551_array = np.frombuffer(rgba5551_data, dtype=np.uint16).reshape(height, width)
    channel_map = {
        'r': ((rgba5551_array >> 11) & 0x1F) << 3,
        'g': ((rgba5551_array >> 6) & 0x1F) << 3,
        'b': ((rgba5551_array >> 1) & 0x1F) << 3,
        'a': (rgba5551_array & 0x01) * 255
    }
    rgba8888 = np.stack((channel_map['r'], channel_map['g'], channel_map['b'], channel_map['a']), axis=-1).astype(np.uint8)

    return rgba8888.tobytes()


def rgba4444_to_rgba8888(rgba4444_data: bytearray, width, height):
    rgba4444_array = np.frombuffer(rgba4444_data, dtype=np.uint16).reshape(height, width)
    channel_map = {
        'r': ((rgba4444_array >> 12) & 0x0F) << 4,
        'g': ((rgba4444_array >> 8) & 0x0F) << 4,
        'b': ((rgba4444_array >> 4) & 0x0F) << 4,
        'a': (rgba4444_array & 0x0F) << 4
    }
    rgba8888 = np.stack((channel_map['r'], channel_map['g'], channel_map['b'], channel_map['a']), axis=-1).astype(np.uint8)

    return rgba8888.tobytes()


def rgba_to_bgra(rgba_data: bytearray):
    rgba_array = np.frombuffer(rgba_data, dtype=np.uint8).reshape(-1, 4)
    rgba_array = rgba_array[:, [2, 1, 0, 3]]  # Swap R and B channels
    return rgba_array.tobytes()

def rgba_to_abgr(rgba_data: bytearray):
    rgba_array = np.frombuffer(rgba_data, dtype=np.uint8).reshape(-1, 4)
    rgba_array = rgba_array[:, [3, 2, 1, 0]]  # Rearrange to ABGR
    return rgba_array.tobytes()

def rgba_to_argb(rgba_data: bytearray):
    rgba_array = np.frombuffer(rgba_data, dtype=np.uint8).reshape(-1, 4)
    rgba_array = rgba_array[:, [3, 0, 1, 2]]  # Rearrange to ARGB
    return rgba_array.tobytes()


from_rgba8888_function_map = {
    "DXT1": rgba8888_to_dxt1,
    "DXT3": rgba8888_to_dxt3,
    "DXT5": rgba8888_to_dxt5,
    "B4G4R4A4": rgba8888_to_rgba4444,
    "B5G5R5A1": rgba8888_to_rgba5551,
    "B5G6R5": rgba8888_to_rgb565,
}


to_rgba8888_function_map = {
    "DXT1": blockCompressor.decompress_bc1_intel,
    "DXT3": blockCompressor.decompress_dxt3,
    "DXT5": blockCompressor.decompress_bc3_intel,
    "B4G4R4A4": rgba4444_to_rgba8888,
    "B5G5R5A1": rgba5551_to_rgba8888,
    "B5G6R5": rgb565_to_rgba8888,
}


def DDS_to_NutTexture(dds, target_format: str):
    dds: BrDDS
    nut = NutTexture()

    nut.width = dds.header.width
    nut.height = dds.header.height
    
    #get the source format
    if not dds.header.pixel_format.fourCC or dds.header.pixel_format.fourCC == "DDPF_RGB":
        # use bitmasks to determine source format
        nut_pixel_format = nut_pf_bitmasks[dds.header.pixel_format.bitmasks]
        dds_pixel_format = Pixel_Formats[nut_pixel_format]
    else:
        dds_pixel_format = dds.header.pixel_format.fourCC

    # Convert DDS to RGBA8888 first
    rgba8888_data = to_rgba8888_function_map[dds_pixel_format](dds.mipmaps[0], nut.width, nut.height)

    # Convert RGBA8888 to the target format
    if target_format != 'R8G8B8A8':
        image_data = from_rgba8888_function_map[target_format](
            rgba8888_data, nut.width, nut.height, ['a', 'r', 'g', 'b'], 'big'
        )
    else:
        image_data = np.frombuffer(rgba8888_data, dtype=np.uint8).reshape(-1, 4)
        image_data = image_data[:, [3, 0, 1, 2]].tobytes()

    nut.pixel_format = pixel_formats_map[target_format]
    nut.mipmaps = [image_data]
    nut.texture_data = image_data
    nut.mipmap_count = 1
    nut.is_cube_map = False
    nut.cubemap_format = 0
    nut.data_size = len(nut.texture_data)
    nut.header_size = 48

    if nut.mipmap_count > 1:
        nut.header_size += (nut.mipmap_count * 4)

    if nut.header_size % 16 != 0:
        nut.header_size += 16 - (nut.header_size % 16)

    nut.header_size += 32

    nut.total_size = nut.data_size + nut.header_size

    return nut


def NutTexture_to_DDS(nuttex: NutTexture):
    dds = DDS()
    dds.magic = 'DDS '
    header = dds.header = DDS_Header()
    header.pixel_format = DDS_PixelFormat()
    header.size = 124
    # DDSD_CAPS | DDSD_HEIGHT | DDSD_WIDTH | DDSD_PIXELFORMAT
    header.flags = 0x1 | 0x2 | 0x4 | 0x1000

    header.width = nuttex.width
    header.height = nuttex.height
    header.mipMapCount = nuttex.mipmap_count

    # check if nuttex.pixel_format is in nut_pf_fourcc
    if nuttex.pixel_format in nut_pf_fourcc.values():

        header.pixel_format.fourCC = list(nut_pf_fourcc.keys())[list(
            nut_pf_fourcc.values()).index(nuttex.pixel_format)]
        header.flags |= 0x80000  # LINEAR_SIZE
        header.pixel_format.flags = 0x4  # DDPF_FOURCC

        if header.pixel_format.fourCC == 'DXT1':
            header.pitchOrLinearSize = nuttex.width * nuttex.height // 2
        else:
            header.pitchOrLinearSize = nuttex.width * nuttex.height

        header.pixel_format.rgbBitCount = 0
        header.pixel_format.bitmasks = (0, 0, 0, 0)

        dds.mipmaps = nuttex.mipmaps
        dds.texture_data = nuttex.texture_data

    elif nuttex.pixel_format in nut_pf_bitmasks.values():
        header.flags |= 0x8  # DDSD_PITCH
        header.pitchOrLinearSize = nuttex.width * nut_bpp[nuttex.pixel_format]
        header.pixel_format.fourCC = None
        header.pixel_format.rgbBitCount = nut_bpp[nuttex.pixel_format] * 8
        header.pixel_format.bitmasks = list(nut_pf_bitmasks.keys())[list(
            nut_pf_bitmasks.values()).index(nuttex.pixel_format)]
        if nuttex.pixel_format in (6, 7, 17):
            header.pixel_format.flags = 0x40 | 0x01  # DDPF_RGB | DDPF_ALPHAPIXELS
        else:
            header.pixel_format.flags = 0x40  # DDPF_RGB

        if nuttex.pixel_format in (6, 7, 8):
            dds.mipmaps = nuttex.mipmaps
            texture_data = array('u', nuttex.texture_data)
            texture_data.byteswap()
            dds.texture_data = texture_data.tobytes()
        elif nuttex.pixel_format in (14, 17):
            dds.mipmaps = nuttex.mipmaps
            texture_data = array('l', nuttex.texture_data)
            texture_data.byteswap()
            dds.texture_data = texture_data.tobytes()

    header.pixel_format.size = 32
    if header.mipMapCount > 1:
        header.flags |= 0x20000  # DDSD_MIPMAPCOUNT
        header.caps1 = 0x8 | 0x1000 | 0x400000 # DDSCAPS_COMPLEX | DDSCAPS_MIPMAP | DDSCAPS_TEXTURE
    else:
        header.caps1 = 0x1000
    header.depth = 1
    header.reserved = [0] * 11
    header.caps2 = 0
    header.caps3 = 0
    header.caps4 = 0
    header.reserved2 = 0

    br = BinaryReader(endianness=Endian.LITTLE)
    br.write_struct(BrDDS(), dds)

    return bytes(br.buffer())


def TGA_to_NutTexture(tga, target_format: str):
    nut = NutTexture()

    tga: TGA
    nut.width = tga.Width
    nut.height = tga.Height
    nut.pixel_format = pixel_formats_map[target_format]

    # Get RGBA8888 data from TGA (properly converted from any source format)
    rgba_data = tga.get_rgba()

    if target_format != 'R8G8B8A8':
        # Convert RGBA8888 to target format
        image_data = from_rgba8888_function_map[target_format](
            rgba_data, tga.Width, tga.Height, ['r', 'g', 'b', 'a'], 'little'
        )
    else:
        # Convert RGBA to ARGB for R8G8B8A8 format
        image_data = np.frombuffer(rgba_data, dtype=np.uint8).reshape(-1, 4)
        image_data = image_data[:, [3, 0, 1, 2]].tobytes()  # RGBA -> ARGB

    nut.mipmaps = [image_data]
    nut.texture_data = image_data
    nut.mipmap_count = 1
    nut.is_cube_map = False
    nut.cubemap_format = 0
    nut.data_size = len(nut.texture_data)
    nut.header_size = 48

    if nut.mipmap_count > 1:
        nut.header_size += (nut.mipmap_count * 4)

    if nut.header_size % 16 != 0:
        nut.header_size += 16 - (nut.header_size % 16)

    nut.header_size += 32

    nut.total_size = nut.data_size + nut.header_size

    return nut


def NutTexture_to_TGA(nuttex: NutTexture):
    # Assume nuttex.texture_data is in some format that needs conversion to RGBA
    # For now, use rgbaToTGA which properly handles RGBA -> BGRA conversion
    return rgbaToTGA(nuttex.width, nuttex.height, nuttex.texture_data)


def PNG_to_NutTexture(png, target_format: str):
    nut = NutTexture()
    png:PNG
    nut.width = png.IHDR.Width
    nut.height = png.IHDR.Height
    nut.pixel_format = pixel_formats_map[target_format]
    
    
    if target_format != 'R8G8B8A8':
        image_data = from_rgba8888_function_map[target_format](png.get_rgba(), png.IHDR.Width, png.IHDR.Height, ['a','r','g','b'], 'big')
    else:
        image_data = np.frombuffer(png.get_rgba(), dtype=np.uint8).reshape(-1,4)
        image_data = image_data[:, [3,0,1,2]].tobytes()
    nut.mipmaps = [image_data]
    nut.texture_data = image_data
    nut.mipmap_count = 1
    nut.is_cube_map = False
    nut.cubemap_format = 0
    nut.data_size = len(nut.texture_data)
    nut.header_size = 48
    
    if nut.mipmap_count > 1:
        nut.header_size += (nut.mipmap_count * 4)
    
    if nut.header_size % 16 != 0:
        nut.header_size += 16 - (nut.header_size % 16)
    
    nut.header_size += 32
    
    
    nut.total_size = nut.data_size + nut.header_size

    return nut


def read_texture_from_file(filepath: str):
    """reads the first 4 bytes, determines the texture type and the returns the texture type and an object representing the texture"""
    with open(filepath, 'rb') as f:
        header = f.read(4)
        f.seek(0)
        if header == b'DDS ':
            dds = read_dds(f.read())
            return 'DDS', dds
        elif header == b'\x00\x00\x02\x00':
            tga = read_tga(f.read())
            return 'TGA', tga
        elif header[1:4] == b'PNG':
            png = read_png(f.read())
            return 'PNG', png
        else:
            print(f"Invalid texture format: {header}")
            return None, None

def read_texture_data(texture: bytearray):
    """reads the first 4 bytes, determines the texture type and the returns the texture type and an object representing the texture"""
    with io.BytesIO(texture) as f:
        header = f.read(4)
        f.seek(0)
        if header == b'DDS ':
            dds = read_dds(f.read())
            return 'DDS', dds
        elif header == b'\x00\x00\x02\x00':
            tga = read_tga(f.read())
            return 'TGA', tga
        elif header[1:4] == b'PNG':
            png = read_png(f.read())
            return 'PNG', png
        else:
            print(f"Invalid texture format: {header}")
            return None, None


def convert_texture(texture: bytearray, target_format: str):
    #read the first 4 bytes of the byte array to determine the texture format
    if not target_format:
        # default to source format
        target_format = None
    with io.BytesIO(texture) as f:
        header = f.read(4)
        f.seek(0)
        if header == b'DDS ':
            dds = read_dds(f.read())
            nut = DDS_to_NutTexture(dds, target_format)
            return nut
        elif header == b'\x00\x00\x02\x00':
            tga = read_tga(f.read())
            nut = TGA_to_NutTexture(tga, target_format)
            return nut
        elif header[1:4] == b'PNG':
            png = read_png(f.read())
            nut = PNG_to_NutTexture(png, target_format)
            return nut

        else:
            raise ValueError("Invalid texture format")