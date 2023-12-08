from ...util import *
import threading

# Based on Smash Forge Nut implementation
# https://github.com/jam1garner/Smash-Forge/blob/master/Smash%20Forge/Filetypes/Textures/NUT.cs
class BrNut(BrStruct):
    def __br_read__(self, br: BinaryReader):
        self.magic = br.read_str(4)

        if self.magic != "NTP3":
            raise Exception('Invalid NUT magic.')

        self.version = br.read_uint16()
        self.texture_count = br.read_uint16()

        br.read_uint32(2)
        self.textures = br.read_struct(BrNutTexture, self.texture_count, self)

    def __br_write__(self, br: 'BinaryReader', nut: 'Nut'):
        br.write_str('NTP3')
        br.write_uint16(0x0100)
        br.write_uint16(len(nut.textures))
        br.write_uint64(0)

        for tex in nut.textures:
            br.write_struct(BrNutTexture(), tex)


class BrNutTexture(BrStruct):
    def __br_read__(self, br: BinaryReader, nut: BrNut):
        pos = br.pos()
        self.total_size = br.read_uint32()
        br.read_uint32()

        self.data_size = br.read_uint32()
        self.header_size = br.read_uint16()
        br.read_uint16()

        br.read_uint8()
        self.mipmap_count = br.read_uint8()
        br.read_uint8()
        self.pixel_format = br.read_uint8()

        self.width = br.read_uint16()
        self.height = br.read_uint16()

        br.read_uint32()
        self.cubemap_format = br.read_uint32()

        self.is_cube_map = False
        if self.cubemap_format & 0x200:
            self.is_cube_map = True

        if nut.version < 0x200:
            self.data_offset = 0x10 + self.header_size
            br.read_uint32(4)
        else:
            self.data_offset = br.read_uint32(4)[0]

        if self.is_cube_map:
            (self.cubemap_size1, self.cubemap_size2, _, _) = br.read_uint32(4)

        if self.mipmap_count > 1:
            self.mipmap_sizes = br.read_uint32(self.mipmap_count)
            br.align_pos(16)

        # eXt and GIDX
        br.seek(0x18, Whence.CUR)

        # Probably always 0 in xfbins
        self.hash_id = br.read_uint32()
        br.read_uint32()

        if self.is_cube_map:
            self.cubemap_faces = [br.read_bytes(
                self.cubemap_size1) for i in range(6)]
            self.texture_data = self.mipmaps = b''.join(self.cubemap_faces)

        elif self.mipmap_count > 1:
            if sum(self.mipmap_sizes) != self.data_size:

                self.texture_data = self.mipmaps = br.read_bytes(
                    self.mipmap_sizes[0])
                self.data_size = self.mipmap_sizes[0]
                self.mipmap_count = 1
                self.header_size = 80
                self.total_size = self.header_size + self.data_size

            else:
                self.mipmaps = [br.read_bytes(
                    self.mipmap_sizes[i]) for i in range(self.mipmap_count)]
                self.texture_data = b''.join(self.mipmaps)

        else:
            self.mipmaps = [br.read_bytes(self.data_size)]
            self.texture_data = self.mipmaps[0]

    def __br_write__(self, br: 'BinaryReader', nutTex: 'NutTexture'):
        start = br.pos()
        br.write_uint32(nutTex.total_size)
        br.write_uint32(0)

        br.write_uint32(nutTex.data_size)
        br.write_uint16(nutTex.header_size)

        br.write_uint16(0)
        br.write_uint8(0)

        br.write_uint8(nutTex.mipmap_count)
        br.write_uint8(0)
        br.write_uint8(nutTex.pixel_format)

        br.write_uint16(nutTex.width)
        br.write_uint16(nutTex.height)

        br.write_uint32(0)

        br.write_uint32(nutTex.cubemap_format)

        for i in range(4):
            br.write_uint32(0)

        if nutTex.cubemap_format & 0x200:
            for i in range(2):
                br.write_uint32(nutTex.cubemap_size)
            for i in range(2):
                br.write_uint32(0)

        if nutTex.mipmap_count > 1:
            for mip in nutTex.mipmaps:
                br.write_uint32(len(mip))
                
            if (br.pos() - start) % 0x10 != 0:
                br.write_bytes(b'\x00' * (0x10 - ((br.pos() - start) % 0x10)))

        br.write_str('eXt')
        br.write_uint8(0)
        br.write_uint32(0x20)
        br.write_uint32(0x10)
        br.write_uint32(0)

        br.write_str('GIDX')
        br.write_uint32(0x10)
        br.write_uint32(0)
        br.write_uint32(0)

        if nutTex.is_cube_map:
            for face in nutTex.cubemap_faces:
                br.write_bytes(face)
        elif nutTex.mipmap_count > 1:
            for mip in nutTex.mipmaps:
                br.write_bytes(mip)
        else:
            br.write_bytes(nutTex.texture_data)
