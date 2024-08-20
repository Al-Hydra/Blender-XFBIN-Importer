from typing import List

import bpy
from bpy.props import (BoolProperty, CollectionProperty, IntProperty,
                       StringProperty)
from bpy.types import Panel, PropertyGroup
from ...xfbin_lib.xfbin.structure.nucc import NuccChunkTexture
from ...xfbin_lib.xfbin.structure.nut import Nut, NutTexture, Pixel_Formats
from ..common.helpers import XFBIN_TEXTURES_OBJ
from .common import draw_xfbin_list
from ...xfbin_lib.xfbin.structure import dds
from ...xfbin_lib.xfbin.structure.br import br_dds

class XFBIN_UL_TextureList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            row.prop(item, 'name',emboss= False, text='', icon='IMAGE_DATA')
            row.prop(item, 'path', text='',emboss=False, icon='FILE_FOLDER')
            #row.prop(item, 'reference', text='Reference', icon='FILE_TICK', toggle=True)
            row.prop(item, 'reference', text='', icon='FILE_TICK', toggle=True, icon_only=True)

        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon='MATERIAL_DATA')
            layout.label(text="", icon='FILE_FOLDER')
            layout.label(text="", icon='TEXTURE')
            layout.label(text="", icon='LINKED')


class XFBIN_UL_TexturePreviewList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row()
            row.prop(item, 'image', text='', icon='IMAGE_DATA')
            #read only properties
            row.label(text = f'Format: {item.pixel_format}  Size: {item.width}x{item.height}.')
            #row.prop(item, 'pixel_format', text='Format', emboss=False)
        
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon='MATERIAL_DATA')
            layout.label(text="", icon='FILE_FOLDER')
            layout.label(text="", icon='TEXTURE')
            layout.label(text="", icon='LINKED')


class XFBIN_TexChunks_OT_AddNUT(bpy.types.Operator):
    """Add a NUT texture to the XFBIN"""
    bl_idname = 'xfbin_texchunks.add_nut'
    bl_label = 'Add NUT'

    def execute(self, context):
        data: TextureChunksListPropertyGroup = context.scene.xfbin_texture_chunks_data
        chunks = data.texture_chunks
        nut = chunks.add()
        nut.texture_name = 'Texture'
        nut.path = 'Texture.nut'
        nut.texture_count = 1

        data.texture_chunk_index = len(chunks) - 1

        return {'FINISHED'}
    

class XFBIN_TexChunks_OT_RemoveNUT(bpy.types.Operator):
    """Remove a NUT texture from the XFBIN"""
    bl_idname = 'xfbin_texchunks.remove_nut'
    bl_label = 'Remove NUT'

    def execute(self, context):
        data: TextureChunksListPropertyGroup = context.scene.xfbin_texture_chunks_data
        chunks = data.texture_chunks
        index = data.texture_chunk_index

        if not chunks:
            # Should not happen
            self.report({'WARNING'}, 'No Textures to remove')
            return {'CANCELLED'}

        chunks.remove(index)

        data.texture_chunk_index = min(index, len(chunks) - 1)

        return {'FINISHED'}
    

class XFBIN_TexChunks_OT_MoveNUT(bpy.types.Operator):
    """Move a NUT texture in the XFBIN"""
    bl_idname = 'xfbin_texchunks.move_nut'
    bl_label = 'Move NUT'

    direction: bpy.props.EnumProperty(
        name='Direction',
        items=(
            ('UP', 'Up', ''),
            ('DOWN', 'Down', ''),
        ),
    )

    def execute(self, context):
        data: TextureChunksListPropertyGroup = context.scene.xfbin_texture_chunks_data
        chunks = data.texture_chunks
        index = data.texture_chunk_index

        if not chunks:
            # Should not happen
            return {'CANCELLED'}

        if self.direction == 'UP':
            chunks.move(index, index - 1)
            data.texture_chunk_index -= 1
        elif self.direction == 'DOWN':
            chunks.move(index, index + 1)
            data.texture_chunk_index += 1

        return {'FINISHED'}


