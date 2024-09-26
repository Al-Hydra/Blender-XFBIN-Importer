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
from .panels.materials_panel import (NUD_ShaderPropertyGroup, NUD_ShaderParamPropertyGroup, NUD_ShaderTexPropertyGroup)



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
        default=False,
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
        name='Export original bone',
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

                #create dytamics chunk
                if self.export_dynamics:
                    dynamics_chunk = self.make_dynamics(armature_obj, clump, context)
                    self.xfbin.add_chunk_page(dynamics_chunk)

                
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
        meshes: List[Mesh] = [obj for obj in armature_obj.children if obj.type == 'MESH' and obj.name in context.view_layer.objects]

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
            # Create the model chunks as a dict to make it easier to preserve order
            model_chunks = {m.name: m for m in self.make_models(meshes, clump, old_clump, context)}

            # Set the model chunks and model groups based on the clump data
            #clump.model_chunks = [model_chunks[c.value] for c in clump_data.models if c.value in model_chunks]
            lod_list = ["lod1", "lod2", "LOD1", "LOD2"]
            if clump.coord_flag0 > 1:
                clump.model_chunks = [model_chunks[c.value] for c in clump_data.models if c.value in model_chunks and not any(lod in c.value for lod in lod_list)]
            else:
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
                g.unk = group.unk
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
            opacity = bone.get('opacity')
            flags = bone.get('flags')

            
            if opacity is not None:
                node.opacity = opacity
            else:
                node.opacity = 1.0
            if flags is not None:
                node.flags = flags
            else:
                node.flags = 0
            
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
            opacity = bone.get('opacity')
            flags = bone.get('flags')

            
            if opacity is not None:
                node.opacity = opacity
            else:
                node.opacity = 1.0
            if flags is not None:
                node.flags = flags
            else:
                node.flags = 0
            

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
    

    def make_models(self, objects: List[Object], clump: NuccChunkClump, old_clump: NuccChunkClump, context) -> List[NuccChunkModel]:
        bpy.ops.object.mode_set(mode='OBJECT')

        model_chunks = list()

        coord_indices_dict = {
            name: i
            for i, name in enumerate([c.name for c in clump.coord_chunks])
        }

        # Get a list of all models in from the old clump
        old_clump_all_models = list(dict.fromkeys(
            chain(old_clump.model_chunks, *old_clump.model_groups))) if old_clump else None

        for obj in objects:
            if self.export_specific_meshes:
                # Use existing models from the old clump if the current model is not supposed to be exported
                mesh_index = self.meshes_to_export.find(obj.name)
                if mesh_index == -1:
                    continue

                if self.meshes_to_export[mesh_index].value is False:
                    if old_clump:
                        old_model = [c for c in old_clump_all_models if c and c.name == obj.name]
                        if old_model:
                            model_chunks.append(old_model[0])
                    continue

            nud_data: NudPropertyGroup = obj.xfbin_nud_data
            # Create the chunk and set its properties
            chunk = NuccChunkModel(clump.filePath, obj.name)
            chunk.clump_chunk = clump
            chunk.has_data = True
            chunk.has_props = True

            #Check for modelhit objects and skip them
            if obj.name.endswith('[HIT]'):
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

            # Create the nud
            chunk.nud = Nud()
            chunk.nud.name = chunk.name

            # Always treat nuds as having only 1 mesh group
            chunk.nud.mesh_groups = [NudMeshGroup()]
            mesh_group = chunk.nud.mesh_groups[0]
            mesh_group.name = chunk.name

            mesh_group.bone_flags = nud_data.bone_flag

            mesh_group.meshes = list()

            # Get the armature's data
            armature: Armature = obj.parent.data
            mesh_bone = armature.bones.get(nud_data.mesh_bone)
            obj_parent_type = obj.parent_type

            #bounding box and bounding sphere calculations
            bbox_corners = [mesh_bone.matrix_local.inverted() @ Vector(corner) for corner in obj.bound_box]

            bbox_corners_world = [obj.matrix_world @ corner for corner in bbox_corners]

            # Get the minimum and maximum coordinates
            min_corner = Vector((min(corner[i] for corner in bbox_corners_world) for i in range(3)))
            max_corner = Vector((max(corner[i] for corner in bbox_corners_world) for i in range(3)))

            # Calculate the bounding sphere center (average of all corners)
            center = sum(bbox_corners, Vector((0, 0, 0))) / len(bbox_corners)

            # Calculate the bounding sphere radius (max distance from center to any corner)
            radius = max((corner - center).length for corner in bbox_corners)

            chunk.bounding_box = list((min_corner * 100)) + list((max_corner * 100)) if nud_data.model_attributes & 0x04 else tuple()

            chunk.nud.bounding_sphere = pos_m_to_cm_tuple([*center, radius])
            mesh_group.bounding_sphere = pos_m_to_cm_tuple([*center, radius])
            mesh_group.unk_values = nud_data.unk_values
            #set the current object as the active object
            context.view_layer.objects.active = obj
            bpy.ops.object.mode_set(mode='OBJECT')

            # Generate a mesh with modifiers applied, and put it into a bmesh
            mesh: Mesh = obj.evaluated_get(context.evaluated_depsgraph_get()).data

            # Transform the mesh by the inverse of its bone's matrix, if it was not parented to it
            if mesh_bone and mesh_bone.get("matrix"):
                mesh.transform(Matrix(mesh_bone["matrix"]).inverted())
            elif mesh_bone:
                mesh.transform(mesh_bone.matrix_local.inverted())

            #triangulate the mesh
            mesh.calc_loop_triangles()

            #calculate tangents
            mesh.calc_tangents()

            mesh_vertices = mesh.vertices
            mesh_loops = mesh.loops

            # Get the vertex groups
            v_groups = obj.vertex_groups

            #get the first color layer and if it doesn't exist make one
            if len(mesh.color_attributes) > 0:
                color_layer = mesh.color_attributes[0].data
            else:
                color_layer = mesh.vertex_colors.new(name='Color', type = "BYTE_COLOR", domain = "CORNER")
                color_layer = mesh.color_attributes[0].data

            #try to get the first 4 uv layers
            uv_layers = list()

            for i, uv_layer in enumerate(mesh.uv_layers):
                uv_layers.append(uv_layer.data)
                if i == 3:
                    break

           # create a list for each material
           # mat_meshes = [list() for mat in mesh.materials]

            mat_meshes = {mat.name: list() for mat in mesh.materials}

            for tri_loops in mesh.loop_triangles:
                tri_loops: MeshLoopTriangle
                 
                #get the material index
                mat_index = tri_loops.material_index

                mat_meshes[mesh.materials[mat_index].name].append(tri_loops)
            
            for mat_name, mesh in mat_meshes.items():

                faces = [None] * len(mesh)
                face_index = 0
                vertices = [None] * len(mesh)
                vertex_index = 0

                for tri_loops in mesh:
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
                        vert.position = pos_scaled_from_blender(v.co @ obj.matrix_world)
                        vert.normal = pos_from_blender(l.normal)
                        vert.tangent = pos_from_blender(l.tangent)
                        vert.bitangent = l.bitangent_sign * Vector(vert.normal).cross(Vector(vert.tangent))

                        # Color
                        if color_layer:
                            vert.color = [int(c*255) for c in color_layer[l_index].color_srgb]

                        # UV
                        vert.uv = list()
                        for uv_layer in uv_layers:
                            vert.uv.append(uv_from_blender(uv_layer[l_index].uv))
                        
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

                if len(vertices) < 3:
                    self.operator.report(
                        {'WARNING'}, f'[NUD MESH] {obj.name} has no valid faces and will be skipped.')
                    continue

                if len(vertices) > NudMesh.MAX_VERTICES:
                    self.operator.report(
                        {'WARNING'}, f'[NUD MESH] {obj.name} has {len(vertices)} vertices (limit is {NudMesh.MAX_VERTICES}) and will be skipped.')
                    continue

                if len(faces) > NudMesh.MAX_FACES:
                    self.operator.report(
                        {'WARNING'}, f'[NUD MESH] {obj.name} has {len(faces)} faces (limit is {NudMesh.MAX_FACES}) and will be skipped.')
                    continue

                mat_mesh = NudMesh()
                mat_mesh.vertices = vertices
                mat_mesh.faces = faces

                # set the correct vertex/bone/uv formats

                #we'll set the vertex type to 3 if the mesh is deformable and 7 if not
                if RiggingFlag.SKINNED in chunk.rigging_flag: 
                    mat_mesh.vertex_type = int(0x03)
                    mat_mesh.bone_type = int(0x10)
                    mat_mesh.face_flag = int(4)
                else:
                    mat_mesh.vertex_type = int(0x07)
                    mat_mesh.bone_type = int(0x00)
                    mat_mesh.face_flag = int(0x00)
                
                mat_mesh.uv_type = int(2)

                # Add the material chunk for this mesh
                if len(obj.data.materials) == 0:
                    self.operator.report(
                        {'WARNING'}, f'[NUD MESH] {obj.name} has no material and will be skipped.')
                    continue
                else:
                    mat = self.make_xfbin_material(obj.data.materials[mat_name], clump, context)
                
                chunk.material_chunks.append(mat)

                # Get the material properties of this mesh
                mat_mesh.materials = self.make_nud_materials(obj, obj.data.materials[mat_name], clump, context)

                # Only add the mesh if it doesn't exceed the vertex and face limits
                mesh_group.meshes.append(mat_mesh)


            model_chunks.append(chunk)

            #update the mesh object
            obj.update_tag()


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
        

    def make_nud_materials(self, model, material, clump: NuccChunkClump, context) -> List[NudMaterial]:
        shaders = list()
        blender_mat = material

        #print(f'Exporting material {material.name} for {model.name}')

        def set_shader_props(shader, shader_settings):
            shader.sourceFactor = shader_settings.source_factor
            shader.destFactor = shader_settings.destination_factor
            shader.alphaTest = shader_settings.alpha_test
            shader.alphaFunction = shader_settings.alpha_function
            shader.refAlpha = shader_settings.alpha_reference
            shader.cullMode = int(shader_settings.cull_mode)
            shader.unk1 = shader_settings.unk1
            shader.unk2 = shader_settings.unk2
            shader.zBufferOffset = shader_settings.zbuffer_offset
        
        def set_texture_props(texture, tex_props):
            texture.baseID = tex_props.baseID
            texture.groupID = tex_props.groupID
            texture.subGroupID = tex_props.subGroupID
            texture.textureID = tex_props.textureID
            texture.mapMode = tex_props.mapMode
            texture.wrapModeS = int(tex_props.wrapModeS)
            texture.wrapModeT = int(tex_props.wrapModeT)
            texture.minFilter = int(tex_props.minFilter)
            texture.magFilter = int(tex_props.magFilter)
            texture.mipDetail = tex_props.mipDetail
            texture.unk1 = tex_props.unk1
            texture.LOD = tex_props.LOD

        model_props: NudPropertyGroup = model.xfbin_nud_data

        mat_props = blender_mat.xfbin_material_data

        model_flags = RiggingFlag(reduce(lambda x, y: int(x) |
                                                    int(y), model_props.rigging_flag.union(model_props.rigging_flag_extra), 0))

        # Get the main shader
        if len(mat_props.NUD_Shaders) > 0:
            shader_count = 0

            if model.xfbin_nud_data.bone_flag != 16:

                shader = mat_props.NUD_Shaders[shader_count]
                shader: NUD_ShaderPropertyGroup
                m = NudMaterial()
                m.flags = hex_str_to_int(shader.name)

                shader_count += 1
                
                if material.xfbin_material_data.use_object_props:
                    set_shader_props(m, model.xfbin_nud_data.shader_settings)
                else:
                    set_shader_props(m, shader)

                m.textures = list()
                for texture in mat_props.NUTextures:
                    t = NudMaterialTexture()

                    set_texture_props(t, texture)

                    m.textures.append(t)

                m.properties = list()
                
                for param in shader.shader_params:
                    param: NUD_ShaderParamPropertyGroup
                    p = NudMaterialProperty()
                    p.name = param.name

                    p.values = list()
                    for i in range(param.count):
                        p.values.append(param.values[i].value)

                    m.properties.append(p)

                shaders.append(m)

            # make extra shaders depending on the flags
            if RiggingFlag.OUTLINE in model_flags:
                shader = mat_props.NUD_Shaders[shader_count]
                m = NudMaterial()
                
                m.flags = hex_str_to_int(shader.name)

                shader_count += 1

                set_shader_props(m, shader)

                m.textures = list()
                for texture in mat_props.NUTextures:
                    t = NudMaterialTexture()

                    set_texture_props(t, texture)

                    m.textures.append(t)

                m.properties = list()
                for param in shader.shader_params:
                    param: NUD_ShaderParamPropertyGroup
                    p = NudMaterialProperty()
                    p.name = param.name

                    p.values = list()
                    for i in range(param.count):
                        p.values.append(param.values[i].value)

                    m.properties.append(p)

                shaders.append(m)
            
            if RiggingFlag.BLUR in model_flags:
                shader = mat_props.NUD_Shaders[shader_count]
                shader_count += 1
                m = NudMaterial()

                if len(mat_props.NUD_Shaders) > shader_count:
                
                    #copy the first shader
                    for attr, value in shaders[0].__dict__.items():
                        setattr(m, attr, value)

                    #set params
                    m.properties = list()
                    for param in shader.shader_params:
                        param: NUD_ShaderParamPropertyGroup
                        p = NudMaterialProperty()
                        p.name = param.name

                        p.values = list()
                        for i in range(param.count):
                            p.values.append(param.values[i].value)

                        m.properties.append(p)
                
                else:
                    set_shader_props(m, shader)

                    m.textures = list()
                    for texture in mat_props.NUTextures:
                        t = NudMaterialTexture()

                        set_texture_props(t, texture)

                        m.textures.append(t)

                    m.properties = list()
                    for param in shader.shader_params:
                        param: NUD_ShaderParamPropertyGroup
                        p = NudMaterialProperty()
                        p.name = param.name

                        p.values = list()
                        for i in range(param.count):
                            p.values.append(param.values[i].value)

                        m.properties.append(p)


                #change the shader name depending on the skinning flag
                if RiggingFlag.UNSKINNED in model_flags:
                    m.flags = 0x0000E000
                else:
                    m.flags = 0x0000E100

                shaders.append(m)
            
            if RiggingFlag.SHADOW in model_flags:
                shader = mat_props.NUD_Shaders[shader_count]
                shader_count += 1
                m = NudMaterial()

                if len(mat_props.NUD_Shaders) > shader_count:
                
                    #copy the first shader
                    for attr, value in shaders[0].__dict__.items():
                        setattr(m, attr, value)
                    
                    #set params
                    m.properties = list()
                    for param in shader.shader_params:
                        param: NUD_ShaderParamPropertyGroup
                        p = NudMaterialProperty()
                        p.name = param.name

                        p.values = list()
                        for i in range(param.count):
                            p.values.append(param.values[i].value)

                        m.properties.append(p)
                
                else:
                    set_shader_props(m, shader)

                    m.textures = list()
                    for texture in mat_props.NUTextures:
                        t = NudMaterialTexture()

                        set_texture_props(t, texture)

                        m.textures.append(t)

                    m.properties = list()
                    for param in shader.shader_params:
                        param: NUD_ShaderParamPropertyGroup
                        p = NudMaterialProperty()
                        p.name = param.name

                        p.values = list()
                        for i in range(param.count):
                            p.values.append(param.values[i].value)

                        m.properties.append(p)


                #get the correct shader name
                m.flags = 0x0000E001

                shaders.append(m)

        return shaders

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
            chunk.BlendRate = pg.blendRate[0]
            chunk.BlendType = pg.blendRate[1]
        
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
            texture: XfbinTextureChunkPropertyGroup = bpy.context.scene.xfbin_texture_chunks_data.texture_chunks.get(mattex.name)
            t = NuccChunkTexture(texture.path, texture.name)
            if not texture.reference and self.export_textures:
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
        
        if pg.texGroupsCount > 1:
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
    
    def make_dynamics(self, armature_obj: Object, clump: NuccChunkClump, context) -> NuccChunkDynamics:
        dynamics_data: DynamicsPropertyGroup = armature_obj.xfbin_dynamics_data
        clump_data: ClumpPropertyGroup = armature_obj.xfbin_clump_data
        dynamics = NuccChunkDynamics(clump_data.path, clump_data.name)
        dynamics.has_data = True
        dynamics.has_props = True
        dynamics.clump_chunk = clump

        dynamics.SPGroupCount = len(dynamics_data.spring_groups)
        dynamics.ColSphereCount = len(dynamics_data.collision_spheres)
       
        #spring_group_names = []
        dynamics.SPGroup = list()
        for spring_group in dynamics_data.spring_groups:
            spring_group: SpringGroupsPropertyGroup
            d = Dynamics1()
            
            d.name = spring_group.bone_spring   
            d.Bounciness = spring_group.dyn1
            d.Elasticity = spring_group.dyn2
            d.Stiffness = spring_group.dyn3
            d.Movement = spring_group.dyn4
            d.coord_index = armature_obj.data.bones.find(spring_group.bone_spring)
            d.BonesCount = len(armature_obj.data.bones[spring_group.bone_spring].children_recursive) + 1
            if spring_group.maintain_shape:
                d.shorts = [2] * d.BonesCount
            else:
                d.shorts = [0] * d.BonesCount
            
            dynamics.SPGroup.append(d)
            #spring_group_names.append(spring_group.bone_spring)
        
        dynamics.SPGroup = sorted(dynamics.SPGroup, key=lambda x: x.coord_index)
        spring_group_names = [x.name for x in dynamics.SPGroup]
        
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
            c.coord_index = armature_obj.data.bones.find(col.bone_collision)

            c.attach_groups = int(col.attach_groups)

            c.negative_unk = -1
            
            c.attached_groups_count = col.attached_count

            c.attached_groups = [spring_group_names.index(x.bone_spring) for x in col.attached_groups]

            dynamics.ColSphere.append(c)

        return dynamics

def menu_func_export(self, context):
    self.layout.operator(ExportXfbin.bl_idname, text='XFBIN Model Container (.xfbin)')
