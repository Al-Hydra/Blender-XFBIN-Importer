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
from .common.shaders import (shaders_dict, collision_mat)
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
    name: StringProperty(name="Name", subtype='FILE_PATH')


class ImportXFBIN(Operator, ImportHelper):
    """Loads an XFBIN file into blender"""
    bl_idname = "import_scene.xfbin"
    bl_label = "Import XFBIN"

    #files_list: CollectionProperty(type=XFBIN_IMPORT_FILES)

    files: CollectionProperty(type=bpy.types.OperatorFileListElement, options={'HIDDEN', 'SKIP_SAVE'})

    directory: StringProperty(subtype='DIR_PATH', options={'HIDDEN', 'SKIP_SAVE'})

    use_full_material_names: BoolProperty(
        name="Full material names",
        description="Display full name of materials in NUD meshes, instead of a shortened form")

    filter_glob: StringProperty(default="*.xfbin", options={"HIDDEN"})

    import_textures: BoolProperty(name='Import Textures', default=True)

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

        layout.prop(self, 'import_textures')
        layout.prop(self, "clear_textures")
        layout.prop(self, 'skip_lod_tex')
        layout.prop(self, 'use_full_material_names')
        layout.prop(self, 'import_modelhit')

        #add a list of files to import
        layout.label(text="Files:")
        layout.template_list("XFBIN_UL_IMPORT_LIST", "", self, "files", self, "index", rows=5)

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

    import_textures: BoolProperty(name='Import Textures', default=True)

    clear_textures: BoolProperty(name='Clear Textures List', default=False,
                                 description='Clear the textures list before importing\n'
                                              "WARNING: Only enable this option if you're sure of what you're doing")

    skip_lod_tex: BoolProperty(name='Skip LOD Textures', default=False)

    import_modelhit: BoolProperty(name='Import Stage Collision', default=True)

    index: IntProperty(name="Index")
    
    print("TRIGGERED")

    def execute(self, context):

        start_time = time.time()

        print("EXECUTING")
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
        self.import_textures = import_settings.get('import_textures')
        self.clear_textures = import_settings.get('clear_textures')
        self.skip_lod_tex = import_settings.get('skip_lod_tex')
        self.import_modelhit = import_settings.get('import_modelhit')

    xfbin: Xfbin
    collection: bpy.types.Collection

    def read(self, context):
        self.xfbin = read_xfbin(self.filepath)
        self.collection = self.make_collection(context)

        # Storing specific chunks in lists would help with importing them in a specific order
        # it's always better to import textures first, then models, then animations
        texture_chunks: List[NuccChunkTexture] = list()
        clump_chunks: List[NuccChunkClump] = list()
        dynamics_chunks: List[NuccChunkDynamics] = list()
        anm_chunks: List[NuccChunkAnm] = list()
        cam_chunks: List[NuccChunkCamera] = list()

        if self.clear_textures:
            bpy.context.scene.xfbin_texture_chunks_data.clear()


        for page in self.xfbin.pages:
            # Add all texture chunks inside the xfbin
            texture_chunks.extend(page.get_chunks_by_type('nuccChunkTexture'))

            dynamics_chunks.extend(page.get_chunks_by_type('nuccChunkDynamics'))

            clump_chunks.extend(page.get_chunks_by_type('nuccChunkClump'))
            anm_chunks.extend(page.get_chunks_by_type('NuccChunkAnm'))
            cam_chunks.extend(page.get_chunks_by_type('NuccChunkCamera'))

            

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
        
        # Import all dynamics chunks
        for dyn in dynamics_chunks:
            dyn: NuccChunkDynamics = dyn
            self.make_dynamics(dyn, context)
    
        # Create an empty object to store the anm chunks list
        empty_anm = bpy.data.objects.new(
            f'{XFBIN_ANMS_OBJ} [{self.collection.name}]', None)
        empty_anm.empty_display_size = 0

        self.collection.objects.link(empty_anm)
        empty_anm.xfbin_anm_chunks_data.init_data(anm_chunks, cam_chunks, context)
        for anm in anm_chunks: # Create camera objects for each anm that has a camera chunk
            for cam in cam_chunks:
                if anm.filePath != cam.filePath: # If cam and anm have same filepath they're in the same page
                    continue
                
                anm: NuccChunkAnm
                cam: NuccChunkCamera

                cam_data = bpy.data.cameras.new(f"{cam.name} ({anm.name})")
                cam_data.lens_unit = 'MILLIMETERS'
                cam_data.lens = focal_to_blender(cam.fov, 36.0)

                camera = bpy.data.objects.new(f"{cam.name} ({anm.name})", cam_data)
                camera.rotation_mode = 'QUATERNION'
                camera.animation_data_create()
                camera.animation_data.action = bpy.data.actions.get(f"{anm.name} (camera)")
                
                self.collection.objects.link(camera)

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

    def make_dynamics(self, dynamics: NuccChunkDynamics, context):

        dynamics_obj = bpy.data.objects.new(
            f'{XFBIN_DYNAMICS_OBJ} [{dynamics.name}]', None)
        dynamics_obj.empty_display_size = 0

        # Set the Xfbin dynamics properties
        dynamics_obj.xfbin_dynamics_data.init_data(dynamics)

        # Use Spring Group names instead of indices for attached spring groups
        for col in dynamics_obj.xfbin_dynamics_data.collision_spheres:
            if col.attach_groups == True and col.attached_count > 0:
                for c in range(col.attached_count):
                    col.attached_groups[c].value = next((sp.name for sp in dynamics_obj.xfbin_dynamics_data.spring_groups if col.attached_groups[c].value == str(sp.spring_group_index)), None)

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

            # Store these unknown values to set when exporting
            bone['unk_float'] = node.unkFloat
            bone['unk_short'] = node.unkShort
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
            
            material = bpy.data.materials.new(material_name)
            material.xfbin_material_data.init_data(xfbin_mat, mesh, mesh_flags)

            meshmat = mesh.materials[0]
            
            shader = int_to_hex_str(meshmat.flags, 4)
            

            '''if shader in shaders_dict:
                material = shaders_dict.get(shader)(
                    self, meshmat, xfbin_mat, material_name, material_name)
                
                material.xfbin_material_data.init_data(xfbin_mat)
                materials.append(material)
            else:'''
            material = shaders_dict.get("default")(
                self, meshmat, xfbin_mat, material, material_name)

            
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

