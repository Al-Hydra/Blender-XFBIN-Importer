from typing import List, Optional

import bpy
from bpy.props import (BoolProperty, CollectionProperty, IntProperty,
                       StringProperty)
from bpy.types import Action, Panel, PropertyGroup, UIList

from ...xfbin_lib.xfbin.structure.nucc import NuccChunkAnm, NuccChunkCamera, NuccChunkLightDirc, NuccChunkLightPoint, NuccChunkAmbient
from ...xfbin_lib.xfbin.structure.anm import AnmClump, AnmBone, AnmModel, AnmKeyframe
from ..common.helpers import XFBIN_ANMS_OBJ
from .common import draw_xfbin_list, XFBIN_OPERATORS

#UI Lists



class XFBIN_UL_ANM_CLUMP(UIList):
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.split(factor=0.5)
            row.prop(item, 'name', text='', emboss=False)
            row.prop(item, 'ref_name', text='', emboss=False)
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)


#anm panels buttons

class XFBIN_OT_ANM_BUTTON_ADD(bpy.types.Operator):
    bl_idname = 'xfbin.anm_button_add'
    bl_label = 'Add'
    bl_description = 'Add to list'
    
    add_option: bpy.props.EnumProperty(
        items=[('amm_chunks', 'anm_chunks', ''),
                ('anm_clumps', 'anm_clumps', ''),
                ('cameras', 'cameras', ''),
                ('lightdircs', 'lightdircs', ''),
                ('lightpoints', 'lightpoints', ''),
                ('ambients', 'ambients', ''),
                ('models', 'models', ''),
                ('bones', 'bones', ''),
                ('materials', 'materials', '')],
    )

    #universal function to add to list
    def add_to_list(self, context, data, prop_name, index):
        item = getattr(data, prop_name)
        item.add()
        
        #set index to the last item
        setattr(data, index, len(item) - 1)
        return {'FINISHED'}

    def execute(self, context):
        anm_obj = context.object
        data: AnmChunksListPropertyGroup = anm_obj.xfbin_anm_chunks_data
        
        if self.add_option == 'anm_chunks':
            return self.add_to_list(context, data, 'anm_chunks', 'anm_chunk_index')
        elif self.add_option == 'anm_clumps':
            return self.add_to_list(context, data.anm_chunks[data.anm_chunk_index], 'anm_clumps', 'clump_index')
        elif self.add_option == 'cameras':
            return self.add_to_list(context, data.anm_chunks[data.anm_chunk_index], 'cameras', 'camera_index')
        elif self.add_option == 'lightdircs':
            return self.add_to_list(context, data.anm_chunks[data.anm_chunk_index], 'lightdircs', 'lightdirc_index')
        elif self.add_option == 'lightpoints':
            return self.add_to_list(context, data.anm_chunks[data.anm_chunk_index], 'lightpoints', 'lightpoint_index')
        elif self.add_option == 'ambients':
            return self.add_to_list(context, data.anm_chunks[data.anm_chunk_index], 'ambients', 'ambient_index')
        elif self.add_option == 'models':
            return self.add_to_list(context, data.anm_chunks[data.anm_chunk_index].anm_clumps[data.anm_chunk_index], 'models', 'model_index')
        elif self.add_option == 'bones':
            return self.add_to_list(context, data.anm_chunks[data.anm_chunk_index].anm_clumps[data.anm_chunk_index], 'bones', 'bone_index')
        elif self.add_option == 'materials':
            return self.add_to_list(context, data.anm_chunks[data.anm_chunk_index].anm_clumps[data.anm_chunk_index], 'materials', 'material_index')
        return {'FINISHED'}


