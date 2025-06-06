import bpy
from bpy.props import (BoolProperty, CollectionProperty, FloatProperty, PointerProperty,
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
            row.prop(item, 'name',emboss= False, text='', icon='IMAGE_DATA')
            row.prop_search(item, 'name', bpy.context.scene.xfbin_texture_chunks_data, 'texture_chunks', text='')


class XFBIN_MatTexture_OT_Add(bpy.types.Operator):
    bl_idname = 'xfbin_mat.texture_add'
    bl_label = 'Add Texture'

    def execute(self, context):
        obj = context.object
        mat: XfbinMaterialPropertyGroup = obj.active_material.xfbin_material_data
        texture: XfbinMaterialTexturesPropertyGroup = mat.NUTextures.add()
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
            newTexture: XfbinMaterialTexturesPropertyGroup = mat.NUTextures.add()
            newTexture.name = mat.NUTextures[texture_index].name

        return {'FINISHED'}


class XfbinMaterialTexturesPropertyGroup(PropertyGroup):
    def update_name(self, context):
        self.name = self.texture.name


    name: StringProperty(default='new_texture')
    
    texture: bpy.props.PointerProperty(
        type=XfbinTextureChunkPropertyGroup,
        update=update_name)

    magFilter: EnumProperty(default='2', items=(
                            ('1', 'Nearest', ''),
                            ('2', 'Linear', ''),
                            ))
    
    minFilter: EnumProperty(default='2', items=(
                            ('1', 'Nearest', ''),
                            ('2', 'Linear', ''),
                            ('3', 'Nearest Mipmap Nearest', ''),
                            ('4', 'Linear Mipmap Nearest', ''),
                            ('5', 'Nearest Mipmap Linear', ''),
                            ('6', 'Linear Mipmap Linear', ''),
                            ))
    mapMode: IntProperty(default=0)
    mipDetail: IntProperty(default=6)
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
    
    baseID: IntProperty(default=0)
    groupID: IntProperty(default=0)
    subGroupID: IntProperty(default=0)
    textureID: IntProperty(default=0)
    unk1: IntProperty(default=0)
    LOD: IntProperty(default=7783)


    def init_data(self, chunk):
        self.name = chunk.name
    

    def init_tex_props(self, tex):
        self.magFilter = str(tex.magFilter)
        self.minFilter = str(tex.minFilter)
        self.mapMode = tex.mapMode
        self.mipDetail = tex.mipDetail
        self.wrapModeS = str(tex.wrapModeS)
        self.wrapModeT = str(tex.wrapModeT)

        self.baseID = tex.baseID
        self.groupID = tex.groupID
        self.subGroupID = tex.subGroupID
        self.textureID = tex.textureID
        self.unk1 = tex.unk1
        self.LOD = tex.LOD


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


class XFBIN_MatShader_OT_Copy(bpy.types.Operator):
    bl_idname = 'xfbin_mat.shader_copy'
    bl_label = 'Copy Shader'

    def execute(self, context):
        obj = context.object
        mat: XfbinMaterialPropertyGroup = obj.active_material.xfbin_material_data
        clipboard: XfbinMatClipboardPropertyGroup = bpy.context.scene.xfbin_material_clipboard
        shader_index = mat.NUD_Shader_index

        if len(mat.NUD_Shaders) > 0:
            clipboard.shader_clipboard.init_copy(mat.NUD_Shaders[shader_index])

            self.report({'INFO'}, f'Shader ({mat.NUD_Shaders[shader_index].name}) from ({obj.active_material.name}) to clipboard')
        return {'FINISHED'}


class XFBIN_MatShader_OT_Paste(bpy.types.Operator):
    bl_idname = 'xfbin_mat.shader_paste'
    bl_label = 'Paste Shader'

    def execute(self, context):
        obj = context.object
        mat: XfbinMaterialPropertyGroup = obj.active_material.xfbin_material_data
        clipboard: XfbinMatClipboardPropertyGroup = bpy.context.scene.xfbin_material_clipboard

        if len(mat.NUD_Shaders) > 0:
            newShader: NUD_ShaderPropertyGroup = mat.NUD_Shaders.add()
            newShader.init_copy(clipboard.shader_clipboard)

            self.report({'INFO'}, f'Shader ({clipboard.shader_clipboard.name}) from clipboard to ({obj.active_material.name})')
        

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


class XFBIN_MatParam_OT_Copy(bpy.types.Operator):
    bl_idname = 'xfbin_mat.param_copy'
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
            clipboard: XfbinMatClipboardPropertyGroup = bpy.context.scene.xfbin_material_clipboard
            clipboard.shader_param_clipboard.init_copy(shader.shader_params[param_index])

            self.report({'INFO'}, f'Param ({shader.shader_params[param_index].name}) from ({obj.active_material.name}) to clipboard')
        return {'FINISHED'}


class XFBIN_MatParam_OT_Paste(bpy.types.Operator):
    bl_idname = 'xfbin_mat.param_paste'
    bl_label = 'Paste Param'

    def execute(self, context):
        obj = context.object
        mat: XfbinMaterialPropertyGroup = obj.active_material.xfbin_material_data
        shader_index = mat.NUD_Shader_index
        if shader_index < 0:
            return {'CANCELLED'}
        
        shader: NUD_ShaderPropertyGroup = mat.NUD_Shaders[shader_index]
        clipboard: XfbinMatClipboardPropertyGroup = bpy.context.scene.xfbin_material_clipboard

        if len(shader.shader_params) > 0:
            newParam: NUD_ShaderParamPropertyGroup = shader.shader_params.add()
            
            for k, v in clipboard.shader_param_clipboard.items():
                newParam[k] = v

            self.report({'INFO'}, f'Param ({clipboard.shader_param_clipboard.name}) from clipboard to ({obj.active_material.name})')
        
        #set index
        shader.NUD_ShaderParam_index = len(shader.shader_params) - 1

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
        self.values.clear()
        for i in range(param.count):
            v = self.values.add()
            v.value = param.values[i].value
        
        self.count = param.count
        


class NUD_ShaderTexPropertyGroup(PropertyGroup):
    name = StringProperty()
    magFilter: IntProperty()
    minFilter: IntProperty()
    mapMode: IntProperty()
    mipDetail: IntProperty()
    wrapModeS: IntProperty()
    wrapModeT: IntProperty()
    baseID: IntProperty()
    groupID: IntProperty()
    subGroupID: IntProperty()
    textureID: IntProperty()

    unk1: IntProperty()
    LOD: IntProperty()


    def init_data(self, tex):
        self.magFilter = tex.magFilter
        self.minFilter = tex.minFilter
        self.mapMode = tex.mapMode
        self.mipDetail = tex.mipDetail
        self.wrapModeS = tex.wrapModeS
        self.wrapModeT = tex.wrapModeT
        self.baseID = tex.baseID
        self.groupID = tex.groupID
        self.subGroupID = tex.subGroupID
        self.textureID = tex.textureID
        self.unk1 = tex.unk1
        self.LOD = tex.LOD


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

    is_initialized: BoolProperty(
        default = False
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
        
        self.is_initialized = True
    
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
        max=1,
        subtype = "FACTOR"
    )
    glare: FloatProperty(name='Glare', min=0, max=1, subtype= "FACTOR")

    UV0: BoolProperty(name='Use UV0', default=True)
    UV1: BoolProperty(name='Use UV1')
    UV2: BoolProperty(name='Use UV2')
    UV3: BoolProperty(name='Use UV3')
    Blend: BoolProperty(name='Use Blend Rate')
    useFallOff: BoolProperty(name='Use fallOff')
    useOutlineID: BoolProperty(name='Use outlineID')

    uvOffset0: FloatVectorProperty(name='uvOffset0', size=4, default=(0.0, 0.0, 1.0, 1.0))
    uvOffset1: FloatVectorProperty(name='uvOffset1', size=4, default=(0.0, 0.0, 1.0, 1.0))
    uvOffset2: FloatVectorProperty(name='uvOffset2', size=4, default=(0.0, 0.0, 1.0, 1.0))
    uvOffset3: FloatVectorProperty(name='uvOffset3', size=4, default=(0.0, 0.0, 1.0, 1.0))
    blendRate: FloatVectorProperty(name='', size=2, default=(0.0, 0.0))
    fallOff: FloatProperty(name='fallOff')
    outlineID: FloatProperty(name='outlineID', default=1)
    
    default_alpha: FloatProperty(name='Default Alpha', default=0)
    default_glare: FloatProperty(name='Default Glare', default=0)
    default_UV0: BoolProperty(name='Default UV0', default=True)
    default_UV1: BoolProperty(name='Default UV1')
    default_UV2: BoolProperty(name='Default UV2')
    default_UV3: BoolProperty(name='Default UV3')
    default_Blend: BoolProperty(name='Default Blend Rate')
    default_useFallOff: BoolProperty(name='Default fallOff')
    default_useOutlineID: BoolProperty(name='Default outlineID')
    
    default_uvOffset0: FloatVectorProperty(name='Default uvOffset0', size=4, default=(0.0, 0.0, 1.0, 1.0))
    default_uvOffset1: FloatVectorProperty(name='Default uvOffset1', size=4, default=(0.0, 0.0, 1.0, 1.0))
    default_uvOffset2: FloatVectorProperty(name='Default uvOffset2', size=4, default=(0.0, 0.0, 1.0, 1.0))
    default_uvOffset3: FloatVectorProperty(name='Default uvOffset3', size=4, default=(0.0, 0.0, 1.0, 1.0))
    default_blendRate: FloatVectorProperty(name='Default Blend Rate', size=2, default=(0.0, 0.0))
    default_fallOff: FloatProperty(name='Default fallOff')
    default_outlineID: FloatProperty(name='Default outlineID', default=1)
    

    texGroupsCount: IntProperty(name='Texture Groups Count', min=0, max=4, default=1)
    

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

    mainShader: PointerProperty(
        type= NUD_ShaderPropertyGroup,
        name = "Main Shader"
    )

    outlineShader: PointerProperty(
        type= NUD_ShaderPropertyGroup,
        name = "Outline Shader"
    )

    blurShader: PointerProperty(
        type= NUD_ShaderPropertyGroup,
        name = "Blur Shader"
    )

    shadowShader: PointerProperty(
        type= NUD_ShaderPropertyGroup,
        name = "Shadow Shader"
    )

    use_object_props: BoolProperty(default=True)

    NUD_Shader_index: IntProperty()

    def update_name(self):
        self.name = self.material_name
    
    def reset_to_default(self):
        self.alpha = self.default_alpha
        self.glare = self.default_glare
        
        self.UV0 = self.default_UV0
        self.uvOffset0 = self.default_uvOffset0
        self.UV1 = self.default_UV1
        self.uvOffset1 = self.default_uvOffset1
        self.UV2 = self.default_UV2
        self.uvOffset2 = self.default_uvOffset2
        self.UV3 = self.default_UV3
        self.uvOffset3 = self.default_uvOffset3
        self.Blend = self.default_Blend
        self.blendRate = self.default_blendRate
        self.useFallOff = self.default_useFallOff
        self.fallOff = self.default_fallOff
        self.useOutlineID = self.default_useOutlineID
        self.outlineID = self.default_outlineID

    
    def set_as_default(self):
        self.default_alpha = self.alpha
        self.default_glare = self.glare
        
        self.default_UV0 = self.UV0
        self.default_uvOffset0 = self.uvOffset0
        self.default_UV1 = self.UV1
        self.default_uvOffset1 = self.uvOffset1
        self.default_UV2 = self.UV2
        self.default_uvOffset2 = self.uvOffset2
        self.default_UV3 = self.UV3
        self.default_uvOffset3 = self.uvOffset3
        self.default_Blend = self.Blend
        self.default_blendRate = self.blendRate
        self.default_useFallOff = self.useFallOff
        self.default_fallOff = self.fallOff
        self.default_useOutlineID = self.useOutlineID
        self.default_outlineID = self.outlineID
        


    def init_data(self, material: NuccChunkMaterial, mesh, mesh_flags):
        self.material_name = material.name
        #print(f"material name: {material.name}")

        self.alpha = material.alpha / 255
        self.glare = material.glare

        self.flags = material.flags
        
        if material.flags & 0x01:
            self.UV0 = self.default_UV0 = True
            self.uvOffset0 = self.default_uvOffset0 = material.UV0
        if material.flags & 0x02:
            self.UV1 = self.default_UV1 = True
            self.uvOffset1 = self.default_uvOffset1 = material.UV1
        if material.flags & 0x04:
            self.UV2 = self.default_UV2 = True
            self.uvOffset2 = self.default_uvOffset2 = material.UV2
        if material.flags & 0x08:
            self.UV3 = self.default_UV3 = True
            self.uvOffset3 = self.default_uvOffset3 = material.UV3
        if material.flags & 0x10:
            self.Blend = self.default_Blend = True
            self.blendRate[0] = self.default_blendRate[0] = material.BlendRate
            self.blendRate[1] = self.default_blendRate[1] = material.BlendRate
        if material.flags & 0x20:
            self.useFallOff = self.default_useFallOff = True
            self.fallOff = self.default_fallOff = material.fallOff
        if material.flags & 0x40:
            self.useOutlineID = self.default_useOutlineID = True
            self.outlineID = self.default_outlineID = material.outlineID
        
        '''self.texture_groups.clear()
        for group in material.texture_groups:
            g = self.texture_groups.add()
            g.init_data(group)'''
        
        self.texGroupsCount = len(material.texture_groups)

        s_type_index = -1
        
        if mesh_flags[0] & 0x2 or mesh_flags[0] & 1 and not mesh_flags[1] == 16 or mesh_flags[0] & 0x100:
            s_type_index += 1
            main_shader = mesh.materials[s_type_index]

            if self.mainShader.is_initialized:
                self.mainShader.init_data(main_shader)
            else:
                self.mainShader.init_data(main_shader)
                s = self.NUD_Shaders.add()
                s.init_data(main_shader)

        if mesh_flags[0] & 0x4:
            try:
                s_type_index += 1
                outline_shader = mesh.materials[s_type_index]
            except:
                s_type_index -= 1
                outline_shader = mesh.materials[s_type_index]
            

            if self.outlineShader.is_initialized:
                self.outlineShader.init_data(outline_shader)
            else:
                self.outlineShader.init_data(outline_shader)
                s = self.NUD_Shaders.add()
                s.init_data(outline_shader)

        if mesh_flags[0] & 0x10:
            try:
                s_type_index += 1
                blur_shader = mesh.materials[s_type_index]
            except:
                s_type_index -= 1
                blur_shader = mesh.materials[s_type_index]

            if self.blurShader.is_initialized:
                self.blurShader.init_data(blur_shader)
            else:
                self.blurShader.init_data(blur_shader)
                s = self.NUD_Shaders.add()
                s.init_data(blur_shader)
        
        if mesh_flags[0] & 0x20:
            try:
                s_type_index += 1
                shadow_shader = mesh.materials[s_type_index]
            except:
                s_type_index -= 1
                shadow_shader = mesh.materials[s_type_index]

            if self.shadowShader.is_initialized:
                self.shadowShader.init_data(shadow_shader)
            else:
                self.shadowShader.init_data(shadow_shader)
                s = self.NUD_Shaders.add()
                s.init_data(shadow_shader)
        
        '''mesh_shaders = mesh.materials
        for shader in mesh_shaders:
            if str(hex(shader.flags)) in self.NUD_Shaders.keys():
                print('shader already exists')
                s = self.NUD_Shaders[str(hex(shader.flags))]
                s.init_data(shader)
            else:
                s = self.NUD_Shaders.add()
                s.init_data(shader)
            
            print(f"added shader {hex(shader.flags)}")'''
        
        #print(f"shader count {len(self.NUD_Shaders)}")
        self.NUTextures.clear()
        
        #for tg_index, tex_group in enumerate(material.texture_groups):
        if material.texture_groups:
            for tex_index, tex_chunk in enumerate(material.texture_groups[0].texture_chunks):
                if bpy.context.scene.xfbin_texture_chunks_data.texture_chunks.get(tex_chunk.name):
                    texture = bpy.context.scene.xfbin_texture_chunks_data.texture_chunks[tex_chunk.name]
                else:
                    #create a new texture chunk
                    texture = bpy.context.scene.xfbin_texture_chunks_data.texture_chunks.add()
                    texture.init_data(tex_chunk)
                
                nut = self.NUTextures.add()
                nut.init_data(texture)
                
                #get the texture props from the first nud shader
                nud_shader = self.NUD_Shaders[0]
                if len(nud_shader.shader_tex_props) > tex_index:
                    props = nud_shader.shader_tex_props[tex_index]
                    nut.init_tex_props(props)      
    

    def init_copy(self, matprop):
        self.alpha = matprop.alpha
        self.glare = matprop.glare
        
        self.UV0 = matprop.UV0
        self.uvOffset0 = matprop.uvOffset0
        self.UV1 = matprop.UV1
        self.uvOffset1 = matprop.uvOffset1
        self.UV2 = matprop.UV2
        self.uvOffset2 = matprop.uvOffset2
        self.UV3 = matprop.UV3
        self.uvOffset3 = matprop.uvOffset3
        self.Blend = matprop.Blend
        self.blendRate = matprop.blendRate
        self.useFallOff = matprop.useFallOff
        self.fallOff = matprop.fallOff
        self.useOutlineID = matprop.useOutlineID
        self.outlineID = matprop.outlineID

        '''self.texture_groups.clear()
        for group in matprop.texture_groups:
            g = self.texture_groups.add()
            g.init_data(group)'''
        
        self.texGroupsCount = matprop.texGroupsCount

        self.NUD_Shaders.clear()
        for shader in matprop.NUD_Shaders:
            s = self.NUD_Shaders.add()
            s.init_copy(shader)
        
        self.NUTextures.clear()
        for texture in matprop.NUTextures:
            t = self.NUTextures.add()
            t.init_data(texture)
            t.init_tex_props(texture)



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

        #copy paste ops
        row = layout.row()
        row.operator('xfbin_mat.copy', icon='COPYDOWN', text='Copy')
        row.operator('xfbin_mat.paste', icon='PASTEDOWN', text='Paste')
        
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
                        
            if material.useFallOff:
                row.prop(material, 'fallOff')
            
            row = box.row()
            row.prop(material, 'useOutlineID')
            row = box.row()
            if material.useOutlineID:
                
                row.prop(material, 'outlineID')

            row.prop(material, 'texGroupsCount')
            
            row = box.row()

            row.operator('xfbin_mat.reset_to_default', icon='FILE_REFRESH')
            row.operator('xfbin_mat.set_as_default', icon='FILE_TICK')
            

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
        row.prop(mat, "use_object_props", text="Per Object Shader Properties (Main Shader Only)")

        row = col.row()

        #draw_xfbin_list(row, 0, mat, f'{mat}', 'NUD_Shaders', 'NUD_Shader_index', enable_text=False)

        row.template_list(
            "XFBIN_UL_MatShaders", "", mat, "NUD_Shaders", mat, "NUD_Shader_index",
            rows=4, maxrows=10, type='DEFAULT'
        )

        col = row.column(align=True)
        col.operator("xfbin_mat.shader_add", icon='ADD', text="")
        col.operator("xfbin_mat.shader_remove", icon='REMOVE', text="")
        col.operator("xfbin_mat.shader_copy", icon='COPYDOWN', text="")
        col.operator("xfbin_mat.shader_paste", icon='PASTEDOWN', text="")
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
            col = row.column(align=True)
            col.operator("xfbin_mat.param_add", icon='ADD', text="")
            col.operator("xfbin_mat.param_remove", icon='REMOVE', text="")
            col.operator("xfbin_mat.param_copy", icon='COPYDOWN', text="")
            col.operator("xfbin_mat.param_paste", icon='PASTEDOWN', text="")
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

            '''row = layout.row()
            col1 = row.column(align=True)
            col1.prop(mat.mainShader, 'name', text='Main')
            col1row = col1.row()
            col1row.template_list(
                "XFBIN_UL_MatParams", "", mat.mainShader, "shader_params", mat.mainShader, "NUD_ShaderParam_index",
            )
            col1col = col1.column(align=True)


            col2 = row.column(align=True)
            col2.prop(mat.outlineShader, 'name', text='Outline')
            col2row = col2.row()
            col2row.template_list(
                "XFBIN_UL_MatParams", "", mat.outlineShader, "shader_params", mat.outlineShader, "NUD_ShaderParam_index",
            )

            col3 = row.column(align=True)
            col3.prop(mat.blurShader, 'name', text='Blur')
            col3row = col3.row()
            col3row.template_list(
                "XFBIN_UL_MatParams", "", mat.blurShader, "shader_params", mat.blurShader, "NUD_ShaderParam_index",
            )

            col4 = row.column(align=True)
            col4.prop(mat.shadowShader, 'name', text='Shadow')
            col4row = col4.row()
            col4row.template_list(
                "XFBIN_UL_MatParams", "", mat.shadowShader, "shader_params", mat.shadowShader, "NUD_ShaderParam_index",
            )'''

            box = layout.box()
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
            texture_n: XfbinMaterialTexturesPropertyGroup = mat.NUTextures[texture_index]
            texture = bpy.context.scene.xfbin_texture_chunks_data.texture_chunks.get(texture_n.name)
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
            row.prop(texture_n, 'baseID')
            row.prop(texture_n, 'groupID')
            row.prop(texture_n, 'subGroupID')
            row.prop(texture_n, 'textureID')
            row.prop(texture_n, 'unk1')
            row.prop(texture_n, 'LOD')


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
        mat_texture: XfbinMaterialTexturesPropertyGroup = mat_textures[mat_texture_index]
        nut_texture = bpy.context.scene.xfbin_texture_chunks_data.texture_chunks.get(mat_texture.name)
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
        image.source = 'FILE'
        #add custom properties to the image
        image['nut_pixel_format'] = str(texdata.header.pixel_format)
        image['nut_mipmaps_count'] = str(texdata.header.mipMapCount)

        texture.image = image
        texture.name = image.name
        texture.width = str(texdata.header.width)
        texture.height = str(texdata.header.height)

        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)

        return {'RUNNING_MODAL'}


