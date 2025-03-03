import os
from itertools import chain
from typing import List
import time
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
from ..xfbin_lib.xfbin.structure import dds
from .common.coordinate_converter import *
from .common.helpers import (XFBIN_DYNAMICS_OBJ, XFBIN_ANMS_OBJ, XFBIN_TEXTURES_OBJ,
                             int_to_hex_str)
from .materials.shaders import (shaders_dict, collision_mat)
import cProfile


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
    
    def __init__(self):
        self.name = ""


class ImportXFBIN(Operator, ImportHelper):
    """Loads an XFBIN file into blender"""
    bl_idname = "import_scene.xfbin"
    bl_label = "Import XFBIN"

    files_list: CollectionProperty(type=XFBIN_IMPORT_FILES)
    
    fl_index: IntProperty(name="Index")

    files: CollectionProperty(type=bpy.types.OperatorFileListElement, options={'HIDDEN', 'SKIP_SAVE'})

    directory: StringProperty(subtype='DIR_PATH', options={'HIDDEN', 'SKIP_SAVE'})

    use_full_material_names: BoolProperty(
        name="Full material names",
        description="Display full name of materials in NUD meshes, instead of a shortened form")

    filter_glob: StringProperty(default="*.xfbin", options={"HIDDEN"})

    import_all_textures: BoolProperty(name='Import All Textures', default=True)
    
    import_animations: BoolProperty(name='Import Animations', default=True)

    clear_textures: BoolProperty(name='Clear Textures List', default=False,
                                 description='Clear the textures list before importing\n'
                                              "WARNING: Only enable this option if you're sure of what you're doing")

    skip_lod_tex: BoolProperty(name='Skip LOD Textures', default=False)

    import_modelhit: BoolProperty(name='Import Stage Collision', default=True)

    index: IntProperty(name="Index")

    def draw(self, context):
        layout = self.layout

        layout.use_property_split = True
        layout.use_property_decorate = True

        layout.prop(self, 'import_all_textures')
        layout.prop(self, "clear_textures")
        layout.prop(self, 'skip_lod_tex')
        layout.prop(self, 'use_full_material_names')
        layout.prop(self, 'import_modelhit')

        #add a list of files to import
        layout.label(text="Files:")
        layout.template_list("XFBIN_UL_IMPORT_LIST", "", self, "files_list", self, "fl_index", rows=5)

        row = layout.row(align=True)
        row.operator("xfbin.import_add_file", icon='ADD', text="")
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

    index: IntProperty(name="Index")
    

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
        self.use_full_material_names = import_settings.get(
            "use_full_material_names")
        self.import_all_textures = import_settings.get('import_all_textures')
        self.clear_textures = import_settings.get('clear_textures')
        self.skip_lod_tex = import_settings.get('skip_lod_tex')
        self.import_modelhit = import_settings.get('import_modelhit')
        
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
        
        #animations
        
        # Create an empty object to store the anm chunks list
        empty_anm = bpy.data.objects.new(
            f'{XFBIN_ANMS_OBJ} [{self.collection.name}]', None)
        empty_anm.empty_display_size = 0

        self.collection.objects.link(empty_anm)
        
        actions = self.make_actions(anm_chunks, cam_chunks, context)

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

        all_model_chunks = list(dict.fromkeys(
            chain(clump.model_chunks, *map(lambda x: x.model_chunks, clump.model_groups))))
        for nucc_model in all_model_chunks:

            if isinstance(nucc_model, NuccChunkModelPrimitiveBatch):
                self.make_primitive_batch(nucc_model, armature_obj, context)
                continue
            elif not (isinstance(nucc_model, NuccChunkModel) and nucc_model.nud):
                continue

            # Create modelhit object
            modelhit_obj = None
            if self.import_modelhit:
                modelhit_obj = self.make_modelhit(nucc_model.hit_chunk, armature_obj, context)
            
            nud = nucc_model.nud

            # Create an empty to store the NUD's properties, and set the armature to be its parent
            blender_mesh = bpy.data.meshes.new(nucc_model.name)
            #blender_mesh.auto_smooth_angle = 180
            #blender_mesh.use_auto_smooth = True
            #blender_mesh.create_normals_split()

            #create a bmesh to store all the meshes
            bm = bmesh.new()

            # Get the bone range that this NUD uses
            bone_range = nud.get_bone_range()

            # Set the mesh bone as the object's parent bone, if it exists (it should)
            mesh_bone = None
            if nucc_model.coord_chunk:
                mesh_bone: Bone = armature_obj.data.bones.get(
                    nucc_model.coord_chunk.name)

            custom_normals = list()

            deform = bm.verts.layers.deform.new("Vertex Weights")
            color = bm.loops.layers.color.new("Color")
            
            '''
            This is an unreliable way to get the number of UV layers, since the number of UV layers can vary between meshes
            uv_count = len(nud.mesh_groups[0].meshes[0].vertices[0].uv)
            uv_layers = [bm.loops.layers.uv.new(f"UV_{i}") for i in range(uv_count)]
            '''

            uv_layers = {}

            for group in nud.mesh_groups:
                for mat_index, mesh in enumerate(group.meshes):
                    mat_chunk = nucc_model.material_chunks[mat_index]

                    #add the material to the mesh
                    blender_mesh.materials.append(self.make_material(mat_chunk, mesh, [nucc_model.rigging_flag, group.bone_flags]))

                    uv_count = len(mesh.vertices[0].uv)

                    #check if the uv layers already exist
                    for uv in range(uv_count):
                        if not uv_layers.get(uv):
                            uv_layers[uv] = bm.loops.layers.uv.new(f"UV_{uv}")
                    

                    vCount = len(bm.verts)

                    # Vertices
                    for vtx in mesh.vertices:
                        vert = bm.verts.new(pos_scaled_to_blender(vtx.position))

                        # Tangents cannot be applied
                        normal = pos_to_blender(vtx.normal)
                        custom_normals.append(pos_to_blender(vtx.normal))
                        vert.normal = normal

                        if vtx.bone_weights:
                            for bone_id, bone_weight in zip(vtx.bone_ids, vtx.bone_weights):
                                if bone_weight > 0:
                                    vertex_group_index = vertex_group_indices[clump.coord_chunks[bone_id].name]
                                    vert[deform][vertex_group_index] = bone_weight
                        else:
                            vertex_group_index = vertex_group_indices[nucc_model.coord_chunk.name]
                            vert[deform][vertex_group_index] = 1

                    # Set up the indexing table inside the bmesh so lookups work
                    bm.verts.ensure_lookup_table()
                    bm.verts.index_update()

                    # For each triangle, add it to the bmesh
                    for mesh_face in mesh.faces:
                        tri_idxs = mesh_face

                        # Skip "degenerate" triangles
                        if len(set(tri_idxs)) != 3:
                            continue

                        try:
                            face = bm.faces.new((bm.verts[tri_idxs[0]+vCount], bm.verts[tri_idxs[1]+vCount], bm.verts[tri_idxs[2]+vCount]))
                            face.smooth = True
                            #set face material
                            face.material_index = mat_index

                            # Set up the UVs and colors for each vertex in the face
                            for loop in face.loops:
                                loop[color] = [x / 255 for x in mesh.vertices[loop.vert.index - vCount].color]
                                for uvi in range(uv_count):
                                    loop[uv_layers[uvi]].uv = uv_to_blender(mesh.vertices[loop.vert.index - vCount].uv[uvi])

                        except Exception as e:
                            # We might get duplicate faces for some reason
                            # print(e)
                            pass
                    
                    
            bm.to_mesh(blender_mesh)
            bm.free()
            

            blender_mesh.normals_split_custom_set_from_vertices(custom_normals)
            mesh_obj: bpy.types.Object = bpy.data.objects.new(
                nucc_model.name, blender_mesh)
            
            # Set the NUD properties
            mesh_obj.xfbin_nud_data.init_data(
                nucc_model, nucc_model.coord_chunk.name if nucc_model.coord_chunk else None)

            # set the mesh's parent to the armature
            mesh_obj.parent = armature_obj

            # Set the mesh's parent bone to the mesh bone
            if mesh_bone:
                mesh_obj.parent_bone = mesh_bone.name
            
            # If we're not going to parent it, transform the mesh by the bone's matrix
            if mesh_bone:                        
                blender_mesh.transform(nucc_model.coord_chunk.node.matrix)
             
            #set active color
            mesh_obj.data.color_attributes.render_color_index = 0
            mesh_obj.data.color_attributes.active_color_index = 0

            # Link the mesh object to the collection
            self.collection.objects.link(mesh_obj)

            #parent the modelhit to the empty
            #if modelhit_obj:
            #    modelhit_obj.parent = empty

            # Create the vertex groups for all bones (required)
            for name in [coord.node.name for coord in clump.coord_chunks]:
                mesh_obj.vertex_groups.new(name=name)
            
            '''# Create the vertex groups for bones in the bone range
            for name in [clump.coord_chunks[i].name for i in range(bone_range[0], bone_range[1]+1)]:
                mesh_obj.vertex_groups.new(name=name)'''

            # Apply the armature modifier
            modifier = mesh_obj.modifiers.new(
                type='ARMATURE', name="Armature")
            modifier.object = armature_obj

            # Add the xfbin materials to the mesh
            #for blender_mat in blender_mats:
            #    overall_mesh.materials.append(blender_mat)
                    
                    
    def make_modelhit(self, modelhit: NuccChunkModelHit, armature_obj: Object, context):

        if not isinstance(modelhit, NuccChunkModelHit):
            pass
        else:

            # Make an empty to store the modelhit's properties, and set the armature to be its parent
            hit_empty = bpy.data.objects.new(f'{modelhit.name}_[HIT]', None)
            hit_empty.empty_display_size = 0
            hit_empty.parent = armature_obj

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

                # parent the object to the empty
                obj.parent = hit_empty

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

        vertex = 0
        for i, mesh in enumerate(batch.meshes):
            obj = self.make_primitive_vertex(f"{batch.name}_{i}",
                                             batch.primitive_vertex_chunk.vertices[vertex:vertex+mesh.vertex_count],
                                             armature_obj, armature_obj.data.bones[mesh.parent_bone].name)
            
            #transform the object by the bone matrix
            obj.data.transform(armature_obj.data.bones[mesh.parent_bone].matrix_local.to_4x4())
            
            # link the object to the current collection
            self.collection.objects.link(obj)

            # parent the object to the empty
            obj.parent = primitive_empty

        #TODO: use batch.material_chunk to make a material

        '''mat: XfbinMaterialPropertyGroup = self.materials.add()
        material = mat.init_data(batch.material_chunk)'''

    def make_primitive_vertex(self, name, vertices, armature_obj: Object, parent_bone):

        bm = bmesh.new()
        # Make a mesh to store the primitive vertex data
        mesh = bpy.data.meshes.new(f'{name}')

        uv = [v.uv for v in vertices]
        color = [v.color for v in vertices]

        for i in range(0, len(vertices), 3):
            # add verts
            bmv1 = bm.verts.new(vertices[i].position)
            bmv1.normal = vertices[i].normal
            bmv2 = bm.verts.new(vertices[i+1].position)
            bmv2.normal = vertices[i+1].normal
            bmv3 = bm.verts.new(vertices[i+2].position)
            bmv3.normal = vertices[i+2].normal

            # draw faces
            face = bm.faces.new((bmv1, bmv2, bmv3))
        
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        # clean up
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
        bmesh.ops.scale(bm, vec=(0.01, 0.01, 0.01), verts=bm.verts)

        # apply the changes to the mesh we created
        bm.to_mesh(mesh)

        #add uv data
        mesh.uv_layers.new(name='UVMap')
        uv_layer = mesh.uv_layers.active.data
        for i, uv in enumerate(uv_layer):
            uv.uv = vertices[i].uv
        
        #add color data
        mesh.vertex_colors.new(name='Color')
        color_layer = mesh.vertex_colors.active.data
        for i, color in enumerate(color_layer):
            color.color = vertices[i].color

        # free bmesh
        bm.free()
        
        # create a new object with our mesh data
        obj = bpy.data.objects.new(f'{name}', mesh)

        return obj

    '''def make_texture(self, name, nut_texture: NuccChunkTexture):
        #convert Nut Texture to DDS
        self.texture_data = dds.NutTexture_to_DDS(nut_texture)


        if bpy.data.images.get(self.name):
            #update existing image
            self.image = bpy.data.images[name]
            self.image.pack(data=self.texture_data, data_len=len(self.texture_data))
            self.image.source = 'FILE'
            self.image.filepath_raw = path
            self.image.use_fake_user = True
            self.image['nut_pixel_format'] = self.pixel_format        

        else:
            #create new image
            self.image = bpy.data.images.new(tex_name, width=self.width, height=self.height)
            self.image.pack(data=self.texture_data, data_len=len(self.texture_data))
            self.image.source = 'FILE'
            self.image.filepath_raw = path
            self.image.use_fake_user = True
            #add custom properties to the image
            self.image['nut_pixel_format'] = self.pixel_format  
            self.image['nut_mipmaps_count'] = self.mipmap_count   '''

    def make_material(self, xfbin_mat: NuccChunkMaterial, mesh, mesh_flags) -> Material:
        material_name = xfbin_mat.name
        if not bpy.data.materials.get(material_name):
            
            #material = bpy.data.materials.new(material_name)
            #material.xfbin_material_data.init_data(xfbin_mat, mesh, mesh_flags)

            #meshmat = mesh.materials[0]
            
            shader = int_to_hex_str(mesh.materials[0].flags, 4)
            

            if shader in shaders_dict:
                material = shaders_dict.get(shader)(self, mesh, xfbin_mat, mesh_flags)
            else:
                material = shaders_dict.get("default")( self, mesh, xfbin_mat, mesh_flags)

            
        else:
            material = bpy.data.materials.get(material_name)
            material.xfbin_material_data.init_data(xfbin_mat, mesh, mesh_flags)

        return material

    def nud_mesh_to_bmesh(self, mesh: NudMesh, clump: NuccChunkClump, vertex_group_indices, custom_normals, mat_index) -> BMesh:
        bm = bmesh.new()

        deform = bm.verts.layers.deform.new("Vertex Weights")
        color = bm.loops.layers.color.new("Color")
        
        uv_layers = [bm.loops.layers.uv.new(f"UV_{i}") for i in range(len(mesh.vertices[0].uv))]


        # Vertices
        for vtx in mesh.vertices:
            vert = bm.verts.new(pos_scaled_to_blender(vtx.position))

            # Tangents cannot be applied
            #normal = pos_to_blender(vtx.normal)
            custom_normals.append(pos_to_blender(vtx.normal))
            #vert.normal = normal

            if vtx.bone_weights:
                for bone_id, bone_weight in zip(vtx.bone_ids, vtx.bone_weights):
                    if bone_weight > 0:
                        vertex_group_index = vertex_group_indices[clump.coord_chunks[bone_id].name]
                        vert[deform][vertex_group_index] = bone_weight

        # Set up the indexing table inside the bmesh so lookups work
        bm.verts.ensure_lookup_table()
        bm.verts.index_update()

        # For each triangle, add it to the bmesh
        for mesh_face in mesh.faces:
            tri_idxs = mesh_face

            # Skip "degenerate" triangles
            if len(set(tri_idxs)) != 3:
                continue

            try:
                face = bm.faces.new(
                    (bm.verts[tri_idxs[0]], bm.verts[tri_idxs[1]], bm.verts[tri_idxs[2]]))
                face.smooth = True
                #set face material
                face.material_index = mat_index

                # Set up the UVs and colors for each vertex in the face
                for loop in face.loops:
                    loop[color] = [x / 255 for x in mesh.vertices[loop.vert.index].color]
                    for i in range(len(mesh.vertices[0].uv)):
                        loop[uv_layers[i]].uv = uv_to_blender(mesh.vertices[loop.vert.index].uv[i])

            except Exception as e:
                # We might get duplicate faces for some reason
                # print(e)
                pass

        return bm

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
            group_name = action.groups.new(anm.name).name
                
                # Link the camera to the collection and to animation empty
                #camera.parent = empty_anm
            
            '''for lightdirc in lightdirc_chunks:
                if anm.filePath != lightdirc.filePath:
                    continue

                anm: NuccChunkAnm
                lightdirc: NuccChunkLightDirc

                lightdirc_data = bpy.data.lights.new(f"{lightdirc.name} ({anm.name})", 'SUN')
        
                light_dirc = bpy.data.objects.new(f"{lightdirc.name} ({anm.name})", lightdirc_data)
                light_dirc.rotation_mode = 'QUATERNION'
                light_dirc.animation_data_create()
                light_dirc.animation_data.action = bpy.data.actions.get(f"{anm.name} (lightdirc)")
                

                self.collection.objects.link(light_dirc)
                light_dirc.parent = empty_anm
            
            for lightpoint in lightpoint_chunks:
                if anm.filePath != lightpoint.filePath:
                    continue

                anm: NuccChunkAnm
                lightpoint: NuccChunkLightPoint

                lightpoint_data = bpy.data.lights.new(f"{lightpoint.name} ({anm.name})", 'POINT')
                lightpoint_data.use_custom_distance = True
        
                light_point = bpy.data.objects.new(f"{lightpoint.name} ({anm.name})", lightpoint_data)
                light_point.rotation_mode = 'QUATERNION'
                light_point.animation_data_create()
                light_point.animation_data.action = bpy.data.actions.get(f"{anm.name} (lightpoint)")
                
                self.collection.objects.link(light_point)
                light_point.parent = empty_anm'''

            '''for ambient in ambient_chunks:
                if anm.filePath != ambient.filePath:
                    continue

                anm: NuccChunkAnm
                ambient_chunk: NuccChunkAmbient


                # Since ambient light is environment light, we need to use the World settings
                # Therefore, we don't need to create a light object for it but a World object to the scene


                ambient_data = bpy.data.lights.new(f"{ambient_chunk.name} ({anm.name})", 'AREA')

                ambient = bpy.data.objects.new(f"{ambient_chunk.name} ({anm.name})", ambient_data)
                ambient.animation_data_create()
                ambient.animation_data.action = bpy.data.actions.get(f"{anm.name} (ambient)")

                self.collection.objects.link(ambient)
                ambient.parent = empty_anm'''

            start_time = time.time()

            for entry in anm.other_entries:
                entry: AnmEntry

                if entry.entry_format == AnmEntryFormat.CAMERA:
                    #for cameras we're gonna need to make a separate action for each camera
                    camera_action = bpy.data.actions.new(f'{anm.name} (camera)')
                    group_name = action.groups.new("camera").name
                
                    for curve in entry.curves:
                        if curve is None or (not len(curve.keyframes)) or curve.data_path == AnmDataPath.UNKNOWN:
                            continue

                        frames = list(map(lambda x: frame_to_blender(x.frame), curve.keyframes))
                        
                        values = convert_anm_values(curve.data_path, list(map(lambda x: x.value, curve.keyframes)))
                        
                        insert_keyframes(camera_action, curve.data_path, group_name, frames, values)
                    
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

                arm_obj = bpy.data.objects.get(clump.chunk.name)
                if arm_obj is None:
                    arm_obj = bpy.data.objects.get(clump.chunk.name + ' [C]')

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
                        arm_mat[arm_bone.name] = Matrix(arm_bone.get('matrix'))
                        arm_rot[arm_bone.name] = arm_bone.get('rotation_quat')
                        arm_loc[arm_bone.name] = arm_bone.get('orig_coords')[0]
                        arm_sca[arm_bone.name] = arm_bone.get('orig_coords')[2]
                        arm_blender_mat[arm_bone.name] = arm_bone.matrix
                        arm_euler[arm_bone.name] = [math.radians(x) for x in arm_bone.get('orig_coords')[1]]

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
                        
                        insert_keyframes(clump_action, data_path, group_name, frames, values)

                #materials
                '''for material in clump.materials:
                    
                    blender_mat = bpy.data.materials.get(material.name)
                    if not blender_mat:
                        continue
                    
                    group_name = action.groups.new(material.name).name
                    
                    blender_mat.animation_data_create()
                    blender_mat.node_tree.animation_data_create()
                    
                    
                    
                    
                    blender_mat.animation_data.action = action
                    
                    mat_action = blender_mat.animation_data.action
                    
                    #find the output node
                    nodetree = blender_mat.node_tree                    
                    output_node = nodetree.get_output_node('EEVEE')
                    
                    #get the node linked to the output node
                    if output_node:
                        shader_node = output_node.inputs['Surface'].links[0].from_node
                    else:
                        continue
                    
                    
                    for curve in material.anm_entry.curves:
                        
                        #UVs
                        input_string = material_inputs.get(curve.data_path)
                        if input_string:
                            node_input = shader_node.inputs.get(input_string)
                            if node_input:
                                for keyframe in curve.keyframes:
                                    node_input.default_value = keyframe.value[0]
                                    node_input.keyframe_insert(data_path="default_value", frame=keyframe.frame * 0.01
                                
                                for keyframe in curve.keyframes:
                                    # Insert keyframe into the action
                                    fcurve = mat_action.fcurves.find(f'node_tree.nodes["{shader_node.name}"].inputs["{input_string}"].default_value', index=0)
                                    if not fcurve:
                                        fcurve = mat_action.fcurves.new(data_path=f'node_tree.nodes["{shader_node.name}"].inputs["{input_string}"].default_value', index=0, action_group=group_name)
                                    fcurve.keyframe_points.insert(frame=keyframe.frame * 0.01, value=keyframe.value[0])'''
        

            actions.append(action)
    
        
        #print(f"Animation(s) imported in: {time.time() - start_time}")
        context.scene.render.fps = 30

        return actions