class XFBIN_OT_ANM_BUTTON_REMOVE(bpy.types.Operator):
    bl_idname = 'xfbin.anm_button_remove'
    bl_label = 'Remove'
    bl_description = 'Remove from list'
    
    remove_option: bpy.props.EnumProperty(
        items=[('anm_chunks', 'anm_chunks', ''),
                ('anm_clumps', 'anm_clumps', ''),
                ('cameras', 'cameras', ''),
                ('lightdircs', 'lightdircs', ''),
                ('lightpoints', 'lightpoints', ''),
                ('ambients', 'ambients', ''),
                ('models', 'models', ''),
                ('bones', 'bones', ''),
                ('materials', 'materials', '')],
    )

    #universal function to remove from list
    def remove_from_list(self, context, data, prop_name, index):
        item = getattr(data, prop_name)
        item.remove(getattr(data, index))
        setattr(data, index, max(0, min(getattr(data, index), len(item) - 1)) )
       
        return {'FINISHED'}


    def execute(self, context):
        anm_obj = context.object
        data: AnmChunksListPropertyGroup = anm_obj.xfbin_anm_chunks_data
        
        if self.remove_option == 'anm_chunks':
            return self.remove_from_list(context, data, 'anm_chunks', 'anm_chunk_index')
        elif self.remove_option == 'anm_clumps':
            return self.remove_from_list(context, data.anm_chunks[data.anm_chunk_index], 'anm_clumps', 'clump_index')
        elif self.remove_option == 'cameras':
            return self.remove_from_list(context, data.anm_chunks[data.anm_chunk_index], 'cameras', 'camera_index')
        elif self.remove_option == 'lightdircs':
            return self.remove_from_list(context, data.anm_chunks[data.anm_chunk_index], 'lightdircs', 'lightdirc_index')
        elif self.remove_option == 'lightpoints':
            return self.remove_from_list(context, data.anm_chunks[data.anm_chunk_index], 'lightpoints', 'lightpoint_index')
        elif self.remove_option == 'ambients':
            return self.remove_from_list(context, data.anm_chunks[data.anm_chunk_index], 'ambients', 'ambient_index')
        elif self.remove_option == 'models':
            return self.remove_from_list(context, data.anm_chunks[data.anm_chunk_index].anm_clumps[data.anm_chunk_index], 'models', 'model_index')
        elif self.remove_option == 'bones':
            return self.remove_from_list(context, data.anm_chunks[data.anm_chunk_index].anm_clumps[data.anm_chunk_index], 'bones', 'bone_index')
        elif self.remove_option == 'materials':
            return self.remove_from_list(context, data.anm_chunks[data.anm_chunk_index].anm_clumps[data.anm_chunk_index], 'materials', 'material_index')
        return {'FINISHED'}


class XFBIN_OT_ANM_BUTTON_MOVE_UP(bpy.types.Operator):
    bl_idname = 'xfbin.anm_button_move_up'
    bl_label = 'Move Up'
    bl_description = 'Move item up'

    move_option: bpy.props.EnumProperty(
        items=[('anm_chunks', 'anm_chunks', ''),
                ('anm_clumps', 'anm_clumps', ''),
                ('cameras', 'cameras', ''),
                ('lightdircs', 'lightdircs', ''),
                ('lightpoints', 'lightpoints', ''),
                ('ambients', 'ambients', ''),
                ('models', 'models', ''),
                ('bones', 'bones', ''),
                ('materials', 'materials', '')],
    )

    #universal function to move item up
    def move_item_up(self, context, data, prop_name, index):
        item = getattr(data, prop_name)
        item_index = getattr(data, index)
        if item_index > 0:
            item.move(item_index, item_index - 1)
            setattr(data, index, item_index - 1)
        return {'FINISHED'}

    def execute(self, context):
        anm_obj = context.object
        data: AnmChunksListPropertyGroup = anm_obj.xfbin_anm_chunks_data
        
        if self.move_option == 'anm_chunks':
            return self.move_item_up(context, data, 'anm_chunks', 'anm_chunk_index')
        elif self.move_option == 'anm_clumps':
            return self.move_item_up(context, data.anm_chunks[data.anm_chunk_index], 'anm_clumps', 'clump_index')
        elif self.move_option == 'cameras':
            return self.move_item_up(context, data.anm_chunks[data.anm_chunk_index], 'cameras', 'camera_index')
        elif self.move_option == 'lightdircs':
            return self.move_item_up(context, data.anm_chunks[data.anm_chunk_index], 'lightdircs', 'lightdirc_index')
        elif self.move_option == 'lightpoints':
            return self.move_item_up(context, data.anm_chunks[data.anm_chunk_index], 'lightpoints', 'lightpoint_index')
        elif self.move_option == 'ambients':
            return self.move_item_up(context, data.anm_chunks[data.anm_chunk_index], 'ambients', 'ambient_index')
        elif self.move_option == 'models':
            return self.move_item_up(context, data.anm_chunks[data.anm_chunk_index].anm_clumps[data.anm_chunk_index], 'models', 'model_index')
        elif self.move_option == 'bones':
            return self.move_item_up(context, data.anm_chunks[data.anm_chunk_index].anm_clumps[data.anm_chunk_index], 'bones', 'bone_index')
        elif self.move_option == 'materials':
            return self.move_item_up(context, data.anm_chunks[data.anm_chunk_index].anm_clumps[data.anm_chunk_index], 'materials', 'material_index')
        return {'FINISHED'}
    

