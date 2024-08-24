import bpy, mathutils
from bpy.props import (EnumProperty, FloatVectorProperty, IntProperty,
                       IntVectorProperty, StringProperty)
from bpy.types import Panel, PropertyGroup

from ...xfbin_lib.xfbin.structure.nucc import NuccChunkModel, RiggingFlag
from ..common.coordinate_converter import pos_cm_to_m_tuple
from .common import draw_copy_paste_ops, matrix_prop
from .materials_panel import NUD_ShaderPropertyGroup



class NudPropertyGroup(PropertyGroup):
    """Property group that contains attributes of a nuccChunkModel."""

    clump_chunk_name: StringProperty(name="Clump Chunk Name")

    hit_chunk_name: StringProperty(name="Hit Chunk Name")

    mesh_bone: StringProperty(
        name='Mesh Bone',
        description='The bone that this NUD is attached to'
    )

    rigging_flag: EnumProperty(
        name='Rigging Flag',
        items=[('1', 'Unskinned (0x01)', ''),
               ('2', 'Skinned (0x02)', ''),
               ('4', 'Outline (0x04)', ''), ],
        description='Affects the NUD\'s rigging. Unskinned and Skinned should not be enabled at the same time. Examples:\n'
        'Eyes (Storm): Unskinned (0x01)\n'
        'Eyes (JoJo): Skinned (0x02)\n'
        'Teeth (Storm): Unskinned & Body (0x05)\n'
        'Teeth (JoJo): Unskinned (0x01)\n'
        'Body and tongue: Skinned & Body (0x06)\n',
        options={'ENUM_FLAG'},
        default={'2', '4'},
    )

    rigging_flag_extra: EnumProperty(
        name='Rigging Flag (Extra)',
        items=[('16', 'Blur (0x10)', ''),
               ('32', 'Shadow (0x20)', ''), ],
        description='Both are usually always on',
        options={'ENUM_FLAG'},
        default={'16', '32'},
    )

    bone_flag: IntProperty(
        name='Bone Flag',
        min=0,
        max=255,
        default=0x14,
    )

    model_attributes: IntProperty(
        name='Model Attributes',
        min=0,
        max=255,
        default=0x00,
    )

    render_layer: IntProperty(
        name='Render Layer',
        min=0,
        max=255,
        default=0x00,
    )

    light_mode: IntProperty(
        name='Light Mode',
        min=0,
        max=255,
        default=0x00,
    )

    light_category: IntProperty(
        name='Light Category',
        default=0
    )

    bounding_box: FloatVectorProperty(
        name='Bounding Box',
        description='Only applies when attribute flags contains 0x04',
        size=6,
    )

    bounding_sphere_nud: FloatVectorProperty(
        name='Bounding Sphere (NUD)',
        size=4,
    )

    bounding_sphere_group: FloatVectorProperty(
        name='Bounding Sphere (Group)',
        size=8,
    )

    shader_settings: bpy.props.PointerProperty(type=NUD_ShaderPropertyGroup)

    def init_data(self, model: NuccChunkModel, mesh_bone: str):
        #print(f"model name: {model.name}")
        self.mesh_bone = mesh_bone
        self.clump_chunk_name = model.clump_chunk.name
        if model.hit_chunk.name == '':
            self.hit_chunk_name = 'None'
        else:
            self.hit_chunk_name = model.hit_chunk.name
        
        # Set the rigging flag
        rigging_flag = set()
        if model.rigging_flag & RiggingFlag.UNSKINNED:
            rigging_flag.add('1')
        if model.rigging_flag & RiggingFlag.SKINNED:
            rigging_flag.add('2')
        if model.rigging_flag & RiggingFlag.OUTLINE:
            rigging_flag.add('4')

        self.rigging_flag = rigging_flag

        # Set the extra rigging flag
        rigging_flag_extra = set()
        if model.rigging_flag & RiggingFlag.BLUR:
            rigging_flag_extra.add('16')
        if model.rigging_flag & RiggingFlag.SHADOW:
            rigging_flag_extra.add('32')

        self.rigging_flag_extra = rigging_flag_extra

        # Get the first (and only) group's bounding sphere and bone flag
        groups = model.nud.mesh_groups
        if groups:
            self.bone_flag = groups[0].bone_flags
            self.bounding_sphere_group = pos_cm_to_m_tuple(tuple(groups[0].bounding_sphere))

        # Set the material flags
        self.model_attributes = model.model_attributes
        self.render_layer = model.render_layer
        self.light_mode = model.light_mode_id
        self.light_category = model.light_category
        #self.material_flags = tuple(model.material_flags)

        # Set the flag1 floats
        self.bounding_box = model.bounding_box if model.bounding_box else [0] * 6

        # Set the NUD's bounding sphere
        self.bounding_sphere_nud = pos_cm_to_m_tuple(tuple(model.nud.bounding_sphere))

        # Set the shader settings
        self.shader_settings.init_data(model.nud.mesh_groups[0].meshes[0].materials[0])



class NudPropertyPanel(Panel):
    """Panel that displays the NudPropertyGroup attached to the selected empty object."""

    bl_idname = 'OBJECT_PT_nud'
    bl_label = "[XFBIN] NUD Properties"

    bl_space_type = "PROPERTIES"
    bl_context = "object"
    bl_region_type = "WINDOW"

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.parent and obj.parent.type == 'ARMATURE'

    def draw(self, context):
        layout = self.layout
        obj = context.object
        data: NudPropertyGroup = obj.xfbin_nud_data

        draw_copy_paste_ops(layout, 'xfbin_nud_data', 'NUD Properties')

        collection = bpy.data.collections[obj.users_collection[0].name]
        row = layout.row()

        row.prop_search(data, 'mesh_bone', obj.parent.data, 'bones')
        row.prop_search(data, 'hit_chunk_name', collection, 'objects')

        layout.label(text='Mesh Flags')
        box = layout.box()
        box.prop(data, 'rigging_flag')
        box.prop(data, 'rigging_flag_extra')

        layout.prop(data, 'bone_flag')

        box = layout.box()
        row = box.row()
        row.prop(data, 'model_attributes')
        row.prop(data, 'render_layer')
        row.prop(data, 'light_mode')
        row.prop(data, 'light_category')

        shader = data.shader_settings

        box = layout.box()
        row = box.row()
        row.label(text='Default Shader Settings')
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


nud_property_groups = (
    NudPropertyGroup,
)

nud_classes = (
    *nud_property_groups,
    NudPropertyPanel,

)
