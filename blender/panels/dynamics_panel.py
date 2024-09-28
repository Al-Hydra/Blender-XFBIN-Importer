from typing import List

import bpy, bmesh
from bpy.props import (BoolProperty, CollectionProperty, IntProperty,
                       StringProperty, FloatProperty, EnumProperty)
from bpy.types import Panel, PropertyGroup

from ...xfbin_lib.xfbin.structure.nucc import NuccChunkDynamics, Dynamics1, Dynamics2
from ..common.helpers import XFBIN_DYNAMICS_OBJ
from .common import (EmptyPropertyGroup, draw_copy_paste_ops, draw_xfbin_list,
                     matrix_prop_group, matrix_prop_search, IntPropertyGroup, StringPropertyGroup, PointerProperty, FloatPropertyGroup)


#custom ui list for spring groups

class XFBIN_UL_SpringGroups(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            row.prop(item, 'name', text='', emboss=False, icon_value=icon)
            row.prop_search(item, 'bone_spring', context.object.data, 'bones', text='')


class XFBIN_SpringGroup_OT_Add(bpy.types.Operator):
    bl_idname = 'xfbin_dyn.spring_group_add'
    bl_label = 'Add Spring Group'
    bl_description = 'Add a new spring group'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        context.object.xfbin_dynamics_data.spring_groups.add()
        context.object.xfbin_dynamics_data.sg_index = len(context.object.xfbin_dynamics_data.spring_groups) - 1
        return {'FINISHED'}


class XFBIN_SpringGroup_OT_Remove(bpy.types.Operator):
    bl_idname = 'xfbin_dyn.spring_group_remove'
    bl_label = 'Remove Spring Group'
    bl_description = 'Remove the selected spring group'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        data: DynamicsPropertyGroup = context.object.xfbin_dynamics_data
        data.spring_groups.remove(data.sg_index)

        if data.sg_index >= len(data.spring_groups):
            data.sg_index = len(data.spring_groups) - 1
        return {'FINISHED'}


class XFBIN_SpringGroup_OT_Move(bpy.types.Operator):
    bl_idname = 'xfbin_dyn.spring_group_move'
    bl_label = 'Move Spring Group'
    bl_description = 'Move the selected spring group up or down in the list'
    bl_options = {'REGISTER', 'UNDO'}

    direction: EnumProperty(
        items=(
            ('UP', 'Up', ''),
            ('DOWN', 'Down', ''),
        ),
        name='Direction',
    )

    def execute(self, context):
        data: DynamicsPropertyGroup = context.object.xfbin_dynamics_data
        index = data.sg_index
        if self.direction == 'UP':
            data.spring_groups.move(index, index - 1)
            data.sg_index -= 1
        elif self.direction == 'DOWN':
            data.spring_groups.move(index, index + 1)
            data.sg_index += 1
        return {'FINISHED'}


class XFBIN_SpringGroup_OT_Copy(bpy.types.Operator):
    bl_idname = 'xfbin_dyn.spring_group_copy'
    bl_label = 'Copy Spring Group'
    bl_description = 'Copy the selected spring group'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        data: DynamicsPropertyGroup = context.object.xfbin_dynamics_data
        bpy.context.scene.xfbin_dynamics_clipboard.copy_spring_group(data.spring_groups[data.sg_index])
        #set the index to the last item in the list
        data.sg_index = len(data.spring_groups) - 1

        return {'FINISHED'}


class XFBIN_SpringGroup_OT_Paste(bpy.types.Operator):
    bl_idname = 'xfbin_dyn.spring_group_paste'
    bl_label = 'Paste Spring Group'
    bl_description = 'Paste the copied spring group'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        data: DynamicsPropertyGroup = context.object.xfbin_dynamics_data

        sg = data.spring_groups.add()
        for k, v in bpy.context.scene.xfbin_dynamics_clipboard.spring_groups_clipboard.items():
            sg[k] = v
        return {'FINISHED'}


class XFBIN_UL_CollisionGroups(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            row.prop(item, 'name', text='', emboss=False, icon_value=icon)
            row.prop_search(item, 'bone_collision', context.object.data, 'bones', text='')


class XFBIN_CollisionGroup_OT_Add(bpy.types.Operator):
    bl_idname = 'xfbin_dyn.collision_group_add'
    bl_label = 'Add Collision Group'
    bl_description = 'Add a new collision group'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        context.object.xfbin_dynamics_data.collision_spheres.add()
        context.object.xfbin_dynamics_data.cs_index = len(context.object.xfbin_dynamics_data.collision_spheres) - 1
        return {'FINISHED'}


class XFBIN_CollisionGroup_OT_Remove(bpy.types.Operator):
    bl_idname = 'xfbin_dyn.collision_group_remove'
    bl_label = 'Remove Collision Group'
    bl_description = 'Remove the selected collision group'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        data: DynamicsPropertyGroup = context.object.xfbin_dynamics_data
        data.collision_spheres.remove(data.cs_index)

        if data.cs_index >= len(data.collision_spheres):
            data.cs_index = len(data.collision_spheres) - 1
        return {'FINISHED'}
    
class XFBIN_CollisionGroup_OT_Move(bpy.types.Operator):
    bl_idname = 'xfbin_dyn.collision_group_move'
    bl_label = 'Move Collision Group'
    bl_description = 'Move the selected collision group up or down in the list'
    bl_options = {'REGISTER', 'UNDO'}

    direction: EnumProperty(
        items=(
            ('UP', 'Up', ''),
            ('DOWN', 'Down', ''),
        ),
        name='Direction',
    )

    def execute(self, context):
        data: DynamicsPropertyGroup = context.object.xfbin_dynamics_data
        index = data.cs_index
        if self.direction == 'UP':
            data.collision_spheres.move(index, index - 1)
            data.cs_index -= 1
        elif self.direction == 'DOWN':
            data.collision_spheres.move(index, index + 1)
            data.cs_index += 1
        return {'FINISHED'}
    
class XFBIN_CollisionGroup_OT_Copy(bpy.types.Operator):
    bl_idname = 'xfbin_dyn.collision_group_copy'
    bl_label = 'Copy Collision Group'
    bl_description = 'Copy the selected collision group'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        data: DynamicsPropertyGroup = context.object.xfbin_dynamics_data
        bpy.context.scene.xfbin_dynamics_clipboard.copy_collision_group(data.collision_spheres[data.cs_index])
        #set the index to the last item in the list
        data.cs_index = len(data.collision_spheres) - 1

        return {'FINISHED'}
    
class XFBIN_CollisionGroup_OT_Paste(bpy.types.Operator):
    bl_idname = 'xfbin_dyn.collision_group_paste'
    bl_label = 'Paste Collision Group'
    bl_description = 'Paste the copied collision group'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        data: DynamicsPropertyGroup = context.object.xfbin_dynamics_data

        col = data.collision_spheres.add()
        for k, v in bpy.context.scene.xfbin_dynamics_clipboard.collision_spheres_clipboard.items():
            col[k] = v
        return {'FINISHED'}
    



class SpringGroupsPropertyGroup(PropertyGroup):

    def update_count(self, context):
        extra = self.bone_count - len(self.flags)
        if extra > 0:
            for _ in range(extra):
                self.flags.add()
        elif extra < 0:
            for _ in range(abs(extra)):
                self.flags.remove(len(self.flags) - 1)
        else:
            return
    
    
    def spring_bone_update(self, context):
        if not self.init_done:
            return
        
        armature_obj = context.object
        bone = armature_obj.data.bones.get(self.bone_spring)
        sg_list = [sg for sg in context.object.xfbin_dynamics_data.spring_groups]
        sg_list.pop(context.object.xfbin_dynamics_data.sg_index)
        if bone:
            
            #check if one of the bones in the spring group has more than one child
            for child in bone.children_recursive:
                if len(child.children) > 1:
                    self.name = f'({child.name}) a child of ({bone.name}) has more than one child'
                    self.bone_count = 0
                    return
            
            #check if this bone or one of its children is already in a spring group
            for s in sg_list:
                
                #check if the bone is already in a spring group
                if s.bone_spring == bone.name:
                    self.name = f'({bone.name}) is already in a spring group'
                    return                

                #check if the bone is a child of a bone in a spring group
                elif bone in armature_obj.data.bones[s.bone_spring].children_recursive:
                    self.name = f'({bone.name}) is a child of ({s.bone_spring}) which is already in a spring group'
                    self.bone_count = 0
                    return
                
            #update the bone index, count and name
            self.bone_count = len(bone.children_recursive) + 1
            self.name = f'{bone.name}'
            self.spring_group_index = 0
        else:
            self.name = f'{self.bone_spring} is not a valid bone'
            self.bone_count = 0
            return
        

    bone_index: IntProperty(
        name='Bone Index',
    )

    bone_count: IntProperty(
        name='Bones Count',
        update= update_count
    )

    dyn1: FloatProperty(
        name='Bounciness',
        default=0.6
    )

    dyn2: FloatProperty(
        name='Elasticity',
        default=0.8
    )

    dyn3: FloatProperty(
        name='Stiffness',
        default=0.3
    )

    dyn4: FloatProperty(
        name='Movement',
        default=1
    )
    flags: CollectionProperty(
        type = IntPropertyGroup,
        name='Bone flag',
    )

    bone_spring: StringProperty(
        name= 'Bone',
        update= spring_bone_update
    )
    
    spring_group_index: IntProperty(
        name= 'Spring Group Index'
    )

    maintain_shape: BoolProperty(
        name='Maintain Shape',
    )

    init_done: BoolProperty(
        default= True
    )

    def update_name(self):
        self.name = 'Spring Group'

    def init_data(self, sgroup: Dynamics1):
        self.bone_index = sgroup.coord_index
        self.bone_count = sgroup.BonesCount
        self.dyn1 = sgroup.Bounciness
        self.dyn2 = sgroup.Elasticity
        self.dyn3 = sgroup.Stiffness
        self.dyn4 = sgroup.Movement
        self.spring_group_index = 0
        

        self.flags.clear()
        for flag in sgroup.shorts:
            f = self.flags.add()
            f.value = flag
            if flag & 2:
                self.maintain_shape = True
class CollisionSpheresPropertyGroup(PropertyGroup):

    def update_count(self, context):
        if not self.init_done:
            return
        extra = self.attached_count - len(self.attached_groups)
        if extra > 0:
            for _ in range(extra):
                self.attached_groups.add()
        elif extra < 0:
            for _ in range(abs(extra)):
                self.attached_groups.remove(len(self.attached_groups) - 1)
        else:
            return

    def collision_bone_update(self, context):
        if not self.init_done:
            return
        armature_obj = ''
        for obj in bpy.data.objects:
            if obj.type == 'ARMATURE' and obj.xfbin_clump_data.path == context.object.xfbin_dynamics_data.path:
                armature_obj = obj
        #col_count = len(context.object.xfbin_dynamics_data.collision_spheres)

        #find the group index
        col_count = 0
        for i, c in enumerate(context.object.xfbin_dynamics_data.collision_spheres):
            if c.name == self.name:
                col_count = i + 1
        if armature_obj != '':
            for i, b in enumerate(armature_obj.data.bones):
                if b.name == self.bone_collision:
                    self.bone_index = i
                    self.name = f'Collision Group {col_count - 1} [{b.name}]'

    offset_x: FloatProperty(
        name='X Offset',
    )

    offset_y: FloatProperty(
        name='Y Offset',
    )

    offset_z: FloatProperty(
        name='Z Offset',
    )

    scale_x: FloatProperty(
        name='X Scale',
        default= 10.0
    )

    scale_y: FloatProperty(
        name='Y Scale',
        default= 10.0
    )

    scale_z: FloatProperty(
        name='Z Scale',
        default= 10.0
    )

    bone_index: IntProperty(
    name='Bone Index',
    )

    attach_groups: BoolProperty(
        name='Attach Spring Groups',
    )

    attached_count: IntProperty(
        name='Attached Spring Groups Count',
        update= update_count,
        default= 0,
        min = 0,
        max = 65535
    )

    attached_groups: CollectionProperty(
        type = SpringGroupsPropertyGroup,
        name='Attached Spring Groups',
    )

    bone_collision: StringProperty(
        name= 'Bone',
        update= collision_bone_update
    )

    sg_enum: StringProperty(
        name='Spring Group')
    
    init_done: BoolProperty(
        default= True
    )

    def update_name(self):
        self.name = 'Collision Group'

        

    def init_data(self, colsphere: Dynamics2):
        #offset values
        self.offset_x = colsphere.offset_x
        self.offset_y = colsphere.offset_y
        self.offset_z = colsphere.offset_z
        #scale values
        self.scale_x = colsphere.scale_x
        self.scale_y = colsphere.scale_y
        self.scale_z = colsphere.scale_z
        #rest of the values
        self.bone_index = colsphere.coord_index
        self.attach_groups = colsphere.attach_groups

        if self.attach_groups == 0:
            self.attach_groups = False
        elif self.attach_groups == 1:
            self.attach_groups = True

        #attached spring groups
        self.attached_count = colsphere.attached_groups_count
        '''self.attached_groups.clear()
        for group in colsphere.attached_groups:
            g = self.attached_groups.add()
            g.value = str(group)'''
        
        

class DynamicsPropertyGroup(PropertyGroup):

    path: StringProperty(
        name='Chunk Path',
        description='',
    )

    clump_name: StringProperty(
        name='Clump Name',
    )

    sg_count: IntProperty(
        name='Spring Groups Count',
    )

    cs_count: IntProperty(
        name='Collision Spheres Count',
    )

    spring_groups: CollectionProperty(
        type=SpringGroupsPropertyGroup,
    )

    sg_index: IntProperty()

    collision_spheres: CollectionProperty(
        type=CollisionSpheresPropertyGroup,
    )

    cs_index: IntProperty()

    name: StringProperty(
    )

    use_constraints: BoolProperty(
        name='Use Constraints',
        default= False
    )

    def bonename(self, index, clump):
        return bpy.data.objects[f'{clump}'].data.bones[index].name

    def init_data(self,context, dynamics: NuccChunkDynamics):
        self.path = dynamics.filePath

        # Set the properties
        self.name = self.clump_name = dynamics.clump_chunk.name

        self.sg_count = dynamics.SPGroupCount
        self.cs_count = dynamics.ColSphereCount
        
        # Add spring groups
        self.spring_groups.clear()
        for sgroup in dynamics.SPGroup:
            s: SpringGroupsPropertyGroup = self.spring_groups.add()
            s.init_done = False
            s.init_data(sgroup)
            s.bone_spring = s.name = context.object.data.bones[sgroup.coord_index].name
            s.init_done = True

        sorted_spring_groups = sorted(self.spring_groups, key= lambda x: x.bone_index)
        # Add collision groups
        self.collision_spheres.clear()
        for i, colsphere in enumerate(dynamics.ColSphere):
            c: CollisionSpheresPropertyGroup = self.collision_spheres.add()
            c.init_done = False
            c.init_data(colsphere)
            c.bone_collision = context.object.data.bones[colsphere.coord_index].name
            c.name = f'Collision Group {i} [{c.bone_collision}]'
            if colsphere.attach_groups == 1:
                c.attach_groups = True
                for index in colsphere.attached_groups:
                    g = c.attached_groups.add()
                    g.bone_spring = sorted_spring_groups[index].name
            c.init_done = True
        
        

class DynamicsPropertyPanel(Panel):

    bl_idname = 'OBJECT_PT_xfbin_dynamics'
    bl_label = '[XFBIN] Dynamics Properties'

    bl_space_type = 'PROPERTIES'
    bl_context = 'physics'
    bl_region_type = 'WINDOW'

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type == 'EMPTY' and obj.parent is None and obj.name.startswith(XFBIN_DYNAMICS_OBJ) or obj.type == 'ARMATURE'

    def draw(self, context):
        obj = context.object
        layout = self.layout
        data: DynamicsPropertyGroup = obj.xfbin_dynamics_data
        
        draw_copy_paste_ops(layout, 'xfbin_dynamics_data', 'Dynamics Properties')

        box = layout.box()
        box.label(text='Spring Groups')
        #draw_xfbin_list(layout, 0, data, f'xfbin_dynamics_data', 'spring_groups', 'sg_index')
        col = box.column()
        row = col.row()
        row.template_list('XFBIN_UL_SpringGroups', '', data, 'spring_groups', data, 'sg_index')
        col = row.column(align=True)
        col.operator(XFBIN_SpringGroup_OT_Add.bl_idname, icon='ADD', text='')
        col.operator(XFBIN_SpringGroup_OT_Remove.bl_idname, icon='REMOVE', text='')
        col.operator(XFBIN_SpringGroup_OT_Copy.bl_idname, icon='COPYDOWN', text='')
        col.operator(XFBIN_SpringGroup_OT_Paste.bl_idname, icon='PASTEDOWN', text='')
        col.operator(XFBIN_SpringGroup_OT_Move.bl_idname, icon='TRIA_UP', text='').direction = 'UP'
        col.operator(XFBIN_SpringGroup_OT_Move.bl_idname, icon='TRIA_DOWN', text='').direction = 'DOWN'

        box = layout.box()
        row = box.row()
        row.operator(XFBIN_OT_AddBoneToSpringGroup.bl_idname)
        row.operator(SpringGroupSelectBone.bl_idname)

        sg_index = data.sg_index


        if data.spring_groups and sg_index >= 0:
            spring_groups: SpringGroupsPropertyGroup = data.spring_groups[sg_index]
            box = layout.box()
            row = box.row()
            row.prop(spring_groups, 'dyn1')
            row.prop(spring_groups, 'dyn2')
            row.prop(spring_groups, 'dyn3')
            row.prop(spring_groups, 'dyn4')
            row.prop(spring_groups, 'maintain_shape')
            #matrix_prop_group(box, spring_groups, 'flags', spring_groups.bone_count, 'Bone Flags')

        
        layout.label(text='Collision Groups')
        #draw_xfbin_list(layout, 1, data, f'xfbin_dynamics_data', 'collision_spheres', 'cs_index')
        row = layout.row()
        col = row.column()
        col.template_list('XFBIN_UL_CollisionGroups', '', data, 'collision_spheres', data, 'cs_index')
        cs_index = data.cs_index
        col = row.column(align=True)
        col.operator(XFBIN_CollisionGroup_OT_Add.bl_idname, icon='ADD', text='')
        col.operator(XFBIN_CollisionGroup_OT_Remove.bl_idname, icon='REMOVE', text='')
        col.operator(XFBIN_CollisionGroup_OT_Copy.bl_idname, icon='COPYDOWN', text='')
        col.operator(XFBIN_CollisionGroup_OT_Paste.bl_idname, icon='PASTEDOWN', text='')
        col.operator(XFBIN_CollisionGroup_OT_Move.bl_idname, icon='TRIA_UP', text='').direction = 'UP'
        col.operator(XFBIN_CollisionGroup_OT_Move.bl_idname, icon='TRIA_DOWN', text='').direction = 'DOWN'



        if data.collision_spheres:
            collision_spheres: CollisionSpheresPropertyGroup = data.collision_spheres[cs_index]
            box = layout.box()
            row = box.row()
            row.operator(CollisionsLiveEdit.bl_idname)
            row.prop(data, 'use_constraints')
            row = box.row()
            row.prop(collision_spheres, 'offset_x')
            row.prop(collision_spheres, 'offset_y')
            row.prop(collision_spheres, 'offset_z')
            row = box.row()
            row.prop(collision_spheres, 'scale_x')
            row.prop(collision_spheres, 'scale_y')
            row.prop(collision_spheres, 'scale_z')
            row = box.row()
            row.prop(collision_spheres, 'attach_groups')
            row.prop(collision_spheres, 'attached_count')
            
            if collision_spheres.attach_groups == True and collision_spheres.attached_count > 0:
                row = box.row()
                for i in range(collision_spheres.attached_count):
                    row = box.row()
                    row.prop_search(collision_spheres.attached_groups[i], 'bone_spring', data, 'spring_groups', text='')
                #matrix_prop_search(box, collision_spheres, 'attached_groups', data, 'spring_groups', collision_spheres.attached_count, 'Attached Spring Groups')
                    
                

class XfbinDynamicsClipboardPropertyGroup(PropertyGroup):

    spring_groups_clipboard: PointerProperty(type=SpringGroupsPropertyGroup)
    spring_group_values: CollectionProperty(type=FloatPropertyGroup)

    collision_spheres_clipboard: PointerProperty(type=CollisionSpheresPropertyGroup)
    collision_sphere_values: CollectionProperty(type=FloatPropertyGroup)

    dynamics_clipboard: PointerProperty(type=DynamicsPropertyGroup)

    def copy_spring_group(self, spring_group: SpringGroupsPropertyGroup):
        for k,v in spring_group.items():
            self.spring_groups_clipboard[k] = v
    
    def copy_collision_group(self, collision_group: CollisionSpheresPropertyGroup):
        for k,v in collision_group.items():
            self.collision_spheres_clipboard[k] = v
    
    

class XFBIN_OT_AddBoneToSpringGroup(bpy.types.Operator):
    bl_idname = 'xfbin_dyn.add_bone_to_spring_group'
    bl_label = 'Add Selected Bones as Spring Groups'
    bl_description = 'Add selected bones in pose mode as spring groups'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        return context.object and context.object.type == 'ARMATURE' and context.mode == 'POSE'

    def execute(self, context):
        data: DynamicsPropertyGroup = context.object.xfbin_dynamics_data
        
        
        armature_obj = context.object
        for bone in context.selected_pose_bones:
            continue_add = True
            
            if bone.name in [sg.bone_spring for sg in data.spring_groups]:
                self.report({'ERROR'}, f'({bone.name}) is already in a spring group')
                continue
            
            else:
                if bone.children:
                    if len(bone.children) > 1:
                        self.report({'ERROR'}, f'({bone.name}) has more than one child. THIS WILL CAUSE ISSUES')
                        
                    for child in bone.children:
                        if len(child.children) > 1:
                            self.report({'ERROR'}, f'({child.name}) a child of ({bone.name}) has more than one child. THIS WILL CAUSE ISSUES')
                            continue
                    
                #check if the bone or one of its children is already in a spring group
                for sg in data.spring_groups:
                    if bone in armature_obj.pose.bones[sg.bone_spring].children_recursive:
                        self.report(
                            {'ERROR'}, f'({bone.name}) is a child of ({sg.bone_spring}) which is already in a spring group')
                        continue_add = False
                        continue
                
                if not continue_add:
                    continue

                sg = data.spring_groups.add()
                sg.bone_spring = sg.name = bone.name
                sg.spring_bone_update(context)
                data.sg_index = len(data.spring_groups) - 1


        return {'FINISHED'}


class update_dynamics(bpy.types.Operator):
    bl_idname = "object.update_dynamics"
    bl_label = "Update Dynamics"
    bl_description = "Update Spring and Collision groups. You must click this button whenever you make changes"
    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type == 'EMPTY' and obj.parent is None and obj.name.startswith(XFBIN_DYNAMICS_OBJ) or obj.type == "ARMATURE"
    def execute(self, context):
        for obj in bpy.data.objects:
            if obj.type == 'ARMATURE' and obj.xfbin_clump_data.path == context.object.xfbin_dynamics_data.path:
                armature_obj = obj
        
        #find dynamics objects
        dyn_objs = [o for o in bpy.data.objects if o.name.startswith(XFBIN_DYNAMICS_OBJ)]

        def update(dynamics_object):
            #update spring groups
            for index, sp in enumerate(sorted(dynamics_object.xfbin_dynamics_data.spring_groups, key= lambda x: x.bone_index)):
                #check if the bone exists
                if sp.bone_spring not in armature_obj.data.bones:
                        self.report(
                        {'WARNING'}, f'Spring Group "{sp.bone_spring}" Could not be found in "{armature_obj.name}". Please remove it')
                
                #update bone index, count and name
                for i, b in enumerate(armature_obj.data.bones):
                    if sp.bone_spring == b.name:
                        sp.bone_index = i
                        sp.bone_count = len(b.children_recursive) + 1
                        sp.name = f'Spring Group [{b.name}]'
                        sp.spring_group_index = index
                        if len(sp.flags) > sp.bone_count:
                            for i in range(sp.flags - sp.bone_count):
                                sp.flags.remove(len(sp.flags) - 1)
                        elif len(sp.flags) < sp.bone_count:
                            for i in range(sp.bone_count - sp.flags):
                                sp.flags.add()
                        
                        

            #update collision groups
            for index, col in enumerate(dynamics_object.xfbin_dynamics_data.collision_spheres):
                if col.bone_collision not in armature_obj.data.bones:
                    self.report(
                        {'WARNING'}, f'Collision Group "{col.bone_collision}" Could not be found in "{armature_obj.name}". Please remove it')
                #check if the attached spring group exists in the dynamics object
                if len(col.attached_groups) > 0:
                    for ag in col.attached_groups:
                        if dynamics_object.xfbin_dynamics_data.spring_groups.get(ag.value) is None:
                            self.report(
                                {'WARNING'}, f'Attached Group "{ag.value}" in "{col.name}" Could not be found. Please remove it')
                
                #update bone index and name
                for i, b in enumerate(armature_obj.data.bones):
                    if col.bone_collision in armature_obj.data.bones and col.bone_collision == b.name:
                        col.bone_index = i
                        col.name = f'Collision Group {index} [{b.name}]'
                
                #check if there's a collision object for this group then use its coordinates
                colobj = context.view_layer.objects.get(col.name)
                if colobj:
                    col.offset_x = colobj.location.x * 100
                    col.offset_y = colobj.location.y * 100
                    col.offset_z = colobj.location.z * 100
                    col.scale_x = colobj.scale.x
                    col.scale_y = colobj.scale.y
                    col.scale_z = colobj.scale.z


        #try to only update the active dynamics object
        if len(dyn_objs) < 1:
            self.report({'WARNING'}, f'There is no dnyamics chunk object in this collection {bpy.context.collection.name}')
        elif context.object in dyn_objs:
            update(context.object)
        else:
            for dyn in dyn_objs:
                update(dyn)
        
        return {'FINISHED'}

class MakeCollisions(bpy.types.Operator):
    bl_idname = "object.collisions"
    bl_label = "Make Collision Objects"
    bl_description = 'Create a representation of collisions in blender'
    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type == 'EMPTY' and obj.parent is None and obj.name.startswith(XFBIN_DYNAMICS_OBJ) or obj.type == "ARMATURE"
    def execute(self, context):
        collection_name = f'{bpy.context.object.xfbin_dynamics_data.clump_name} Collision'

        #Remove any collection that has the same name and its objects
        for c in bpy.data.collections:
            if c.name.startswith(collection_name):
                if len(c.objects) > 0:
                    for o in c.objects:
                        bpy.data.objects.remove(o)
                bpy.data.collections.remove(c)

        collection = bpy.data.collections.new(collection_name)

        clump = bpy.context.object.xfbin_dynamics_data.clump_name

        bpy.context.scene.collection.children.link(collection)

        for col in bpy.context.object.xfbin_dynamics_data.collision_spheres:
            #Adds an empty sphere with the correct size
            mesh = bpy.data.meshes.new(col.name)
            bm = bmesh.new()
            bmesh.ops.create_icosphere(bm, subdivisions = 2, radius= 0.01)
            bm.to_mesh(mesh)
            bm.free()
            sphere = bpy.data.objects.new(col.name, mesh)
            
            #Link the new object we create to the collection
            collection.objects.link(sphere)
            
            #Add object constraint to attach the sphere
            con = sphere.constraints.new(type= 'CHILD_OF')
            con.name = f'{col.name} Child Of {clump}'
            con.target = bpy.data.objects[clump]
            con.subtarget = bpy.data.objects[clump].data.bones[col.bone_collision].name
            
            #set inverse to false
            con.set_inverse_pending = False

            #Add wireframe modifier
            mod = sphere.modifiers.new('Collision Wireframe', 'WIREFRAME')
            mod.thickness =  0.0001
            
            #Add a material
            matname = col.name
            if matname in bpy.data.materials:
                bpy.data.materials.remove(bpy.data.materials.get(matname))
            
            mat = bpy.data.materials.new(matname)
            mat.use_nodes = True
            mat.node_tree.nodes.remove(mat.node_tree.nodes['Principled BSDF'])
            output = mat.node_tree.nodes.get('Material Output')
            rgb = mat.node_tree.nodes.new('ShaderNodeRGB')
            if col.attach_groups == True and col.attached_count > 0:
                rgb.outputs[0].default_value = (0.8, 0.075, 0.7, 1)
            else:
                rgb.outputs[0].default_value = (0.02, 0.04, 0.8, 1)
            mat.node_tree.links.new(rgb.outputs[0], output.inputs[0])
            mat.shadow_method = 'NONE'

            #link material
            sphere.data.materials.append(mat)
            
            #Set the empty as the active object
            bpy.ops.object.select_all(action='DESELECT')
            sphere.select_set(True)
            bpy.context.view_layer.objects.active = sphere
        
            #use collision group info to represent the sphere
            sphere.scale = (col.scale_x, col.scale_y, col.scale_z)
            sphere.location = (col.offset_x * 0.01, col.offset_y * 0.01, col.offset_z * 0.01)

            #Create an empty mesh to view the local xyz axes
            axes = bpy.data.objects.new(f'{col.name} XYZ', None)
            axes.empty_display_type = 'ARROWS'
            axes.empty_display_size = 0.01
            collection.objects.link(axes)
            
            #add constraints
            con2 = axes.constraints.new(type= 'CHILD_OF')
            con2.name = f'Child Of {axes.name}'
            con2.target = bpy.data.objects[sphere.name]
            #Don't set inverse
            con2.set_inverse_pending = False

            
            
        return {'FINISHED'}

class UpdateCollision(bpy.types.Operator):
    bl_idname = "object.update_coliision"
    bl_label = "Use object coordinates"
    bl_description = 'Copy the position and scale info from an existing collision object'
    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type == 'EMPTY' and obj.parent is None and obj.name.startswith(XFBIN_DYNAMICS_OBJ) or obj.type == "ARMATURE"
    def execute(self, context):
        
        cs_index = context.object.xfbin_dynamics_data.cs_index
        colgroup = context.object.xfbin_dynamics_data.collision_spheres
        name = colgroup[cs_index].name
        if colgroup[cs_index]:
            obj = context.view_layer.objects.get(colgroup[cs_index].name)
            if obj:
                colgroup[cs_index].offset_x = obj.location[0] * 100
                colgroup[cs_index].offset_y = obj.location[1] * 100
                colgroup[cs_index].offset_z = obj.location[2] * 100
                colgroup[cs_index].scale_x = obj.scale[0]
                colgroup[cs_index].scale_y = obj.scale[1]
                colgroup[cs_index].scale_z = obj.scale[2]
            else:
                self.report({"WARNING"}, 'Collision object was not found, use (Make Collisions) button to create it')

        return {'FINISHED'}


class SpringGroupSelectBone(bpy.types.Operator):
    bl_idname = "object.spring_group_select_bone"
    bl_label = "Select Bone"
    bl_description = 'Select the bone in the armature'
    @classmethod
    def poll(cls, context):
        obj = context.object
        #check if we're in pose mode
        if context.mode != 'POSE':
            return False
        return obj.type == "ARMATURE"
    def execute(self, context):
        data: DynamicsPropertyGroup = context.object.xfbin_dynamics_data
        bone = data.spring_groups[data.sg_index].bone_spring
        if bone in context.object.pose.bones:
            context.object.pose.bones[bone].bone.select = True
        else:
            self.report({'ERROR'}, f'{bone} is not a valid bone')
        return {'FINISHED'}


class CollisionsLiveEdit(bpy.types.Operator):
    bl_idname = "object.collisions_live_edit"
    bl_label = "Live Edit Collision Objects"
    bl_description = 'Edit the collision objects in real time'

    main_armature: None
    dyn_armature: None

    @classmethod
    def poll(cls, context):
        return context.mode == "POSE" and context.object.type == "ARMATURE"
        
    def execute(self, context):
        dynamics_data: DynamicsPropertyGroup = context.object.xfbin_dynamics_data
        spring_groups = dynamics_data.spring_groups
        collision_spheres = dynamics_data.collision_spheres
        self.main_armature = context.object

        #get the parent collection
        xfbin_collection = context.object.users_collection[0]
        
        #make an icosphere to be used as shape
        if 'XFBIN Collision Sphere' not in bpy.data.meshes:
            mesh = bpy.data.meshes.new('XFBIN Collision Sphere')
            bm = bmesh.new()
            bmesh.ops.create_icosphere(bm, subdivisions = 2, radius= 1)
            bm.to_mesh(mesh)
            bm.free()
        else:
            mesh = bpy.data.meshes['XFBIN Collision Sphere']
        
        if 'XFBIN Collision Sphere' not in bpy.data.objects:
            sphere = bpy.data.objects.new('XFBIN Collision Sphere', mesh)        

        #check if a skeleton for dynamics exists
        self.dyn_armature = xfbin_collection.get(f'{context.object.name}_Dynamics')
        if self.dyn_armature is None:
            data_armature = bpy.data.armatures.new(f'{context.object.name}_Dynamics')
            self.dyn_armature = bpy.data.objects.new(f'{context.object.name}_Dynamics', data_armature)

            #link the armature to the collection
            xfbin_collection.objects.link(self.dyn_armature)
        
        #make sure that we are in object mode
        bpy.ops.object.mode_set(mode='OBJECT')

        #set the dynamics armature as the active object
        bpy.context.view_layer.objects.active = self.dyn_armature
        self.dyn_armature.select_set(True)

        #clear the armature
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.armature.select_all(action='DESELECT')
        bpy.ops.armature.delete()
        
        #add bones for each collision sphere
        for col in collision_spheres:
            bone = self.dyn_armature.data.edit_bones.new(col.name)
            #get the parent bone matrix
            parent_name = col.bone_collision
            parent = context.object.data.bones.get(parent_name)
            bone.head = (0, 0, 0)
            bone.tail = (0, 0.001, 0)
            bone.use_deform = False
        

        #make sure that we are in object mode
        bpy.ops.object.mode_set(mode='POSE')

        for col in collision_spheres:
            col: CollisionSpheresPropertyGroup
            bone = self.dyn_armature.pose.bones.get(col.name)
            if bone:
                bone.custom_shape = bpy.data.objects['XFBIN Collision Sphere']
                #set wireframe
                if col.attach_groups:
                    bone.color.palette = 'CUSTOM'
                    #Set normal color
                    bone.color.custom.normal = (0.8, 0.075, 0.7)
                    #Set selected color
                    bone.color.custom.select = (0.9, 0.31, 0.7)
                    #set active color
                    bone.color.custom.active = (1, 0.46, 0.7)
                else:
                    bone.color.palette = 'CUSTOM'
                    #Set normal color
                    bone.color.custom.normal = (0.02, 0.04, 0.8)
                    #Set selected color
                    bone.color.custom.select = (0.02, 0.32, 0.8)
                    #set active color
                    bone.color.custom.active = (0.02, 0.57, 0.8)
                bone.bone.show_wire = True
                bone.use_custom_shape_bone_size = False
                bone.location = (col.offset_x * 0.01, col.offset_y * 0.01, col.offset_z * 0.01)
                bone.scale = (col.scale_x * 0.01, col.scale_y * 0.01, col.scale_z * 0.01)


                copy_transforms = bone.constraints.new('COPY_TRANSFORMS')
                copy_transforms.target = context.object
                copy_transforms.subtarget = col.bone_collision
                copy_transforms.mix_mode = 'BEFORE'

                if col.attach_groups and dynamics_data.use_constraints:
                    for sg in col.attached_groups:
                        if sg.bone_spring in spring_groups:
                            sg: SpringGroupsPropertyGroup
                            #get the last child in the spring group
                            last_child = self.main_armature.pose.bones[sg.bone_spring].children_recursive[-1]

                            #clear constraints
                            '''for c in last_child.constraints:
                                last_child.constraints.remove(c)'''
                            
                            #check if a constraint already exists
                            if last_child.constraints.get(f'{col.name} IK') is None:

                                #set IK constraint
                                ik = last_child.constraints.new('IK')
                                ik.name = f'{col.name} IK'
                            else:
                                ik = last_child.constraints.get(f'{col.name} IK')

                            ik.target = self.dyn_armature
                            ik.subtarget = bone.name
                            ik.chain_count = len(self.main_armature.pose.bones[sg.bone_spring].children_recursive) + 1
        

        self._timer = context.window_manager.event_timer_add(0.1, window=context.window)
        context.window_manager.modal_handler_add(self)
        self.report({'INFO'}, 'Press ESC to cancel')
        return {'RUNNING_MODAL'}
    
    def modal(self, context, event):
        if event.type == 'ESC':
            return self.cancel(context)
        
        #if the context mode is not pose mode then cancel
        if context.mode != 'POSE':
            return self.cancel(context)
        
        if event.type == 'TIMER':
            try:
                active_pose_bone = context.active_pose_bone
                active_index = self.dyn_armature.pose.bones.find(active_pose_bone.name)
            except:
                active_pose_bone = None
                active_index = -1
            for col in self.dyn_armature.pose.bones:
                #find the collision group
                if col.name in self.main_armature.xfbin_dynamics_data.collision_spheres:
                    colgroup = self.main_armature.xfbin_dynamics_data.collision_spheres[col.name]
                    #set the list index
                    self.main_armature.xfbin_dynamics_data.cs_index = active_index
                    
                    colgroup.offset_x = col.location[0] * 100
                    colgroup.offset_y = col.location[1] * 100
                    colgroup.offset_z = col.location[2] * 100
                    colgroup.scale_x = col.scale[0] * 100
                    colgroup.scale_y = col.scale[1] * 100
                    colgroup.scale_z = col.scale[2] * 100
            

            for k, v in self.main_armature.xfbin_dynamics_data.items():
                self.dyn_armature.xfbin_dynamics_data[k] = v
            
            self.dyn_armature.xfbin_dynamics_data.cs_index = self.main_armature.xfbin_dynamics_data.cs_index
                
            
        return {'PASS_THROUGH'}
    
    def cancel(self, context):
        context.window_manager.event_timer_remove(self._timer)
         #swap to object mode
        bpy.ops.object.mode_set(mode='OBJECT')
        #remove the armature
        bpy.data.objects.remove(self.dyn_armature)
        #set the main armature as the active object
        context.view_layer.objects.active = self.main_armature

        #remove constraints
        '''for bone in self.main_armature.pose.bones:
            for c in bone.constraints:
                bone.constraints.remove(c)'''
        return {'CANCELLED'}

dynamics_chunks_property_groups = (
    SpringGroupsPropertyGroup,
    CollisionSpheresPropertyGroup,
    DynamicsPropertyGroup,
    XfbinDynamicsClipboardPropertyGroup
)

dynamics_chunks_classes = (
    *dynamics_chunks_property_groups,
    XFBIN_UL_SpringGroups,
    XFBIN_SpringGroup_OT_Add,
    XFBIN_SpringGroup_OT_Remove,
    XFBIN_SpringGroup_OT_Move,
    XFBIN_SpringGroup_OT_Copy,
    XFBIN_SpringGroup_OT_Paste,
    XFBIN_OT_AddBoneToSpringGroup,
    XFBIN_UL_CollisionGroups,
    XFBIN_CollisionGroup_OT_Add,
    XFBIN_CollisionGroup_OT_Remove,
    XFBIN_CollisionGroup_OT_Move,
    XFBIN_CollisionGroup_OT_Copy,
    XFBIN_CollisionGroup_OT_Paste,
    DynamicsPropertyPanel,
    update_dynamics,
    SpringGroupSelectBone,
    CollisionsLiveEdit
)