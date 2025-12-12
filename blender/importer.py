import os
from itertools import chain
from typing import List
import time
from .panels.scene_manager_panel import XfbinSceneManagerPropertyGroup
import bmesh
import bpy
from bmesh.types import BMesh
from bpy.props import BoolProperty, StringProperty, CollectionProperty, IntProperty
from bpy.types import Action, Camera, Bone, Material, Object, Operator, UIList
from bpy_extras.io_utils import ImportHelper
from mathutils import Matrix, Quaternion, Vector, Euler

from ..xfbin_lib.xfbin.structure.anm import (AnmDataPath, AnmEntry,
                                             AnmEntryFormat)
from ..xfbin_lib.xfbin.structure.nucc import (CoordNode, NuccChunkAnm, NuccChunkCamera,
                                              NuccChunkLightDirc,
                                              NuccChunkLightPoint,
                                              NuccChunkAmbient,
                                              NuccChunkDynamics,
                                              NuccChunkClump, NuccChunkModel,
                                              NuccChunkModelHit,
                                              NuccChunkModelPrimitiveBatch,
                                              NuccChunkPrimitiveVertex,
                                              PrimitiveVertex,
                                              NuccChunkTexture,
                                              NuccChunkMaterial)
from ..xfbin_lib.xfbin.structure.nud import NudMesh
from ..xfbin_lib.xfbin.structure.xfbin import Xfbin
from ..xfbin_lib.xfbin.xfbin_reader import read_xfbin
from .common.coordinate_converter import *
from .common.helpers import (XFBIN_DYNAMICS_OBJ, XFBIN_ANMS_OBJ, XFBIN_TEXTURES_OBJ,
                             int_to_hex_str)