class XFBIN_OT_ANM_BUTTON_MOVE_DOWN(bpy.types.Operator):
    bl_idname = 'xfbin.anm_button_move_down'
    bl_label = 'Move Down'
    bl_description = 'Move item down'

    move_option: bpy.props.EnumProperty(
        items=[('anm_chunks', 'anm_chunks', ''),
                ('anm_clumps', 'anm_clumps', ''),
                ('cameras', 'cameras', ''),
                ('lightdircs', 'lightdircs', ''),
                ('lightpoints', 'lightpoints', ''),
                ('ambients', 'ambients', ''),
                ('models', 'models', ''),
                ('bones', 'bones', ''),
                ('materials', 'materials', '')],
    )

    #universal function to move item down
    def move_item_down(self, context, data, prop_name, index):
        item = getattr(data, prop_name)
        item_index = getattr(data, index)
        if item_index < len(item) - 1:
            item.move(item_index, item_index + 1)
            #get the index variable name
            setattr(data, index, item_index + 1)
        return {'FINISHED'}

    def execute(self, context):
        anm_obj = context.object
        data: AnmChunksListPropertyGroup = anm_obj.xfbin_anm_chunks_data
        
        if self.move_option == 'anm_chunks':
            return self.move_item_down(context, data, 'anm_chunks', 'anm_chunk_index')
        elif self.move_option == 'anm_clumps':
            return self.move_item_down(context, data.anm_chunks[data.anm_chunk_index], 'anm_clumps', 'clump_index')
        elif self.move_option == 'cameras':
            return self.move_item_down(context, data.anm_chunks[data.anm_chunk_index], 'cameras', 'camera_index')
        elif self.move_option == 'lightdircs':
            return self.move_item_down(context, data.anm_chunks[data.anm_chunk_index], 'lightdircs', 'lightdirc_index')
        elif self.move_option == 'lightpoints':
            return self.move_item_down(context, data.anm_chunks[data.anm_chunk_index], 'lightpoints', 'lightpoint_index')
        elif self.move_option == 'ambients':
            return self.move_item_down(context, data.anm_chunks[data.anm_chunk_index], 'ambients', 'ambient_index')
        elif self.move_option == 'models':
            return self.move_item_down(context, data.anm_chunks[data.anm_chunk_index].anm_clumps[data.anm_chunk_index], 'models', 'model_index')
        elif self.move_option == 'bones':
            return self.move_item_down(context, data.anm_chunks[data.anm_chunk_index].anm_clumps[data.anm_chunk_index], 'bones', 'bone_index')
        elif self.move_option == 'materials':
            return self.move_item_down(context, data.anm_chunks[data.anm_chunk_index].anm_clumps[data.anm_chunk_index], 'materials', 'material_index')
        return {'FINISHED'}
    

        

