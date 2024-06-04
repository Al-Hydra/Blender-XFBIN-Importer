from multiprocessing import cpu_count
from functools import reduce
from itertools import chain
from os import path
from typing import Dict, List
import time

import bmesh
import bpy
from bpy.props import (BoolProperty, CollectionProperty, EnumProperty,
                       StringProperty)
from bpy.types import (Armature, EditBone, Mesh, MeshLoop, MeshLoopTriangle,
                       MeshVertex, Object, Operator)
from bpy_extras.io_utils import ExportHelper
from mathutils import Matrix, Vector

from ..xfbin_lib.xfbin.structure.br.br_nud import (NudBoneType, NudUvType,
                                                   NudVertexType)
from ..xfbin_lib.xfbin.structure.br.br_nut import BrNut
from ..xfbin_lib.xfbin.structure.nucc import (ClumpModelGroup, CoordNode,
                                              Dynamics1, Dynamics2,
                                              MaterialTextureGroup, ModelHit,
                                              NuccChunkClump, NuccChunkCoord,
                                              NuccChunkDynamics,
                                              NuccChunkMaterial,
                                              NuccChunkModel,
                                              NuccChunkModelHit, NuccChunkNull,
                                              NuccChunkTexture, RiggingFlag)
from ..xfbin_lib.xfbin.structure.nud import (Nud, NudMaterial,
                                             NudMaterialProperty,
                                             NudMaterialTexture, NudMesh,
                                             NudMeshGroup, NudVertex)
from ..xfbin_lib.xfbin.structure.nut import Nut, NutTexture
from ..xfbin_lib.xfbin.structure.dds import DDS_to_NutTexture, read_dds
from ..xfbin_lib.xfbin.structure.xfbin import Xfbin
from ..xfbin_lib.xfbin.util.binary_reader.binary_reader.binary_reader import (
    BinaryReader, Endian)
from ..xfbin_lib.xfbin.util.iterative_dict import IterativeDict
from ..xfbin_lib.xfbin.xfbin_reader import read_xfbin
from ..xfbin_lib.xfbin.xfbin_writer import write_xfbin_to_path
from .common.coordinate_converter import *
from .common.helpers import (XFBIN_DYNAMICS_OBJ, XFBIN_TEXTURES_OBJ,
                             hex_str_to_int)
from .panels.clump_panel import (ClumpModelGroupPropertyGroup,
                                 ClumpPropertyGroup)
from .panels.common import BoolPropertyGroup
from .panels.dynamics_panel import (CollisionSpheresPropertyGroup,
                                    DynamicsPropertyGroup,
                                    SpringGroupsPropertyGroup)
from .panels.nud_mesh_panel import (NudMaterialPropertyGroup,
                                    NudMaterialPropPropertyGroup,
                                    NudMaterialTexturePropertyGroup,
                                    NudMeshPropertyGroup)
from .panels.nud_panel import NudPropertyGroup
from .panels.texture_chunks_panel import (NutTexturePropertyGroup,
                                          TextureChunksListPropertyGroup,
                                          XfbinTextureChunkPropertyGroup)
from .panels.materials_panel import (GlobalNutPropertyGroup)