from .materials.shaders import (shaders_dict, collision_mat)
import cProfile
from zlib import crc32
import numpy as np
class XFBIN_UL_IMPORT_LIST(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        
        layout.prop(item, "name", text="", emboss=False)

class XFBIN_OT_IMPORT_ADD_FILE(Operator):
    bl_idname = "xfbin.import_add_file"
    bl_label = "Add File"

    def execute(self, context):
        context.scene.xfbin_import_files_data.add()
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return self.execute(context)
    

class XFBIN_OT_IMPORT_REMOVE_FILE(Operator):
    bl_idname = "xfbin.import_remove_file"
    bl_label = "Remove File"

    index: IntProperty(name="Index")

    def execute(self, context):
        context.scene.xfbin_import_files_data.remove(self.index)
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return self.execute(context)
    

class XFBIN_OT_IMPORT_CLEAR_FILES(Operator):
    bl_idname = "xfbin.import_clear_files"
    bl_label = "Clear Files"

    def execute(self, context):
        context.scene.xfbin_import_files_data.clear()
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return self.execute(context)


class XFBIN_OT_IMPORT_MOVE_FILE(Operator):
    bl_idname = "xfbin.import_move_file"
    bl_label = "Move File"

    index: IntProperty(name="Index")
    direction: IntProperty(name="Direction")

    def execute(self, context):
        context.scene.xfbin_import_files_data.move(self.index, self.index + self.direction)
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return self.execute(context)


class XFBIN_IMPORT_FILES(bpy.types.PropertyGroup):
    name: StringProperty(name="path", subtype='FILE_PATH')
    


class ImportXFBIN(Operator, ImportHelper):
    """Loads an XFBIN file into blender"""
    bl_idname = "import_scene.xfbin"
    bl_label = "Import XFBIN"

    files_list: CollectionProperty(type=XFBIN_IMPORT_FILES)
    
    fl_index: IntProperty(name="Index")

    files: CollectionProperty(type=bpy.types.OperatorFileListElement, options={'HIDDEN', 'SKIP_SAVE'})

    directory: StringProperty(subtype='DIR_PATH', options={'HIDDEN', 'SKIP_SAVE'})

    filter_glob: StringProperty(default="*.xfbin", options={"HIDDEN"})
    
    import_animations: BoolProperty(name='Import Animations', default=True)

    clear_textures: BoolProperty(name='Clear Textures List', default=False,
                                 description='Clear the textures list before importing\n'
                                              "WARNING: Only enable this option if you're sure of what you're doing")

    import_modelhit: BoolProperty(name='Import Stage Collision', default=True)


    def draw(self, context):
        layout = self.layout

        layout.prop(self, "clear_textures")
        layout.prop(self, 'import_modelhit')
        layout.prop(self, 'import_animations')
        #layout.

        #add a list of files to import
        #layout.label(text="Files:")
        #layout.template_list("XFBIN_UL_IMPORT_LIST", "", self, "files_list", self, "fl_index", rows=5)

        #row = layout.row(align=True)
        #row.operator("xfbin.import_add_file", icon='ADD', text="")
        '''row.operator("xfbin.import_remove_file", icon='REMOVE', text="").index = self.index
        row.operator("xfbin.import_clear_files", icon='X', text="")
        row = layout.row(align=True)
        row.operator("xfbin.import_move_file", icon='TRIA_UP', text="").index = self.index
        row.operator("xfbin.import_move_file", icon='TRIA_DOWN', text="").index = self.index'''
        
    
    def execute(self, context):

        start_time = time.time()
        for file in self.files:
            
            self.filepath = os.path.join(self.directory, file.name)

            importer = XfbinImporter(
                self, self.filepath, self.as_keywords(ignore=("filter_glob",)))

            importer.read(context)

        elapsed_s = "{:.2f}s".format(time.time() - start_time)
        self.report({'INFO'}, "XFBIN import finished in " + elapsed_s)
        #print("XFBIN import finished in " + elapsed_s)


        return {'FINISHED'}
        # except Exception as error:
        #     print("Catching Error")
        #     self.report({"ERROR"}, str(error))
        # return {'CANCELLED'}

class DropXFBIN(Operator):
    """Allows XFBIN files to be dropped into the viewport to import them"""
    bl_idname = "import_scene.drop_xfbin"
    bl_label = "Import XFBIN"

    #files_list: CollectionProperty(type=XFBIN_IMPORT_FILES)

    files: CollectionProperty(type=bpy.types.OperatorFileListElement, options={'HIDDEN', 'SKIP_SAVE'})

    directory: StringProperty(subtype='DIR_PATH', options={'HIDDEN', 'SKIP_SAVE'})

    use_full_material_names: BoolProperty(
        name="Full material names",
        description="Display full name of materials in NUD meshes, instead of a shortened form")

    filter_glob: StringProperty(default="*.xfbin", options={"HIDDEN"})

    import_all_textures: BoolProperty(name='Import Textures', default=True)
    
    import_animations: BoolProperty(name='Import Animations', default=True)

    clear_textures: BoolProperty(name='Clear Textures List', default=False,
                                 description='Clear the textures list before importing\n'
                                              "WARNING: Only enable this option if you're sure of what you're doing")

    skip_lod_tex: BoolProperty(name='Skip LOD Textures', default=False)

    import_modelhit: BoolProperty(name='Import Stage Collision', default=True)
    

    def execute(self, context):

        start_time = time.time()

        for file in self.files:
            
            self.filepath = os.path.join(self.directory, file.name)

            importer = XfbinImporter(
                self, self.filepath, self.as_keywords(ignore=("filter_glob",)))

            importer.read(context)

        elapsed_s = "{:.2f}s".format(time.time() - start_time)
        self.report({'INFO'}, "XFBIN import finished in " + elapsed_s)
        #print("XFBIN import finished in " + elapsed_s)


        return {'FINISHED'}

class XFBIN_FH_import(bpy.types.FileHandler):
    bl_idname = "XFBIN_FH_import"
    bl_label = "File handler for XFBIN files"
    bl_import_operator = "import_scene.drop_xfbin"
    bl_file_extensions = ".xfbin"

    @classmethod
    def poll_drop(cls, context):
        return (context.area and context.area.type == 'VIEW_3D')

class XfbinImporter:
    def __init__(self, operator: Operator, filepath: str, import_settings: dict):
        self.operator = operator
        self.filepath = filepath
        self.clear_textures = import_settings.get('clear_textures')
        self.import_modelhit = import_settings.get('import_modelhit')
        self.import_animations = import_settings.get('import_animations')
        
        # get the file name without extension
        xfbin_file = os.path.basename(self.filepath).split('.')[0]
        
        self.xfbin_hash = crc32(xfbin_file.encode('utf-8'))
        
        #check if XFBIN Scene Manager exists if not create it
        if not bpy.data.collections.get("XFBIN Scene Manager"):
            bpy.data.collections.new("XFBIN Scene Manager")
            #link the collection to the scene
            bpy.context.scene.collection.children.link(bpy.data.collections.get("XFBIN Scene Manager"))
        
        scene_manager_collection = bpy.data.collections.get("XFBIN Scene Manager")
        
        if not bpy.data.objects.get("XFBIN Scene Manager"):
            scene_manager = bpy.data.objects.new("XFBIN Scene Manager", None)
            scene_manager.empty_display_size = 0
            scene_manager_collection.objects.link(scene_manager)


    xfbin: Xfbin
    collection: bpy.types.Collection

    def read(self, context):
        self.xfbin = read_xfbin(self.filepath)
        self.collection = self.make_collection(context)

        # Storing specific chunks in lists would help with importing them in a specific order
        # it's always better to import textures first, then models, then animations
        texture_chunks: List[NuccChunkTexture] = list()
        clump_chunks: List[NuccChunkClump] = list()
        dynamics_chunks = {}
        anm_chunks: List[NuccChunkAnm] = list()
        cam_chunks: List[NuccChunkCamera] = list()
        lightdirc_chunks: List[NuccChunkLightDirc] = list()
        lightpoint_chunks: List[NuccChunkLightPoint] = list()
        ambient_chunks: List[NuccChunkLightPoint] = list()


        if self.clear_textures:
            bpy.context.scene.xfbin_texture_chunks_data.clear()

        #sort the chunks by type

        for page in self.xfbin.pages:
            for chunk in page.chunks:
                if isinstance(chunk, NuccChunkTexture):
                    texture_chunks.append(chunk)
                elif isinstance(chunk, NuccChunkClump):
                    clump_chunks.append(chunk)
                elif isinstance(chunk, NuccChunkAnm):
                    anm_chunks.append(chunk)
                elif isinstance(chunk, NuccChunkCamera):
                    cam_chunks.append(chunk)
                elif isinstance(chunk, NuccChunkLightDirc):
                    lightdirc_chunks.append(chunk)
                elif isinstance(chunk, NuccChunkLightPoint):
                    lightpoint_chunks.append(chunk)
                elif isinstance(chunk, NuccChunkAmbient):
                    ambient_chunks.append(chunk)
                elif isinstance(chunk, NuccChunkDynamics):
                    dynamics_chunks.update({chunk.name: chunk})

            
        # Set the Xfbin textures properties
        bpy.context.scene.xfbin_texture_chunks_data.init_data(texture_chunks)
        
        # Import all clump chunks
        for clump in clump_chunks:

            # Clear unsupported chunks to avoid issues
            '''if clump.clear_non_model_chunks() > 0:
                print(clump.clear_non_model_chunks())
                self.operator.report(
                    {'WARNING'}, f'Some chunks in {clump.name} have unsupported types and will not be imported')'''

            armature_obj = self.make_armature(clump, context)
            self.make_objects(clump, armature_obj, context)

            # Set the armature as the active object after importing everything
            bpy.ops.object.mode_set(mode='OBJECT')
            context.view_layer.objects.active = armature_obj

            # Update the models' PointerProperty to use the models that were just imported
            armature_obj.xfbin_clump_data.update_models(armature_obj)

            #add clump dynamics
            clump_dynamics = dynamics_chunks.get(clump.name)
            if clump_dynamics:
                self.make_dynamics(armature_obj, clump_dynamics, context)
        
    

        #import cameras
        self.make_cameras(cam_chunks, context)
        
        #import lightdirc_chunks
        self.make_lightdircs(lightdirc_chunks, context)
        
        #import lightpoint_chunks
        self.make_lightpoints(lightpoint_chunks, context)
        
        #animations
        
        # Create an empty object to store the anm chunks list
        if self.import_animations:
            actions = self.make_actions(anm_chunks, cam_chunks, context)
            if actions:
                empty_anm = bpy.data.objects.new(
                    f'{XFBIN_ANMS_OBJ} [{self.collection.name}]', None)
                empty_anm.empty_display_size = 0

                self.collection.objects.link(empty_anm)

                empty_anm.xfbin_anm_chunks_data.init_data(anm_chunks, cam_chunks, lightdirc_chunks, lightpoint_chunks, ambient_chunks, context)

        

              
    def make_collection(self, context) -> bpy.types.Collection:
        """
        Build a collection to hold all of the objects and meshes from the GMDScene.
        :param context: The context used by the import process.
        :return: A collection which the importer can add objects and meshes to.
        """

        collection_name = os.path.basename(self.filepath).split('.')[0]
        collection = bpy.data.collections.new(collection_name)
        # Link the new collection to the currently active collection.
        context.collection.children.link(collection)
        return collection
    
    
    def make_cameras(self, cam_chunks: List[NuccChunkCamera], context):
        for cam in cam_chunks:
                
            if bpy.data.objects.get(f"{cam.name}"):
                camera = bpy.data.objects.get(f"{cam.name}")
            else:
                cam_data = bpy.data.cameras.new(f"{cam.name}")
                cam_data.lens_unit = 'MILLIMETERS'
                cam_data.lens = focal_to_blender(cam.fov, 36.0)

                camera = bpy.data.objects.new(f"{cam.name}", cam_data)
                camera.rotation_mode = 'QUATERNION'
                
                self.collection.objects.link(camera)
    
    
    def make_lightdircs(self, lightdirc_chunks: List[NuccChunkLightDirc], context):
        scene = context.scene
        xfbin_scene_manager: XfbinSceneManagerPropertyGroup = scene.xfbin_scene

        rotation180 = Euler((np.radians(180), 0, 0), 'XYZ').to_quaternion()
        
        for light in lightdirc_chunks:
            # get the light object if it exists
            light_object = bpy.data.objects.get(f"{light.name}")
            if light_object:
                continue

            #create Arrow Empty
            #light_object = bpy.data.objects.new(name=f'{light.name}', object_data=None)
            light_data = bpy.data.lights.new(name=f"{light.name}", type='SUN')
            light_object = bpy.data.objects.new(name=f'{light.name}', object_data=light_data)
            #light_object.rotation_mode = 'QUATERNION'

            scene.collection.objects.link(light_object)
            
            # the 180 rotation is done because the arrow empty points up so we have to account of that
            light_rotation = Quaternion((light.rotation[3], light.rotation[0], light.rotation[1], light.rotation[2])).inverted()
            light_rotation = light_rotation.to_euler()
            
            light_object.rotation_euler = light_rotation
            #xfbin_scene_manager.lightdir_object = light_object
            #xfbin_scene_manager.lightdir_color = (light.color[0], light.color[1], light.color[2])
    
    
    def make_lightpoints(self, lightpoint_chunks: List[NuccChunkLightPoint], context):
        scene = context.scene
        xfbin_scene_manager: XfbinSceneManagerPropertyGroup = scene.xfbin_scene
        for light in lightpoint_chunks:

            #create Sphere Empty
            light_object = bpy.data.objects.new(name=f'{light.name}', object_data=None)
            light_object.empty_display_type = 'SPHERE'
            light_object.empty_display_size = 1
            scene.collection.objects.link(light_object)
            xfbin_scene_manager.lightpoint_object0 = light_object
    

    def make_dynamics(self, dynamics_obj, dynamics: NuccChunkDynamics, context):
        # Set the Xfbin dynamics properties
        dynamics_obj.xfbin_dynamics_data.init_data(context, dynamics)

        if dynamics_obj.type != "ARMATURE":
            self.collection.objects.link(dynamics_obj)

    def make_armature(self, clump: NuccChunkClump, context):
        armature_name = clump.name

        armature = bpy.data.armatures.new(f"{armature_name}")
        armature.display_type = 'STICK'

        armature_obj = bpy.data.objects.new(f"{armature_name}", armature)
        armature_obj.show_in_front = True
        armature_obj['xfbin_clump'] = True

        # Set the Xfbin clump properties
        armature_obj.xfbin_clump_data.init_data(clump)

        self.collection.objects.link(armature_obj)

        context.view_layer.objects.active = armature_obj
        bpy.ops.object.mode_set(mode='EDIT')

        bone_matrices = dict()

        def make_bone(node: CoordNode):

            # Find the local->world matrix for the parent bone, and use this to find the local->world matrix for the current bone
            if node.parent:
                parent_matrix = node.parent.matrix
            else:
                parent_matrix = Matrix.Identity(4)

            # Convert the node values
            pos = pos_cm_to_m(node.position)
            rot = rot_to_blender(node.rotation).to_quaternion()
            sca = Vector(node.scale)

            # Set up the transformation matrix
            this_bone_matrix = parent_matrix @ Matrix.LocRotScale(pos, rot, sca)

            #print(f"-------------------{node.name}-------------------")
            #print(this_bone_matrix)

            # Add the matrix to the dictionary
            bone_matrices[node.name] = this_bone_matrix
            node.matrix = this_bone_matrix

            bone = armature.edit_bones.new(node.name)
            bone.use_relative_parent = False
            bone.use_deform = True

            # Having a long tail would offset the meshes parented to the mesh bones, so we avoid that for now
            bone.tail = Vector((0, 0.001, 0))

            bone.matrix = this_bone_matrix
            bone.parent = armature.edit_bones.get(node.parent.name) if node.parent else None

            # Store the signs of the node's scale to apply when exporting, as applying them here (if negative) will break the rotation
            bone['scale_signs'] = [-1 if x < 0 else 1 for x in node.scale]

            bone['opacity'] = node.opacity
            bone['flags'] = node.flags
            bone['matrix'] = node.matrix
            bone["orig_coords"] = [node.position, node.rotation, node.scale]
            bone["rotation_quat"] = rot

            #relative_matrix = parent_matrix.inverted() @ this_bone_matrix
            #dloc, drot, dsca = relative_matrix.decompose()
            #print(f"-------------------{node.name}-------------------")
            #print(dloc, drot, dsca)

            for child in node.children:
                make_bone(child)

        for root in clump.root_nodes:
            make_bone(root)
        
        
        bpy.ops.object.mode_set(mode='OBJECT')

        #add the opacity property in pose mode
        for b in armature_obj.pose.bones:
            b["opacity"] = float(armature_obj.data.bones[b.name]['opacity'])

        return armature_obj

    def make_objects(self, clump: NuccChunkClump, armature_obj: Object, context):
        vertex_group_list = [coord.node.name for coord in clump.coord_chunks]
        vertex_group_indices = {
            name: i
            for i, name in enumerate(vertex_group_list)
        }

        all_model_chunks = list(dict.fromkeys(list(chain(*[g.model_chunks for g in clump.model_groups]))))
        for nucc_model in all_model_chunks:

            if isinstance(nucc_model, NuccChunkModelPrimitiveBatch):
                self.make_primitive_batch(nucc_model, armature_obj, context)
                continue
            elif not (isinstance(nucc_model, NuccChunkModel) and hasattr(nucc_model, 'nud')):
                continue

            # Create modelhit object
            modelhit_obj = None
            if self.import_modelhit:
                modelhit_obj = self.make_modelhit(nucc_model.hit_chunk, armature_obj, nucc_model.coord_chunk.name, context)
            nud = nucc_model.nud

            # Create an empty to store the NUD's properties, and set the armature to be its parent
            blender_mesh = bpy.data.meshes.new(nucc_model.name)
            

            # Set the mesh bone as the object's parent bone, if it exists (it should)
            mesh_bone = None
            if nucc_model.coord_chunk:
                mesh_bone: Bone = armature_obj.data.bones.get(
                    nucc_model.coord_chunk.name)


            normal_arrays = []
            color_arrays = []
            boneID_arrays = []
            boneWeight_arrays = []
            uv_dict = {}
            
            # first loop to get the uv count and prepare the layers
            for group in nud.mesh_groups:
                for mat_index, mesh in enumerate(group.meshes):
                    if 'uv0' in mesh.vertices.dtype.names:
                        uv_dict["uv0"] = []
                    if 'uv1' in mesh.vertices.dtype.names:
                        uv_dict["uv1"] = []
                    if 'uv2' in mesh.vertices.dtype.names:
                        uv_dict["uv2"] = []
                    if 'uv3' in mesh.vertices.dtype.names:
                        uv_dict["uv3"] = []
            

            #create a bmesh to store all the submeshes
            bm = bmesh.new()
            vCount = 0
            for group in nud.mesh_groups:
                for mat_index, mesh in enumerate(group.meshes):
                    mat_chunk = nucc_model.material_chunks[mat_index]

                    #add the material to the mesh
                    try:
                        shader = int_to_hex_str(mesh.materials[0].flags, 4)
                        blender_mesh.materials.append(self.make_material(mat_chunk, mesh, [nucc_model.rigging_flag, group.bone_flags]))
                    except Exception as e:
                        print(f"Error adding material {mat_chunk.name} to mesh {mesh.name} \n"
                              f"Error message: {e}")
                        pass
                    
                    vCount = len(bm.verts)
                    
                    verts = [bm.verts.new((pos[0] * 0.01, pos[1] * 0.01, pos[2] * 0.01)) for pos in mesh.vertices['position']]
                    bm.verts.ensure_lookup_table()
                    
                    vertex_count = len(mesh.vertices)
                    
                    if 'normal' in mesh.vertices.dtype.names:
                        normal_arrays.append(mesh.vertices['normal'])
                    if 'color' in mesh.vertices.dtype.names:
                        color_arrays.append(mesh.vertices['color'])
                    
                    for uv_key in uv_dict.keys():
                        if uv_key in mesh.vertices.dtype.names:
                            # create a float32 array for the uvs
                            f32_array = mesh.vertices[uv_key].astype(np.float32)
                            uv_dict[uv_key].append(f32_array)
                        else:
                            # assign [0,1] uvs if the mesh doesn't have this uv layer
                            f32_array = np.zeros((vertex_count, 2), dtype=np.float32)
                            f32_array[:,1] = 1.0
                            uv_dict[uv_key].append(f32_array)
                        
                    
                    if 'bone_ids' in mesh.vertices.dtype.names:
                        boneID_arrays.append(mesh.vertices['bone_ids'])
                    if 'bone_weights' in mesh.vertices.dtype.names:
                        boneWeight_arrays.append(mesh.vertices['bone_weights'])
                    
                    
                    for face in mesh.faces:
                        try:
                            face_verts = [bm.verts[vCount + vi] for vi in face]
                            f = bm.faces.new(face_verts)
                            f.material_index = mat_index
                        except Exception as e:
                            #print(f"Error creating face with verts {face_verts} in mesh {mesh.name} \n"
                            #      f"Error message: {e}")
                            pass
                        
            
            bm.to_mesh(blender_mesh)
            bm.free()
            
            #merge all the submesh arrays
            all_normals = np.concatenate(normal_arrays) if normal_arrays else None
            all_colors = np.concatenate(color_arrays) if color_arrays else None
            all_boneIDs = np.concatenate(boneID_arrays) if boneID_arrays else None
            all_boneWeights = np.concatenate(boneWeight_arrays) if boneWeight_arrays else None
            

            #print(f"vertex count: {len(blender_mesh.vertices)}, normal count: {len(all_normals) if all_normals is not None else 0}")
            
            # set smooth shading
            blender_mesh.polygons.foreach_set("use_smooth", np.ones(len(blender_mesh.polygons), dtype=np.int8))
            
            # apply normals if they exist
            if all_normals is not None:
                blender_mesh.normals_split_custom_set_from_vertices(all_normals)
            
            loops = blender_mesh.loops
            loop_count = len(loops)
            loop_vert_indices = np.empty(loop_count, dtype=np.int32)
            loops.foreach_get("vertex_index", loop_vert_indices)
            
            #apply vertex colors
            if all_colors is not None:
                color_layer = blender_mesh.vertex_colors.new(name="Color")
                color_data = color_layer.data
                
                colors = all_colors.astype(np.float32) / 255.0
                
                loop_colors = colors[loop_vert_indices]
                
                color_data.foreach_set("color", loop_colors.flatten())
            #apply UVs
            for i, (uv_key, uv_arrays) in enumerate(uv_dict.items()):
                if uv_arrays:
                    uv_arrays = np.concatenate(uv_arrays)
                    uv_layer = blender_mesh.uv_layers.new(name=f"UV_{i}")
                    uv_data = uv_layer.data
                    loop_uvs = uv_arrays[loop_vert_indices]
                    loop_uvs[:,1] = 1.0 - loop_uvs[:,1]
                    uv_data.foreach_set("uv", loop_uvs.flatten())
                
            
            mesh_obj: bpy.types.Object = bpy.data.objects.new(
                nucc_model.name, blender_mesh)
            
            
            for vg_name in vertex_group_list:
                mesh_obj.vertex_groups.new(name=vg_name)
            
            # add vertex weights
            if all_boneIDs is not None and all_boneWeights is not None:
                # Vectorized vertex weight assignment
                num_verts = len(all_boneIDs)
                for bone_idx in range(len(vertex_group_list)):
                    # Find all vertices that have this bone with non-zero weight
                    mask = (all_boneIDs == bone_idx) & (all_boneWeights > 0)
                    vert_indices, weight_slot = np.where(mask)
                    
                    if len(vert_indices) > 0:
                        group = mesh_obj.vertex_groups[bone_idx]
                        weights = all_boneWeights[vert_indices, weight_slot]
                        
                        # Add all weights for this bone at once
                        for vert_idx, weight in zip(vert_indices, weights):
                            group.add([int(vert_idx)], weight, 'ADD')
            
            
            # Set the NUD properties
            mesh_obj.xfbin_nud_data.init_data(
                nucc_model, nucc_model.coord_chunk.name if nucc_model.coord_chunk else None)

            # set the mesh's parent to the armature
            mesh_obj.parent = armature_obj

            # Set the mesh's parent bone to the mesh bone
            if mesh_bone:
                mesh_obj.parent_bone = mesh_bone.name
                # add full weight to the parent bone
                vg = mesh_obj.vertex_groups.get(mesh_bone.name)
                if vg and all_boneIDs is None:
                    vg.add(range(len(blender_mesh.vertices)), 1.0, 'ADD')
            
            # If we're not going to parent it, transform the mesh by the bone's matrix
            if mesh_bone and nucc_model.coord_chunk.node.matrix:                        
                blender_mesh.transform(nucc_model.coord_chunk.node.matrix)
             
            #set active color
            mesh_obj.data.color_attributes.render_color_index = 0
            mesh_obj.data.color_attributes.active_color_index = 0

            # Link the mesh object to the collection
            self.collection.objects.link(mesh_obj)

            #parent the modelhit to the empty
            #if modelhit_obj:
            #    modelhit_obj.parent = empty


            # Apply the armature modifier
            modifier = mesh_obj.modifiers.new(
                type='ARMATURE', name="Armature")
            modifier.object = armature_obj

            # Add the xfbin materials to the mesh
            #for blender_mat in blender_mats:
            #    overall_mesh.materials.append(blender_mat)
                    
                    
    def make_modelhit(self, modelhit: NuccChunkModelHit, armature_obj: Object, parent_name, context):

        if not isinstance(modelhit, NuccChunkModelHit):
            pass
        else:

            # Make an empty to store the modelhit's properties, and set the armature to be its parent
            hit_empty = bpy.data.objects.new(f'{modelhit.name}_[HIT]', None)
            hit_empty.empty_display_size = 0
            hit_empty.parent = armature_obj
            hit_empty.parent_type = 'BONE'
            hit_empty.parent_bone = parent_name

            # link the empty to the collection
            self.collection.objects.link(hit_empty)

            # Set the modelhit properties
            hit_empty.xfbin_modelhit_data.init_data(modelhit)

            for i, sec in enumerate(modelhit.vertex_sections):
                bm = bmesh.new()
                # Make a mesh to store the modelhit's vertex data
                mesh = bpy.data.meshes.new(f'{modelhit.name}_{i}')

                for v in range(0, len(sec.mesh_vertices), 3):
                    # add verts
                    bmv1 = bm.verts.new(sec.mesh_vertices[v])
                    bmv2 = bm.verts.new(sec.mesh_vertices[v+1])
                    bmv3 = bm.verts.new(sec.mesh_vertices[v+2])

                    # draw faces
                    face = bm.faces.new((bmv1, bmv2, bmv3))
                
                bm.verts.ensure_lookup_table()
                bm.faces.ensure_lookup_table()

                # clean up
                bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
                bmesh.ops.scale(bm, vec=(0.01, 0.01, 0.01), verts=bm.verts)

                # apply the changes to the mesh we created
                bm.to_mesh(mesh)

                # free bmesh
                bm.free()

                # create a new object with our mesh data
                obj = bpy.data.objects.new(f'{modelhit.name}_{i}', mesh)

                # link the object to the current collection
                self.collection.objects.link(obj)

                #obj.parent_type = 'BONE'
                obj.parent = hit_empty
                #obj.parent_bone = parent_name

                # create a material for the object
                mat = collision_mat(obj.name)
                obj.data.materials.append(mat)

                obj.xfbin_modelhit_mesh_data.init_data(sec)
            return hit_empty

    def make_primitive_batch(self, batch: NuccChunkModelPrimitiveBatch, armature_obj: Object, context):

        # Make an empty and set the armature to be its parent
        primitive_empty = bpy.data.objects.new(f'{batch.name}_[PRIMITIVE]', None)
        primitive_empty.empty_display_size = 0
        primitive_empty.parent = armature_obj
        # link the empty to the collection
        self.collection.objects.link(primitive_empty)
        
        #material = mat.init_data(batch.material_chunk)
        material = self.make_material_primitive(batch.material_chunk)
        blender_mesh = bpy.data.meshes.new(f"{batch.name}")
        obj = bpy.data.objects.new(f"{batch.name}", blender_mesh)
        
        self.collection.objects.link(obj)
        
        uvs = []
        colors = []
        weights = {}
        
        vertex = 0
        bm = bmesh.new()
        for i, mesh in enumerate(batch.meshes):
            
            vertex_group = obj.vertex_groups.new(name=armature_obj.data.bones[mesh.parent_bone].name)
            vertices = batch.primitive_vertex_chunk.vertices[vertex:vertex+mesh.vertex_count]
            
            #has uv
            has_uv = hasattr(vertices[0], 'uv') if len(vertices) > 0 else False
            has_color = hasattr(vertices[0], 'color') if len(vertices) > 0 else False
            
            if has_uv:
                uv_layer = bm.loops.layers.uv.new('UV_0')
            if has_color:
                color_layer = bm.loops.layers.color.new('Color')
            
            parent_matrix = armature_obj.data.bones[mesh.parent_bone].matrix_local
            
            for v in range(0, mesh.vertex_count, 3):
                # add verts
                pos1 = vertices[v].position
                pos1 = parent_matrix @ Vector(pos1) * 0.01
                bmv1 = bm.verts.new(pos1)
                bmv1.normal = parent_matrix @ Vector(vertices[v].normal)

                pos2 = vertices[v + 1].position
                pos2 = parent_matrix @ Vector(pos2) * 0.01
                bmv2 = bm.verts.new(pos2)
                bmv2.normal = parent_matrix @ Vector(vertices[v + 1].normal)

                pos3 = vertices[v + 2].position
                pos3 = parent_matrix @ Vector(pos3) * 0.01
                bmv3 = bm.verts.new(pos3)
                bmv3.normal = parent_matrix @ Vector(vertices[v + 2].normal)
                
                bm.verts.ensure_lookup_table()
                bm.verts.index_update()
                
                # add weights
                vertex_group.add([bmv1.index], 1.0, 'ADD')
                vertex_group.add([bmv2.index], 1.0, 'ADD')
                vertex_group.add([bmv3.index], 1.0, 'ADD')
                

                # draw faces
                face = bm.faces.new((bmv1, bmv2, bmv3))
                face.smooth = True
                
                #uv
                bmv1_uv = vertices[v].uv
                bmv2_uv = vertices[v + 1].uv
                bmv3_uv = vertices[v + 2].uv
                
                face.loops[0][uv_layer].uv = (bmv1_uv[0], 1.0 - bmv1_uv[1])
                face.loops[1][uv_layer].uv = (bmv2_uv[0], 1.0 - bmv2_uv[1])
                face.loops[2][uv_layer].uv = (bmv3_uv[0], 1.0 - bmv3_uv[1])
                
                #color
                face.loops[0][color_layer] = vertices[v].color
                face.loops[1][color_layer] = vertices[v + 1].color
                face.loops[2][color_layer] = vertices[v + 2].color
                
                
            vertex += mesh.vertex_count
        
        # apply the changes to the mesh we created
        bm.to_mesh(blender_mesh)
        bm.free()

        # parent the object to the empty
        obj.parent = primitive_empty
        
        # assign the material to the object
        obj.data.materials.append(material)



    def make_material(self, xfbin_mat: NuccChunkMaterial, mesh, mesh_flags) -> Material:
        material_name = xfbin_mat.name
        if not bpy.data.materials.get(material_name):
            
            shader = int_to_hex_str(mesh.materials[0].flags, 4)
            

            if shader in shaders_dict:
                try:
                    material = shaders_dict.get(shader)(self, mesh, xfbin_mat, mesh_flags, self.xfbin_hash)
                except Exception as e:
                    self.operator.report(
                        {'WARNING'}, f"There was an error creating the material {material_name} using shader {shader} \n{e}")
                    material = shaders_dict.get("default")(self, mesh, xfbin_mat, mesh_flags, self.xfbin_hash)
            else:
                material = shaders_dict.get("default")( self, mesh, xfbin_mat, mesh_flags, self.xfbin_hash)

            
        else:
            material = bpy.data.materials.get(material_name)
            material.xfbin_material_data.init_data(xfbin_mat, mesh, mesh_flags)

        return material

    
    def make_material_primitive(self, xfbin_mat: NuccChunkMaterial) -> Material:
        material_name = xfbin_mat.name
        if not bpy.data.materials.get(material_name):
            material = shaders_dict.get("primitive")( self,xfbin_mat, self.xfbin_hash)

        else:
            material = bpy.data.materials.get(material_name)

        return material


    def make_actions(self, anm_chunks: NuccChunkAnm, cam_chunks: NuccChunkCamera, context) -> List[Action]:
        actions: List[bpy.types.Action] = list()
        
        material_inputs = { "U0_LocX": "uvOffset0 Offset X",
                            "V0_LocY": "uvOffset0 Offset Y",
                            "U1_LocX": "uvOffset1 Offset X",
                            "V1_LocY": "uvOffset1 Offset Y",
                            "U2_LocX": "uvOffset2 Offset X",
                            "V2_LocY": "uvOffset2 Offset Y",
                            "U3_LocX": "uvOffset3 Offset X",
                            "V3_LocY": "uvOffset3 Offset Y",
                            "U0_ScaleX": "uvOffset0 Scale X",
                            "V0_ScaleY": "uvOffset0 Scale Y",
                            "U1_ScaleX": "uvOffset1 Scale X",
                            "V1_ScaleY": "uvOffset1 Scale Y",
                            "U2_ScaleX": "uvOffset2 Scale X",
                            "V2_ScaleY": "uvOffset2 Scale Y",
                            "U3_ScaleX": "uvOffset3 Scale X",
                            "V3_ScaleY": "uvOffset3 Scale Y",
        }
        for anm in anm_chunks:
            
            #we'll try to include everything in this animation
            action = bpy.data.actions.new(f"{anm.name}")
            # scene manager
            action.layers.new(name="AnimLayer")
            #create a strip
            action.layers[0].strips.new(type="KEYFRAME")
            #create a channelbag
            scene_action_slot = action.slots.new(id_type='SCENE', name="XFBIN_Scene")
            #apply the anim to the scene
            bpy.context.scene.animation_data_create()
            bpy.context.scene.animation_data.action = action

            bpy.context.scene.animation_data.action_slot = scene_action_slot
            
            #scene fcurves
            channelbag = action.layers[0].strips[0].channelbag(scene_action_slot)
            if channelbag:
                scene_fcurves = channelbag.fcurves
            else:
                scene_fcurves = action.layers[0].strips[0].channelbags.new(scene_action_slot).fcurves
            
            start_time = time.time()

            for entry in anm.other_entries:
                entry: AnmEntry

                if entry.entry_format == AnmEntryFormat.CAMERA:
                    camera_action = action
                    group_name = entry.name
                    #get or create the camera object
                    camera_obj = bpy.data.objects.get(entry.name)
                    if not camera_obj:
                        camera_obj = bpy.data.objects.new(entry.name, bpy.data.cameras.new(entry.name))
                        print(f"Camera {entry.name} not found for animation {anm.name}")
                        self.collection.objects.link(camera_obj)

                    camera_obj.animation_data_create()
                    camera_obj.animation_data.action = camera_action
                    
                    slot = camera_obj.animation_data.action.slots.get(f"OB{camera_obj.name}")
                    if not slot:
                        slot = camera_obj.animation_data.action.slots.new(id_type="OBJECT", name=f"{camera_obj.name}")
                    
                    camera_obj.animation_data.action_slot = slot
                    channelbag = action.layers[0].strips[0].channelbag(slot)
                    if channelbag:
                        fcurves = channelbag.fcurves
                    else:
                        fcurves = action.layers[0].strips[0].channelbags.new(slot).fcurves
                    
                    for curve in entry.curves:
                        if curve is None or (not len(curve.keyframes)) or curve.data_path == AnmDataPath.UNKNOWN:
                            continue

                        frames = list(map(lambda x: frame_to_blender(x.frame), curve.keyframes))
                        
                        values = convert_anm_values(curve.data_path, list(map(lambda x: x.value, curve.keyframes)))
                        
                        insert_keyframes_fc(fcurves, curve.data_path, group_name, frames, values)

                elif entry.entry_format == AnmEntryFormat.LIGHTDIRC:
                    invert_xyz
                    
                    light_obj = bpy.data.objects.get(entry.name)
                    if not light_obj:
                        light_data = bpy.data.lights.new(name=f"{entry.name}", type='SUN')
                        light_obj = bpy.data.objects.new(name=f'{entry.name}', object_data=light_data)
                        self.collection.objects.link(light_obj)
                    
                    xfbin_scene.lightdirc_object = light_obj
                    
                    light_obj.animation_data_create()
                    light_obj.animation_data.action = action
                    
                    slot = light_obj.animation_data.action.slots.get(f"OB{light_obj.name}")
                    if not slot:
                        slot = light_obj.animation_data.action.slots.new(id_type="OBJECT", name=f"{light_obj.name}")
                    light_obj.animation_data.action_slot = slot
                    
                    channelbag = action.layers[0].strips[0].channelbag(slot)
                    if channelbag:
                        light_fcurves = channelbag.fcurves
                    else:
                        light_fcurves = action.layers[0].strips[0].channelbags.new(slot).fcurves
                    
                    for curve in entry.curves:
                        if curve is None or (not len(curve.keyframes)) or curve.data_path == AnmDataPath.UNKNOWN:
                            continue

                        frames = list(map(lambda x: frame_to_blender(x.frame), curve.keyframes))
                        
                        values = convert_anm_values(curve.data_path, list(map(lambda x: x.value, curve.keyframes)))
                        
                        values = np.array(values)
                        if curve.data_path == "rotation":
                            new_rotations = []
                            for v in values:
                                q = Quaternion((v[3], v[0], v[1], -v[2]))#.inverted()
                                #q = quat180 @ q
                                new_rotations.append(q.to_euler('ZYX'))
                            values = np.array(new_rotations)
                            curve.data_path = "rotation_euler"
                            fcurves = light_fcurves
                        """elif curve.data_path == "color":
                            fcurves = scene_fcurves
                            curve.data_path = 'xfbin_scene.lightdir_color'
                        elif curve.data_path == "energy":
                            fcurves = scene_fcurves
                            curve.data_path = 'xfbin_scene.lightdir_intensity'"""
                        
                        insert_keyframes_fc(fcurves, curve.data_path, group_name, frames, values.tolist())
                    
                    '''if curve.data_path == AnmDataPath.COLOR:
                        data_path = 'data.color'
                    
                    elif curve.data_path == AnmDataPath.ENERGY:
                        data_path = 'data.energy'

                    elif curve.data_path == AnmDataPath.RADIUS:
                        data_path = 'data.shadow_soft_size'

                    elif curve.data_path == AnmDataPath.CUTOFF:
                        data_path = 'data.cutoff_distance'

                    else:
                        print(curve.data_path)
                        data_path = f'{curve.data_path}'''
                    
                
                    '''for i in range(len(values[0])):
                        fc = action.fcurves.new(data_path=data_path, index=i, action_group=group_name)
                        fc.keyframe_points.add(len(frames))
                        fc.keyframe_points.foreach_set('co', [x for co in list(map(lambda f, v: (f, v[i]), frames, values)) for x in co])
                        fc.update()'''
                    
                    '''if entry.entry_format == AnmEntryFormat.AMBIENT:
                        world = bpy.data.worlds["World"]
                        if not world.use_nodes:
                            world.use_nodes = True

                        node_tree = world.node_tree

                        if "Background" not in node_tree.nodes:
                            bg_node = node_tree.nodes.new(type='ShaderNodeBackground')
                            bg_node.name = "Background"
                        else:
                            bg_node = node_tree.nodes["Background"]
                        
                        if curve.data_path == AnmDataPath.COLOR:
                            for i in range(4):  # RGBA
                                fc = action.fcurves.new(
                                    data_path=f'node_tree.nodes["Background"].inputs[0].default_value', 
                                    index=i, 
                                    action_group=group_name
                                )
                                fc.keyframe_points.add(len(frames))
                                fc.keyframe_points.foreach_set('co', [x for co in list(
                                    map(lambda f, v: (f, v[i]), frames, values)) for x in co])
                                fc.update()'''
                            
            
            
            for clump in anm.clumps:
                #clump_action = bpy.data.actions.new(f'{anm.name} ({clump.name})')
                clump_action = action
                #if action.name == "2knnwin11":
                #    breakpoint()

                arm_obj = bpy.data.objects.get(clump.chunk.name)
                if arm_obj is None:
                    arm_obj = bpy.data.objects.get(clump.chunk.name + ' [C]')
                
                if arm_obj is None:
                    # create an armature for this clump
                    arm_obj = self.create_anm_clump(clump, context)
                
                
                # create a slot for the armature
                arm_obj.animation_data_create()
                arm_obj.animation_data.action = clump_action
                
                slot = arm_obj.animation_data.action.slots.get(f"OB{arm_obj.name}")
                if not slot:
                    slot = arm_obj.animation_data.action.slots.new(id_type="OBJECT", name=f"{arm_obj.name}")
                else:
                    # use the reference name
                    slot = arm_obj.animation_data.action.slots.new(id_type="OBJECT", name=f"{clump.referenced_name}")
                arm_obj.animation_data.action_slot = slot
                
                channelbag = action.layers[0].strips[0].channelbag(slot)
                if channelbag:
                    clump_fcurves = channelbag.fcurves
                else:
                    clump_fcurves = action.layers[0].strips[0].channelbags.new(slot).fcurves
                

                arm_sca = dict()
                arm_mat = dict()
                arm_rot = dict()
                arm_loc = dict()
                arm_blender_mat = dict()
                arm_euler = dict()

                if arm_obj is not None:
                    context.view_layer.objects.active = arm_obj

                    for arm_bone in arm_obj.data.bones:
                        #arm_sca[arm_bone.name] = arm_bone.get('scale_signs')
                        if arm_bone.get('matrix'):
                            arm_mat[arm_bone.name] = Matrix(arm_bone.get('matrix'))
                            arm_rot[arm_bone.name] = arm_bone.get('rotation_quat')
                            arm_loc[arm_bone.name] = arm_bone.get('orig_coords')[0]
                            arm_sca[arm_bone.name] = arm_bone.get('orig_coords')[2]
                            arm_blender_mat[arm_bone.name] = arm_bone.matrix
                            arm_euler[arm_bone.name] = [math.radians(x) for x in arm_bone.get('orig_coords')[1]]
                        else:
                            arm_mat[arm_bone.name] = arm_bone.matrix_local
                            arm_rot[arm_bone.name] = arm_bone.matrix_local.to_quaternion()
                            arm_loc[arm_bone.name] = arm_bone.head_local
                            arm_sca[arm_bone.name] = Vector((1, 1, 1))
                            arm_blender_mat[arm_bone.name] = arm_bone.matrix_local
                            #arm_euler[arm_bone.name] = [math.radians(x) for x in arm_bone.get('orig_coords')[1]]

                        #Set the rotation mode to quaternion
                        pose_bone = arm_obj.pose.bones[arm_bone.name]
                        pose_bone.rotation_mode = "QUATERNION"
                    

                #bones
                for bone in clump.bones:
                    group_name = action.groups.new(bone.name).name

                    '''if bone.anm_entry is None:
                        continue'''



                    mat_parent = arm_mat.get(bone.parent.name, Matrix.Identity(4)) if bone.parent else Matrix.Identity(4)
                    #parent_sca = arm_sca.get(bone.parent.name, Vector((1, 1, 1))) if bone.parent else Vector((1, 1, 1))
                    mat = arm_mat.get(bone.name, Matrix.Identity(4))
                    bmat = arm_blender_mat.get(bone.name, Matrix.Identity(4)) if arm_obj else Matrix.Identity(4)

                    mat = (mat_parent.inverted() @ mat)
                    loc, rot, sca = mat.decompose()
                    loc = Vector(arm_loc.get(bone.name, loc)) * 0.01
                    sca = Vector(arm_sca.get(bone.name, sca))
                    rot = Quaternion(arm_rot.get(bone.name, rot))

                    bone_path = f'pose.bones["{group_name}"]'
                    


                    for curve in bone.curves:
                        #if curve is None or (not len(curve.keyframes)) or curve.data_path == AnmDataPath.UNKNOWN:
                        #    continue

                        frames = list(map(lambda x: frame_to_blender(x.frame), curve.keyframes))
                        
                        values = convert_anm_values_tranformed(curve.data_path, [x.value for x in curve.keyframes], loc, rot, sca)
                        

                        if curve.data_path == "rotation_euler":
                            curve.data_path = "rotation_quaternion"
                        
                        data_path = f'{bone_path}.{curve.data_path}'
                        
                        insert_keyframes_fc(clump_fcurves, data_path, group_name, frames, values)

                #materials
                xfbin_scene = context.scene.xfbin_scene
                scene_material_inputs = {"U0_LocX": ("uvOffset0", 0),
                                        "V0_LocY": ("uvOffset0", 1),
                                        "U1_LocX": ("uvOffset1", 0),
                                        "V1_LocY": ("uvOffset1", 1),
                                        "U2_LocX": ("uvOffset2", 0),
                                        "V2_LocY": ("uvOffset2", 1),
                                        "U3_LocX": ("uvOffset3", 0),
                                        "V3_LocY": ("uvOffset3", 1),
                                        "U0_ScaleX": ("uvScale0", 0),
                                        "V0_ScaleY": ("uvScale0", 1),
                                        "U1_ScaleX": ("uvScale1", 0),
                                        "V1_ScaleY": ("uvScale1", 1),
                                        "U2_ScaleX": ("uvScale2", 0),
                                        "V2_ScaleY": ("uvScale2", 1),
                                        "U3_ScaleX": ("uvScale3", 0),
                                        "V3_ScaleY": ("uvScale3", 1),
                                        "Falloff": ("falloff", 0),
                                        "BlendRate1": ("blendRate", 0),
                                        "BlendRate2": ("blendRate", 1),
                                        "Glare": ("glare", 0),
                                        "Alpha": ("alpha", 0),
                                        "OutlineID": ("outlineID", 0),}
                
                for material in clump.materials:
                    
                    blender_mat = bpy.data.materials.get(material.name)
                    if not blender_mat:
                        continue
                    
                    group_name = action.groups.new(material.name).name
                    
                    # get or add the material
                    scene_mat = xfbin_scene.xfbin_materials.get(material.name)
                    if not scene_mat:
                        scene_mat = xfbin_scene.xfbin_materials.add()
                        scene_mat.material = blender_mat
                        scene_mat.name = material.name
                        
                    scene_mat_index = xfbin_scene.xfbin_materials.find(material.name)
                    
                    #link the material to the scene manager
                    node_tree = blender_mat.node_tree
                    if not node_tree:
                        continue
                    for i in range(4):
                        uv_offset_name = f'SceneUVoffset{i}'
                        uv_scale_name = f'SceneUVscale{i}'
                        uv_offset_node = node_tree.nodes.get(uv_offset_name)
                        uv_scale_node = node_tree.nodes.get(uv_scale_name)
                        if uv_offset_node:
                            uv_offset_node.attribute_name = f"xfbin_scene.xfbin_materials[{scene_mat_index}].uvOffset{i}"
                        if uv_scale_node:
                            uv_scale_node.attribute_name = f"xfbin_scene.xfbin_materials[{scene_mat_index}].uvScale{i}"
                    
                    # blend rate node
                    blend_rate_node = node_tree.nodes.get('SceneBlendRate')
                    if blend_rate_node:
                        blend_rate_node.attribute_name = f"xfbin_scene.xfbin_materials[{scene_mat_index}].blendRate"
                    
                    # falloff node
                    falloff_node = node_tree.nodes.get('SceneFalloff')
                    if falloff_node:
                        falloff_node.attribute_name = f"xfbin_scene.xfbin_materials[{scene_mat_index}].falloff"
                    
                    # useSceneNode
                    use_scene_node = node_tree.nodes.get('useSceneManager')
                    if use_scene_node:
                        use_scene_node.outputs[0].default_value = 1.0
                
                    for curve in material.curves:
                        if curve is None or (not len(curve.keyframes)) or curve.data_path == AnmDataPath.UNKNOWN:
                            continue

                        frames = list(map(lambda x: frame_to_blender(x.frame), curve.keyframes))
                        values = convert_anm_values(curve.data_path, list(map(lambda x: x.value, curve.keyframes)))
                        
                        material_info = scene_material_inputs.get(curve.data_path)
                        if not material_info:
                            continue
                        data_path = f'xfbin_scene.xfbin_materials[{scene_mat_index}].{material_info[0]}'
                        
                        insert_material_keyframes(scene_fcurves, data_path, group_name, frames, values, material_info[1])

            actions.append(action)
    
        
        #print(f"Animation(s) imported in: {time.time() - start_time}")
        context.scene.render.fps = 30

        return actions

    def create_anm_clump(self, clump, context):
        #print(f"Creating armature for clump {clump.chunk.name}")
        
        bones_for_constraints = []
        
        # get the armature first
        armature_obj = bpy.data.objects.get(clump.referenced_name)
        if armature_obj:
            return armature_obj
        
        armature_data = bpy.data.armatures.new(clump.referenced_name)
        armature_obj = bpy.data.objects.new(clump.referenced_name, armature_data)
        armature_data.display_type = 'STICK'
        self.collection.objects.link(armature_obj)
        
        # create bones
        bpy.context.view_layer.objects.active = armature_obj
        bpy.ops.object.mode_set(mode='EDIT')
        for bone in clump.bones:
            edit_bone = armature_data.edit_bones.new(bone.name)
            if bone.parent:
                # get the parent edit bone
                parent_edit_bone = armature_data.edit_bones.get(bone.parent.name)
                if parent_edit_bone:
                    edit_bone.parent = parent_edit_bone
                else:
                    bones_for_constraints.append((edit_bone, bone))
            
            # set tail pos
            edit_bone.head = Vector((0, 0, 0))
            edit_bone.tail = Vector((0, 0.01, 0))
        
        
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # add bone constreaints for bones with parents from another armature
        '''for edit_bone, bone in bones_for_constraints:
            pose_bone = armature_obj.pose.bones.get(bone.name)
            constraint = pose_bone.constraints.new('COPY_TRANSFORMS')'''
            
            # get the target object
            
            
            #constraint.target = bpy.data.objects.get(bone.parent.referenced_name)
            #constraint.subtarget = bone.parent.name
        
        return armature_obj


def insert_material_keyframes(fcurves, data_path, group_name, frames, values, index):
    if values:
        try:
            fc = fcurves.new(data_path=data_path, index=index)
        except:
            return
        fc.keyframe_points.add(len(frames))
        fc.keyframe_points.foreach_set('co', [x for co in list(map(lambda f, v: (f, v[0]), frames, values)) for x in co])
        fc.update()

def insert_keyframes(action, data_path, group_name, frames, values):
    if values:
        for i in range(len(values[0])):
            fc = action.fcurves.new(data_path=data_path, index=i, action_group=group_name)
            fc.keyframe_points.add(len(frames))
            fc.keyframe_points.foreach_set('co', [x for co in list(map(lambda f, v: (f, v[i]), frames, values)) for x in co])
            fc.update()


def insert_keyframes_fc(fcurves, data_path, group_name, frames, values):
    data_paths = [fc.data_path for fc in fcurves]
    if values:
        for i in range(len(values[0])):
            fc = fcurves.new(data_path=data_path, index=i)
            fc.keyframe_points.add(len(frames))
            fc.keyframe_points.foreach_set('co', [x for co in list(map(lambda f, v: (f, v[i]), frames, values)) for x in co])
            fc.update()


def convert_anm_values_tranformed(data_path: AnmDataPath, values, loc: Vector, rot: Quaternion, sca: Vector):
    if data_path == "location":
        updated_values = list()
        updated_loc = loc
        updated_loc.rotate(rot.inverted())
        for value_loc in values:
            vec_loc = Vector(value_loc) * 0.01
            vec_loc.rotate(rot.inverted())
            updated_values.append(vec_loc - updated_loc)
        return updated_values

    if data_path == "rotation_euler":
        rotation_list = []
        for value_rot in values:
            euler = rot_to_blender(value_rot)
            quat = euler.to_quaternion()
            quat = Quaternion((quat.w, quat.x, quat.y, quat.z))
            result_quat = rot.inverted() @ quat
            rotation_list.append(result_quat)

        return rotation_list

    if data_path == "rotation_quaternion":
        
        quat_array = np.array(values, dtype=np.float64)
        quat_array = quat_array[:, [3,0,1,2]]  * [1, -1, -1, -1]  # Convert to (w, x, y, z) and invert the quaternions
        bind_rot_array = np.array([[rot.w, -rot.x, -rot.y, -rot.z]], dtype=np.float64)
        
        result_array = np_mult_quaternions(bind_rot_array, quat_array)
        
        #invert y and z rotation, only if the scale has negative values on those axes
        if all(s < 0 for s in sca):
            #result_array[:,0] *= -1
            result_array[:,1] *= -1
            result_array[:,2] *= -1
            result_array[:,3] *= -1

        return result_array.tolist()

    if data_path == "scale":
        scale_list =  [Vector([abs(s / b) for s, b in zip(scale, sca)]) for scale in values]
        return scale_list
    
    return values


def np_mult_quaternions(q1: np.ndarray, q2: np.ndarray) -> np.ndarray:
    # q1 and q2 are arrays of shape (N, 4) representing quaternions
    w1, x1, y1, z1 = q1[:, 0], q1[:, 1], q1[:, 2], q1[:, 3]
    w2, x2, y2, z2 = q2[:, 0], q2[:, 1], q2[:, 2], q2[:, 3]

    w = w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2
    x = w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2
    y = w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2
    z = w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2

    return np.column_stack((w, x, y, z))

def convert_anm_values(data_path: AnmDataPath, values):
    if data_path == "location":
        return list(map(lambda x: pos_cm_to_m_tuple(x), values))
        #return [x*0.01 for x in values]
    if data_path == "rotation_euler":
        #return list(map(lambda x: rot_to_blender(x)[:], values))
        return [rot_to_blender(x)[:] for x in values]
    if data_path == "rotation_quaternion":
        #return list(map(lambda x: Quaternion((x[3], *x[:3])).inverted()[:], values))
        return [Quaternion((x[3], *x[:3])).inverted()[:] for x in values]
    if data_path == "scale":
        #return list(map(lambda x: Vector(([abs(y) for y in x]))[:], values))
        return [Vector(([abs(y) for y in x]))[:] for x in values]
    if data_path == "data.lens":
        #return list(map(lambda x: (focal_to_blender(x[0], 36.0),), values))
        return [(focal_to_blender(x[1], 36.0),) for x in values]

    return values


def menu_func_import(self, context):
    self.layout.operator(ImportXFBIN.bl_idname,
                         text='XFBIN Model / Animation Container (.xfbin)')
