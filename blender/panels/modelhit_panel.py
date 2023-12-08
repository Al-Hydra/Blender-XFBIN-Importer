from typing import List

import bpy
from bpy.props import (BoolProperty, CollectionProperty, EnumProperty,
                       FloatProperty, FloatVectorProperty, IntProperty,
                       IntVectorProperty, StringProperty)
from bpy.types import Panel, PropertyGroup

from ...xfbin_lib.xfbin.structure.nucc import ModelHit, NuccChunkModelHit
from ..common.helpers import int_to_hex_str
from .common import (EmptyPropertyGroup, IntPropertyGroup, StringPropertyGroup,
                     draw_copy_paste_ops, draw_xfbin_list, matrix_prop_group,
                     matrix_prop_search)


class ModelHitMesh(PropertyGroup):

    color: IntVectorProperty(name="Color", size=3,
                             default=(0, 0, 0), min=0, max=255)
    col_flags: IntVectorProperty(name="Flags", size=3,
                                default=(0, 0, 0), min=0, max=0xf)
    flags: IntVectorProperty(name="Flags", size=3,
                             default=(0, 0, 0), min=0, max=255)

    def init_data(self, hit_sec: ModelHit):
        self.flags = hit_sec.flags
        self.color = (
            hit_sec.flags[2] & 0xF0, hit_sec.flags[1] & 0xF0, hit_sec.flags[0] & 0xF0)
        self.col_flags = (
            hit_sec.flags[0] & 0x0F, hit_sec.flags[1] & 0x0F, hit_sec.flags[2] & 0x0F)
        
        #self.color = self.hex_to_rgb()
    
    def srgb_to_linearrgb(self, c):
        if   c < 0:       return 0
        elif c < 0.04045: return c/12.92
        else:             return ((c+0.055)/1.055)**2.4

    def hex_to_rgb(self, h,alpha=1):
        r = (h & 0xff0000) >> 16
        g = (h & 0x00ff00) >> 8
        b = (h & 0x0000ff)
        return tuple([self.srgb_to_linearrgb(c/0xff) for c in (r,g,b)] + [alpha])



class ModelHitPropertyGroup(PropertyGroup):
    path: StringProperty(name="Path")

    mesh_count: IntProperty(name="Mesh Count")

    def init_data(self, hit: NuccChunkModelHit):
        self.name = hit.name
        self.path = hit.filePath
        self.mesh_count = hit.mesh_count


class ModelHitPanel(Panel):

    bl_idname = 'OBJECT_PT_ModelHit'
    bl_label = "[XFBIN] ModelHit Properties"

    bl_space_type = "PROPERTIES"
    bl_context = "object"
    bl_region_type = "WINDOW"

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type == 'EMPTY' and obj.name.endswith('[HIT]') and obj.parent.type == 'ARMATURE'

    def draw(self, context):
        layout = self.layout
        obj = context.object
        data: ModelHitPropertyGroup = obj.xfbin_modelhit_data

        draw_copy_paste_ops(layout, 'xfbin_modelhit_data',
                            'ModelHit Properties')
        row = layout.row()
        row.prop(data, "path")


class ModelHitMeshPanel(Panel):

    bl_idname = 'OBJECT_PT_ModelHitMesh'
    bl_label = "[XFBIN] ModelHitMesh Properties"

    bl_space_type = "PROPERTIES"
    bl_context = "object"
    bl_region_type = "WINDOW"

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj

    def draw(self, context):
        layout = self.layout
        obj = context.object
        data: ModelHitMesh = obj.xfbin_modelhit_mesh_data

        draw_copy_paste_ops(layout, 'xfbin_modelhit_mesh_data',
                            'ModelHit Mesh Properties')
        row = layout.row()
        row.prop(data, "color")
        row.prop(data, "col_flags")


model_hit_property_groups = (
    ModelHitMesh,
    ModelHitPropertyGroup,
)

model_hit_classes = (
    ModelHitMesh,
    ModelHitPropertyGroup,
    ModelHitMeshPanel,
    ModelHitPanel
)
