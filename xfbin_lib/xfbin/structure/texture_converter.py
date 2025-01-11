from .nut import *
from .tga import *
from .dds import *

def DDS_to_NutTexture(dds):
    dds: BrDDS
    nut = NutTexture()

    nut.width = dds.header.width
    nut.height = dds.header.height

    if dds.header.pixel_format.fourCC != '':
        nut.pixel_format = nut_pf_fourcc[dds.header.pixel_format.fourCC]
        nut.mipmaps = list()
        nut.texture_data = b''
        for mip in dds.mipmaps:
            if len(mip) < 16:
                mip += b'\x00' * (16 - len(mip))
            nut.mipmaps.append(mip)
            nut.texture_data += mip

    elif dds.header.pixel_format.bitmasks:
        nut.pixel_format = nut_pf_bitmasks[dds.header.pixel_format.bitmasks]
        nut.mipmaps = list()
        nut.texture_data = b''

        if nut.pixel_format == 17:
            for mip in dds.mipmaps:
                mip = array('l', mip)
                mip.byteswap()
                nut.mipmaps.append(mip.tobytes())
                nut.texture_data += mip.tobytes()

        else:
            for mip in dds.mipmaps:
                if len(mip) < 16:
                    mip += b'\x00' * (16 - len(mip))
                mip = array('u', mip)
                mip.byteswap()
                nut.mipmaps.append(mip.tobytes())
                nut.texture_data += mip.tobytes()

    nut.mipmap_count = dds.header.mipMapCount

    nut.is_cube_map = False
    nut.cubemap_format = 0

    nut.data_size = len(nut.texture_data)
    nut.header_size = 48

    if dds.header.mipMapCount > 1:
        nut.header_size += (dds.header.mipMapCount * 4)

    
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


def TGA_to_NutTexture(tga):
    nut = NutTexture()

    tga.ImageData = BGRA_to_ARGB(tga.ImageData)
    
    nut.width = tga.Width
    nut.height = tga.Height
    nut.pixel_format = 17
    nut.mipmaps = [tga.ImageData]
    nut.texture_data = tga.ImageData
    nut.mipmap_count = 1
    nut.is_cube_map = False
    nut.cubemap_format = 0
    nut.data_size = len(nut.texture_data)
    nut.header_size = 48
    nut.total_size = nut.data_size + nut.header_size

    return nut


def NutTexture_to_TGA(nuttex: NutTexture):
    tga = TGA()

    tga.ImageID = ""
    tga.ColorMapType = 0
    tga.DataTypeCode = DataTypes.UNCOMPRESSED_TRUE_COLOR.value
    tga.ColorMapOrigin = 0
    tga.ColorMapLength = 0
    tga.ColorMapDepth = 0
    tga.x_Origin = 0
    tga.y_Origin = 0
    tga.Width = nuttex.width
    tga.Height = nuttex.height
    tga.BitsPerPixel = 32
    tga.ImageDescriptor = 0
    tga.ImageData = nuttex.texture_data

    with BinaryReader(endianness=Endian.LITTLE) as br:
        br.write_struct(TGA(), tga)

        return bytes(br.buffer())


def convert_texture(texture: bytearray):
    #read the first 4 bytes of the byte array to determine the texture format
    with io.BytesIO(texture) as f:
        header = f.read(4)
        f.seek(0)
        if header == b'DDS ':
            dds = read_dds(f.read())
            nut = DDS_to_NutTexture(dds)
            return nut
        elif header == b'\x00\x00\x02\x00':
            tga = read_tga(f.read())
            nut = TGA_to_NutTexture(tga)
            return nut

        else:
            raise ValueError("Invalid texture format")