class AnmClumpBonePropertyGroup(PropertyGroup):
    name: StringProperty()
    ref_name: StringProperty()

    def init_data(self, bone: AnmBone):
        self.name = bone.name
        self.ref_name = bone.referenced_name

class AnmClumpModelPropertyGroup(PropertyGroup):
    name: StringProperty()
    ref_name: StringProperty()

    def init_data(self, model: AnmModel):
        self.name = model.name
        self.ref_name = model.referenced_name

class AnmClumpMaterialPropertyGroup(PropertyGroup):
    name: StringProperty()
    ref_name: StringProperty()

    def init_data(self, material: AnmBone):
        self.name = material.name
        self.ref_name = material.referenced_name

class AnmClumpPropertyGroup(PropertyGroup):
    def update_clump_name(self, context):
        self.update_name()

    name: StringProperty(
        name="Name",
        default='new_clump',
        update=update_clump_name,
    )
    
    ref_name: StringProperty(name="Ref Name")

    clump_index: IntProperty(name="Index")

    models: CollectionProperty(type=AnmClumpModelPropertyGroup)
    model_index: IntProperty(name="Model Index")

    bones: CollectionProperty(type=AnmClumpBonePropertyGroup)
    bone_index: IntProperty(name="Bone Index")

    materials: CollectionProperty(type=AnmClumpMaterialPropertyGroup)
    material_index: IntProperty(name="Material Index")
    
    def update_name(self):
        if self.name != self.name:
            self.name = self.name

    def init_data(self, clump: AnmClump):
        self.name = clump.name
        self.ref_name = clump.referenced_name
        
        self.models.clear()
        for model in clump.models:
            item = self.models.add()
            item.init_data(model)

        
        self.bones.clear()
        self.materials.clear()
        
        for bone in clump.bones:
            item = self.bones.add()
            item.init_data(bone)
        
        for material in clump.materials:
            item = self.materials.add()
            item.init_data(material)

class CameraPropertyGroup(PropertyGroup):
    def update_camera_name(self, context):
        self.update_name()

    name: StringProperty(
        name="Name",
        default='new_camera',
        update=update_camera_name,
    )

    path: StringProperty(name="Path")

    camera_index: IntProperty(name="Index")

    def update_name(self):
        if self.name != self.name:
            self.name = self.name

    def init_data(self, camera: Optional[NuccChunkCamera] = None):
        if camera:
            self.name = camera.name
            self.path = camera.filePath
    
class LightDircPropertyGroup(PropertyGroup):
    def update_lightdirc_name(self, context):
        self.update_name()

    name: StringProperty(
        name="Name",
        default='new_lightdirc',
        update=update_lightdirc_name,
    )

    path: StringProperty(name="Path")

    lightdirc_index: IntProperty(name="Index")

    def update_name(self):
        if self.name != self.name:
            self.name = self.name

    def init_data(self, lightdirc: Optional[NuccChunkLightDirc] = None):
        if lightdirc:
            self.name = lightdirc.name
            self.path = lightdirc.filePath

class LightPointPropertyGroup(PropertyGroup):
    def update_lightpoint_name(self, context):
        self.update_name()

    name: StringProperty(
        name="Name",
        default='new_lightpoint',
        update=update_lightpoint_name,
    )

    path: StringProperty(name="Path")

    lightpoint_index: IntProperty(name="Index")

    def update_name(self):
        if self.name != self.name:
            self.name = self.name

    def init_data(self, lightpoint: Optional[NuccChunkLightPoint] = None):
        if lightpoint:
            self.name = lightpoint.name
            self.path = lightpoint.filePath