def make_actions(anm: NuccChunkAnm, context) -> List[Action]:
    #print(f"-------------------{anm.name}-------------------")
    start_time = time.time()

    actions = list()
    
   # try:
    for entry in anm.other_entries:
        entry: AnmEntry

        action = bpy.data.actions.new(
            f'{anm.name} ({AnmEntryFormat(entry.entry_format).name.lower()})')
        
        group_name = action.groups.new(anm.name).name

        for curve in entry.curves:
            if curve is None or (not len(curve.keyframes)) or curve.data_path == AnmDataPath.UNKNOWN:
                continue

            #frames = list(map(lambda x: frame_to_blender(x.frame), curve.keyframes))
            frames = [frame_to_blender(x.frame) for x in curve.keyframes]
            
            #values = convert_anm_values(curve.data_path, list(map(lambda x: x.value, curve.keyframes)))
            values = convert_anm_values(curve.data_path, [x.value for x in curve.keyframes])

            if curve.data_path == AnmDataPath.CAMERA:
                # TODO: change camera rotation mode to quaternion, and lens unit to FOV
                # This should be done on playing the animation chunk
                data_path = 'data.lens'
            else:
                data_path = f'{AnmDataPath(curve.data_path).name.lower()}'


            for i in range(len(values[0])):
                fc = action.fcurves.new(
                    data_path=data_path, index=i, action_group=group_name)
                fc.keyframe_points.add(len(frames))
                fc.keyframe_points.foreach_set('co', [x for co in list(map(lambda f, v: (f, v[i]), frames, values)) for x in co])

                fc.update()
    
    for clump in anm.clumps:
        action = bpy.data.actions.new(f'{anm.name} ({clump.name})')

        arm_obj = bpy.data.objects.get(clump.chunk.name)
        if arm_obj is None:
            arm_obj = bpy.data.objects.get(clump.chunk.name)

        arm_sca = dict()
        arm_mat = dict()

        if arm_obj is not None:
            context.view_layer.objects.active = arm_obj

            for arm_bone in arm_obj.data.bones:
                arm_sca[arm_bone.name] = arm_bone.get('scale_signs')
                arm_mat[arm_bone.name] = Matrix(arm_bone.get('matrix', Matrix.Identity(4)))
            
            for arm_bone in arm_obj.pose.bones:
                arm_bone.rotation_mode = "QUATERNION"
                

        for bone in clump.bones:
            group_name = action.groups.new(bone.name).name

            if bone.anm_entry is None:
                continue


            mat_parent = arm_mat.get(bone.parent.name, Matrix.Identity(
                4)) if bone.parent else Matrix.Identity(4)
            mat = arm_mat.get(bone.name, Matrix.Identity(4))

            mat = (mat_parent.inverted() @ mat)
            loc, rot, sca = mat.decompose()
            rot.invert()
            sca = Vector(map(lambda a: 1/a, sca))

            bone_path = f'pose.bones["{group_name}"]'

            bone_parent = False
            if bone.parent:
                bone_parent = True


            for curve in bone.anm_entry.curves:
                if curve is None or (not len(curve.keyframes)) or curve.data_path == AnmDataPath.UNKNOWN:
                    continue

                frames = list(map(lambda x: frame_to_blender(x.frame), curve.keyframes))

                if (bone.parent != None):
                    #values = convert_anm_values_tranformed(curve.data_path, list(map(lambda x: x.value, curve.keyframes)), loc, rot, sca, rotate_vector, bone_parent)
                    values = convert_anm_values_tranformed(curve.data_path, [x.value for x in curve.keyframes], loc, rot, sca, bone_parent)
                else:
                    #values = convert_anm_values_tranformed_root(curve.data_path, list(map(lambda x: x.value, curve.keyframes)), loc, rot, sca)
                    values = convert_anm_values_tranformed_root(curve.data_path, [x.value for x in curve.keyframes], loc, rot, sca)

                if (curve.data_path == AnmDataPath.ROTATION_EULER):
                    curve.data_path = AnmDataPath.ROTATION_QUATERNION

                data_path = f'{bone_path}.{AnmDataPath(curve.data_path).name.lower()}'

                for i in range(len(values[0])):
                    fc = action.fcurves.new(
                        data_path=data_path, index=i, action_group=group_name)
                    fc.keyframe_points.add(len(frames))
                    fc.keyframe_points.foreach_set('co', [x for co in list(map(lambda f, v: (f, v[i]), frames, values)) for x in co])

                    fc.update()

        actions.append(action)
    '''except Exception as e:
        print(e)'''


    #calculate the time it took to make the actions
    print(f"Time: {time.time() - start_time}")


    '''
    # Create the constraints for the armatures if they exist
    for p in anm.coord_parents:
        if anm.clumps[p.parent_clump_index] != anm.clumps[p.child_clump_index]: # The parent and child clump are different, so it's a constraint

            arm_obj = bpy.data.objects.get(anm.clumps[p.child_clump_index].chunk.name + ' [C]')
            target_arm_obj = bpy.data.objects.get(anm.clumps[p.parent_clump_index].chunk.name + ' [C]')
            target_bone = anm.clumps[p.parent_clump_index].bones[p.parent_coord_index].name

            if arm_obj and target_arm_obj:
                # Create the child of constraint for the armature using the target armature and bone

                # Set the armature as the active object
                context.view_layer.objects.active = arm_obj

                # Check if the 'Child Of' constraint already exists, if not, add it
                if 'Child Of' not in arm_obj.constraints:
                    childof_constraint = arm_obj.constraints.new(type='CHILD_OF')
                else:
                    childof_constraint = arm_obj.constraints['Child Of']

                # Set the 'Child Of' constraint properties
                childof_constraint.target = target_arm_obj
                childof_constraint.subtarget = target_bone
                childof_constraint.inverse_matrix = Matrix.Identity(4)
            else: # One of the armatures doesn't exist
                print(f"Couldn't find one of the constraint armatures: {anm.clumps[p.child_clump_index].chunk.name + ' [C]'}")'''
                

    context.scene.render.fps = 30

    return actions





