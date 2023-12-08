import bpy
from bpy.props import (CollectionProperty, EnumProperty, FloatProperty,
                       IntProperty, StringProperty)
from bpy.types import Panel, PropertyGroup

from ...xfbin_lib.xfbin.structure.nud import (NudMaterial, NudMaterialProperty,
                                              NudMaterialTexture, NudMesh)
from ..common.helpers import format_hex_str, int_to_hex_str
from .clump_panel import ClumpPropertyGroup
from .common import FloatPropertyGroup, draw_copy_paste_ops, draw_xfbin_list, matrix_prop_group


class NudMaterialPropPropertyGroup(PropertyGroup):
    def update_prop_name(self, context):
        self.update_name()

    def update_count(self, context):
        extra = self.count - len(self.values)
        if extra > 0:
            for _ in range(extra):
                self.values.add()

    prop_name: StringProperty(
        name='Name',
        default='NU_useStColor',  # This usually has no values, so it's safe to have it as the default name
        update=update_prop_name,
    )

    count: IntProperty(
        name='Value count',
        min=0,
        max=0xFF,
        update=update_count,
    )

    values: CollectionProperty(
        type=FloatPropertyGroup,
        name='Values',
    )

    def update_name(self):
        self.name = self.prop_name

    def init_data(self, material_prop: NudMaterialProperty):
        self.prop_name = material_prop.name
        self.count = len(material_prop.values)

        self.values.clear()
        for val in material_prop.values:
            f = self.values.add()
            f.value = val


class NudMaterialTexturePropertyGroup(PropertyGroup):
    unk0: IntProperty(
        name='Unk 0',
        min=-0x80_00_00_00,
        max=0x7F_FF_FF_FF,
    )

    map_mode: IntProperty(
        name='Map mode',
        min=0,
        max=0xFF_FF,
    )

    wrap_mode_s: IntProperty(
        name='Wrap mode S',
        min=0,
        max=0xFF,
    )

    wrap_mode_t: IntProperty(
        name='Wrap mode T',
        min=0,
        max=0xFF,
    )

    min_filter: IntProperty(
        name='Min filter',
        min=0,
        max=0xFF,
    )

    mag_filter: IntProperty(
        name='Mag filter',
        min=0,
        max=0xFF
    )

    mip_detail: IntProperty(
        name='Mip detail',
        min=0,
        max=0xFF,
    )

    unk1: IntProperty(
        name='Unk 1',
        min=0,
        max=0xFF,
    )

    unk2: IntProperty(
        name='Unk 2',
        min=-0x80_00,
        max=0x7F_FF,
    )

    def update_name(self):
        if not self.name:
            self.name = 'Texture'

    def init_data(self, texture: NudMaterialTexture):
        self.unk0 = texture.unk0
        self.map_mode = texture.mapMode
        self.wrap_mode_s = texture.wrapModeS
        self.wrap_mode_t = texture.wrapModeT
        self.min_filter = texture.minFilter
        self.mag_filter = texture.magFilter
        self.mip_detail = texture.mipDetail
        self.unk1 = texture.unk1
        self.unk2 = texture.unk2


class NudMaterialPropertyGroup(PropertyGroup):
    def update_material_id(self, context):
        old_val = self.material_id
        new_val = format_hex_str(self.material_id, 4)

        if new_val and len(new_val) < 12:
            if old_val != new_val:
                self.material_id = new_val
        else:
            self.material_id = '00 00 00 00'

        self.update_name()

    material_id: StringProperty(
        name='Material ID (Hex)',
        default='00 00 F0 0A',  # Just a generic material ID from Storm 4
        update=update_material_id,
    )

    source_factor: IntProperty(
        name='Source Factor',
        min=0,
        max=0xFF_FF,
    )

    dest_factor: IntProperty(
        name='Destination Factor',
        min=0,
        max=0xFF_FF,
    )

    alpha_test: IntProperty(
        name='Alpha Test',
        min=0,
        max=0xFF,
    )

    alpha_function: IntProperty(
        name='Alpha Function',
        min=0,
        max=0xFF,
    )

    ref_alpha: IntProperty(
        name='Reference Alpha',
        min=0,
        max=0xFF_FF,
    )

    cull_mode: IntProperty(
        name='Cull Mode',
        min=0,
        max=0xFF_FF,
        default=0x405,
    )

    unk1: FloatProperty(
        name='Unk 1',
    )

    unk2: FloatProperty(
        name='Unk 2',
    )

    zbuffer_offset: IntProperty(
        name='ZBuffer Offset',
        min=-0x80_00_00_00,
        max=0x7F_FF_FF_FF,
    )

    textures: CollectionProperty(
        type=NudMaterialTexturePropertyGroup
    )

    texture_index: IntProperty()

    material_props: CollectionProperty(
        type=NudMaterialPropPropertyGroup
    )

    material_prop_index: IntProperty()

    def update_name(self):
        self.name = self.material_id

    def init_data(self, material: NudMaterial):
        self.material_id = int_to_hex_str(material.flags, 4)

        self.source_factor = material.sourceFactor
        self.dest_factor = material.destFactor
        self.alpha_test = material.alphaTest
        self.alpha_function = material.alphaFunction
        self.ref_alpha = material.refAlpha
        self.cull_mode = material.cullMode
        self.unk1 = material.unk1
        self.unk2 = material.unk2
        self.zbuffer_offset = material.zBufferOffset

        # Add textures
        self.textures.clear()
        for texture in material.textures:
            t = self.textures.add()
            t.init_data(texture)

        # Add material props
        self.material_props.clear()
        for property in material.properties:
            p = self.material_props.add()
            p.init_data(property)