class XFBIN_TexChunks_OT_DuplicateNUT(bpy.types.Operator):
    """Duplicate a NUT texture in the XFBIN"""
    bl_idname = 'xfbin_texchunks.duplicate_nut'
    bl_label = 'Duplicate NUT'

    def execute(self, context):
        data: TextureChunksListPropertyGroup = context.scene.xfbin_texture_chunks_data
        chunks = data.texture_chunks
        index = data.texture_chunk_index

        if not chunks:
            # Should not happen
            self.report({'ERROR'}, 'No Textures to duplicate')
            return {'CANCELLED'}

        chunks.add()
        chunks[-1].name = chunks[index].name
        chunks[-1].path = chunks[index].path
        chunks[-1].texture_count = chunks[index].texture_count
        chunks[-1].textures.clear()
        for i, texture in enumerate(chunks[index].textures):
            t = chunks[-1].textures.add()
            t.name = texture.name
            t.image = texture.image
            t.width = texture.width
            t.height = texture.height
            t.pixel_format = texture.pixel_format
            t.mipmap_count = texture.mipmap_count
            t.cubemap_format = texture.cubemap_format
            t.cubemap_size = texture.cubemap_size
            t.is_cubemap = texture.is_cubemap

        data.texture_chunk_index = len(chunks) - 1

        return {'FINISHED'}


class NutTexturePropertyGroup(PropertyGroup):


    def update_texture(self, context):
        if self.image:
            self.width = str(self.image.size[0])
            self.height = str(self.image.size[1])

            def get_pixel_format(ddsf):
                if ddsf.header.pixel_format.fourCC in dds.nut_pf_fourcc.keys():
                    pf = dds.nut_pf_fourcc[ddsf.header.pixel_format.fourCC]
                    return Pixel_Formats[pf]


                elif ddsf.header.pixel_format.bitmasks in dds.nut_pf_bitmasks.keys():
                    pf = dds.nut_pf_bitmasks[ddsf.header.pixel_format.bitmasks]
                    return Pixel_Formats[pf]

                else:
                    return 'UNSUPPORTED'
            
            #read pixel format
            if self.image.packed_files:
                ddsf = dds.read_dds(self.image.packed_file.data)
                self.pixel_format = get_pixel_format(ddsf)
            else:
                #try to read the file from the path
                ddsf = dds.read_dds(open(self.image.filepath, 'rb').read())
                self.pixel_format = get_pixel_format(ddsf)
        else:
            self.width = ''
            self.height = ''
            self.pixel_format = ''


    name: StringProperty(name="Name")
    image: bpy.props.PointerProperty(type=bpy.types.Image, name="Image", update=update_texture)
    index: IntProperty(name="Index")
    width: StringProperty(name="Width")
    height: StringProperty(name="Height")
    pixel_format: StringProperty(name="Pixel Format")
    mipmap_count: IntProperty(name="Mipmap Count", default=0)
    cubemap_format: IntProperty(name="Cubemap Format", default=0)
    cubemap_size: IntProperty(name="Cubemap Size", default=0)
    is_cubemap: BoolProperty(name="Is Cubemap", default=False)
    
    def update_name(self):
        #update texture count
        data: TextureChunksListPropertyGroup = bpy.context.object.xfbin_texture_chunks_data
        chunks = data.texture_chunks
        index = data.texture_chunk_index

        chunks[index].texture_count = len(chunks[index].textures)

        self.name = f'{chunks[index].name}_{len(chunks[index].textures) - 1}'

    def init_data(self, nut_texture: NutTexture, tex_name, path = ''):
        self.name = tex_name
        self.width = str(nut_texture.width)
        self.height = str(nut_texture.height)
        self.pixel_format = Pixel_Formats[nut_texture.pixel_format]
        self.mipmap_count = nut_texture.mipmap_count
        self.is_cubemap = nut_texture.is_cube_map

        if self.cubemap_format & 0x200:
            self.cubemap_format = nut_texture.cubemap_format
            self.cubemap_size = nut_texture.cubemap_size
            self.cubemap_faces = nut_texture.cubemap_faces

        #convert Nut Texture to DDS
        self.texture_data = dds.NutTexture_to_DDS(nut_texture)


        if bpy.data.images.get(self.name):
            #update existing image
            image = bpy.data.images[self.name]
            image.pack(data=self.texture_data, data_len=len(self.texture_data))
            image.source = 'FILE'
            image.use_fake_user = True
            image['nut_pixel_format'] = self.pixel_format
            image['nut_mipmaps_count'] = self.mipmap_count

            #assign the image in the end to avoid the update_texture function being called
            self.image = image

        else:
            #create new image
            image = bpy.data.images.new(self.name, width=int(self.width), height=int(self.height))
            image.pack(data=self.texture_data, data_len=len(self.texture_data))
            image.source = 'FILE'
            image.use_fake_user = True
            image['nut_pixel_format'] = self.pixel_format
            image['nut_mipmaps_count'] = self.mipmap_count

            #assign the image in the end to avoid the update_texture function being called
            self.image = image