def convert_anm_values_tranformed(data_path: AnmDataPath, values, loc: Vector, rot: Quaternion, sca: Vector, parent: bool):
    if data_path == AnmDataPath.LOCATION:
        updated_values = list()
        for value_loc in values:
            vec_loc = Vector([value_loc[0],value_loc[1],value_loc[2]])
            vec_loc.rotate(rot)
            updated_values.append(vec_loc)
        updated_loc = loc
        updated_loc.rotate(rot)

        #return list(map(lambda x: ((x*0.01) - updated_loc)[:], updated_values))
        return [((x*0.01) - updated_loc)[:] for x in updated_values]

    if data_path == AnmDataPath.ROTATION_EULER:
        rotations = []
        startQuat = rot
        for frot in values:
            endQuat = rot @ rot_to_blender(frot).to_quaternion()
            if startQuat.dot(endQuat) < 0:
                endQuat.negate()
            
            rotations.append(endQuat)
        
        return rotations

    if data_path == AnmDataPath.ROTATION_QUATERNION:
        quat_list = list()

        for rotation in values:
            
            bind_rotaion = rot.conjugated()
            rotation = Quaternion((rotation[3], *rotation[:3]))
            #rotate it with the new rotation
            bind_rotaion.rotate(rotation)
            #invert the result
            quat_list.append(Quaternion(bind_rotaion).conjugated())

        return quat_list

    if data_path == AnmDataPath.SCALE:
        #return list(map(lambda x: (Vector(([abs(y) for y in x])))[:], values))
        return [Vector(([abs(y) for y in x]))[:] for x in values]
    return values