class ExportXfbin(Operator, ExportHelper):
    """Export current collection as XFBIN file"""
    bl_idname = 'export_scene.xfbin'
    bl_label = 'Export XFBIN'

    filename_ext = '.xfbin'

    filter_glob: StringProperty(default='*.xfbin', options={'HIDDEN'})

    def collection_update(self, context):
        self.meshes_to_export.clear()
        col = bpy.data.collections.get(self.collection)
        

        if col:
            for armature in [obj for obj in col.objects if obj.type == 'ARMATURE']:
                for empty in [obj for obj in armature.children if obj.type == 'EMPTY']:
                    self.meshes_to_export.add().name = empty.name
        


    filepath: StringProperty(
        name='File Path',
        description='Filepath used for exporting the XFBIN file',
        maxlen=1024,
        subtype='FILE_PATH',
    )

    collection: StringProperty(
        name='Collection',
        description='The collection to be exported. All armatures in the collection will be converted and put in the same XFBIN',
        update=collection_update,
    )

    inject_to_xfbin: BoolProperty(
        name='Inject to existing XFBIN',
        description='If True, will add (or overwrite) the exportable models as pages in the selected XFBIN.\n'
        'If False, will create a new XFBIN and overwrite the old file if it exists.\n\n'
        'NOTE: If True, the selected path has to be an XFBIN file that already exists, and that file will be overwritten',
        default=True,
    )

    export_clumps: BoolProperty(
        name='Export clumps',
        description='If True, will export the armatures and their contents of each to the XFBIN.',
        default=True,
    )

    export_meshes: BoolProperty(
        name='Export meshes',
        description='If True, will export the meshes of each armature in the collection to the XFBIN.\n'
        'If False, will NOT rebuild the meshes nor update the ones in the XFBIN.\n\n'
        'NOTE: "Inject to existing XFBIN" has to be enabled for this option to take effect',
        default=True,
    )

    export_bones: BoolProperty(
        name='Export bones',
        description='If True, will export the bones of each armature in the collection to the XFBIN.\n'
        'If False, will NOT update the bone coordinates in the XFBIN.\n\n'
        'NOTE: "Inject to existing XFBIN" has to be enabled for this option to take effect',
        default=True,
    )

    use_original_coords: BoolProperty(
        name='Export orignal bones',
        description='If this option is enabled, the original bone info would be exported if found insted of the modified one',
        default=True,
    )

    export_textures: BoolProperty(
        name='Export textures',
        description='If True, will include the NUT textures provided in the "Texture Chunks" panel in the "#XFBIN Textures" object to the XFBIN.\n'
        'If False, will NOT export any textures, and will reuse the textures from the existing XFBIN.\n\n',
        default=True,
    )

    inject_to_clump: BoolProperty(
        name='Inject to existing Clump',
        description='If True, will ONLY overwrite existing models/bones in the clumps of the existing XFBIN.\n'
        'If False, will rebuild the clumps instead of copying their contents.\n'
        'Should be used whenever rebuilding an XFBIN results in undesired behavior.\n\n'
        'NOTE: The "Clump Properties" of each armature will be ignored if this option is enabled.\n'
        'NOTE: "Inject to existing XFBIN" has to be enabled for this option to take effect',
        default=False,
    )

    export_specific_meshes: BoolProperty(
        name='Export specific meshes',
        description='If True, will export only the selected (NUD) models in the box below.\n'
        'If "Inject to existing XFBIN" is also enabled, the existing models will be used instead of the non-exported models.\n'
        'If False, will export all models in the collection',
        default=False,
    )

    meshes_to_export: CollectionProperty(
        type=BoolPropertyGroup,
    )

    export_dynamics: BoolProperty(
        name='Export Dynamics (Physics)',
        description='',
        default=True,
    )
    
    def draw(self, context):
        layout = self.layout

        layout.label(text='Select a collection to export:')
        layout.prop_search(self, 'collection', bpy.data, 'collections')

        if self.collection:
            inject_row = layout.row()
            inject_row.prop(self, 'inject_to_xfbin')

            layout.prop(self, 'export_textures')
            layout.prop(self, 'export_clumps')

            if self.export_clumps:
                box = layout.box()
                box.prop(self, 'inject_to_clump')

                box.prop(self, 'export_meshes')
                if self.export_meshes:
                    box.prop(self, 'export_specific_meshes')

                box.prop(self, 'export_bones')

                if self.export_bones:
                    box.prop(self, 'use_original_coords')

                box.prop(self, 'export_dynamics')


            if self.export_specific_meshes:
                # Update the "meshes to export" collection
                if not self.meshes_to_export:
                    self.collection_update(context)

                box1 = layout.box()
                collection = bpy.data.collections.get(self.collection)

                if not collection:
                    box1.label(text='No collection has been selected.')
                else:
                    box1.label(text='Selected models:')
                    # Draw a check box for each NUD to choose which models should be exported
                    for item in self.meshes_to_export:
                        row = box1.split(factor=0.80)

                        row.label(text=item.name)
                        row.prop(item, 'value', text='')

    def invoke(self, context, event):
        # Set the collection to the active collection if no collection has been selected
        if not self.collection:
            if bpy.context.collection.name in bpy.data.collections:
                self.collection = bpy.context.collection.name
            else:
                #set the collection to the first collection in the list if the active collection is not in the list
                self.collection = ''
        
        # set the file name to the collection name if no file name has been set
        if not self.filepath:
            self.filepath = self.collection + '.xfbin' if self.collection else 'untitled.xfbin'
        
        # open the file browser
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


    def execute(self, context):
        #import time


        if not self.collection:
            self.report({'ERROR'}, 'No collection has been selected.')
            
            # open the file browser again
            context.window_manager.fileselect_add(self)
            return {'RUNNING_MODAL'}

        # try:
        start_time = time.time()
        exporter = XfbinExporter(self, self.filepath, self.as_keywords(ignore=('filter_glob',)))
        exporter.export_collection(context)

        elapsed_s = "{:.2f}s".format(time.time() - start_time)
        self.report({'INFO'}, f'Finished exporting {exporter.collection.name} in {elapsed_s}')
        print(f'Finished exporting {exporter.collection.name} in {elapsed_s}')
        return {'FINISHED'}
        # except Exception as e:
        #     print(e)
        #     self.report({'ERROR'}, str(e))
        # return {'CANCELLED'}