class AmbientPropertyGroup(PropertyGroup):
    def update_ambient_name(self, context):
        self.update_name()

    name: StringProperty(
        name="Name",
        default='new_ambient',
        update=update_ambient_name,
    )

    path: StringProperty(name="Path")

    ambient_index: IntProperty(name="Index")

    def update_name(self):
        if self.name != self.name:
            self.name = self.name

    def init_data(self, ambient: Optional[NuccChunkAmbient] = None):
        if ambient:
            self.name = ambient.name
            self.path = ambient.filePath


class XfbinAnmChunkPropertyGroup(PropertyGroup):
    def update_anm_name(self, context):
        self.update_name()

    anm_name: StringProperty(
        name="Name",
        default='new_anm',
        update=update_anm_name,
    )

    path: StringProperty(name="Path")

    is_looped: BoolProperty(name="Looped", default=False)

    frame_count: IntProperty(name="Frame Count", default=0)

    frame_size: IntProperty(name="Frame Size", default=100)


    export_material_animations: BoolProperty(
    name="Export material animations", 
    description="Exports material actions if there are any",
    default=False)


    clump_index: IntProperty(name="Clump Index")

    anm_clumps: CollectionProperty(
        type=AnmClumpPropertyGroup,
    )

    camera_index: IntProperty()
    cameras: CollectionProperty(
        type=CameraPropertyGroup,
    )

    lightdirc_index: IntProperty()
    lightdircs: CollectionProperty(
        type=LightDircPropertyGroup,
    )

    lightpoint_index: IntProperty()
    lightpoints: CollectionProperty(
        type=LightPointPropertyGroup,
    )

    ambient_index: IntProperty()
    ambients: CollectionProperty(
        type=AmbientPropertyGroup,
    )

    def update_name(self):
        self.name = self.anm_name

    def init_data(self, anm: NuccChunkAnm, camera: Optional[NuccChunkCamera], lightdirc: Optional[NuccChunkLightDirc],
                lightpoint: Optional[NuccChunkLightPoint], ambient: Optional[NuccChunkAmbient]):
        
        self.anm_name = anm.name
        self.path = anm.filePath
        self.is_looped = anm.loop_flag
        self.frame_count = anm.frame_count // anm.frame_size
        self.frame_size = anm.frame_size

        self.anm_clumps.clear()
        for clump in anm.clumps:
            clump_prop: AnmClumpPropertyGroup = self.anm_clumps.add()
            clump_prop.init_data(clump)

        self.cameras.clear()
        if camera:
            camera_prop: CameraPropertyGroup = self.cameras.add()
            camera_prop.init_data(camera)

        self.lightdircs.clear()
        if lightdirc:
            lightdirc_prop: LightDircPropertyGroup = self.lightdircs.add()
            lightdirc_prop.init_data(lightdirc)
        
        self.lightpoints.clear()
        if lightpoint:
            lightpoint_prop: LightPointPropertyGroup = self.lightpoints.add()
            lightpoint_prop.init_data(lightpoint)

        self.ambients.clear()
        if ambient:
            ambient_prop: AmbientPropertyGroup = self.ambients.add()
            ambient_prop.init_data(ambient)
    

class AnmChunksListPropertyGroup(PropertyGroup):
    anm_chunks: CollectionProperty(
        type=XfbinAnmChunkPropertyGroup,
    )

    anm_chunk_index: IntProperty()

    def init_data(self, anm_chunks: List[NuccChunkAnm], cam_chunks: List[NuccChunkCamera], 
                lightdirc_chunks: List[NuccChunkLightDirc], lightpoint_chunks: List[NuccChunkLightPoint], ambient_chunks: List[NuccChunkAmbient], context):
        
        self.anm_chunks.clear()

        cam_dict = {cam.filePath: cam for cam in cam_chunks}
        lightdirc_dict = {lightdirc.filePath: lightdirc for lightdirc in lightdirc_chunks}
        lightpoint_dict = {lightpoint.filePath: lightpoint for lightpoint in lightpoint_chunks}
        ambient_dict = {ambient.filePath: ambient for ambient in ambient_chunks}


        for anm in anm_chunks:
            camera = cam_dict.get(anm.filePath, None)
            lightdirc = lightdirc_dict.get(anm.filePath, None)
            lightpoint = lightpoint_dict.get(anm.filePath, None)
            ambient = ambient_dict.get(anm.filePath, None)

            a: XfbinAnmChunkPropertyGroup = self.anm_chunks.add()
            a.init_data(anm, camera, lightdirc, lightpoint, ambient)

            
                