def convert_anm_values_tranformed_root(data_path: AnmDataPath, values, loc: Vector, rot: Quaternion, sca: Vector):
    if data_path == AnmDataPath.LOCATION:
        #return list(map(lambda x: (loc + pos_cm_to_m(x))[:], values))
        return [loc + pos_cm_to_m(x) for x in values]
    if data_path == AnmDataPath.ROTATION_EULER:
        #return list(map(lambda x: (((rot_to_blender(x).to_quaternion()).to_euler()).to_quaternion())[:], values))
        return [rot_to_blender(x).to_quaternion() for x in values]
    if data_path == AnmDataPath.ROTATION_QUATERNION:
        #return list(map(lambda x: (Quaternion((x[3], *x[:3])).inverted())[:], values))
        return [Quaternion((x[3], *x[:3])).inverted() for x in values]
    if data_path == AnmDataPath.SCALE:
        #return list(map(lambda x: (Vector(([abs(y) for y in x])))[:], values))
        return [Vector(([abs(y) for y in x])) for x in values]
    return values


def convert_anm_values(data_path: AnmDataPath, values):
    if data_path == AnmDataPath.LOCATION:
        #return list(map(lambda x: pos_cm_to_m_tuple(x), values))
        return [pos_cm_to_m_tuple(x) for x in values]
    if data_path == AnmDataPath.ROTATION_EULER:
        #return list(map(lambda x: rot_to_blender(x)[:], values))
        return [rot_to_blender(x)[:] for x in values]
    if data_path == AnmDataPath.ROTATION_QUATERNION:
        #return list(map(lambda x: Quaternion((x[3], *x[:3])).inverted()[:], values))
        return [Quaternion((x[3], *x[:3])).inverted()[:] for x in values]
    if data_path == AnmDataPath.SCALE:
        #return list(map(lambda x: Vector(([abs(y) for y in x]))[:], values))
        return [Vector(([abs(y) for y in x]))[:] for x in values]
    if data_path == AnmDataPath.CAMERA:
        #return list(map(lambda x: (focal_to_blender(x[0], 36.0),), values))
        return [(focal_to_blender(x[0], 36.0),) for x in values]

    return values


def menu_func_import(self, context):
    self.layout.operator(ImportXFBIN.bl_idname,
                         text='XFBIN Model Container (.xfbin)')