class XFBIN_Material_OT_Copy(bpy.types.Operator):
    bl_idname = 'xfbin_mat.copy'
    bl_label = 'Copy Material'

    def execute(self, context):
        obj = context.object
        mat: XfbinMaterialPropertyGroup = obj.active_material.xfbin_material_data
        clipboard = bpy.context.scene.xfbin_material_clipboard
        
        clipboard.init_copy_material(mat)

        self.report({'INFO'}, f"XFBIN Material ({obj.active_material.name}) copied to clipboard")

        return {'FINISHED'}
        



class XFBIN_Material_OT_Paste(bpy.types.Operator):
    bl_idname = 'xfbin_mat.paste'
    bl_label = 'Paste Material'

    def execute(self, context):
        obj = context.object
        mat: XfbinMaterialPropertyGroup = obj.active_material.xfbin_material_data
        clipboard = bpy.context.scene.xfbin_material_clipboard
        mat.init_copy(clipboard.material_clipboard)

        self.report({'INFO'}, f"XFBIN Material ({obj.active_material.name}) pasted from clipboard")

        return {'FINISHED'}


class XfbinMatClipboardPropertyGroup(PropertyGroup):
    
    material_clipboard: PointerProperty(
        type=XfbinMaterialPropertyGroup,
        name='Material Clipboard'
    )

    shader_clipboard: PointerProperty(
        type=NUD_ShaderPropertyGroup,
        name='Shader Clipboard'
    )

    shader_param_clipboard: PointerProperty(
        type=NUD_ShaderParamPropertyGroup,
        name='Shader Param Clipboard'
    )

    texture_clipboard: PointerProperty(
        type=XfbinMaterialTexturesPropertyGroup,
        name='Texture Clipboard'
    )

    def init_copy_material(self, matprop):
        self.material_clipboard.init_copy(matprop)
    
    def init_copy_shader(self, shader):
        self.shader_clipboard.init_copy(shader)
    
    def init_copy_shader_param(self, param):
        self.shader_param_clipboard.init_copy(param)
    
    def init_copy_texture(self, texture):
        self.texture_clipboard.init_copy(texture)