class AnmChunksPropertyPanel(Panel):

    bl_idname = 'OBJECT_PT_xfbin_animation'
    bl_label = '[XFBIN] Animation Properties'

    bl_space_type = 'PROPERTIES'
    bl_context = 'object'
    bl_region_type = 'WINDOW'

    @classmethod
    def poll(cls, context):
        # get the outliner object
        
        obj = context.object
        return obj and obj.type == 'EMPTY' and obj.parent is None and obj.name.startswith(XFBIN_ANMS_OBJ)
    
    def draw(self, context):
        obj = context.object
        layout = self.layout
        data: AnmChunksListPropertyGroup = obj.xfbin_anm_chunks_data
        draw_xfbin_list(layout, 0, data, 'xfbin_anm_chunks_data', 'anm_chunks', 'anm_chunk_index')
        #draw_xfbin_list_search(layout, 0, data, 'xfbin_anm_chunks_data', 'anm_chunks', 'anm_chunk_index')
        anm_index = data.anm_chunk_index

        box = layout.box()
        box.label(text="Animation Properties:")

        if anm_index >= 0 and anm_index < len(data.anm_chunks):
            chunk: XfbinAnmChunkPropertyGroup = data.anm_chunks[anm_index]
            box.prop_search(chunk, 'name', bpy.data, 'actions', text="Action")
            box.prop(chunk, 'path')
            box.prop(chunk, 'is_looped')
            
            row = box.row()
            row.prop(chunk, 'frame_count')
            row.prop(chunk, 'frame_size')

            anm = data.anm_chunks[anm_index]

            #play button
            box.operator('obj.play_animation', text='Play Animation', icon='PLAY')
        
            row = box.row()
            row.prop(anm, 'export_material_animations')      

            #clumps
            row = layout.row()
            row.label(text="Clumps:")
            clump_box = layout.box()
            row = clump_box.row()
            row.label(text="Name:")
            row.label(text="Referenced Name:")
            
            row = clump_box.row()

            col = row.column()
            row = col.row()
            row.template_list('XFBIN_UL_ANM_CLUMP', 'Clumps', anm, 'anm_clumps', anm, 'clump_index')
            col = row.column()
            col.operator('xfbin.anm_button_add', text='', icon='ADD').add_option = 'anm_clumps'
            col.operator('xfbin.anm_button_remove', text='', icon='REMOVE').remove_option = 'anm_clumps'
            col.operator('xfbin.anm_button_move_up', text='', icon='TRIA_UP').move_option = 'anm_clumps'
            col.operator('xfbin.anm_button_move_down', text='', icon='TRIA_DOWN').move_option = 'anm_clumps'

            if len(anm.anm_clumps) > 0:
                clump = anm.anm_clumps[anm.clump_index]

                box = clump_box.box()
                row = box.row()
                row.prop_search(clump, 'name', bpy.data, 'armatures', text="Clump", icon='OUTLINER_OB_ARMATURE')
                row.prop_search(clump, 'ref_name', bpy.data, 'armatures', text="Referenced Clump", icon='OUTLINER_OB_ARMATURE')



            #models
            layout.label(text="Models:")
            models_box = layout.box()
            row = models_box.row()
            row.label(text="Name:")
            row.label(text="Referenced Name:")
            
            
            models_box.template_list('XFBIN_UL_ANM_CLUMP', 'Models', clump, 'models', clump, 'model_index')

            if clump.model_index >= 0 and clump.model_index < len(clump.models):
                model = clump.models[clump.model_index]
                box = models_box.box()
                row = box.row()
                row.prop_search(model, 'name', bpy.context.scene, 'objects', text="Model")
                row.prop_search(model, 'ref_name', bpy.context.scene, 'objects', text="Referenced Model")

            #bones
            layout.label(text="Bones:")
            
            bones_box = layout.box()
            row = bones_box.row()
            row.label(text="Name:")
            row.label(text="Referenced Name:")
            
            bones_box.template_list('XFBIN_UL_ANM_CLUMP', 'Bones', clump, 'bones', clump, 'bone_index')
            
            if clump.bone_index >= 0 and clump.bone_index < len(clump.bones):
                bone = clump.bones[clump.bone_index]
                box = bones_box.box()
                row = box.row()
                row.prop_search(bone, 'name', bpy.context.scene, 'objects', text="Bone")
                row.prop_search(bone, 'ref_name', bpy.context.scene, 'objects', text="Referenced Bone")

            #materials
            layout.label(text="Materials:")
            
            materials_box = layout.box()
            row = materials_box.row()
            row.label(text="Name:")
            row.label(text="Referenced Name:")
            
            materials_box.template_list('XFBIN_UL_ANM_CLUMP', 'Materials', clump, 'materials', clump, 'material_index')
            
            if clump.material_index >= 0 and clump.material_index < len(clump.materials):
                material = clump.materials[clump.material_index]
                box = materials_box.box()
                row = box.row()
                row.prop_search(material, 'name', bpy.context.scene, 'objects', text="Material")
                row.prop_search(material, 'ref_name', bpy.context.scene, 'objects', text="Referenced Material")


            # cameras
            camera_box = layout.box()
            camera_box.label(text="Cameras:")

            camera = anm.cameras[anm.camera_index] if anm.cameras and anm.camera_index < len(anm.cameras) else None

            if camera:
                camera_box.prop(camera, 'name')
                camera_box.prop(camera, 'path')
                draw_xfbin_list(camera_box, 5, anm, f'xfbin_anm_chunks_data.anm_chunks[{anm_index}]', 'cameras', 'camera_index')
                box = camera_box.box()
                box.prop_search(anm.cameras[anm.camera_index], 'name', bpy.data, 'cameras', text="Camera", icon='CAMERA_DATA')
                
            else:
                draw_xfbin_list(camera_box, 5, anm, f'xfbin_anm_chunks_data.anm_chunks[{anm_index}]', 'cameras', 'camera_index')
            

            lightdirc_box = layout.box()
            lightdirc_box.label(text="Directional Lights:")

            lightdirc = anm.lightdircs[anm.lightdirc_index] if anm.lightdircs and anm.lightdirc_index < len(anm.lightdircs) else None

            if lightdirc:
                lightdirc_box.prop(lightdirc, 'name')
                lightdirc_box.prop(lightdirc, 'path')

                draw_xfbin_list(lightdirc_box, 6, anm, f'xfbin_anm_chunks_data.anm_chunks[{anm_index}]', 'lightdircs', 'lightdirc_index')

                box = lightdirc_box.box()
                box.prop_search(anm.lightdircs[anm.lightdirc_index], 'name', bpy.data, 'objects', text="LightDirc", icon='LIGHT')
            else:
                draw_xfbin_list(lightdirc_box, 6, anm, f'xfbin_anm_chunks_data.anm_chunks[{anm_index}]', 'lightdircs', 'lightdirc_index')


            lightpoint_box = layout.box()
            lightpoint_box.label(text="Point Lights:")

            lightpoint = anm.lightpoints[anm.lightpoint_index] if anm.lightpoints and anm.lightpoint_index < len(anm.lightpoints) else None

            if lightpoint:
                lightpoint_box.prop(lightpoint, 'name')
                lightpoint_box.prop(lightpoint, 'path')

                draw_xfbin_list(lightpoint_box, 7, anm, f'xfbin_anm_chunks_data.anm_chunks[{anm_index}]', 'lightpoints', 'lightpoint_index')

                box = lightpoint_box.box()
                box.prop_search(anm.lightpoints[anm.lightpoint_index], 'name', bpy.data, 'objects', text="LightPoint", icon='LIGHT')
            else:
                draw_xfbin_list(lightpoint_box, 7, anm, f'xfbin_anm_chunks_data.anm_chunks[{anm_index}]', 'lightpoints', 'lightpoint_index')

            ambient_box = layout.box()
            ambient_box.label(text="Ambient Lights:")

            ambient = anm.ambients[anm.ambient_index] if anm.ambients and anm.ambient_index < len(anm.ambients) else None

            if ambient:
                ambient_box.prop(ambient, 'name')
                ambient_box.prop(ambient, 'path')

                draw_xfbin_list(ambient_box, 8, anm, f'xfbin_anm_chunks_data.anm_chunks[{anm_index}]', 'ambients', 'ambient_index')

                box = ambient_box.box()
                box.prop_search(anm.ambients[anm.ambient_index], 'name', bpy.data, 'lights', text="Ambient", icon='WORLD')
            else:
                draw_xfbin_list(ambient_box, 8, anm, f'xfbin_anm_chunks_data.anm_chunks[{anm_index}]', 'ambients', 'ambient_index')

            

