import bpy
from bpy.props import (BoolProperty, CollectionProperty, FloatProperty, PointerProperty,
                       FloatVectorProperty, IntProperty, StringProperty, EnumProperty)
from bpy.types import Object, Panel, PropertyGroup



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
    '''xfbin_materials : CollectionProperty(
        type=XfbinSceneMaterialPropertyGroup,
        name='XFBIN Materials',
    )
    
    xfbin_material_index: IntProperty(
        name='XFBIN Material Index',
    )'''


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
        '''row.label(text='Scene Materials:')
        
        row = box.row()
        # list
        row.template_list("XFBIN_UL_SceneMaterials", "", xfbin_scene_manager, "xfbin_materials", xfbin_scene_manager, "xfbin_material_index")
        col = row.column(align=True)
        col.operator("xfbin_mat.shader_add", icon='ADD', text="")
        col.operator("xfbin_mat.shader_remove", icon='REMOVE', text="")
        
        row = box.row()
        row.separator()
        row = box.row()
        row.label(text='Material UV Offsets (selected material):')
        row = box.row()
        if xfbin_scene_manager.xfbin_materials and xfbin_scene_manager.xfbin_material_index >= 0:
            matprop: XfbinSceneMaterialPropertyGroup = xfbin_scene_manager.xfbin_materials[xfbin_scene_manager.xfbin_material_index]
            row.prop(matprop, 'uvOffset0', text='UV0 Offset')
            row.prop(matprop, 'uvScale0', text='UV0 Scale')
            row = box.row()
            row.prop(matprop, 'uvOffset1', text='UV1 Offset/Scale')
            row = box.row()
            row.prop(matprop, 'uvOffset2', text='UV2 Offset/Scale')
            row = box.row()
            row.prop(matprop, 'uvOffset3', text='UV3 Offset/Scale')'''

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
        #light_object.rotation_mode = 'QUATERNION'
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


'''class XFBIN_UL_SceneMaterials(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        if item.material:
            row.label(text=item.material.name, icon='MATERIAL')
        else:
            row.label(text=item.name)
        row.prop(item, 'material',emboss= True, text='', icon='MATERIAL')


class XFBIN_SceneMaterial_OT_Add(bpy.types.Operator):
    bl_idname = 'xfbin_mat.shader_add'
    bl_label = 'Add Shader'

    def execute(self, context):
        xfbin_scene = bpy.context.scene.xfbin_scene
        
        new_mat = xfbin_scene.xfbin_materials.add()
        
        return {'FINISHED'}

class XFBIN_SceneMaterial_OT_Remove(bpy.types.Operator):
    bl_idname = 'xfbin_mat.shader_remove'
    bl_label = 'Remove Shader'

    def execute(self, context):
        xfbin_scene = bpy.context.scene.xfbin_scene
        xfbin_scene.xfbin_materials.remove(xfbin_scene.xfbin_material_index)
        if xfbin_scene.xfbin_material_index > 0:
            xfbin_scene.xfbin_material_index -= 1

        return {'FINISHED'}
    

class XfbinSceneMaterialPropertyGroup(PropertyGroup):
    def update_name(self, context):
        if self.material:
            self.name = self.material.name
        else:
            self.name = 'Material'
    name: StringProperty(name='Name', default='Material')
    
    material: PointerProperty(
        type= bpy.types.Material,
        name='Material',
        update= update_name
    )
    
    uvOffset0: FloatVectorProperty(name='UV Offset', size=2, default=(0.0, 0.0))
    uvScale0: FloatVectorProperty(name='UV Scale', size=2, default=(1.0, 1.0))
    uvOffset1: FloatVectorProperty(name='UV Offset', size=2, default=(0.0, 0.0))
    uvScale1: FloatVectorProperty(name='UV Scale', size=2, default=(1.0, 1.0))
    uvOffset2: FloatVectorProperty(name='UV Offset', size=2, default=(0.0, 0.0))
    uvScale2: FloatVectorProperty(name='UV Scale', size=2, default=(1.0, 1.0))
    uvOffset3: FloatVectorProperty(name='UV Offset', size=2, default=(0.0, 0.0))
    uvScale3: FloatVectorProperty(name='UV Scale', size=2, default=(1.0, 1.0))'''

scene_property_groups = (
    XfbinSceneManagerPropertyGroup,
)

scene_classes = (
    *scene_property_groups,
    XFBIN_Scene_OT_CreateLight,
    XFBIN_Scene_OT_CreatePointLight,
    XfbinSceneManagerPanel,
)