def insert_keyframes(action, data_path, group_name, frames, values):
    if values:
        for i in range(len(values[0])):
            fc = action.fcurves.new(data_path=data_path, index=i, action_group=group_name)
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
        rotations = [rot.rotation_difference(rot_to_blender(rotation).to_quaternion()) for rotation in values]
        
        return rotations

    if data_path == "rotation_quaternion":
        
        #method 1
        quat_list = [rot.rotation_difference(Quaternion((rotation[3], *rotation[:3])).inverted()) for rotation in values]
        
        #method 2
        '''quat_list = []
        for rotation in values:
            quat = Quaternion((rotation[3], *rotation[:3]))
            brot = rot.copy()
            brot.rotate(quat)
            
            quat_list.append(brot.inverted())'''
            
        #Method 3
        '''quat_list = []
        for rotation in values:
            # Create the quaternion from the rotation values and invert it
            # Adjust for negative scale
            quat = Quaternion((rotation[3], *rotation[:3])).inverted()
            
            # Apply the inverted rotation to the original rotation
            if any(s < 0 for s in sca):
                #convert the rotation to euler then swap the axis
                rotation = Quaternion((rotation[3], *rotation[:3])).to_euler('ZYX')
                rotation = Euler((rotation.z, rotation.y, rotation.x), 'XYZ')
                brot = rot.inverted() @ rotation.to_quaternion()
                brot.invert()
            else:
                brot = rot.inverted() @ quat
            
            quat_list.append(brot)'''

        return quat_list

    if data_path == "scale":
        scale_list =  [Vector([abs(s / b) for s, b in zip(scale, sca)]) for scale in values]
        return scale_list
    
    return values



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
