import bpy
from bpy.props import (EnumProperty, FloatVectorProperty, IntProperty,
                       IntVectorProperty, StringProperty)
from bpy.types import Panel, PropertyGroup

from ...xfbin_lib.xfbin.structure.nucc import NuccChunkModel, RiggingFlag
from ..common.coordinate_converter import pos_cm_to_m_tuple
from .common import draw_copy_paste_ops, matrix_prop


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
        return obj and obj.type == 'EMPTY' and obj.parent and obj.parent.type == 'ARMATURE'

    def draw(self, context):
        layout = self.layout
        obj = context.object
        data: NudPropertyGroup = obj.xfbin_nud_data

        draw_copy_paste_ops(layout, 'xfbin_nud_data', 'NUD Properties')

        layout.prop_search(data, 'mesh_bone', obj.parent.data, 'bones')

        layout.label(text='Rigging Flags')
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

        if data.model_attributes & 0x04:
            layout.prop(data, 'bounding_box')

        matrix_prop(layout, data, 'bounding_sphere_nud', 4, 'Bounding Sphere (NUD)')

        row = layout.row()
        row.operator(create_bounding_sphere.bl_idname)
        row.operator(update_bounding_sphere.bl_idname)
        matrix_prop(layout, data, 'bounding_sphere_group', 8, 'Bounding Sphere (Group)')

        collection = bpy.data.collections[obj.users_collection[0].name]
        layout.prop_search(data, 'hit_chunk_name', collection, 'objects')

class create_bounding_sphere(bpy.types.Operator):
    bl_idname = "object.create_bounding_sphere"
    bl_label = "Create Bounding Sphere Object"
    bl_description = 'Creates an empty object using bounding sphere location and scale values'
    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type == 'EMPTY' and obj.parent is not None
    def execute(self, context):
        obj = context.object
        data: NudPropertyGroup = obj.xfbin_nud_data
        
        #Create a new collection for bounding spheres
        if not bpy.data.collections.get(f'{obj.users_collection[0].name} [BOUNDING SPHERES]'):
            collection = bpy.data.collections.new(f'{obj.users_collection[0].name} [BOUNDING SPHERES]')
            bpy.context.scene.collection.children.link(collection)

        else:
            collection = bpy.data.collections[f'{obj.users_collection[0].name} [BOUNDING SPHERES]']
        
        
        #remove existing bounding sphere
        if bpy.data.objects.get(f'{obj.name} Bounding Sphere'):
            bpy.data.objects.remove(bpy.data.objects[f'{obj.name} Bounding Sphere'])
        
        #create new bounding sphere
        empty = bpy.data.objects.new(f'{obj.name} Bounding Sphere', None)
        empty.empty_display_type = 'SPHERE'
        empty.empty_display_size = data.bounding_sphere_nud[3]
        empty.location = data.bounding_sphere_nud[0:3]
        
        #link the object to the collection we created
        collection.objects.link(empty)

        return {'FINISHED'}

class update_bounding_sphere(bpy.types.Operator):
    bl_idname = "object.update_bounding_sphere"
    bl_label = "Update bounding sphere values"
    bl_description = 'Updates the bounding sphere values if an object exists'
    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type == 'EMPTY' and obj.parent is not None
    def execute(self, context):
        obj = context.object
        data: NudPropertyGroup = obj.xfbin_nud_data
        
        collection = bpy.data.collections.get(f'{obj.users_collection[0].name} [BOUNDING SPHERES]')
        
        if not collection:
            self.report({'ERROR'}, 'No bounding sphere collection found')
            return {'CANCELLED'}
        
        bsphere = collection.objects.get(f'{obj.name} Bounding Sphere')

        if not bsphere:
            self.report({'ERROR'}, f'Bounding sphere object ({obj.name} Bounding Sphere) not found')
            return {'CANCELLED'}
        
        #update the bounding sphere values
        data.bounding_sphere_nud[0:3] = bsphere.location
        data.bounding_sphere_nud[3] = (bsphere.scale[0] + bsphere.scale[1] + bsphere.scale[2]) / 3
        return {'FINISHED'}

nud_property_groups = (
    NudPropertyGroup,
)

nud_classes = (
    *nud_property_groups,
    NudPropertyPanel,
    create_bounding_sphere,
    update_bounding_sphere
)