class XfbinExporter:
    def __init__(self, operator: Operator, filepath: str, export_settings: dict):
        self.operator = operator
        self.filepath = filepath
        self.collection: bpy.types.Collection = bpy.data.collections[export_settings.get('collection')]

        self.inject_to_xfbin = export_settings.get('inject_to_xfbin')

        self.export_clumps = export_settings.get('export_clumps')
        self.export_meshes = export_settings.get('export_meshes')
        self.export_bones = export_settings.get('export_bones')
        self.use_original_coords = export_settings.get('use_original_coords')
        self.export_textures = export_settings.get('export_textures')
        self.inject_to_clump = export_settings.get('inject_to_clump')
        self.export_specific_meshes = export_settings.get('export_specific_meshes')
        self.meshes_to_export = export_settings.get('meshes_to_export')
        self.export_dynamics = export_settings.get('export_dynamics')


    xfbin: Xfbin

    def export_collection(self, context):
        self.xfbin = Xfbin()
        if self.inject_to_xfbin:
            if not path.isfile(self.filepath):
                raise Exception(f'Cannot inject XFBIN - File does not exist: {self.filepath}')

            self.xfbin = read_xfbin(self.filepath)
        else:
            #self.export_meshes = self.export_bones = self.export_textures = True
            self.inject_to_clump = False


        # Export textures
        '''if self.export_textures:
            obj_name = f'{XFBIN_TEXTURES_OBJ} [{self.collection.name}]'
            texture_chunks_obj = self.collection.objects.get(obj_name)

            if not texture_chunks_obj:
                self.operator.report(
                    {'WARNING'}, f'Could not export textures. Make sure that the "{obj_name}" object is inside the collection.')
            else:
                texture_chunks_data: TextureChunksListPropertyGroup = texture_chunks_obj.xfbin_texture_chunks_data
                
                for i in range(len(texture_chunks_data.texture_chunks)):
                    tex_chunk: NuccChunkTexture = self.make_texture(texture_chunks_data.texture_chunks[i])
                    if tex_chunk.nut.texture_count > 0:
                        self.xfbin.add_chunk_page(tex_chunk)'''

                
        # Export clumps
        if self.export_clumps:
            for armature_obj in [obj for obj in self.collection.objects if obj.type == 'ARMATURE']:
                # Create a NuccChunkClump from the armature
                clump = self.make_clump(armature_obj, context)

                #get the dynamics object
                dynamics_obj = self.collection.objects.get(f'{XFBIN_DYNAMICS_OBJ} [{armature_obj.name[:-4]}]')
                if dynamics_obj:
                    dynamics = self.make_dynamics(dynamics_obj, context, clump)
                    self.xfbin.add_chunk_page(dynamics)
                
                if not self.inject_to_clump:
                    self.xfbin.add_clump_page(clump)
                else:
                    # Try to get the clump in the existing xfbin
                    old_clump = self.xfbin.get_chunk_page(clump)

                    if old_clump:
                        # There should be only 1 clump per page anyway
                        old_clump: NuccChunkClump = old_clump[1].get_chunks_by_type(NuccChunkClump)[0]
                    else:
                        self.operator.report(
                            {'WARNING'}, f'{clump.name} was not found in the existing XFBIN and will be skipped.')
                        continue

                    clump_coords = {c.name: c for c in clump.coord_chunks}
                    clump_models = {c.name: c for c in clump.model_chunks}

                    # Copy the coords
                    for coord in old_clump.coord_chunks:
                        new_coord = clump_coords.get(coord.node.name)
                        if new_coord is not None:
                            coord.node.copy_from(new_coord.node)

                    # Copy the models
                    for model in old_clump.model_chunks:
                        new_model = clump_models.get(model.name)
                        if new_model is not None:
                            model.copy_from(new_model)

                    # Copy the model groups
                    for i, group in enumerate(old_clump.model_groups):
                        if i >= len(clump.model_groups):
                            break

                        new_group = clump.model_groups[i]
                        new_group_models = {c.name: c for c in new_group.model_chunks}

                        group.flag0 = new_group.flag0
                        group.flag1 = new_group.flag1
                        group.unk = new_group.unk

                        for model in group.model_chunks:
                            new_model = new_group_models.get(model.name)
                            if new_model is not None:
                                model.copy_from(new_model)

        # Write the xfbin
        write_xfbin_to_path(self.xfbin, self.filepath)
        

    def make_clump(self, armature_obj: Object, context) -> NuccChunkClump:
        """Creates and returns a NuccChunkClump made from an Armature and its child meshes."""

        # Set the armature as the active object to be able to get its edit bones
        context.view_layer.objects.active = armature_obj

        armature: Armature = armature_obj.data
        empties: List[Mesh] = [obj for obj in armature_obj.children if obj.type == 'EMPTY']

        clump_data: ClumpPropertyGroup = armature_obj.xfbin_clump_data

        # Remove the added " [C]" from the clump's name if it exists
        clump = NuccChunkClump(clump_data.path, armature.name[:-4] if armature.name.endswith(' [C]') else armature.name)
        old_clump = None
        clump.has_data = True
        clump.has_props = True

        # Get the clump data properties
        clump.field00 = clump_data.field00

        clump.coord_flag0 = clump_data.coord_flag0
        clump.coord_flag1 = clump_data.coord_flag1

        clump.model_flag0 = clump_data.model_flag0
        clump.model_flag1 = clump_data.model_flag1

        if self.inject_to_xfbin:
            # Try to get the clump in the existing xfbin
            old_clump = self.xfbin.get_chunk_page(clump)

            if old_clump:
                # There should be only 1 clump per page anyway
                old_clump: NuccChunkClump = old_clump[1].get_chunks_by_type(NuccChunkClump)[0]

        if self.export_bones:
            clump.coord_chunks = self.make_coords(armature, clump, context)
        elif self.export_bones and self.use_original_coords:
            clump.coord_chunks = old_clump.coord_chunks
        elif old_clump:
            clump.coord_chunks = old_clump.coord_chunks
        '''else:
            self.operator.report({'ERROR_INVALID_INPUT'}, 'Could not export bones. Please check the exporter options.')
            raise Exception('Failed to export.')'''

        # Export meshes
        if self.export_meshes:
            # Create the material chunks
            xfbin_mats = dict()
            '''for mat in clump_data.materials:
                xfbin_mats[mat.material_name] = self.make_xfbin_material(mat, clump, context)'''

            # Create the model chunks as a dict to make it easier to preserve order
            model_chunks = {m.name: m for m in self.make_models(empties, clump, old_clump, context)}

            # Set the model chunks and model groups based on the clump data
            clump.model_chunks = [model_chunks[c.value] for c in clump_data.models if c.value in model_chunks]

            # Add a None reference for model groups that might use it
            # Hopefully no actual models have that name...
            model_chunks['None'] = None

            # Add the model groups from the clump data
            clump.model_groups = list()
            for group in clump_data.model_groups:
                group: ClumpModelGroupPropertyGroup
                g = ClumpModelGroup()

                g.flag0 = group.flag0
                g.flag1 = group.flag1
                g.unk = hex_str_to_int(group.unk)
                g.model_chunks = [model_chunks[c.value] for c in group.models if c.value in model_chunks]

                clump.model_groups.append(g)
        elif old_clump:
            clump.model_chunks = old_clump.model_chunks
            clump.model_groups = old_clump.model_groups
        else:
            self.operator.report({'ERROR_INVALID_INPUT'}, 'Could not export meshes. Please check the exporter options.')
            raise Exception('Failed to export.')

        return clump

    def make_coords(self, armature: Armature, clump: NuccChunkClump, context) -> List[NuccChunkCoord]:
        bpy.ops.object.mode_set(mode='EDIT')

        coords: List[NuccChunkCoord] = list()
        

        def make_coord(bone: EditBone, coord_parent: CoordNode = None, parent_matrix: Matrix = Matrix.Identity(4)):
            coord = NuccChunkCoord(clump.filePath, bone.name)
            coord.node = CoordNode(coord)
            coord.has_props = True
            coord.has_data = True
            
            # Set up the node
            node = coord.node
            node.parent = coord_parent

            local_matrix: Matrix = parent_matrix.inverted() @ bone.matrix
            pos, _, sca = local_matrix.decompose()  # Rotation should be converted from the matrix directly

            # Apply the scale signs if they exist
            scale_signs = bone.get('scale_signs')
            if scale_signs is not None:
                sca *= Vector(scale_signs)

            # Set the coordinates of the node
            node.position = pos_m_to_cm(pos)
            node.rotation = rot_from_blender(local_matrix.to_euler('ZYX'))
            node.scale = sca[:]

            # Set the unknown values if they were imported
            unk_float = bone.get('unk_float')
            unk_short = bone.get('unk_short')

            
            if unk_float is not None:
                node.unkFloat = unk_float
            if unk_short is not None:
                node.unkShort = unk_short
            
            # Add the coord chunk to the list
            coords.append(coord)

            # Recursively add all children of each bone
            for c in bone.children:
                make_coord(c, node, bone.matrix)
        
        def make_coord_og(bone: EditBone, coord_parent: CoordNode = None, parent_matrix: Matrix = Matrix.Identity(4)):
            coord = NuccChunkCoord(clump.filePath, bone.name)
            coord.node = CoordNode(coord)
            coord.has_props = True
            coord.has_data = True

            # Set up the node
            node = coord.node
            node.parent = coord_parent

            if bone.get('orig_coords'):
                node.position = tuple(bone['orig_coords'][0])
                node.rotation = tuple(bone['orig_coords'][1])
                node.scale = tuple(bone['orig_coords'][2])
            else:
                local_matrix: Matrix = parent_matrix.inverted() @ bone.matrix
                pos, _, sca = local_matrix.decompose()  # Rotation should be converted from the matrix directly

                # Set the coordinates of the node
                node.position = pos_m_to_cm(pos) #tuple(pos) 
                node.rotation = rot_from_blender(local_matrix.to_euler('ZYX'))
                node.scale = sca[:]

            # Set the unknown values if they were imported
            unk_float = bone.get('unk_float')
            unk_short = bone.get('unk_short')

            
            if unk_float is not None:
                node.unkFloat = unk_float
            if unk_short is not None:
                node.unkShort = unk_short
            

            # Add the coord chunk to the list
            coords.append(coord)

            # Recursively add all children of each bone
            for c in bone.children:
                make_coord_og(c, node, bone.matrix)

        # Iterate through the root bones to process their children in order
        if self.use_original_coords:
            for root_bone in [b for b in armature.edit_bones if b.parent is None]:
                make_coord_og(root_bone)
        else:
            for root_bone in [b for b in armature.edit_bones if b.parent is None]:
                make_coord(root_bone)

        for coord in coords:
            if coord.node.parent:
                coord.node.parent.children.append(coord.node)

        bpy.ops.object.mode_set(mode='OBJECT')

        return coords
    

    def make_models(self, empties: List[Object], clump: NuccChunkClump, old_clump: NuccChunkClump, context) -> List[NuccChunkModel]:
        bpy.ops.object.mode_set(mode='OBJECT')

        model_chunks = list()

        coord_indices_dict = {
            name: i
            for i, name in enumerate([c.name for c in clump.coord_chunks])
        }

        # Get a list of all models in from the old clump
        old_clump_all_models = list(dict.fromkeys(
            chain(old_clump.model_chunks, *old_clump.model_groups))) if old_clump else None

        for empty in empties:
            if self.export_specific_meshes:
                # Use existing models from the old clump if the current model is not supposed to be exported
                mesh_index = self.meshes_to_export.find(empty.name)
                if mesh_index == -1:
                    continue

                if self.meshes_to_export[mesh_index].value is False:
                    if old_clump:
                        old_model = [c for c in old_clump_all_models if c and c.name == empty.name]
                        if old_model:
                            model_chunks.append(old_model[0])
                    continue

            nud_data: NudPropertyGroup = empty.xfbin_nud_data
            # Create the chunk and set its properties
            chunk = NuccChunkModel(clump.filePath, empty.name)
            chunk.clump_chunk = clump
            chunk.has_data = True
            chunk.has_props = True

            #Check for modelhit objects and skip them
            if empty.name.endswith('[HIT]'):
                continue
            
            #correct modelhit name
            if nud_data.hit_chunk_name.endswith('_[HIT]'):
                nud_data.hit_chunk_name = f'{nud_data.hit_chunk_name[:-6]}'
            
            #Get the modelhit object
            if bpy.data.objects.get(f'{nud_data.hit_chunk_name}_[HIT]'):
                chunk.hit_chunk = self.make_modelhit(bpy.data.objects.get(f'{nud_data.hit_chunk_name}_[HIT]'), clump, context)
            else:
                chunk.hit_chunk = NuccChunkNull()

            # Get the index of the mesh bone of this model
            chunk.coord_chunk = None
            chunk.coord_index = coord_indices_dict.get(nud_data.mesh_bone, 0)

            chunk.material_chunks = list()

            # Reduce the set of flags to a single flag
            chunk.rigging_flag = RiggingFlag(reduce(lambda x, y: int(x) |
                                                    int(y), nud_data.rigging_flag.union(nud_data.rigging_flag_extra), 0))

            chunk.model_attributes = nud_data.model_attributes
            chunk.render_layer = nud_data.render_layer
            chunk.light_mode_id = nud_data.light_mode
            chunk.light_category = nud_data.light_category

            chunk.bounding_box = list(nud_data.bounding_box) if nud_data.model_attributes & 0x04 else tuple()

            # Create the nud
            chunk.nud = Nud()
            chunk.nud.name = chunk.name

            # Set the nud's properties
            chunk.nud.bounding_sphere = pos_m_to_cm_tuple(nud_data.bounding_sphere_nud)

            # Always treat nuds as having only 1 mesh group
            chunk.nud.mesh_groups = [NudMeshGroup()]
            mesh_group = chunk.nud.mesh_groups[0]
            mesh_group.name = chunk.name

            mesh_group.bone_flags = nud_data.bone_flag
            mesh_group.bounding_sphere = pos_m_to_cm_tuple(nud_data.bounding_sphere_group)

            mesh_group.meshes = list()

            # Get the armature's data
            armature: Armature = empty.parent.data
            mesh_bone = armature.bones.get(nud_data.mesh_bone)
            empty_parent_type = empty.parent_type

            # Sort the meshes alphabetically (because we made sure they imported in that order)
            for mesh_obj in sorted([c for c in empty.children if c.type == 'MESH'], key=lambda x: x.name):
                mesh_obj: Object

                context.view_layer.objects.active = mesh_obj
                bpy.ops.object.mode_set(mode='OBJECT')

                # Generate a mesh with modifiers applied, and put it into a bmesh
                mesh: Mesh = mesh_obj.evaluated_get(context.evaluated_depsgraph_get()).data

                # Transform the mesh by the inverse of its bone's matrix, if it was not parented to it
                if mesh_bone and empty_parent_type != 'BONE':
                    #print(f"Transforming {mesh_obj.name} by the inverse of {mesh_bone.name}'s matrix")
                    mesh.transform(mesh_bone.matrix_local.to_4x4().inverted())

                mesh.calc_loop_triangles()
                try:
                    mesh.calc_tangents()
                except:
                    self.report({'WARNING'}, f"{mesh_obj.name} tangents can't be calculated, try triangulating the mesh")

                faces = [None] * len(mesh.loop_triangles)
                face_index = 0
                vertices = [None] * len(mesh.loop_triangles)
                vertex_index = 0

                mesh_vertices = mesh.vertices
                mesh_loops = mesh.loops

                # Get the vertex groups
                v_groups = mesh_obj.vertex_groups

                color_layer = None
                if len(mesh.color_attributes) > 0:
                    color_layer = mesh.color_attributes[0].data
                else:
                    self.operator.report({'WARNING'}, f"[NUD MESH] {mesh_obj.name} in {empty.name} has no vertex colors and will be skipped")
                    continue

                uv_layer1 = None
                uv_layer2 = None
                uv_layer3 = None
                uv_layer4 = None
                if len(mesh.uv_layers):
                    uv_layer1 = mesh.uv_layers[0].data
                if len(mesh.uv_layers) > 1:
                    uv_layer2 = mesh.uv_layers[1].data
                if len(mesh.uv_layers) > 2:
                    uv_layer3 = mesh.uv_layers[2].data
                if len(mesh.uv_layers) > 3:
                    uv_layer4 = mesh.uv_layers[3].data

                for tri_loops in mesh.loop_triangles:
                    tri_loops: MeshLoopTriangle

                    verts = vertices[vertex_index] = list()
                    vertex_index += 1

                    for l_index in tri_loops.loops:
                        l: MeshLoop = mesh_loops[l_index]
                        v_index = l.vertex_index
                        v: MeshVertex = mesh_vertices[v_index]

                        # Create and add the vertex
                        vert = NudVertex()
                        verts.append(vert)

                        # Position and normal, tangent, bitangent
                        vert.position = pos_scaled_from_blender(v.co)
                        vert.normal = pos_from_blender(l.normal)
                        vert.tangent = pos_from_blender(l.tangent)
                        vert.bitangent = l.bitangent_sign * Vector(vert.normal).cross(Vector(vert.tangent))

                        # Color
                        vert.color = tuple()
                        color_layer = mesh.color_attributes[0].data
                        if color_layer:
                            vert.color = [int(c*255) for c in color_layer[l_index].color_srgb]

                        # UV
                        vert.uv = list()
                        if uv_layer1:
                            vert.uv.append(uv_from_blender(uv_layer1[l_index].uv))
                        if uv_layer2:
                            vert.uv.append(uv_from_blender(uv_layer2[l_index].uv))
                        if uv_layer3:
                            vert.uv.append(uv_from_blender(uv_layer3[l_index].uv))
                        if uv_layer4:
                            vert.uv.append(uv_from_blender(uv_layer4[l_index].uv))

                        vert.bone_ids = tuple()
                        vert.bone_weights = tuple()

                        # Bone indices and weights
                        # Direct copy of TheTurboTurnip's weight sorting method
                        # https://github.com/theturboturnip/yk_gmd_io/blob/master/yk_gmd_blender/blender/export/legacy/exporter.py#L302-L316

                        # Get a list of (vertex group ID, weight) items sorted in descending order of weight
                        # Take the top 4 elements, for the top 4 most deforming bones
                        # Normalize the weights so they sum to 1
                        b_weights = [(v_groups[g.group].name, g.weight) for g in sorted(
                            v.groups, key=lambda g: 1 - g.weight) if v_groups[g.group].name in coord_indices_dict]
                        if len(b_weights) > 4:
                            b_weights = b_weights[:4]
                        elif len(b_weights) < 4:
                            # Add zeroed elements to b_weights so it's 4 elements long
                            b_weights += [(0, 0.0)] * (4 - len(b_weights))

                        weight_sum = sum(weight for (_, weight) in b_weights)
                        if weight_sum > 0.0:
                            vert.bone_ids = [coord_indices_dict.get(bw[0], 0) for bw in b_weights]
                            vert.bone_weights = [bw[1] / weight_sum for bw in b_weights]
                        else:
                            vert.bone_ids = [0] * 4
                            vert.bone_weights = [0] * 3 + [1]

                vertices_dict = IterativeDict()
                vertices_dict_get = vertices_dict.get_or_next
                for verts in vertices:
                    # Get the vertex indices to make the face
                    faces[face_index] = [vertices_dict_get(x) for x in verts]
                    face_index += 1

                vertices = list(vertices_dict)

                # Free the mesh data after we're done with it
                mesh.free_tangents()

                if len(vertices) < 3:
                    self.operator.report(
                        {'WARNING'}, f'[NUD MESH] {mesh_obj.name} in {empty.name} has no valid faces and will be skipped.')
                    continue

                if len(vertices) > NudMesh.MAX_VERTICES:
                    self.operator.report(
                        {'WARNING'}, f'[NUD MESH] {mesh_obj.name} in {empty.name} has {len(vertices)} vertices (limit is {NudMesh.MAX_VERTICES}) and will be skipped.')
                    continue

                if len(faces) > NudMesh.MAX_FACES:
                    self.operator.report(
                        {'WARNING'}, f'[NUD MESH] {mesh_obj.name} in {empty.name} has {len(faces)} faces (limit is {NudMesh.MAX_FACES}) and will be skipped.')
                    continue

                mesh_data: NudMeshPropertyGroup = mesh_obj.xfbin_mesh_data

                nud_mesh = NudMesh()
                nud_mesh.vertices = vertices
                nud_mesh.faces = faces

                # Get the vertex/bone/uv formats from the mesh property group
                nud_mesh.vertex_type = NudVertexType(int(mesh_data.vertex_type))
                nud_mesh.bone_type = NudBoneType(int(mesh_data.bone_type))
                nud_mesh.uv_type = NudUvType(int(mesh_data.uv_type))
                nud_mesh.face_flag = mesh_data.face_flag

                # Add the material chunk for this mesh
                if len(mesh_obj.data.materials) == 0:
                    self.operator.report(
                        {'WARNING'}, f'[NUD MESH] {mesh_obj.name} in {empty.name} has no material and will be skipped.')
                    continue
                else:
                    mat = self.make_xfbin_material(mesh_obj.data.materials[0], clump, context)
                
                matlist = []
                if mat.name not in matlist:
                    matlist.append(mat.name)
                else:
                    self.operator.report(
                        {'WARNING'}, f'[NUD MESH] {mesh_obj.name} in {empty.name} has a material that is used more than once and will be skipped.')
                    continue

                chunk.material_chunks.append(mat)

                # Get the material properties of this mesh
                nud_mesh.materials = self.make_nud_materials(mesh_data, clump, context)

                # Only add the mesh if it doesn't exceed the vertex and face limits
                mesh_group.meshes.append(nud_mesh)

            if not mesh_group.meshes:
                self.operator.report(
                    {'WARNING'}, f'[NUD] {empty.name} does not contain any exported meshes and will be skipped.')
                continue

            # Only add the model chunk if its NUD contains at least one mesh
            model_chunks.append(chunk)

        return model_chunks

    def make_modelhit(self, obj, clump, context):
        modelhit_data = obj.xfbin_modelhit_data
        modelhit = NuccChunkModelHit(clump.filePath, obj.name[:-6] if obj.name.endswith('_[HIT]') else obj.name)
        modelhit.mesh_count = len(obj.children)
        modelhit.has_props = True
        modelhit.has_data = True
        
        total_vert_size = 0

        modelhit.vertex_sections = list()

        for c in obj.children:
            vert_sec = ModelHit()
            mesh_data = c.xfbin_modelhit_mesh_data
           
            bm = bmesh.new()
            bm.from_mesh(c.data)

            #Scale the mesh to the correct size
            bmesh.ops.scale(bm, vec= (100, 100, 100), verts= bm.verts)
            
            #make sure the mesh is triangulated
            bmesh.ops.triangulate(bm, faces=bm.faces) 
            bmesh.ops.split_edges(bm, edges= bm.edges, verts= bm.verts)
            bm.verts.ensure_lookup_table()
            bm.faces.ensure_lookup_table()

            verts = []
            for face in bm.faces:
                for v in face.verts:
                    verts.append((v.co.x, v.co.y, v.co.z))
            
            vert_sec.mesh_vertices = verts
            vert_sec.mesh_vertex_size = int(len(verts) / 3)
            vert_sec.unk_count = 0
            #vert_sec.flags = mesh_data.flags
            vert_sec.flags = ((mesh_data.color[2] + mesh_data.col_flags[0]), (mesh_data.color[1] + mesh_data.col_flags[1]), (mesh_data.color[0] + mesh_data.col_flags[2]))
            
            modelhit.vertex_sections.append(vert_sec)
            
            #add count of vertices to total_vert_size
            total_vert_size += len(verts)
            bm.free()
        
        modelhit.total_vertex_size = int(total_vert_size / 3)

        return modelhit
        

    def make_nud_materials(self, pg: NudMeshPropertyGroup, clump: NuccChunkClump, context) -> List[NudMaterial]:
        materials = list()

        # There is a maximum of 4 materials per mesh
        for mat in pg.materials[:4]:
            mat: NudMaterialPropertyGroup
            m = NudMaterial()
            m.flags = hex_str_to_int(mat.material_id)

            m.sourceFactor = mat.source_factor
            m.destFactor = mat.dest_factor
            m.alphaTest = mat.alpha_test
            m.alphaFunction = mat.alpha_function
            m.refAlpha = mat.ref_alpha
            m.cullMode = mat.cull_mode
            m.unk1 = mat.unk1
            m.unk2 = mat.unk2
            m.zBufferOffset = mat.zbuffer_offset

            m.textures = list()
            for texture in mat.textures:
                texture: NudMaterialTexturePropertyGroup
                t = NudMaterialTexture()

                t.unk0 = texture.unk0
                t.mapMode = texture.map_mode
                t.wrapModeS = texture.wrap_mode_s
                t.wrapModeT = texture.wrap_mode_t
                t.minFilter = texture.min_filter
                t.magFilter = texture.mag_filter
                t.mipDetail = texture.mip_detail
                t.unk1 = texture.unk1
                t.unk2 = texture.unk2

                m.textures.append(t)

            m.properties = list()
            for prop in mat.material_props:
                prop: NudMaterialPropPropertyGroup
                p = NudMaterialProperty()
                p.name = prop.prop_name

                p.values = list()
                for i in range(prop.count):
                    p.values.append(prop.values[i].value)

                m.properties.append(p)

            materials.append(m)

        return materials

    def make_xfbin_material(self, mat, clump: NuccChunkClump, context) -> NuccChunkMaterial:
        pg = mat.xfbin_material_data

        chunk = NuccChunkMaterial(clump.filePath, mat.name)
        chunk.has_data = True
        chunk.has_props = True

        chunk.alpha = int(pg.alpha * 255)
        chunk.glare = pg.glare

        chunk.flags = 0

        if pg.UV0:
            chunk.flags |= 0x01
            chunk.UV0 = pg.uvOffset0
        
        if pg.UV1:
            chunk.flags |= 0x02
            chunk.UV1 = pg.uvOffset1
        
        if pg.UV2:
            chunk.flags |= 0x04
            chunk.UV2 = pg.uvOffset2
        
        if pg.UV3:
            chunk.flags |= 0x08
            chunk.UV3 = pg.uvOffset3
        
        if pg.Blend:
            chunk.flags |= 0x10
            chunk.BlendRate = pg.blendRate
            chunk.BlendType = pg.blendType
        
        if pg.useFallOff:
            chunk.flags |= 0x20
            chunk.fallOff = pg.fallOff
        
        if pg.useOutlineID:
            chunk.flags |= 0x40
            chunk.outlineID = pg.outlineID

        chunk.texture_groups = list()
        g = MaterialTextureGroup()
        g.unk = 0
        g.texture_chunks = list()
        for mattex in mat.xfbin_material_data.NUTextures:
            texture: XfbinTextureChunkPropertyGroup = bpy.context.scene.xfbin_texture_chunks_data.texture_chunks.get(mattex.texture_name)
            t = NuccChunkTexture(texture.path, texture.name)
            if not texture.reference:
                t.has_data = True
                t.has_props = True
                t.nut = Nut()
                t.nut.magic = 'NTP3'
                t.nut.version = 0x100
                t.nut.textures = []
                t.nut.texture_count = 0

                if texture.textures:
                    for tex in texture.textures:
                        image = tex.image
                        if image:
                            if image.packed_file:
                                image_data = image.packed_file.data
                            else:
                                image.pack()
                                image.source = 'FILE'
                                image_data = image.packed_file.data
                            print(image_data[:4])
                            nuttex: NutTexture = DDS_to_NutTexture(read_dds(image_data))
                            t.nut.textures.append(nuttex)
                            t.nut.texture_count += 1
                        else:
                            self.operator.report({'WARNING'}, f'Could not export texture {tex.name}. Make sure that the image is assigned to the texture.')
                            continue
                else:
                    self.operator.report({'WARNING'}, f'Could not export texture {texture.name}. Make sure that the image is assigned to the texture.')
                    continue

                if t.nut.texture_count == 0:
                    #discard the nut chunk if it has no textures
                    continue
                
                #add texture to texture list
                self.xfbin.add_chunk_page(t)

            g.texture_chunks.append(t)
        
        g2 = MaterialTextureGroup()
        #copy g to g2
        for attr, value in g.__dict__.items():
            setattr(g2, attr, value)
        chunk.texture_groups.append(g)
        chunk.texture_groups.append(g2)

        return chunk
    
    def make_texture(self, texture_chunk: XfbinTextureChunkPropertyGroup):
        #Create a texture chunk
        chunk = NuccChunkTexture(texture_chunk.path, texture_chunk.texture_name)
        chunk.has_props = True

        #Create NUT object
        nut = chunk.nut = Nut()
        nut.magic = 'NTP3'
        nut.version = 0x100
        nut.textures = []
        nut.texture_count = 0
        
        
        for texture in texture_chunk.textures:
            texture: NutTexturePropertyGroup
            
            #get image data
            if not texture.image:
                self.operator.report({'WARNING'}, f'Could not export texture {texture.name}. Make sure that the image is assigned to the texture.')
                continue
            
            image = texture.image

            if image.packed_file:
                image_data = image.packed_file.data  
            
            else:
                image.pack()
                image.source = 'FILE'
                image_data = image.packed_file.data
            
            nuttex: NutTexture = DDS_to_NutTexture(read_dds(image_data))
            
            nut.textures.append(nuttex)
            nut.texture_count += 1
        
        return chunk
    
    def make_dynamics(self, dynamics_obj: Object, context, clump: NuccChunkClump) -> NuccChunkDynamics:
        context.view_layer.objects.active = dynamics_obj
        dynamics_data: DynamicsPropertyGroup = dynamics_obj.xfbin_dynamics_data
        dynamics = NuccChunkDynamics(dynamics_data.path, dynamics_data.clump_name)
        dynamics.has_data = True
        dynamics.has_props = True
        dynamics.clump_chunk = clump

        dynamics.SPGroupCount = len(dynamics_data.spring_groups)
        dynamics.ColSphereCount = len(dynamics_data.collision_spheres)

        #update dynamics chunk values before exporting
        bpy.ops.object.update_dynamics()
       
        dynamics.SPGroup = list()
        for dynamic in sorted(dynamics_data.spring_groups, key= lambda x: x.spring_group_index): 
            dynamic: SpringGroupsPropertyGroup
            d = Dynamics1()
            
            d.Bounciness = dynamic.dyn1
            d.Elasticity = dynamic.dyn2
            d.Stiffness = dynamic.dyn3
            d.Movement = dynamic.dyn4
            d.coord_index = dynamic.bone_index
            d.BonesCount = dynamic.bone_count
            d.shorts = list()
            
            for flag in dynamic.flags:
                d.shorts.append(flag.value)
            dynamics.SPGroup.append(d)
        
        dynamics.ColSphere = list()
        for col in dynamics_data.collision_spheres:
            col: CollisionSpheresPropertyGroup
            c = Dynamics2()
            
            c.offset_x = col.offset_x
            c.offset_y = col.offset_y
            c.offset_z = col.offset_z
            c.scale_x = col.scale_x
            c.scale_y = col.scale_y
            c.scale_z = col.scale_z
            c.coord_index = col.bone_index

            if col.attach_groups == True:
                col.attach_groups = 1
            else:
                col.attach_groups = 0
            c.attach_groups = col.attach_groups

            c.negative_unk = -1
            c.attached_groups = 0
            
            c.attached_groups_count = col.attached_count

            c.attached_groups = list()
            
            for i, g in enumerate(col.attached_groups):
                #print(i, g.value)
                if i <= col.attached_count:
                    if dynamics_data.spring_groups.get(g.value):
                        c.attached_groups.append(dynamics_data.spring_groups.get(g.value).spring_group_index)
                elif i > col.attached_count:
                    print(f"Warning: Attached group {g.value} index out of range")          
            dynamics.ColSphere.append(c)

        return dynamics

def menu_func_export(self, context):
    self.layout.operator(ExportXfbin.bl_idname, text='XFBIN Model Container (.xfbin)')