class NudMeshPropertyGroup(PropertyGroup):
    """Property group that contains attributes of a nuccChunkModel."""

    def update_xfbin_material(self, context):
        xfbin_mat = bpy.data.materials.get(self.xfbin_material)
        xfbin_mat: NudMaterialPropertyGroup = xfbin_mat.xfbin_material_data

        if not (xfbin_mat and xfbin_mat.NUTextures):
            return

        # TODO: Check if we should access other groups as well

        for mat in self.materials:
            for xt, mt in zip(xfbin_mat.NUTextures, mat.textures):
                mt.name = xt.texture_name

    vertex_type: EnumProperty(
        name='Vertex Format',
        items=[
            ('0', 'No normals', ''),
            ('1', 'Normals (Float)', ''),
            ('2', 'Unknown', ''),
            ('3', 'Normals/Tan/Bitan (Float)', ''),
            ('6', 'Normals (Half float)', ''),
            ('7', 'Normals/Tan/Bitan (Half float)', ''),
        ],
        default='3',
        description='Format to save the vertices in when writing.\n'
        'Note: Do NOT change this unless you know what you are doing',
    )

    bone_type: EnumProperty(
        name='Bone Format',
        items=[
            ('0', 'No bones', ''),
            ('16', 'Bones (Float)', ''),
            ('32', 'Bones (Half float)', ''),
            ('64', 'Bones (Byte)', ''),
        ],
        default='16',
        description='Format to save the bones in when writing.\n'
        'Note: Do NOT change this unless you know what you are doing',
    )

    uv_type: EnumProperty(
        name='Vertex Color Format',
        items=[
            ('0', 'No color', ''),
            ('2', 'Color (Byte)', ''),
            ('4', 'Color (Half float)', ''),
        ],
        default='2',
        description='Format to save the vertex color in when writing.\n'
        'Note: Do NOT change this unless you know what you are doing',
    )

    face_flag: IntProperty(
        name='Face Flag',
        min=0,
        max=255,
        default=0x04,
    )

    xfbin_material: StringProperty(
        name='XFBIN Material',
        description='The XFBIN material that this mesh uses',
        update=update_xfbin_material,
    )

    materials: CollectionProperty(
        type=NudMaterialPropertyGroup,
        name='Materials',
        description='Materials used by this NUD mesh',
    )

    material_index: IntProperty()

    def init_data(self, mesh: NudMesh, xfbin_mat_name: str):
        self.vertex_type = str(int(mesh.vertex_type))
        self.bone_type = str(int(mesh.bone_type))
        self.uv_type = str(int(mesh.uv_type))
        self.face_flag = mesh.face_flag

        self.materials.clear()
        for material in mesh.materials:
            m = self.materials.add()
            m.init_data(material)

        # Set the material name after all nud materials have been added to properly update the texture names
        self.xfbin_material = xfbin_mat_name


class NudMaterialPropPropertyPanel(Panel):
    bl_idname = 'OBJECT_PT_nud_material_props'
    bl_label = 'Material Properties'
    bl_parent_id = 'OBJECT_PT_nud_material'

    bl_space_type = 'PROPERTIES'
    bl_context = 'object'
    bl_region_type = 'WINDOW'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        data: NudMeshPropertyGroup = context.object.xfbin_mesh_data
        return data.materials and data.material_index >= 0

    def draw(self, context):
        layout = self.layout
        obj = context.object
        data: NudMeshPropertyGroup = obj.xfbin_mesh_data
        mat: NudMaterialPropertyGroup = data.materials[data.material_index]

        draw_xfbin_list(
            layout, 2, mat, f'xfbin_mesh_data.materials[{data.material_index}]', 'material_props', 'material_prop_index')
        prop_index = mat.material_prop_index

        if mat.material_props and prop_index >= 0:
            material_prop: NudMaterialPropPropertyGroup = mat.material_props[prop_index]
            box = layout.box()

            row = box.row()
            row.prop(material_prop, 'prop_name')
            row.prop(material_prop, 'count')

            matrix_prop_group(box, material_prop, 'values', material_prop.count, 'Values')