class XfbinSceneManagerPropertyGroup(PropertyGroup):
    
    def update_light_properties(self, context):
        light = self.lightdir_object
        if light and light.type == 'LIGHT':
            self.lightdir_vec = light.location
            self.lightdir_color = light.data.color
            self.lightdir_intensity = light.data.energy

    lightdir_intensity: FloatProperty(
        name='Light Intensity',
        default=1.0,
        subtype='NONE',
        min=0.0
    )
    
    lightdir_object: PointerProperty(
        type=bpy.types.Object,
        name='Light Object'
    )
    
    lightdir_color: FloatVectorProperty(
        name='Light Color',
        default=(1.0, 1.0, 1.0),
        min=0.0,
        max=1.0,
        subtype='COLOR',
        size=3
    )

    lightpoint_object0: PointerProperty(
        type=bpy.types.Object,
        name='Light Object 0'
    )
    
    lightpoint_color0: FloatVectorProperty(
        name='Light Color 0',
        default=(1.0, 1.0, 1.0),
        min=0.0,
        max=1.0,
        subtype='COLOR',
        size=3
    )
    
    lightpoint_intensity0: FloatProperty(
        name='Light Intensity 0',
        default=0.0,
        subtype='NONE',
    )
    
    lightpoint_range0: FloatProperty(
        name='Light Range 0',
        default=0.0,
        subtype='NONE',
    )
    
    lightpoint_attenuation0: FloatProperty(
        name='Light Attenuation 0',
        default=0.0,
        subtype='NONE',
    )

    lightpoint_object1: PointerProperty(
        type=bpy.types.Object,
        name='Light Object 1'
    )
    
    lightpoint_color1: FloatVectorProperty(
        name='Light Color 1',
        default=(1.0, 1.0, 1.0),
        min=0.0,
        max=1.0,
        subtype='COLOR',
        size=3
    )
    
    lightpoint_intensity1: FloatProperty(
        name='Light Intensity 1',
        default=0.0,
        subtype='NONE',
    )
    
    lightpoint_range1: FloatProperty(
        name='Light Range 1',
        default=0.0,
        subtype='NONE',
    )
    
    lightpoint_attenuation1: FloatProperty(
        name='Light Attenuation 1',
        default=0.0,
        subtype='NONE',
    )
    
    lightpoint_object2: PointerProperty(
        type=bpy.types.Object,
        name='Light Object 2'
    )
    
    lightpoint_color2: FloatVectorProperty(
        name='Light Color 2',
        default=(1.0, 1.0, 1.0),
        min=0.0,
        max=1.0,
        subtype='COLOR',
        size=3
    )
    
    lightpoint_intensity2: FloatProperty(
        name='Light Intensity 2',
        default=0.0,
        subtype='NONE',
    )
    
    lightpoint_range2: FloatProperty(
        name='Light Range 2',
        default=0.0,
        subtype='NONE',
    )
    
    lightpoint_attenuation2: FloatProperty(
        name='Light Attenuation 2',
        default=0.0,
        subtype='NONE',
    )
    
    lightpoint_object3: PointerProperty(
        type=bpy.types.Object,
        name='Light Object 3'
    )
    
    lightpoint_color3: FloatVectorProperty(
        name='Light Color 3',
        default=(1.0, 1.0, 1.0),
        min=0.0,
        max=1.0,
        subtype='COLOR',
        size=3
    )
    
    lightpoint_intensity3: FloatProperty(
        name='Light Intensity 3',
        default=0.0,
        subtype='NONE',
    )
    
    lightpoint_range3: FloatProperty(
        name='Light Range 3',
        default=0.0,
        subtype='NONE',
    )
    
    lightpoint_attenuation3: FloatProperty(
        name='Light Attenuation 3',
        default=0.0,
        subtype='NONE',
    )
    
    ambient_color: FloatVectorProperty(
        name='Ambient Color',
        default=(0.5, 0.5, 0.5),
        min=0.0,
        max=1.0,
        subtype='COLOR',
        size=3
    )
    
    shade_color: FloatVectorProperty(
        name='Shade Color',
        default=(0.5, 0.5, 0.5, 0.0),
        min=0.0,
        max=1.0,
        subtype='COLOR',
        size=4
    )
    
    stage_color: FloatVectorProperty(
        name='Stage Color',
        default=(1.0, 1.0, 1.0),
        min=0.0,
        max=1.0,
        subtype='COLOR',
        size=3
    )
    
    use_stage_color: BoolProperty(
        name='Use Stage Color',
        default=False
    )
    
    fog_color: FloatVectorProperty(
        name='Fog Color',
        default=(0.0, 0.0, 0.0),
        min=0.0,
        max=1.0,
        subtype='COLOR',
        size=3
    )
    
    fog_start: FloatProperty(
        name='Fog Start',
        default=10.0,
        subtype='NONE',
    )
    
    fog_end: FloatProperty(
        name='Fog End',
        default=10000.0,
        subtype='NONE',
    )
    
    fog_density: FloatProperty(
        name='Fog Density',
        default=0.0,
        min=0.0,
        max=100.0,
        subtype='PERCENTAGE'
    )
    
    cpara_x_pos: FloatProperty(
        name='Color Paraffin X Coordinate',
        default=50.0,
        min=0.0,
        max=100.0,
        subtype='PERCENTAGE'
    )
    cpara_y_pos: FloatProperty(
        name='Color Paraffin Y Coordinate',
        default=50.0,
        min=0.0,
        max=100.0,
        subtype='PERCENTAGE'
    )
    cpara_attenuation_start: FloatProperty(
        name='Color Paraffin Attenuation Start',
        default=10.0,
        min=0.0
        
    )
    
    cpara_attenuation_end: FloatProperty(
        name='Color Paraffin Attenuation End',
        default=25.0,
        min=0.0
    )
    
    cpara_color1: FloatVectorProperty(
        name='Color Paraffin Color 1',
        default=(1.0, 1.0, 1.0),
        min=0.0,
        max=1.0,
        subtype='COLOR',
        size=3
    )
    cpara_color2: FloatVectorProperty(
        name='Color Paraffin Color 2',
        default=(1.0, 1.0, 1.0),
        min=0.0,
        max=1.0,
        subtype='COLOR',
        size=3
    )
    