class PlayAnimation(bpy.types.Operator):
    bl_idname = 'obj.play_animation'
    bl_label = 'Play Animation'
    bl_description = 'Play Animation'

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type == 'EMPTY' and obj.parent is None and obj.name.startswith(XFBIN_ANMS_OBJ)
    
    def execute(self, context):
        #selected animation
        obj = context.object
        data: AnmChunksListPropertyGroup = obj.xfbin_anm_chunks_data
        anm_index = data.anm_chunk_index
        if anm_index >= 0 and anm_index < len(data.anm_chunks):
            chunk: XfbinAnmChunkPropertyGroup = data.anm_chunks[anm_index]
            #set timeline to animation length
            context.scene.frame_start = 0
            context.scene.frame_end = chunk.frame_count
            context.scene.frame_current = 0

            #get all clumps
            clumps = []
            for clump in chunk.anm_clumps:
                c = bpy.context.view_layer.objects.get(clump.name)
                if c:
                    clumps.append(c)
            #print(clumps)

            for clump in clumps:
                #get action
                #print(chunk.name)
                action = bpy.data.actions.get(f'{chunk.name}')
                #print(action)
                if action:
                    #set action
                    clump.animation_data_create()
                    clump.animation_data.action = action
                    #play
            
            #Check if no animation is playing
            if not context.screen.is_animation_playing:
                bpy.ops.screen.animation_play()
            
            self.report({'INFO'}, f'Playing animation {action.name}')
        
        return {'FINISHED'}


anm_chunks_property_groups = (
    AnmClumpBonePropertyGroup,
    AnmClumpMaterialPropertyGroup,
    AnmClumpModelPropertyGroup,
    AnmClumpPropertyGroup,
    CameraPropertyGroup,
    LightDircPropertyGroup,
    LightPointPropertyGroup,
    AmbientPropertyGroup,
    XfbinAnmChunkPropertyGroup,
    AnmChunksListPropertyGroup,
)

anm_chunks_classes = (
    *anm_chunks_property_groups,
    AnmChunksPropertyPanel,
    XFBIN_OT_ANM_BUTTON_ADD,
    XFBIN_OT_ANM_BUTTON_REMOVE,
    XFBIN_OT_ANM_BUTTON_MOVE_UP,
    XFBIN_OT_ANM_BUTTON_MOVE_DOWN,
    XFBIN_UL_ANM_CLUMP,
    PlayAnimation
)