class XfbinTextureChunkPropertyGroup(PropertyGroup):
    def update_texture_name(self, context):
        self.update_name()
    
    def update_count(self, context):
        if self.texture_count > len(self.textures):
            for i in range(self.texture_count - len(self.textures)):
                self.textures.add()
        elif self.texture_count < len(self.textures):
            for i in range(len(self.textures) - self.texture_count):
                self.textures.remove(len(self.textures) - 1)
                self.texture_index = min(0, len(self.textures) - 1)

    texture_name: StringProperty(
        name='Name',
        default='new_texture',
        update=update_texture_name,
    )

    path: StringProperty(
        name='Path',
        description='XFBIN chunk path that will be used for identifying the texture in the XFBIN.\n'
        'Should be the same as the path of the texture in the XFBIN to inject to.\n'
        'Example: "c/1nrt/tex/1nrtbody.nut"',
    )

    texture_count: IntProperty(min=0, update=update_count)
    
    textures: CollectionProperty(type=NutTexturePropertyGroup)

    texture_index: IntProperty()

    def update_name(self):
        self.name = self.texture_name

    def init_data(self, chunk: NuccChunkTexture):
        self.texture_name = chunk.name
        self.path = chunk.filePath
        self.nut: Nut = chunk.nut
        if self.nut:
            self.texture_count = len(self.nut.textures)
            
            self.textures.clear()
            for i, nut_texture in enumerate(self.nut.textures):
                texture = self.textures.add()
                texture.init_data(nut_texture, f'{self.texture_name}_{i}', self.path)
        else:
            self.reference = True
            

    reference: BoolProperty(
        name='Include in XFBIN',
        description='Repack the texture into the XFBIN when exporting.\n'
        'This should be enabled for all textures that are specific to the XFBIN '
        '(i.e. celshade/haching etc should not be included).\n\n'
        'Note: The path to the texture in NUT format (.nut) must be provided',
    )

    nut_path: StringProperty(
        name='NUT Path',
    )


class TextureChunksListPropertyGroup(PropertyGroup):
    texture_chunks: CollectionProperty(
        type=XfbinTextureChunkPropertyGroup,
    )

    texture_chunk_index: IntProperty()

    #clear: BoolProperty()

    def init_data(self, texture_chunks: List[NuccChunkTexture]):
        #self.texture_chunks.clear()
        for texture in texture_chunks:
            t: XfbinTextureChunkPropertyGroup = self.texture_chunks.add()
            t.init_data(texture)

    def clear(self):
        self.texture_chunks.clear()

