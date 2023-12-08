from typing import List, Optional

import bpy
from bpy.props import (BoolProperty, CollectionProperty, IntProperty,
                       StringProperty)
from bpy.types import Action, Panel, PropertyGroup

from ...xfbin_lib.xfbin.structure.nucc import NuccChunkAnm, NuccChunkCamera
from ...xfbin_lib.xfbin.structure.anm import AnmClump, AnmBone, AnmModel, AnmKeyframe
from ..common.helpers import XFBIN_ANMS_OBJ
from ..importer import make_actions
from .common import draw_xfbin_list


class AnmClumpBonePropertyGroup(PropertyGroup):
    name: StringProperty()

    def init_data(self, bone: AnmBone):
        self.name = bone.name

class AnmClumpModelPropertyGroup(PropertyGroup):
    name: StringProperty()

    def init_data(self, model: AnmModel):
        self.name = model.name


class AnmClumpPropertyGroup(PropertyGroup):
    name: StringProperty(name="Name")
    clump_index: IntProperty(name="Index")
    models: CollectionProperty(type=AnmClumpModelPropertyGroup)
    model_index: IntProperty(name="Model Index")
    bones: CollectionProperty(type=AnmClumpBonePropertyGroup)
    bone_index: IntProperty(name="Bone Index")

    def init_data(self, clump: AnmClump):
        self.name = clump.name
        
        self.models.clear()
        for model in clump.models:
            item = self.models.add()
            item.init_data(model)
        
        self.bones.clear()
        for bone in clump.bones:
            item = self.bones.add()
            item.init_data(bone)
        

class CameraPropertyGroup(PropertyGroup):
    name: StringProperty()

    def init_data(self, camera: NuccChunkCamera):
        self.name = camera.name


class XfbinAnmChunkPropertyGroup(PropertyGroup):
    name: StringProperty(name="Name")

    path: StringProperty(name="Path")

    is_looped: BoolProperty(name="Looped", default=False)

    frame_count: IntProperty(name="Frame Count", default=0)

    frame_size: IntProperty(name="Frame Size", default=100)

    anm_clumps: CollectionProperty(
        type=AnmClumpPropertyGroup,
    )

    camera: CollectionProperty(
        type=CameraPropertyGroup,
    )

    clump_index: IntProperty(name="Clump Index")

    camera_index: IntProperty(name="Camera Index")
    
    def init_data(self, anm: NuccChunkAnm, actions: List[Action], camera: Optional[NuccChunkCamera]):
        self.name = anm.name
        self.filepath = anm.filePath
        self.is_looped = anm.loop_flag
        self.frame_count = anm.frame_count // anm.frame_size
        self.frame_size = anm.frame_size

        self.anm_clumps.clear()
        for clump in anm.clumps:
            clump_prop: AnmClumpPropertyGroup = self.anm_clumps.add()
            clump_prop.init_data(clump)

        self.camera.clear()
        if camera is not None:
            camera_prop: CameraPropertyGroup = self.camera.add()
            camera_prop.init_data(camera)

        


class AnmChunksListPropertyGroup(PropertyGroup):
    anm_chunks: CollectionProperty(
        type=XfbinAnmChunkPropertyGroup,
    )

    anm_chunk_index: IntProperty()

    def init_data(self, anm_chunks: List[NuccChunkAnm], cam_chunks: List[NuccChunkCamera], context):
        anm: NuccChunkAnm

        self.anm_chunks.clear()

        """for anm in anm_chunks:
            for cam in cam_chunks:
                if anm.filePath != cam.filePath: # This is only return the first camera that matches the animation but we want to return all animations
                    continue
                a: XfbinAnmChunkPropertyGroup = self.anm_chunks.add()
                a.init_data(anm, make_actions(anm, context), cam)"""

        for anm in anm_chunks:
            has_camera = False

            for cam in cam_chunks:
                if anm.filePath == cam.filePath:
                    has_camera = True
                    a: XfbinAnmChunkPropertyGroup = self.anm_chunks.add()
                    a.init_data(anm, make_actions(anm, context), cam)
                    break

            if not has_camera:
                # Handle animations without matching cameras
                a: XfbinAnmChunkPropertyGroup = self.anm_chunks.add()
                a.init_data(anm, make_actions(anm, context), None)
            


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
        anm_index = data.anm_chunk_index

        box = layout.box()
        box.label(text="Animation Properties:")

        if anm_index >= 0 and anm_index < len(data.anm_chunks):
            chunk: XfbinAnmChunkPropertyGroup = data.anm_chunks[anm_index]
            box.prop(chunk, 'name')
            box.prop(chunk, 'path')
            box.prop(chunk, 'is_looped')
            
            row = box.row()
            row.prop(chunk, 'frame_count')
            row.prop(chunk, 'frame_size')

            #play button
            box.operator('obj.play_animation', text='Play Animation', icon='PLAY')      

            

            #clumps
            layout.label(text="Clumps:")
            anm = data.anm_chunks[anm_index]
            clump = anm.anm_clumps[anm.clump_index]
            draw_xfbin_list(layout, 1, anm, 'xfbin_anm_chunks_data.anm_chunks[anm_chunk_index]', 'anm_clumps', 'clump_index')

            #models
            layout.label(text="Models:")
            draw_xfbin_list(layout, 2, clump, 'xfbin_anm_chunks_data.anm_chunks[anm_chunk_index].anm_clumps[clump_index]', 'models', 'model_index')

            #bones
            layout.label(text="Bones & Materials:")
            draw_xfbin_list(layout, 3, clump, 'xfbin_anm_chunks_data.anm_chunks[anm_chunk_index].anm_clumps[clump_index]', 'bones', 'bone_index')

            # cameras
            layout.label(text="Cameras:")
            draw_xfbin_list(layout, 4, anm, 'xfbin_anm_chunks_data.anm_chunks[anm_chunk_index]', 'camera', 'camera_index')

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
                c = bpy.context.view_layer.objects.get(f'{clump.name} [C]')
                if c:
                    clumps.append(c)
            #print(clumps)

            for clump in clumps:
                #get action
                #print(chunk.name)
                action = bpy.data.actions.get(f'{chunk.name} ({clump.name[:-4]})')
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
    AnmClumpModelPropertyGroup,
    AnmClumpPropertyGroup,
    CameraPropertyGroup,
    XfbinAnmChunkPropertyGroup,
    AnmChunksListPropertyGroup,
)

anm_chunks_classes = (
    *anm_chunks_property_groups,
    AnmChunksPropertyPanel,
    PlayAnimation
)
