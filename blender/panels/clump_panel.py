from itertools import chain

import bpy
from bpy.props import (BoolProperty, CollectionProperty, FloatProperty,
                       FloatVectorProperty, IntProperty, StringProperty)
from bpy.types import Object, Panel, PropertyGroup

from ...xfbin_lib.xfbin.structure.nucc import (ClumpModelGroup,
                                               MaterialTextureGroup,
                                               NuccChunkClump,
                                               NuccChunkMaterial,
                                               NuccChunkTexture,
                                               NuccChunkBillboard,
                                               NuccChunkPrimitiveVertex,
                                               NuccChunkModelPrimitiveBatch)
from ..common.helpers import format_hex_str, hex_str_to_int, int_to_hex_str, XFBIN_DYNAMICS_OBJ, XFBIN_TEXTURES_OBJ 
from .common import (EmptyPropertyGroup, draw_copy_paste_ops, draw_xfbin_list,
                     matrix_prop)


class ClumpModelGroupPropertyGroup(PropertyGroup):
    def update_unk(self, context):
        old_val = self.unk
        new_val = format_hex_str(self.unk, 4)

        if new_val and len(new_val) < 12:
            if old_val != new_val:
                self.unk = new_val
        else:
            self.unk = '00 00 00 00'

    flag0: IntProperty(
        name='Flag 1',
        min=0,
        max=255,
    )

    flag1: IntProperty(
        name='Flag 2',
        min=0,
        max=255,
    )

    unk: StringProperty(
        name='Unk',
        update=update_unk,
    )

    models: CollectionProperty(
        type=EmptyPropertyGroup,
    )

    model_index: IntProperty()

    def update_name(self):
        self.name = 'Group'

    def init_data(self, group: ClumpModelGroup):
        self.flag0 = group.flag0
        self.flag1 = group.flag1
        self.unk = int_to_hex_str(group.unk, 4)

        # Add models
        self.models.clear()
        for model in group.model_chunks:
            m: EmptyPropertyGroup = self.models.add()
            m.value = model.name if model else 'None'


class ClumpPropertyGroup(PropertyGroup):
    name: StringProperty(
        name='Clump Name',
        default='',
    )
    path: StringProperty(
        name='Chunk Path',
        description='XFBIN chunk path that will be used for identifying the clump in the XFBIN.\n'
        'Should be the same as the path of the clump in the XFBIN to inject to.\n'
        'Example: "c\\1nrt\max\\1nrtbod1.max"',
    )

    field00: IntProperty(
        name='Clump Unk',
    )

    coord_flag0: IntProperty(
        name='LOD Levels',
        min=0,
        max=255,
    )

    coord_flag1: IntProperty(
        name='LOD Flag 2',
        min=0,
        max=255,
    )

    model_flag0: IntProperty(
        name='Model Flag 1',
        min=0,
        max=255,
    )

    model_flag1: IntProperty(
        name='Model Flag 2',
        min=0,
        max=255,
    )

    models: CollectionProperty(
        type=EmptyPropertyGroup,
    )

    model_index: IntProperty()

    model_groups: CollectionProperty(
        type=ClumpModelGroupPropertyGroup,
    )

    model_group_index: IntProperty()


    def init_data(self, clump: NuccChunkClump):
        self.name = clump.name
        self.path = clump.filePath

        # Set the properties
        self.field00 = clump.field00

        self.coord_flag0 = clump.coord_flag0
        self.coord_flag1 = clump.coord_flag1

        self.model_flag0 = clump.model_flag0
        self.model_flag1 = clump.model_flag1

        # Add models
        self.models.clear()
        for model in clump.model_chunks:
            m: EmptyPropertyGroup = self.models.add()
            m.value = model.name

        # Add model groups
        self.model_groups.clear()
        for group in clump.model_groups:
            g: ClumpModelGroupPropertyGroup = self.model_groups.add()
            g.init_data(group)
            g.name = 'Group'

    def update_models(self, obj: Object):
        empties = [c for c in obj.children if c.type == 'EMPTY']

        for model in chain(self.models, *map(lambda x: x.models, self.model_groups)):
            empty = [e for e in empties if e.name == model.value]
            if empty:
                model.empty = empty[0]