class NudMaterialTexturePropertyPanel(Panel):
    bl_idname = 'OBJECT_PT_nud_material_texture'
    bl_label = 'Textures'
    bl_parent_id = 'OBJECT_PT_nud_material'

    bl_space_type = 'PROPERTIES'
    bl_context = 'object'
    bl_region_type = 'WINDOW'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        data: NudMeshPropertyGroup = context.object.xfbin_mesh_data
        return data.materials and data.material_index >= 0

    def draw(self, context):
        layout = self.layout
        obj = context.object
        data: NudMeshPropertyGroup = obj.xfbin_mesh_data
        mat: NudMaterialPropertyGroup = data.materials[data.material_index]

        draw_xfbin_list(
            layout, 1, mat, f'xfbin_mesh_data.materials[{data.material_index}]', 'textures', 'texture_index')
        texture_index = mat.texture_index

        if mat.textures and texture_index >= 0:
            texture: NudMaterialTexturePropertyGroup = mat.textures[texture_index]
            box = layout.box()

            box.prop(texture, 'unk0')
            box.prop(texture, 'map_mode')

            row = box.row()
            row.prop(texture, 'wrap_mode_s')
            row.prop(texture, 'wrap_mode_t')

            row = box.row()
            row.prop(texture, 'min_filter')
            row.prop(texture, 'mag_filter')

            row = box.row()
            row.prop(texture, 'mip_detail')
            row.prop(texture, 'unk1')

            box.prop(texture, 'unk2')


class NudMaterialPropertyPanel(Panel):
    bl_idname = 'OBJECT_PT_nud_material'
    bl_label = 'NUD Materials'
    bl_parent_id = 'OBJECT_PT_nud_mesh'

    bl_space_type = 'PROPERTIES'
    bl_context = 'object'
    bl_region_type = 'WINDOW'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        obj = context.object
        data: NudMeshPropertyGroup = obj.xfbin_mesh_data

        draw_xfbin_list(layout, 0, data, 'xfbin_mesh_data', 'materials', 'material_index')
        mat_index = data.material_index

        if data.materials and mat_index >= 0:
            mat: NudMaterialPropertyGroup = data.materials[mat_index]
            box = layout.box()

            box.prop(mat, 'material_id')

            row = box.row()
            row.prop(mat, 'source_factor')
            row.prop(mat, 'dest_factor')

            row = box.row()
            row.prop(mat, 'alpha_test')
            row.prop(mat, 'alpha_function')

            box.prop(mat, 'ref_alpha')
            box.prop(mat, 'cull_mode')

            row = box.row()
            row.prop(mat, 'unk1')
            row.prop(mat, 'unk2')

            box.prop(mat, 'zbuffer_offset')


class NudMeshPropertyPanel(Panel):
    """Panel that displays the NudMeshPropertyGroup attached to the selected mesh object."""

    bl_idname = 'OBJECT_PT_nud_mesh'
    bl_label = '[XFBIN] Mesh Properties'

    bl_space_type = 'PROPERTIES'
    bl_context = 'object'
    bl_region_type = 'WINDOW'

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type == 'MESH' \
            and obj.parent and obj.parent.type == 'EMPTY' \
            and obj.parent.parent and obj.parent.parent.type == 'ARMATURE'

    def draw(self, context):
        layout = self.layout
        obj = context.object
        data: NudMeshPropertyGroup = obj.xfbin_mesh_data
        clump_data: ClumpPropertyGroup = obj.parent.parent.xfbin_clump_data

        draw_copy_paste_ops(layout, 'xfbin_mesh_data', 'Mesh Properties')

        layout.prop(data, 'vertex_type')
        layout.prop(data, 'bone_type')
        layout.prop(data, 'uv_type')
        layout.prop(data, 'face_flag')

        layout.prop_search(data, 'xfbin_material', obj.data, 'materials')



nud_mesh_property_groups = (
    NudMaterialPropPropertyGroup,
    NudMaterialTexturePropertyGroup,
    NudMaterialPropertyGroup,
    NudMeshPropertyGroup,
)

nud_mesh_classes = (
    *nud_mesh_property_groups,
    NudMeshPropertyPanel,
    NudMaterialPropertyPanel,
    NudMaterialTexturePropertyPanel,
    NudMaterialPropPropertyPanel,
)