class XfbinSceneManagerPanel(Panel):
    bl_idname = 'SCENE_PT_XFBIN_scene_manager'
    bl_label = 'XFBIN Scene Manager'
    bl_space_type = 'PROPERTIES'
    bl_context = 'object'
    bl_region_type = 'WINDOW'

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type == 'EMPTY' and obj.name == 'XFBIN Scene Manager'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        xfbin_scene_manager: XfbinSceneManagerPropertyGroup = scene.xfbin_scene

        box = layout
        row = box.row()
        
        lightdir_box = box.box()
        row = lightdir_box.row()
        row.label(text='Light Direction:')
        row = lightdir_box.row()
        row.prop_search(xfbin_scene_manager, 'lightdir_object', bpy.data, 'objects', text='')
        row.prop(xfbin_scene_manager, 'lightdir_color', text='')
        row = lightdir_box.row()
        row.prop(xfbin_scene_manager, 'lightdir_intensity')
        row = lightdir_box.row()
        row.operator('xfbin_scene.create_light', text='Create Light', icon='LIGHT_SUN')
        
        ambinet_box = box.box() 
        row = ambinet_box.row()
        row.label(text='Ambient Light:')
        row = ambinet_box.row()
        row.prop(xfbin_scene_manager, 'ambient_color', text='')
        row = box.row()
        
        fog_box = box.box()
        row = fog_box.row()
        row.label(text='Fog:')
        row = fog_box.row()
        row.prop(xfbin_scene_manager, 'fog_color', text='')
        row = fog_box.row()
        row.prop(xfbin_scene_manager, 'fog_start')
        row.prop(xfbin_scene_manager, 'fog_end')
        row = fog_box.row()
        row.prop(xfbin_scene_manager, 'fog_density')
        row = box.row()
        
        shade_box = box.box()
        row = shade_box.row()
        row.label(text='Shade:')
        row = shade_box.row()
        row.prop(xfbin_scene_manager, 'shade_color', text='Shade Color')
        row = shade_box.row()
        row.prop(xfbin_scene_manager, 'use_stage_color', text='Use Stage Color')
        row.prop(xfbin_scene_manager, 'stage_color', text='Stage Color')
        
        cpara_box = box.box()
        row = cpara_box.row()
        row.label(text='Color Paraffin:')
        row = cpara_box.row()
        row.prop(xfbin_scene_manager, 'cpara_x_pos', text='X Position')
        row.prop(xfbin_scene_manager, 'cpara_y_pos', text='Y Position')
        row = cpara_box.row()
        row.prop(xfbin_scene_manager, 'cpara_attenuation_start', text='Attenuation Start')
        row.prop(xfbin_scene_manager, 'cpara_attenuation_end', text='Attenuation End')
        row = cpara_box.row()
        row.prop(xfbin_scene_manager, 'cpara_color1', text='Start Color')
        row.prop(xfbin_scene_manager, 'cpara_color2', text='End Color')
        
        lightpoints_box = box.box()
        lightpoints_box.label(text='Light Points:')
        row = lightpoints_box.row()
        row.label(text='Light Point 0')
        row = lightpoints_box.row()
        row.prop_search(xfbin_scene_manager, 'lightpoint_object0', bpy.data, 'objects', text='')
        row.prop(xfbin_scene_manager, 'lightpoint_color0', text='')
        row = lightpoints_box.row()
        row.prop(xfbin_scene_manager, 'lightpoint_intensity0', text='Intensity')
        row.prop(xfbin_scene_manager, 'lightpoint_range0', text='Range')
        row.prop(xfbin_scene_manager, 'lightpoint_attenuation0', text='Attenuation')
        row = lightpoints_box.row()
        row.operator('xfbin_scene.create_point_light', text='Create Light', icon='LIGHT_POINT').light_number = 0
        
        row = lightpoints_box.row()
        row.label(text='Light Point 1')
        row = lightpoints_box.row()
        row.prop_search(xfbin_scene_manager, 'lightpoint_object1', bpy.data, 'objects', text='')
        row.prop(xfbin_scene_manager, 'lightpoint_color1', text='')
        row = lightpoints_box.row()
        row.prop(xfbin_scene_manager, 'lightpoint_intensity1', text='Intensity')
        row.prop(xfbin_scene_manager, 'lightpoint_range1', text='Range')
        row.prop(xfbin_scene_manager, 'lightpoint_attenuation1', text='Attenuation')
        row = lightpoints_box.row()
        row.operator('xfbin_scene.create_point_light', text='Create Light', icon='LIGHT_POINT').light_number = 1
        
        
        row = lightpoints_box.row()
        row.label(text='Light Point 2')
        row = lightpoints_box.row()
        row.prop_search(xfbin_scene_manager, 'lightpoint_object2', bpy.data, 'objects', text='')
        row.prop(xfbin_scene_manager, 'lightpoint_color2', text='')
        row = lightpoints_box.row()
        row.prop(xfbin_scene_manager, 'lightpoint_intensity2', text='Intensity')
        row.prop(xfbin_scene_manager, 'lightpoint_range2', text='Range')
        row.prop(xfbin_scene_manager, 'lightpoint_attenuation2', text='Attenuation')
        row = lightpoints_box.row()
        row.operator('xfbin_scene.create_point_light', text='Create Light', icon='LIGHT_POINT').light_number = 2
        
        row = lightpoints_box.row()
        row.label(text='Light Point 3')
        row = lightpoints_box.row()
        row.prop_search(xfbin_scene_manager, 'lightpoint_object3', bpy.data, 'objects', text='')
        row.prop(xfbin_scene_manager, 'lightpoint_color3', text='')
        row = lightpoints_box.row()
        row.prop(xfbin_scene_manager, 'lightpoint_intensity3', text='Intensity')
        row.prop(xfbin_scene_manager, 'lightpoint_range3', text='Range')
        row.prop(xfbin_scene_manager, 'lightpoint_attenuation3', text='Attenuation')
        row = lightpoints_box.row()
        row.operator('xfbin_scene.create_point_light', text='Create Light', icon='LIGHT_POINT').light_number = 3


