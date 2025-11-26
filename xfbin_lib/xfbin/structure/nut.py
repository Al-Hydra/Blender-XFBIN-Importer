from .br.br_nut import *
from enum import Enum


class Nut:
    def init_data(self, br_chunk: BrNut):
        self.magic = br_chunk.magic
        self.version = br_chunk.version

        self.texture_count = br_chunk.texture_count
        self.textures = list()
        for brTex in br_chunk.textures:
            tex = NutTexture()
            tex.init_data(brTex)
            self.textures.append(tex)


class NutTexture:

    def init_data(self, br_chunk: BrNutTexture):
        self.data_size = br_chunk.data_size

        self.header_size = br_chunk.header_size

        self.total_size = self.data_size + self.header_size

        self.mipmap_count = br_chunk.mipmap_count

        self.pixel_format = br_chunk.pixel_format

        self.width = br_chunk.width
        self.height = br_chunk.height

        self.is_cube_map = br_chunk.is_cube_map

        self.cubemap_format = br_chunk.cubemap_format

        if self.is_cube_map:

            self.cubemap_size = br_chunk.cubemap_size1

            self.cubemap_faces = br_chunk.cubemap_faces
        else:
            self.cubemap_faces = None

        if self.mipmap_count > 1:
            self.mipmaps = br_chunk.mipmaps
            self.texture_data = br_chunk.texture_data

        else:
            self.mipmaps = br_chunk.mipmaps
            self.texture_data = br_chunk.texture_data
        

Pixel_Formats = {
    0: 'DXT1',
    1: 'DXT3',
    2: 'DXT5',
    6: 'B5G5R5A1',
    7: 'B4G4R4A4',
    8: 'B5G6R5',
    14: 'R8G8B8A8',
    17: 'R8G8B8A8',
}
