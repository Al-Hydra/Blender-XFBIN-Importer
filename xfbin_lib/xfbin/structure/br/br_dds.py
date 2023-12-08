from array import array
from enum import Enum, IntEnum, IntFlag

from ...util import *

class BrDDS(BrStruct):
    def __br_read__(self, br: BinaryReader):
        self.magic = br.read_str(4)
        if (self.magic != 'DDS '):
            raise Exception('Invalid DDS magic')
        self.header = br.read_struct(BrDDS_Header)

        # compressed textures
        if PixelFormat_Flags.values(self.header.pixel_format.flags) == 'DDPF_FOURCC':

            if self.header.pixel_format.fourCC == 'DX10':
                self.header.pixel_format.dx10_header = br.read_struct(
                    BrDDS_DX10_Header)

            if self.header.pixel_format.fourCC == 'DXT1':
                self.mipmaps = list()
                self.texture_data = bytearray()
                width = self.header.width
                height = self.header.height
                if self.header.mipMapCount == 0:
                    self.header.mipMapCount = 1

                for i in range(self.header.mipMapCount):
                    self.mipmaps.append(br.read_bytes(
                        int((max(1, (width + 3) // 4)) * max(1, (height + 3) // 4) * 8)))

                    self.texture_data.extend(self.mipmaps[i])
                    # calculate next mip map size
                    width = max(1, width // 2)
                    height = max(1, height // 2)
                self.texture_data = bytes(self.texture_data)

            elif self.header.pixel_format.fourCC == 'DXT3' or self.header.pixel_format.fourCC == 'DXT5':
                self.mipmaps = list()
                self.texture_data = bytearray()
                width = self.header.width
                height = self.header.height
                if self.header.mipMapCount == 0:
                    self.header.mipMapCount = 1
                for i in range(self.header.mipMapCount):
                    self.mipmaps.append(br.read_bytes(
                        int((max(1, (width + 3) // 4)) * max(1, (height + 3) // 4) * 16)))

                    self.texture_data.extend(self.mipmaps[i])
                    # calculate next mip map size
                    width = max(1, width // 2)
                    height = max(1, height // 2)
                self.texture_data = bytes(self.texture_data)

        # uncompressed textures
        elif 'DDPF_RGB' in PixelFormat_Flags.values(self.header.pixel_format.flags):
            bitcount = self.header.pixel_format.rgbBitCount
            bitmasks = self.header.pixel_format.bitmasks
            #if bitmasks in ((0xf800, 0x7e0, 0x1f, 0), (0x7c00, 0x3e0, 0x1f, 0x8000), (0x0f00, 0x00f0, 0x000f, 0xf000), (0x00ff0000, 0x0000ff00, 0x000000ff, 0xff000000)):
            self.mipmaps = list()
            self.texture_data = bytearray()
            width = self.header.width
            height = self.header.height
            if self.header.mipMapCount == 0:
                self.header.mipMapCount = 1
            for i in range(self.header.mipMapCount):
                # calculate mip map size and append to list
                self.mipmaps.append(br.read_bytes(
                    (width * bitcount + 7) // 8 * height))
                self.texture_data.extend(self.mipmaps[i])
                # calculate next mip map size
                width = max(1, width // 2)
                height = max(1, height // 2)
            self.texture_data = bytes(self.texture_data)

    def __br_write__(self, br: 'BinaryReader', dds: 'DDS'):
        br.write_str(dds.magic)
        br.write_struct(BrDDS_Header(), dds.header)
        if PixelFormat_Flags.values(dds.header.pixel_format.flags) == 'DDPF_FOURCC':
            if dds.header.pixel_format.fourCC == 'DX10':
                br.write_struct(BrDDS_DX10_Header(),
                                dds.header.pixel_format.dx10_header)

            if dds.header.pixel_format.fourCC in ('DXT1', 'DXT3', 'DXT5'):
                br.write_bytes(dds.texture_data)

        elif 'DDPF_RGB' in PixelFormat_Flags.values(dds.header.pixel_format.flags):
            bitcount = dds.header.pixel_format.rgbBitCount
            bitmasks = dds.header.pixel_format.bitmasks
            #if bitmasks in ((0xf800, 0x7e0, 0x1f, 0), (0x7c00, 0x3e0, 0x1f, 0x8000), (0x0f00, 0x00f0, 0x000f, 0xf000), (0x00ff0000, 0x0000ff00, 0x000000ff, 0xff000000),(0x00ff0000, 0x0000ff00, 0x000000ff, 0x0) ):
            br.write_bytes(dds.texture_data)


class BrDDS_Header(BrStruct):
    def __br_read__(self, br: BinaryReader):
        self.size = br.read_uint32()
        #print(f'Header Size = {self.size}')
        self.flags = br.read_uint32()
        # print flags as a string
        #print(f'Flags = {Header_Flags.values(self.flags)}')
        self.height = br.read_uint32()
        #print(f'Height = {self.height}')
        self.width = br.read_uint32()
        #print(f'Width = {self.width}')
        self.pitchOrLinearSize = br.read_uint32()
        self.depth = br.read_uint32()
        #print(f'Depth = {self.depth}')
        self.mipMapCount = br.read_uint32()
        #print(f'MipMapCount = {self.mipMapCount}')
        self.reserved = br.read_uint32(11)
        #print(f'Reserved = {self.reserved}')
        self.pixel_format = br.read_struct(BrDDS_PixelFormat)

        self.caps1 = br.read_uint32()
        #print(f'Caps1 = {PixelFormat_Caps1.values(self.caps1)}')
        self.caps2 = br.read_uint32()
        #print(f'Caps2 = {PixelFormat_Caps2.values(self.caps2)}')
        self.caps3 = br.read_uint32()
        self.caps4 = br.read_uint32()
        self.reserved2 = br.read_uint32()

    def __br_write__(self, br: 'BinaryReader', dds1: 'DDS_Header'):
        br.write_uint32(dds1.size)
        br.write_uint32(dds1.flags)
        br.write_uint32(dds1.height)
        br.write_uint32(dds1.width)
        br.write_uint32(dds1.pitchOrLinearSize)
        br.write_uint32(dds1.depth)
        br.write_uint32(dds1.mipMapCount)
        br.write_uint32(dds1.reserved)
        br.write_struct(BrDDS_PixelFormat(), dds1.pixel_format)
        br.write_uint32(dds1.caps1)
        br.write_uint32(dds1.caps2)
        br.write_uint32(dds1.caps3)
        br.write_uint32(dds1.caps4)
        br.write_uint32(dds1.reserved2)


class BrDDS_PixelFormat(BrStruct):
    def __br_read__(self, br: BinaryReader):
        self.size = br.read_uint32()
        #print(f'PixelFormat Size = {self.size}')
        self.flags = br.read_uint32()
        #print(f'Flags = {PixelFormat_Flags.values(self.flags)}')
        self.fourCC = br.read_str(4)
        #print(f'FourCC = {self.fourCC}')
        self.rgbBitCount = br.read_uint32()
        #print(f'RGBBitCount = {self.rgbBitCount}')
        self.bitmasks = br.read_uint32(4)
        #print(f'Bitmasks = {self.bitmasks}')

    def __br_write__(self, br: 'BinaryReader', dds2: 'DDS_PixelFormat'):
        br.write_uint32(dds2.size)
        br.write_uint32(dds2.flags)
        if dds2.fourCC is not None:
            br.write_str(dds2.fourCC)
        else:
            br.write_uint32(0)
        br.write_uint32(dds2.rgbBitCount)
        br.write_uint32(dds2.bitmasks)


class BrDDS_DX10_Header(BrStruct):
    def __br_read__(self, br: BinaryReader):
        self.dxgi_format = br.read_uint32()
        #print(f'DXGI Format = {DXGI_Format(self.dxgi_format).name}')
        self.resource_dimension = br.read_uint32()
        #print(f'Resource Dimension = {ResourceDimension(self.resource_dimension).name}')
        self.misc_flag = br.read_uint32()
        #print(f'Misc Flag = {Misc_Flag.values(self.misc_flag)}')
        self.array_size = br.read_uint32()
        #print(f'Array Size = {self.array_size}')
        self.misc_flags2 = br.read_uint32()
        #print(f'Misc Flags2 = {Misc_Flag2(self.misc_flags2).name}')

    def __br_write__(self, br: 'BinaryReader', dds3: 'DDS_DX10_Header'):
        br.write_uint32(dds3.dxgi_format)
        br.write_uint32(dds3.resource_dimension)
        br.write_uint32(dds3.misc_flag)
        br.write_uint32(dds3.array_size)
        br.write_uint32(dds3.misc_flags2)


class Header_Flags(IntFlag):
    DDSD_CAPS = 0x1
    DDSD_HEIGHT = 0x2
    DDSD_WIDTH = 0x4
    DDSD_PITCH = 0x8
    DDSD_PIXELFORMAT = 0x1000
    DDSD_MIPMAPCOUNT = 0x20000
    DDSD_LINEARSIZE = 0x80000
    DDSD_DEPTH = 0x800000

    @classmethod
    def values(cls, flags):
        return '|'.join(name for name in cls.__members__ if flags & getattr(cls, name))


class PixelFormat_Flags(IntFlag):
    DDPF_ALPHAPIXELS = 0x1
    DDPF_ALPHA = 0x2
    DDPF_FOURCC = 0x4
    DDPF_PALETTEINDEXED8 = 0x20
    DDPF_RGB = 0x40
    DDPF_YUV = 0x200
    DDPF_LUMINANCE = 0x20000
    DDPF_BUMPDUDV = 0x80000

    @classmethod
    def values(cls, flags):
        return '|'.join(name for name in cls.__members__ if flags & getattr(cls, name))


class PixelFormat_Caps1(IntFlag):
    DDSCAPS_COMPLEX = 0x8
    DDSCAPS_MIPMAP = 0x400000
    DDSCAPS_TEXTURE = 0x1000

    @classmethod
    def values(cls, flags):
        return '|'.join(name for name in cls.__members__ if flags & getattr(cls, name))


class PixelFormat_Caps2(IntFlag):
    DDSCAPS2_CUBEMAP = 0x200
    DDSCAPS2_CUBEMAP_POSITIVEX = 0x400
    DDSCAPS2_CUBEMAP_NEGATIVEX = 0x800
    DDSCAPS2_CUBEMAP_POSITIVEY = 0x1000
    DDSCAPS2_CUBEMAP_NEGATIVEY = 0x2000
    DDSCAPS2_CUBEMAP_POSITIVEZ = 0x4000
    DDSCAPS2_CUBEMAP_NEGATIVEZ = 0x8000
    DDSCAPS2_VOLUME = 0x200000

    @classmethod
    def values(cls, flags):
        return '|'.join(name for name in cls.__members__ if flags & getattr(cls, name))


class DXGI_Format(IntEnum):
    UNKNOWN = 0
    R32G32B32A32_TYPELESS = 1
    R32G32B32A32_FLOAT = 2
    R32G32B32A32_UINT = 3
    R32G32B32A32_SINT = 4
    R32G32B32_TYPELESS = 5
    R32G32B32_FLOAT = 6
    R32G32B32_UINT = 7
    R32G32B32_SINT = 8
    R16G16B16A16_TYPELESS = 9
    R16G16B16A16_FLOAT = 10
    R16G16B16A16_UNORM = 11
    R16G16B16A16_UINT = 12
    R16G16B16A16_SNORM = 13
    R16G16B16A16_SINT = 14
    R32G32_TYPELESS = 15
    R32G32_FLOAT = 16
    R32G32_UINT = 17
    R32G32_SINT = 18
    R32G8X24_TYPELESS = 19
    D32_FLOAT_S8X24_UINT = 20
    R32_FLOAT_X8X24_TYPELESS = 21
    X32_TYPELESS_G8X24_UINT = 22
    R10G10B10A2_TYPELESS = 23
    R10G10B10A2_UNORM = 24
    R10G10B10A2_UINT = 25
    R11G11B10_FLOAT = 26
    R8G8B8A8_TYPELESS = 27
    R8G8B8A8_UNORM = 28
    R8G8B8A8_UNORM_SRGB = 29
    R8G8B8A8_UINT = 30
    R8G8B8A8_SNORM = 31
    R8G8B8A8_SINT = 32
    R16G16_TYPELESS = 33
    R16G16_FLOAT = 34
    R16G16_UNORM = 35
    R16G16_UINT = 36
    R16G16_SNORM = 37
    R16G16_SINT = 38
    R32_TYPELESS = 39
    D32_FLOAT = 40
    R32_FLOAT = 41
    R32_UINT = 42
    R32_SINT = 43
    R24G8_TYPELESS = 44
    D24_UNORM_S8_UINT = 45
    R24_UNORM_X8_TYPELESS = 46
    X24_TYPELESS_G8_UINT = 47
    R8G8_TYPELESS = 48
    R8G8_UNORM = 49
    R8G8_UINT = 50
    R8G8_SNORM = 51
    R8G8_SINT = 52
    R16_TYPELESS = 53
    R16_FLOAT = 54
    D16_UNORM = 55
    R16_UNORM = 56
    R16_UINT = 57
    R16_SNORM = 58
    R16_SINT = 59
    R8_TYPELESS = 60
    R8_UNORM = 61
    R8_UINT = 62
    R8_SNORM = 63
    R8_SINT = 64
    A8_UNORM = 65
    R1_UNORM = 66
    R9G9B9E5_SHAREDEXP = 67
    R8G8_B8G8_UNORM = 68
    G8R8_G8B8_UNORM = 69
    BC1_TYPELESS = 70
    BC1_UNORM = 71
    BC1_UNORM_SRGB = 72
    BC2_TYPELESS = 73
    BC2_UNORM = 74
    BC2_UNORM_SRGB = 75
    BC3_TYPELESS = 76
    BC3_UNORM = 77
    BC3_UNORM_SRGB = 78
    BC4_TYPELESS = 79
    BC4_UNORM = 80
    BC4_SNORM = 81
    BC5_TYPELESS = 82
    BC5_UNORM = 83
    BC5_SNORM = 84
    B5G6R5_UNORM = 85
    B5G5R5A1_UNORM = 86
    B8G8R8A8_UNORM = 87
    B8G8R8X8_UNORM = 88
    R10G10B10_XR_BIAS_A2_UNORM = 89
    B8G8R8A8_TYPELESS = 90
    B8G8R8A8_UNORM_SRGB = 91
    B8G8R8X8_TYPELESS = 92
    B8G8R8X8_UNORM_SRGB = 93
    BC6H_TYPELESS = 94
    BC6H_UF16 = 95
    BC6H_SF16 = 96
    BC7_TYPELESS = 97
    BC7_UNORM = 98
    BC7_UNORM_SRGB = 99
    AYUV = 100
    Y410 = 101
    Y416 = 102
    NV12 = 103
    P010 = 104
    P016 = 105
    _420_OPAQUE = 106
    YUY2 = 107
    Y210 = 108
    Y216 = 109
    NV11 = 110
    AI44 = 111
    IA44 = 112
    P8 = 113
    A8P8 = 114
    B4G4R4A4_UNORM = 115
    P208 = 130
    V208 = 131
    V408 = 132
    FORCE_UINT = 0xffffffff


class ResourceDimension(IntEnum):
    UNKNOWN = 0
    BUFFER = 1
    TEXTURE1D = 2
    TEXTURE2D = 3
    TEXTURE3D = 4


class Misc_Flag(IntFlag):
    NONE = 0x0
    GENERATE_MIPS = 0x1
    SHARED = 0x2
    TEXTURECUBE = 0x4

    @classmethod
    def values(cls, flags):
        return '|'.join(name for name in cls.__members__ if flags & getattr(cls, name))


class Misc_Flag2(IntEnum):
    ALPHA_MODE_MASK = 0x7
    ALPHA_MODE_UNKNOWN = 0
    ALPHA_MODE_STRAIGHT = 1
    ALPHA_MODE_PREMULTIPLIED = 2
    ALPHA_MODE_OPAQUE = 3
    ALPHA_MODE_CUSTOM = 4