class XFBIN_Scene_OT_CreateLight(bpy.types.Operator):
    bl_idname = 'xfbin_scene.create_light'
    bl_label = 'Create Light'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        xfbin_scene_manager: XfbinSceneManagerPropertyGroup = scene.xfbin_scene

        #create Arrow Empty
        light_object = bpy.data.objects.new(name='Light Direction', object_data=None)
        light_object.empty_display_type = 'SINGLE_ARROW'
        light_object.empty_display_size = 2
        scene.collection.objects.link(light_object)
        xfbin_scene_manager.lightdir_object = light_object

        return {'FINISHED'}
    

class XFBIN_Scene_OT_CreatePointLight(bpy.types.Operator):
    bl_idname = 'xfbin_scene.create_point_light'
    bl_label = 'Create Light'
    bl_options = {'REGISTER', 'UNDO'}

    light_number: IntProperty(
        name='Light Number',
        description='Light Number',
        default=0,
        min=0,
        max=3
    )

    def execute(self, context):
        scene = context.scene
        xfbin_scene_manager: XfbinSceneManagerPropertyGroup = scene.xfbin_scene

        light_object = bpy.data.objects.new(name=f'Light Point {self.light_number}', object_data=None)
        light_object.empty_display_type = 'SPHERE'
        light_object.empty_display_size = 1
        scene.collection.objects.link(light_object)
        setattr(xfbin_scene_manager, f'lightpoint_object{self.light_number}', light_object)

        return {'FINISHED'}