class ClumpModelGroupPropertyPanel(Panel):
    bl_idname = 'OBJECT_PT_xfbin_model_group'
    bl_parent_id = 'OBJECT_PT_xfbin_clump'
    bl_label = 'Model Groups'

    bl_space_type = 'PROPERTIES'
    bl_context = 'object'
    bl_region_type = 'WINDOW'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        obj = context.object
        data: ClumpPropertyGroup = obj.xfbin_clump_data

        draw_xfbin_list(layout, 1, data, f'xfbin_clump_data', 'model_groups', 'model_group_index')
        index = data.model_group_index

        if data.model_groups and index >= 0:
            group: ClumpModelGroupPropertyGroup = data.model_groups[index]
            box = layout.box()

            row = box.row()
            row.prop(group, 'flag0')
            row.prop(group, 'flag1')

            box.prop(group, 'unk')

            box.label(text='Models')
            draw_xfbin_list(box, 2, group, f'xfbin_clump_data.model_groups[{index}]', 'models', 'model_index')
            model_index = group.model_index

            if group.models and model_index >= 0:
                model: EmptyPropertyGroup = group.models[model_index]
                box = box.box()

                box.prop_search(model, 'empty', context.collection, 'all_objects',
                                text='Model Object', icon='OUTLINER_OB_EMPTY')


class ClumpPropertyPanel(Panel):
    """Panel that displays the ClumpPropertyPanel attached to the selected armature object."""

    bl_idname = 'OBJECT_PT_xfbin_clump'
    bl_label = '[XFBIN] Clump Properties'

    bl_space_type = 'PROPERTIES'
    bl_context = 'object'
    bl_region_type = 'WINDOW'

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'ARMATURE'

    def draw(self, context):
        obj = context.object
        layout = self.layout
        data: ClumpPropertyGroup = obj.xfbin_clump_data

        draw_copy_paste_ops(layout, 'xfbin_clump_data', 'Clump Properties')
        row = layout.row()
        row.operator('object.create_dynamics_object', text='Create Dynamics Object')
        row.operator('object.create_textures_object', text='Create Textures Object')

        layout.label(text='LOD Flags:')
        box = layout.box()
        row = box.row()
        row.prop(data, 'coord_flag0')
        row.prop(data, 'coord_flag1')

        layout.prop(data, 'path')

        layout.label(text='Models')
        draw_xfbin_list(layout, 0, data, f'xfbin_clump_data', 'models', 'model_index')
        model_index = data.model_index


        if data.models and model_index >= 0:
            model: EmptyPropertyGroup = data.models[model_index]
            box = layout.box()

            box.prop_search(model, 'empty', context.collection, 'all_objects',
                            text='Model Object', icon='OUTLINER_OB_EMPTY')


class CreateDynamicsObject(bpy.types.Operator):
    """Creates a dynamics object for the selected armature."""

    bl_idname = 'object.create_dynamics_object'
    bl_label = 'Create Dynamics Object'

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'ARMATURE'

    def execute(self, context):
        
        obj = context.object
        data: ClumpPropertyGroup = obj.xfbin_clump_data
        #get object collection
        collection = obj.users_collection[0]

        #check if a dynamics object already exists
        dynamics_obj = collection.objects.get(f'{XFBIN_DYNAMICS_OBJ} [{data.name}]')
        if not dynamics_obj:

            #create dynamics object
            dynamics_obj = bpy.data.objects.new(f'{XFBIN_DYNAMICS_OBJ} [{data.name}]', None)
            dynamics_obj.empty_display_type = 'PLAIN_AXES'
            dynamics_obj.empty_display_size = 0.0001
            collection.objects.link(dynamics_obj)

            #create dynamics object data
            dynamics_data = dynamics_obj.xfbin_dynamics_data

            dynamics_data.clump_name = data.name
            dynamics_data.path = data.path
        
        else:
            self.report({'ERROR'}, f'A dynamics object already exists for {data.name}.')


        return {'FINISHED'}


class CreateTexturesObject(bpy.types.Operator):
    bl_idname = 'object.create_textures_object'
    bl_label = 'Create Textures Object'

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'ARMATURE'

    def execute(self, context):
        
        obj = context.object
        data: ClumpPropertyGroup = obj.xfbin_clump_data
        #get object collection
        collection = obj.users_collection[0]

        #check if a textures object already exists
        textures_obj = collection.objects.get(f'{XFBIN_TEXTURES_OBJ} [{data.name}]')
        if not textures_obj:

            #create textures object
            textures_obj = bpy.data.objects.new(f'{XFBIN_TEXTURES_OBJ} [{data.name}]', None)
            textures_obj.empty_display_type = 'PLAIN_AXES'
            textures_obj.empty_display_size = 0.0001
            collection.objects.link(textures_obj)
        
        else:
            self.report({'ERROR'}, f'A textures object already exists for {data.name}.')


        return {'FINISHED'}
clump_property_groups = (
    ClumpModelGroupPropertyGroup,
    ClumpPropertyGroup,
)

clump_classes = (
    *clump_property_groups,
    ClumpPropertyPanel,
    ClumpModelGroupPropertyPanel,
    CreateDynamicsObject,
    CreateTexturesObject,
)
