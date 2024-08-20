import bpy
from bpy.props import (BoolProperty, CollectionProperty, FloatProperty,
                       FloatVectorProperty, IntProperty, StringProperty, EnumProperty)
from bpy.types import Object, Panel, PropertyGroup

from ...xfbin_lib.xfbin.structure.nucc import (MaterialTextureGroup,
                                               NuccChunkMaterial,
                                               NuccChunkTexture)
from .common import (FloatPropertyGroup, draw_copy_paste_ops, draw_xfbin_list,
                     matrix_prop_group)
from ...xfbin_lib.xfbin.structure.nut import Pixel_Formats
from ...xfbin_lib.xfbin.structure import dds
from ...xfbin_lib.xfbin.structure.br import br_dds
from .texture_chunks_panel import XfbinTextureChunkPropertyGroup, NutTexturePropertyGroup
 
class XFBIN_UL_MatTextures(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            row.prop(item, 'texture_name',emboss= False, text='', icon='IMAGE_DATA')
            row.prop_search(item, 'texture_name', bpy.context.scene.xfbin_texture_chunks_data, 'texture_chunks', text='')

            #row.prop(item, 'path', text='',emboss=False, icon='FILE_FOLDER')
            #row.prop(item, 'reference', text='Reference', icon='FILE_TICK', toggle=True)


class XFBIN_UL_SelectTexture(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            row.prop(item, 'texture_name',emboss= False, text='', icon='IMAGE_DATA')
            row.prop(item, 'path', text='',emboss=False, icon='FILE_FOLDER')
            row.prop(item, 'reference', text='Reference', icon='FILE_TICK', toggle=True)


        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon='MATERIAL_DATA')
            layout.label(text="", icon='FILE_FOLDER')
            layout.label(text="", icon='TEXTURE')
            layout.label(text="", icon='LINKED')


class XFBIN_MatTexture_OT_Add(bpy.types.Operator):
    bl_idname = 'xfbin_mat.texture_add'
    bl_label = 'Add Texture'

    def execute(self, context):
        obj = context.object
        mat: XfbinMaterialPropertyGroup = obj.active_material.xfbin_material_data
        texture: MaterialNutTexturePropertyGroup = mat.NUTextures.add()
        texture.texture_count = 1
        mat.NUT_index = len(mat.NUTextures) - 1
        return {'FINISHED'}

class XFBIN_MatTexture_OT_Remove(bpy.types.Operator):
    bl_idname = 'xfbin_mat.texture_remove'
    bl_label = 'Remove Texture'

    def execute(self, context):
        obj = context.object
        mat: XfbinMaterialPropertyGroup = obj.active_material.xfbin_material_data
        if len(mat.NUTextures) > 0:
            mat.NUTextures.remove(mat.NUT_index)
            #move selection to previous item
            mat.NUT_index = max(0, mat.NUT_index - 1)

        return {'FINISHED'}

class XFBIN_MatTexture_OT_Move(bpy.types.Operator):
    bl_idname = 'xfbin_mat.texture_move'
    bl_label = 'Move Texture'

    direction: bpy.props.EnumProperty(
        items=(
            ('UP', 'Up', ''),
            ('DOWN', 'Down', ''),
        ),
        name='Direction',
    )

    def execute(self, context):
        obj = context.object
        mat: XfbinMaterialPropertyGroup = obj.active_material.xfbin_material_data
        texture_index = mat.NUT_index

        # Get the new index based on the direction
        new_index = texture_index - 1 if self.direction == 'UP' else texture_index + 1

        # Ensure the new index is within the valid range
        new_index = max(0, min(new_index, len(mat.NUTextures) - 1))

        # Move the item
        mat.NUTextures.move(texture_index, new_index)

        # Update the UIList to reflect the moved item and update the selection
        mat.NUT_index = new_index

        return {'FINISHED'}

class XFBIN_MatTexture_OT_Duplicate(bpy.types.Operator):
    bl_idname = 'xfbin_mat.texture_duplicate'
    bl_label = 'Copy Texture'

    def execute(self, context):
        obj = context.object
        mat: XfbinMaterialPropertyGroup = obj.active_material.xfbin_material_data
        texture_index = mat.NUT_index

        if len(mat.NUTextures) > 0:
            newTexture: MaterialNutTexturePropertyGroup = mat.NUTextures.add()
            newTexture.texture_name = mat.NUTextures[texture_index].texture_name

        return {'FINISHED'}


class NutSubTexturePropertyGroup(PropertyGroup):
    def update_texture(self, context):
        if self.texture:
            self.width = str(self.texture.size[0])
            self.height = str(self.texture.size[1])

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
            if self.texture.packed_file:
                ddsf = dds.read_dds(self.texture.packed_file.data)
                self.pixel_format = get_pixel_format(ddsf)
            else:
                #try to read the file from the path
                ddsf = dds.read_dds(open(self.texture.filepath, 'rb').read())
                self.pixel_format = get_pixel_format(ddsf)
        else:
            self.width = ''
            self.height = ''
            self.pixel_format = ''


    texture: bpy.props.PointerProperty(type=bpy.types.Image, update= update_texture)

    width: StringProperty()

    height: StringProperty()

    pixel_format: StringProperty()


class MaterialNutTexturePropertyGroup(PropertyGroup):
    def update_texture_name(self, context):
        self.update_name()
    
    def update_count(self, context):
        if self.texture_count > len(self.textures):
            for i in range(self.texture_count - len(self.textures)):
                self.textures.add()
        elif self.texture_count < len(self.textures):
            for i in range(len(self.textures) - self.texture_count):
                self.textures.remove(-1)

    texture_name: StringProperty(
        name='Texture Name',
        default='new_texture',
        update=update_texture_name,
    )

    path: StringProperty(
        name='Chunk Path',
        description='XFBIN chunk path that will be used for identifying the texture in the XFBIN.\n'
        'Should be the same as the path of the texture in the XFBIN to inject to.\n'
        'Example: "c/1nrt/tex/1nrtbody.nut"',
    )

    textures: CollectionProperty(
        type=NutSubTexturePropertyGroup,
    )

    texture_index: IntProperty()

    texture_count: IntProperty(min=0, update= update_count)

    reference: BoolProperty(
        name='Reference',
        default=False,
    )

    def update_name(self):
        self.name = self.texture_name

    def init_data(self, chunk: NuccChunkTexture):
        self.texture_name = chunk.name
        self.path = chunk.filePath
        if chunk.nut:
            self.texture_count = chunk.nut.texture_count

            self.textures.clear()
            for i in range(chunk.nut.texture_count):
                t: NutSubTexturePropertyGroup = self.textures.add()
                t.texture = bpy.data.images.get(f"{chunk.name}_{i}")
        else:
            self.reference = True

'''
class TextureGroupPropertyGroup(PropertyGroup):
    def update_flag(self, context):
        self.update_name()

    flag: IntProperty(
        name='Flag',
        min=-0x80_00_00_00,
        max=0x7F_FF_FF_FF,
        update=update_flag,
    )

    textures: CollectionProperty(
        type=MaterialNutTexturePropertyGroup,
    )

    texture_index: IntProperty()

    test: StringProperty()

    def update_name(self):
        self.name = str(self.flag)

    def init_data(self, group: MaterialTextureGroup):
        self.flag = group.unk

        self.textures.clear()
        for chunk in group.texture_chunks:
            t: MaterialNutTexturePropertyGroup = self.textures.add()
            t.init_data(chunk)
'''


class XfbinMaterialTexturesPropertyGroup(PropertyGroup):
    def update_texture(self, context):
        self.texture_name = self.texture.name
    
    texture: bpy.props.PointerProperty(type=XfbinTextureChunkPropertyGroup)
    texture_name: StringProperty()

    magFilter: EnumProperty(default='1', items=(
                            ('1', 'Nearest', ''),
                            ('2', 'Linear', ''),
                            ))
    
    minFilter: EnumProperty(default='1', items=(
                            ('1', 'Nearest', ''),
                            ('2', 'Linear', ''),
                            ('3', 'Nearest Mipmap Nearest', ''),
                            ('4', 'Linear Mipmap Nearest', ''),
                            ('5', 'Nearest Mipmap Linear', ''),
                            ('6', 'Linear Mipmap Linear', ''),
                            ))
    mapMode: IntProperty(default=0)
    mipDetail: IntProperty()
    wrapModeS: EnumProperty(default='1', items=(
                            ('1', 'Repeat', ''),
                            ('2', 'Mirror', ''),
                            ('3', 'Extend', ''),
                            ('4', 'Clip', ''),
                            ('5', 'ExtendUnk', ''),
                            ('6', 'Extend & Mirror', '')
                        ))
    
    wrapModeT: EnumProperty(default='1', items=(
                            ('1', 'Repeat', ''),
                            ('2', 'Mirror', ''),
                            ('3', 'Extend', ''),
                            ('4', 'Clip', ''),
                            ('5', 'ExtendUnk', ''),
                            ('6', 'Extend & Mirror', '')
                        ))
    
    unk0: IntProperty(default=0)
    unk1: IntProperty(default=0)
    unk2: IntProperty(default=7783)


    def init_data(self, chunk):
        self.texture_name = chunk.name
    

    def init_tex_props(self, tex):
        self.magFilter = str(tex.magFilter)
        self.minFilter = str(tex.minFilter)
        self.mapMode = tex.mapMode
        self.mipDetail = tex.mipDetail
        self.wrapModeS = str(tex.wrapModeS)
        self.wrapModeT = str(tex.wrapModeT)

        self.unk0 = tex.unk0
        self.unk1 = tex.unk1
        self.unk2 = tex.unk2


class XFBIN_UL_MatShaders(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        row.prop(item, 'name',emboss= False, text='', icon='MATERIAL')


class XFBIN_MatShader_OT_Add(bpy.types.Operator):
    bl_idname = 'xfbin_mat.shader_add'
    bl_label = 'Add Shader'

    def execute(self, context):
        obj = context.object
        mat: XfbinMaterialPropertyGroup = obj.active_material.xfbin_material_data
        shader: NUD_ShaderPropertyGroup = mat.NUD_Shaders.add()
        mat.NUD_Shader_index = len(mat.NUD_Shaders) - 1
        return {'FINISHED'}

class XFBIN_MatShader_OT_Remove(bpy.types.Operator):
    bl_idname = 'xfbin_mat.shader_remove'
    bl_label = 'Remove Shader'

    def execute(self, context):
        obj = context.object
        mat: XfbinMaterialPropertyGroup = obj.active_material.xfbin_material_data
        if len(mat.NUD_Shaders) > 0:
            mat.NUD_Shaders.remove(mat.NUD_Shader_index)
            #move selection to previous item
            mat.NUD_Shader_index = max(0, mat.NUD_Shader_index - 1)

        return {'FINISHED'}


class XFBIN_MatShader_OT_Move(bpy.types.Operator):
    bl_idname = 'xfbin_mat.shader_move'
    bl_label = 'Move Shader'

    direction: bpy.props.EnumProperty(
        items=(
            ('UP', 'Up', ''),
            ('DOWN', 'Down', ''),
        ),
        name='Direction',
    )

    def execute(self, context):
        obj = context.object
        mat: XfbinMaterialPropertyGroup = obj.active_material.xfbin_material_data
        shader_index = mat.NUD_Shader_index

        # Get the new index based on the direction
        new_index = shader_index - 1 if self.direction == 'UP' else shader_index + 1

        # Ensure the new index is within the valid range
        new_index = max(0, min(new_index, len(mat.NUD_Shaders) - 1))

        # Move the item
        mat.NUD_Shaders.move(shader_index, new_index)

        # Update the UIList to reflect the moved item and update the selection
        mat.NUD_Shader_index = new_index

        return {'FINISHED'}

class XFBIN_MatShader_OT_Duplicate(bpy.types.Operator):
    bl_idname = 'xfbin_mat.shader_duplicate'
    bl_label = 'Copy Shader'

    def execute(self, context):
        obj = context.object
        mat: XfbinMaterialPropertyGroup = obj.active_material.xfbin_material_data
        shader_index = mat.NUD_Shader_index

        if len(mat.NUD_Shaders) > 0:
            newShader: NUD_ShaderPropertyGroup = mat.NUD_Shaders.add()
            newShader.init_copy(mat.NUD_Shaders[shader_index])

        return {'FINISHED'}


class XFBIN_UL_MatParams(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        row.prop(item, 'name',emboss= False, text='')
        row.split(factor=0.5)
        row.prop(item, 'count', text='Count')

class XFBIN_MatParam_OT_Add(bpy.types.Operator):
    bl_idname = 'xfbin_mat.param_add'
    bl_label = 'Add Param'

    def execute(self, context):
        obj = context.object
        mat: XfbinMaterialPropertyGroup = obj.active_material.xfbin_material_data
        shader_index = mat.NUD_Shader_index
        if shader_index < 0:
            return {'CANCELLED'}
        
        shader: NUD_ShaderPropertyGroup = mat.NUD_Shaders[shader_index]
        param: NUD_ShaderParamPropertyGroup = shader.shader_params.add()
        shader.NUD_ShaderParam_index = len(shader.shader_params) - 1
        return {'FINISHED'}

class XFBIN_MatParam_OT_Remove(bpy.types.Operator):
    bl_idname = 'xfbin_mat.param_remove'
    bl_label = 'Remove Param'

    def execute(self, context):
        obj = context.object
        mat: XfbinMaterialPropertyGroup = obj.active_material.xfbin_material_data
        shader_index = mat.NUD_Shader_index
        if shader_index < 0:
            return {'CANCELLED'}
        
        shader: NUD_ShaderPropertyGroup = mat.NUD_Shaders[shader_index]
        if len(shader.shader_params) > 0:
            shader.shader_params.remove(shader.NUD_ShaderParam_index)
            #move selection to previous item
            shader.NUD_ShaderParam_index = max(0, shader.NUD_ShaderParam_index - 1)

        return {'FINISHED'}
    
class XFBIN_MatParam_OT_Move(bpy.types.Operator):
    bl_idname = 'xfbin_mat.param_move'
    bl_label = 'Move Param'

    direction: bpy.props.EnumProperty(
        items=(
            ('UP', 'Up', ''),
            ('DOWN', 'Down', ''),
        ),
        name='Direction',
    )

    def execute(self, context):
        obj = context.object
        mat: XfbinMaterialPropertyGroup = obj.active_material.xfbin_material_data
        shader_index = mat.NUD_Shader_index
        if shader_index < 0:
            return {'CANCELLED'}
        
        shader: NUD_ShaderPropertyGroup = mat.NUD_Shaders[shader_index]
        param_index = shader.NUD_ShaderParam_index

        # Get the new index based on the direction
        new_index = param_index - 1 if self.direction == 'UP' else param_index + 1

        # Ensure the new index is within the valid range
        new_index = max(0, min(new_index, len(shader.shader_params) - 1))

        # Move the item
        shader.shader_params.move(param_index, new_index)

        # Update the UIList to reflect the moved item and update the selection
        shader.NUD_ShaderParam_index = new_index

        return {'FINISHED'}
    
class XFBIN_MatParam_OT_Duplicate(bpy.types.Operator):
    bl_idname = 'xfbin_mat.param_duplicate'
    bl_label = 'Copy Param'

    def execute(self, context):
        obj = context.object
        mat: XfbinMaterialPropertyGroup = obj.active_material.xfbin_material_data
        shader_index = mat.NUD_Shader_index
        if shader_index < 0:
            return {'CANCELLED'}
        
        shader: NUD_ShaderPropertyGroup = mat.NUD_Shaders[shader_index]
        param_index = shader.NUD_ShaderParam_index

        if len(shader.shader_params) > 0:
            newParam: NUD_ShaderParamPropertyGroup = shader.shader_params.add()
            newParam.init_copy(shader.shader_params[param_index])

        return {'FINISHED'}
    



class NUD_ShaderParamPropertyGroup(PropertyGroup):
    
    def update_count(self, context):
        if self.count > len(self.values):
            for i in range(self.count - len(self.values)):
                self.values.add()
        elif self.count < len(self.values):
            for i in range(len(self.values) - self.count):
                self.values.remove(-1)
    
    name: StringProperty()
    count: IntProperty(update = update_count, min=0, max=255)
    values: CollectionProperty(
        type=FloatPropertyGroup,
    )

    index: IntProperty()

    def init_data(self, param):
        self.name = param.name
        for value in param.values:
            v = self.values.add()
            v.value = value
        
        self.count = len(param.values)
    
    def init_copy(self, param):
        self.name = param.name
        for value in param.values:
            v = self.values.add()
            v.value = value.value
        
        self.count = param.count


class NUD_ShaderTexPropertyGroup(PropertyGroup):
    name = StringProperty()
    magFilter: IntProperty()
    minFilter: IntProperty()
    mapMode: IntProperty()
    mipDetail: IntProperty()
    wrapModeS: IntProperty()
    wrapModeT: IntProperty()
    unk0: IntProperty()
    unk1: IntProperty()
    unk2: IntProperty()


    def init_data(self, tex):
        self.magFilter = tex.magFilter
        self.minFilter = tex.minFilter
        self.mapMode = tex.mapMode
        self.mipDetail = tex.mipDetail
        self.wrapModeS = tex.wrapModeS
        self.wrapModeT = tex.wrapModeT
        self.unk0 = tex.unk0
        self.unk1 = tex.unk1
        self.unk2 = tex.unk2


class NUD_ShaderPropertyGroup(PropertyGroup):
    def update_shader(self, context):
        self.name = self.name
    
    name: StringProperty(name='Name')
    source_factor: IntProperty(name='Source Factor')
    destination_factor: IntProperty(name='Destination Factor')
    alpha_test: IntProperty(name='Alpha Test')
    alpha_function: IntProperty(name='Alpha Function')
    alpha_reference: IntProperty(name='Alpha Reference')
    cull_mode: EnumProperty(
        name='Cull Mode',
        items=(
            ("0", 'None', ''),
            ("1028", 'Front', ''),
            ("1029", 'Back', ''),
        )
    )
    unk1: FloatProperty()
    unk2: FloatProperty()
    zbuffer_offset: IntProperty(name='Z Buffer Offset')

    shader_params: CollectionProperty(
        type=NUD_ShaderParamPropertyGroup,
    )

    NUD_ShaderParam_index: IntProperty()

    shader_tex_props: CollectionProperty(
        type=NUD_ShaderTexPropertyGroup,
    )


    def init_data(self, shader):
        self.name = str(hex(shader.flags))
        self.source_factor = shader.sourceFactor
        self.destination_factor = shader.destFactor
        self.alpha_test = shader.alphaTest
        self.alpha_function = shader.alphaFunction
        self.alpha_reference = shader.refAlpha
        self.cull_mode = str(shader.cullMode)
        self.unk1 = shader.unk1
        self.unk2 = shader.unk2
        self.zbuffer_offset = shader.zBufferOffset

        self.shader_params.clear()
        for param in shader.properties:
            p = self.shader_params.add()
            p.init_data(param)
        
        self.shader_tex_props.clear()
        for tex in shader.textures:
            t = self.shader_tex_props.add()
            t.init_data(tex)
    
    def init_copy(self, shader):
        self.name = shader.name
        self.source_factor = shader.source_factor
        self.destination_factor = shader.destination_factor
        self.alpha_test = shader.alpha_test
        self.alpha_function = shader.alpha_function
        self.alpha_reference = shader.alpha_reference
        self.cull_mode = shader.cull_mode
        self.unk1 = shader.unk1
        self.unk2 = shader.unk2
        self.zbuffer_offset = shader.zbuffer_offset

        self.shader_params.clear()
        for param in shader.shader_params:
            p = self.shader_params.add()
            p.init_copy(param)
        
        self.shader_tex_props.clear()
        for tex in shader.shader_tex_props:
            t = self.shader_tex_props.add()
            t.init_data(tex)
        


class XfbinMaterialPropertyGroup(PropertyGroup):
    """Property group that contains attributes of a nuccChunkMaterial."""

    alpha: FloatProperty(
        name='Alpha',
        min=0,
        max=255,
    )
    glare: FloatProperty(name='Glare', min=0, max=255)

    UV0: BoolProperty(name='Use UV0')
    UV1: BoolProperty(name='Use UV1')
    UV2: BoolProperty(name='Use UV2')
    UV3: BoolProperty(name='Use UV3')
    Blend: BoolProperty(name='Use Blend Rate and Type')
    useFallOff: BoolProperty(name='Use fallOff')
    useOutlineID: BoolProperty(name='Use outlineID')

    uvOffset0: FloatVectorProperty(name='uvOffset0', size=4)
    uvOffset1: FloatVectorProperty(name='uvOffset1', size=4)
    uvOffset2: FloatVectorProperty(name='uvOffset2', size=4)
    uvOffset3: FloatVectorProperty(name='uvOffset3', size=4)
    blendRate: FloatProperty(name='Blend Rate')
    blendType: FloatProperty(name='Blend Type')
    fallOff: FloatProperty(name='fallOff')
    outlineID: FloatProperty(name='outlineID')

    texGroupsCount: IntProperty(name='Texture Groups Count', min=0, max=4)

    '''texture_groups: CollectionProperty(
        type=TextureGroupPropertyGroup,
        name='Texture Groups',
    )

    texture_group_index: IntProperty()
'''
    NUTextures: CollectionProperty(
        type=XfbinMaterialTexturesPropertyGroup,
        name='NUTextures',
    )

    NUT_index: IntProperty()

    NUD_Shaders: CollectionProperty(
        type=NUD_ShaderPropertyGroup,
        name='NUD Shaders',
    )

    NUD_Shader_index: IntProperty()

    def update_name(self):
        self.name = self.material_name
    
    def __init__(self):
        self.material_name = ""
        self.alpha = 0.0
        self.glare = 0.0

        self.flags = 0
        
        self.UV0 = False
        self.uvOffset0 = (0.0, 0.0, 1.0, 1.0)
        self.UV1 = False
        self.uvOffset1 = (0.0, 0.0, 1.0, 1.0)
        self.UV2 = False
        self.uvOffset2 = (0.0, 0.0, 1.0, 1.0)
        self.UV3 = False
        self.uvOffset3 = (0.0, 0.0, 1.0, 1.0)
        self.Blend = False
        self.blendRate = 0.0
        self.blendType = 0.0
        self.useFallOff = False
        self.fallOff = 0.0
        self.useOutlineID = False
        self.outlineID = 0.0


    def init_data(self, material: NuccChunkMaterial, mesh):
        self.material_name = material.name
        print(f"material name: {material.name}")

        self.alpha = material.alpha * 0.003921569
        self.glare = material.glare

        self.flags = material.flags
        
        if material.flags & 0x01:
            self.UV0 = True
            self.uvOffset0 = material.UV0
        if material.flags & 0x02:
            self.UV1 = True
            self.uvOffset1 = material.UV1
        if material.flags & 0x04:
            self.UV2 = True
            self.uvOffset2 = material.UV2
        if material.flags & 0x08:
            self.UV3 = True
            self.uvOffset3 = material.UV3
        if material.flags & 0x10:
            self.Blend = True
            self.blendRate = material.BlendRate
            self.blendType = material.BlendType
        if material.flags & 0x20:
            self.useFallOff = True
            self.fallOff = material.fallOff
        if material.flags & 0x40:
            self.useOutlineID = True
            self.outlineID = material.outlineID
        
        '''self.texture_groups.clear()
        for group in material.texture_groups:
            g = self.texture_groups.add()
            g.init_data(group)'''
        
        self.texGroupsCount = len(material.texture_groups)
        
        mesh_shaders = mesh.materials
        for shader in mesh_shaders:
            if len(self.NUD_Shaders) >= 4:
                break
            
            if str(hex(shader.flags)) in self.NUD_Shaders.keys():
                print('shader already exists')
                s = self.NUD_Shaders[str(hex(shader.flags))]
                s.init_data(shader)
            else:
                s = self.NUD_Shaders.add()
                s.init_data(shader)
        
        self.NUTextures.clear()
        tex_group = material.texture_groups[0]
        for i, chunk in enumerate(tex_group.texture_chunks):
            if bpy.context.scene.xfbin_texture_chunks_data.texture_chunks.get(chunk.name):
                texture = bpy.context.scene.xfbin_texture_chunks_data.texture_chunks[chunk.name]
            else:
                #create a new texture chunk
                texture = bpy.context.scene.xfbin_texture_chunks_data.texture_chunks.add()
                texture.init_data(chunk)
            
            nut = self.NUTextures.add()
            nut.init_data(texture)
            
            #get the texture props from the first nud shader
            nud_shader = self.NUD_Shaders[0]
            tex = nud_shader.shader_tex_props[i]
            nut.init_tex_props(tex)



class XfbinMaterialPropertyPanel(Panel):
    bl_idname = 'MATERIAL_PT_XFBIN_material'
    bl_label = 'XFBIN Material Data'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'material'
    
    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj.active_material and obj.active_material.xfbin_material_data

    def draw(self, context):
        layout = self.layout
        obj = context.object

        if obj.active_material and obj.active_material.xfbin_material_data:
            material: XfbinMaterialPropertyGroup = obj.active_material.xfbin_material_data
            box = layout.box()

            row = box.row()
            row.prop(material, 'alpha')
            row.prop(material, 'glare')

            row = box.row()
            row.prop(material, 'UV0')
            row.prop(material, 'UV1')
            row.prop(material, 'UV2')
            row.prop(material, 'UV3')
            if material.UV0:
                row = box.row()
                row.prop(material, 'uvOffset0')
            
            if material.UV1:
                row = box.row() 
                row.prop(material, 'uvOffset1')
                        
            if material.UV2:
                row = box.row()
                row.prop(material, 'uvOffset2')
                        
            if material.UV3:
                row = box.row()
                row.prop(material, 'uvOffset3')
            
            row = box.row()
            row.prop(material, 'Blend')
            row.prop(material, 'useFallOff')

            row = box.row()
            if material.Blend:
                row.prop(material, 'blendRate')
                row.prop(material, 'blendType')
                        
            if material.useFallOff:
                row.prop(material, 'fallOff')
            
            row = box.row()
            row.prop(material, 'useOutlineID')
            row = box.row()
            if material.useOutlineID:
                
                row.prop(material, 'outlineID')

            row.prop(material, 'texGroupsCount')
            

class NUD_ShaderPropertyPanel(Panel):
    bl_idname = 'MATERIAL_PT_NUD_shader'
    bl_parent_id = 'MATERIAL_PT_XFBIN_material'
    bl_label = 'NUD Shaders'

    bl_space_type = 'PROPERTIES'
    bl_context = 'object'
    bl_region_type = 'WINDOW'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        mat: XfbinMaterialPropertyGroup = obj.active_material.xfbin_material_data
        return True

    def draw(self, context):
        layout = self.layout
        obj = context.object
        mat: XfbinMaterialPropertyGroup = obj.active_material.xfbin_material_data

        col = layout.column()
        row = col.row()

        row.label(text='Shaders:')
        row.label(text='Shader Params:')

        row = col.row()

        #draw_xfbin_list(row, 0, mat, f'{mat}', 'NUD_Shaders', 'NUD_Shader_index', enable_text=False)

        row.template_list(
            "XFBIN_UL_MatShaders", "", mat, "NUD_Shaders", mat, "NUD_Shader_index",
            rows=4, maxrows=10, type='DEFAULT'
        )   
        col = row.column(align=True)
        col.operator("xfbin_mat.shader_add", icon='ADD', text="")
        col.operator("xfbin_mat.shader_remove", icon='REMOVE', text="")
        col.operator("xfbin_mat.shader_duplicate", icon='DUPLICATE', text="")
        col.operator("xfbin_mat.shader_move", icon='TRIA_UP', text="").direction = 'UP'
        col.operator("xfbin_mat.shader_move", icon='TRIA_DOWN', text="").direction = 'DOWN'


        shader_index = mat.NUD_Shader_index

        if mat.NUD_Shaders and shader_index >= 0:
            shader: NUD_ShaderPropertyGroup = mat.NUD_Shaders[shader_index]
            #draw_xfbin_list(row, 0, shader, f'{shader}', 'shader_params', 'NUD_ShaderParam_index', enable_text=False)

            row.template_list(
                "XFBIN_UL_MatParams", "", shader, "shader_params", shader, "NUD_ShaderParam_index",
                rows=4, maxrows=10, type='DEFAULT'
            )
            col = row.column(align=False)
            col.operator("xfbin_mat.param_add", icon='ADD', text="")
            col.operator("xfbin_mat.param_remove", icon='REMOVE', text="")
            col.operator("xfbin_mat.param_duplicate", icon='DUPLICATE', text="")
            col.operator("xfbin_mat.param_move", icon='TRIA_UP', text="").direction = 'UP'
            col.operator("xfbin_mat.param_move", icon='TRIA_DOWN', text="").direction = 'DOWN'


            param_index = shader.NUD_ShaderParam_index

            row = layout.row()
            if shader.shader_params and param_index >= 0:
                param: NUD_ShaderParamPropertyGroup = shader.shader_params[param_index]
                if param.count > 0:
                    box = layout.box()
                    row = box.row()
                    matrix_prop_group(row, param, 'values', param.count, "Values")

            box = layout.box()
            row = box.row()
            row.prop(shader, 'name')
            row = box.row()
            row.prop(shader, 'source_factor')
            row.prop(shader, 'destination_factor')
            row = box.row()
            row.prop(shader, 'alpha_test')
            row.prop(shader, 'alpha_function')
            row.prop(shader, 'alpha_reference')
            row = box.row()
            row.prop(shader, 'cull_mode')
            row.prop(shader, 'zbuffer_offset')
            row = box.row()
            row.prop(shader, 'unk1')
            row.prop(shader, 'unk2')

            #row = box.row()


class NutTexturePropertyPanel(Panel):
    bl_idname = 'MATERIAL_PT_NUT_texture'
    bl_parent_id = 'MATERIAL_PT_XFBIN_material'
    bl_label = 'Textures'

    bl_space_type = 'PROPERTIES'
    bl_context = 'object'
    bl_region_type = 'WINDOW'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        mat: XfbinMaterialPropertyGroup = obj.active_material.xfbin_material_data
        return True

    def draw(self, context):
        layout = self.layout
        obj = context.object
        mat: XfbinMaterialPropertyGroup = obj.active_material.xfbin_material_data
        #group: TextureGroupPropertyGroup = mat.texture_groups[mat.texture_group_index]

        row = layout.row()
        #row.prop_search(group, 'test', bpy.context.scene.xfbin_texture_chunks_data, 'texture_chunks', text='Texture Name')
        row = layout.row()
        row.template_list(
            "XFBIN_UL_MatTextures", "", mat, "NUTextures", mat, "NUT_index",
            rows=4, maxrows=10, type='DEFAULT'
        )
        col = row.column(align=True)
        col.operator("xfbin_mat.texture_add", icon='ADD', text="")
        col.operator("xfbin_mat.texture_remove", icon='REMOVE', text="")
        col.operator("xfbin_mat.texture_duplicate", icon='DUPLICATE', text="")
        col.operator("xfbin_mat.texture_move", icon='TRIA_UP', text="").direction = 'UP'
        col.operator("xfbin_mat.texture_move", icon='TRIA_DOWN', text="").direction = 'DOWN'

        texture_index = mat.NUT_index
        
        if mat.NUTextures and texture_index >= 0:
            texture_n: MaterialNutTexturePropertyGroup = mat.NUTextures[texture_index]
            texture = bpy.context.scene.xfbin_texture_chunks_data.texture_chunks.get(texture_n.texture_name)
            if texture:
                box = layout.box()
                box.prop(texture, 'texture_count', text='Texture Count')
                for i in range(texture.texture_count):
                    row = box.row() 
                    row.prop(texture.textures[i], 'image', text=f'Texture {i}')
                    row.operator('xfbin_mat_panel.open_image', text='Open a DDS image', icon='FILEBROWSER')
                    row = box.row()
                    row.prop(texture.textures[i], 'width', text='Width', emboss=False)
                    row.prop(texture.textures[i], 'height', text='Height', emboss=False)
                    row.prop(texture.textures[i], 'pixel_format', text='Format', emboss=False)
            

            #texture props panel
            box = layout.box()
            row = box.row()
            row.prop(texture_n, 'magFilter')
            row.prop(texture_n, 'minFilter')
            row = box.row()
            row.prop(texture_n, 'mapMode')
            row.prop(texture_n, 'mipDetail')
            row = box.row()
            row.prop(texture_n, 'wrapModeS')
            row.prop(texture_n, 'wrapModeT')
            row = box.row()
            row.prop(texture_n, 'unk0')
            row.prop(texture_n, 'unk1')
            row.prop(texture_n, 'unk2')


'''
class TextureGroupPropertyPanel(Panel):
    bl_idname = 'MATERIAL_PT_NUT_texture_group'
    bl_parent_id = 'MATERIAL_PT_XFBIN_material'
    bl_label = 'Texture Groups'

    bl_space_type = 'PROPERTIES'
    bl_context = 'object'
    bl_region_type = 'WINDOW'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj.active_material.xfbin_material_data

    def draw(self, context):
        layout = self.layout
        obj = context.object
        mat: XfbinMaterialPropertyGroup = obj.active_material.xfbin_material_data

        draw_xfbin_list(layout, 0, mat, f'{mat}', 'texture_groups', 'texture_group_index')

        texture_group_index = mat.texture_group_index

        if mat.texture_groups and texture_group_index >= 0:
            group: TextureGroupPropertyGroup = mat.texture_groups[texture_group_index]
            box = layout.box()

            box.prop(group, 'flag')
'''

class XFBIN_MatTexture_Open(bpy.types.Operator):
    """Open an image to include in the NUT"""
    bl_idname = 'xfbin_mat_panel.open_image'
    bl_label = 'Open Image (*.dds)'

    filepath: bpy.props.StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default='*.dds', options={'HIDDEN'})

    def execute(self, context):
        obj = context.object
        mat: XfbinMaterialPropertyGroup = obj.active_material.xfbin_material_data
        mat_texture_index = mat.NUT_index

        if mat_texture_index < 0:
            return {'CANCELLED'}
        
        mat_textures = mat.NUTextures
        mat_texture: MaterialNutTexturePropertyGroup = mat_textures[mat_texture_index]
        nut_texture = bpy.context.scene.xfbin_texture_chunks_data.texture_chunks.get(mat_texture.texture_name)
        if not nut_texture:
            return {'CANCELLED'}
        
        texture = nut_texture.textures[mat_texture_index]

        #load the image
        
        with open(self.filepath, 'rb') as ddsf:
            texdata: dds.DDS = dds.read_dds(ddsf.read())

            #check if the dds is in a supported format
            if texdata.header.pixel_format.fourCC in dds.nut_pf_fourcc.keys():
                texture.pixel_format = str(dds.nut_pf_fourcc[texdata.header.pixel_format.fourCC])
            
            elif texdata.header.pixel_format.bitmasks in dds.nut_pf_bitmasks.keys():
                texture.pixel_format = str(dds.nut_pf_bitmasks[texdata.header.pixel_format.bitmasks])
            
            else:
                self.report({'ERROR'}, 'Unsupported DDS format. DDS file must be in one of the following formats:\n'
                'DXT1, DXT3, DXT5, B5G6R5, B5G5R5A1, B4G4R4A4, B8G8R8A8')
                return {'CANCELLED'}

        #load and pack the image
        image = bpy.data.images.load(self.filepath)
        image.alpha_mode = 'STRAIGHT'
        image.name = self.filepath.split('\\')[-1][:-4]
        image.pack()
        #image.pack(data=texdata, data_len=len(texdata))
        image.source = 'FILE'
        #add custom properties to the image
        image['nut_pixel_format'] = str(texdata.header.pixel_format)
        image['nut_mipmaps_count'] = str(texdata.header.mipMapCount)

        texture.textures = image
        texture.name = image.name
        texture.width = str(texdata.header.width)
        texture.height = str(texdata.header.height)

        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)

        return {'RUNNING_MODAL'}


material_property_groups = (
    NutSubTexturePropertyGroup,
    MaterialNutTexturePropertyGroup,
    XfbinMaterialTexturesPropertyGroup,
    NUD_ShaderParamPropertyGroup,
    NUD_ShaderTexPropertyGroup,
    NUD_ShaderPropertyGroup,
    #TextureGroupPropertyGroup,
    XfbinMaterialPropertyGroup,    
)

material_classes = (
    *material_property_groups,
    XFBIN_UL_MatTextures,
    XFBIN_UL_MatShaders,
    XFBIN_UL_MatParams,
    XFBIN_MatTexture_OT_Add,
    XFBIN_MatTexture_OT_Remove,
    XFBIN_MatTexture_OT_Move,
    XFBIN_MatTexture_Open,
    XFBIN_MatTexture_OT_Duplicate,
    XFBIN_MatShader_OT_Add,
    XFBIN_MatShader_OT_Remove,
    XFBIN_MatShader_OT_Move,
    XFBIN_MatShader_OT_Duplicate,
    XFBIN_MatParam_OT_Add,
    XFBIN_MatParam_OT_Remove,
    XFBIN_MatParam_OT_Move,
    XFBIN_MatParam_OT_Duplicate,
    XfbinMaterialPropertyPanel,
    #TextureGroupPropertyPanel,
    NutTexturePropertyPanel,
    NUD_ShaderPropertyPanel,
)