class XFBIN_Mat_OT_ResetToDefault(bpy.types.Operator):
    bl_idname = 'xfbin_mat.reset_to_default'
    bl_label = 'Reset to Default Values'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.object
        mat: XfbinMaterialPropertyGroup = obj.active_material.xfbin_material_data
        mat.reset_to_default()

        return {'FINISHED'}
    
    
class XFBIN_Mat_OT_SetAsDefault(bpy.types.Operator):
    bl_idname = 'xfbin_mat.set_as_default'
    bl_label = 'Set Current Values as Default'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.object
        mat: XfbinMaterialPropertyGroup = obj.active_material.xfbin_material_data
        mat.set_as_default()

        return {'FINISHED'}

material_property_groups = (
    #NutSubTexturePropertyGroup,
    #MaterialNutTexturePropertyGroup,
    XfbinMaterialTexturesPropertyGroup,
    NUD_ShaderParamPropertyGroup,
    NUD_ShaderTexPropertyGroup,
    NUD_ShaderPropertyGroup,
    #TextureGroupPropertyGroup,
    XfbinMaterialPropertyGroup,
    XfbinMatClipboardPropertyGroup,
    XfbinSceneManagerPropertyGroup
)

material_classes = (
    *material_property_groups,
    XFBIN_UL_MatTextures,
    XFBIN_UL_MatShaders,
    XFBIN_UL_MatParams,
    XFBIN_Mat_OT_ResetToDefault,
    XFBIN_Mat_OT_SetAsDefault,
    XFBIN_Material_OT_Copy,
    XFBIN_Material_OT_Paste,
    XFBIN_MatTexture_OT_Add,
    XFBIN_MatTexture_OT_Remove,
    XFBIN_MatTexture_OT_Move,
    XFBIN_MatTexture_Open,
    XFBIN_MatTexture_OT_Duplicate,
    XFBIN_MatShader_OT_Add,
    XFBIN_MatShader_OT_Remove,
    XFBIN_MatShader_OT_Move,
    XFBIN_MatShader_OT_Duplicate,
    XFBIN_MatShader_OT_Copy,
    XFBIN_MatShader_OT_Paste,
    XFBIN_MatParam_OT_Add,
    XFBIN_MatParam_OT_Remove,
    XFBIN_MatParam_OT_Move,
    XFBIN_MatParam_OT_Duplicate,
    XFBIN_MatParam_OT_Copy,
    XFBIN_MatParam_OT_Paste,
    XFBIN_Scene_OT_CreateLight,
    XFBIN_Scene_OT_CreatePointLight,
    XfbinMaterialPropertyPanel,
    #TextureGroupPropertyPanel,
    NutTexturePropertyPanel,
    NUD_ShaderPropertyPanel,
    XfbinSceneManagerPanel,
    
)