class XfbinTextureChunkPropertyPanel(Panel):
    bl_idname = 'TEXTURE_PT_xfbin_texture_chunk_list'
    bl_label = '[XFBIN] Texture Chunks'

    bl_space_type = 'PROPERTIES'
    bl_context = 'texture'
    bl_region_type = 'WINDOW'

    @classmethod
    def poll(cls, context):
        obj = context.object
        return True

    def draw(self, context):
        layout = self.layout
        data: TextureChunksListPropertyGroup = bpy.context.scene.xfbin_texture_chunks_data
        row = layout.row()
        #box = row.box()
        row.template_list('XFBIN_UL_TextureList', 'NUT List', data, 'texture_chunks', data, 'texture_chunk_index', type='DEFAULT')
        index = data.texture_chunk_index
        
        row = row.column()

        row.operator('xfbin_texchunks.add_nut', icon='ADD', text='')
        row.operator('xfbin_texchunks.remove_nut', icon='REMOVE', text='')
        row.operator('xfbin_texchunks.duplicate_nut', icon='DUPLICATE', text='')
        row.operator('xfbin_texchunks.move_nut', icon='TRIA_UP', text='').direction = 'UP'
        row.operator('xfbin_texchunks.move_nut', icon='TRIA_DOWN', text='').direction = 'DOWN'

        
        if len(data.texture_chunks) > 0:
            texture = data.texture_chunks[data.texture_chunk_index]
            index = texture.texture_index
            if not texture.reference:
                row = layout.row()
                col = row.column()
                col.template_list('XFBIN_UL_TexturePreviewList', 'Texture List', texture, 'textures', texture, 'texture_index', type='DEFAULT', rows=5)
                colrow = col.row()
                colrow.prop(texture, 'texture_count', text='Texture Count')
                colrow.operator('xfbin_panel.open_image', icon='FILEBROWSER')
                
                if len(texture.textures) > 0:
                    row.template_ID_preview(texture.textures[index], 'image', hide_buttons=True)


class XFBIN_PANEL_OT_OpenImage(bpy.types.Operator):
    """Open an image to include in the NUT"""
    bl_idname = 'xfbin_panel.open_image'
    bl_label = 'Open Image (*.dds)'

    filepath: bpy.props.StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default='*.dds', options={'HIDDEN'})

    def execute(self, context):
        data: TextureChunksListPropertyGroup = context.scene.xfbin_texture_chunks_data
        chunks = data.texture_chunks
        index = data.texture_chunk_index

        if not chunks:
            # Should not happen
            return {'CANCELLED'}

        texture_chunk: XfbinTextureChunkPropertyGroup = chunks[index]
        textures = texture_chunk.textures
        texture_index = texture_chunk.texture_index

        if not textures:
            # Should not happen
            return {'CANCELLED'}

        texture: NutTexturePropertyGroup = textures[texture_index]
        #load the image
        with open(self.filepath, 'rb') as ddsf:
            texdata: dds.DDS = dds.read_dds(ddsf.read())

            #check if the dds is in a supported format
            if texdata.header.pixel_format.fourCC in dds.nut_pf_fourcc.keys():
                texture.pixel_format = Pixel_Formats[dds.nut_pf_fourcc[texdata.header.pixel_format.fourCC]]
            
            elif texdata.header.pixel_format.bitmasks in dds.nut_pf_bitmasks.keys():
                texture.pixel_format = Pixel_Formats[dds.nut_pf_bitmasks[texdata.header.pixel_format.bitmasks]]
            
            else:
                self.report({'ERROR'}, 'Unsupported DDS format. DDS file must be in one of the following formats:\n'
                'DXT1, DXT3, DXT5, B5G6R5, B5G5R5A1, B4G4R4A4, B8G8R8A8')
                return {'CANCELLED'}

        #load and pack the image
        image = bpy.data.images.load(self.filepath)
        image.alpha_mode = 'STRAIGHT'
        image.name = self.filepath.split('\\')[-1][:-4]
        image.filepath = texture_chunk.nut_path
        image.filepath_raw = self.filepath
        image.pack()
        image.source = 'FILE'
        #add custom properties to the image
        image['nut_pixel_format'] = texture.pixel_format
        image['nut_mipmaps_count'] = texdata.header.mipMapCount


        texture.image = image
        texture.name = image.name
        texture.width = str(texdata.header.width)
        texture.height = str(texdata.header.height)


        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)

        return {'RUNNING_MODAL'}
        

texture_chunks_property_groups = (
    NutTexturePropertyGroup,
    XfbinTextureChunkPropertyGroup,
    TextureChunksListPropertyGroup,
)

texture_chunks_classes = (
    *texture_chunks_property_groups,
    XFBIN_TexChunks_OT_AddNUT,
    XFBIN_TexChunks_OT_RemoveNUT,
    XFBIN_TexChunks_OT_MoveNUT,
    XFBIN_TexChunks_OT_DuplicateNUT,
    XFBIN_UL_TextureList,
    XFBIN_UL_TexturePreviewList,
    XFBIN_PANEL_OT_OpenImage,
    XfbinTextureChunkPropertyPanel,
)
