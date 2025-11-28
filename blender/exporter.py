from multiprocessing import cpu_count
from functools import reduce
from itertools import chain
from os import path
from typing import Dict, List
import time

import bmesh
import bpy
from bpy.props import (BoolProperty, CollectionProperty, EnumProperty, FloatProperty,
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
                                              NuccChunkDynamics, NuccChunk,
                                              NuccChunkMaterial,
                                              NuccChunkModel,
                                              NuccChunkModelHit, NuccChunkNull,
                                              NuccChunkTexture, RiggingFlag)
from ..xfbin_lib.xfbin.structure.nud import (Nud, NudMaterial,
                                             NudMaterialProperty,
                                             NudMaterialTexture, NudMesh,
                                             NudMeshGroup, NudVertex)
from ..xfbin_lib.xfbin.structure.nut import Nut, NutTexture
from .utils.texture_converter import convert_texture
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
from .utils.tristrip import tristrip
from collections import defaultdict
import numpy as np
#import cProfile
#from .tristrip import rust_loader

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
    
    export_tristrips: BoolProperty(
        name='Export Triangle Strips',
        description='If True, will convert triangles to triangle strips\n'
        'If False, will export the triangles as they are.',
        default=True
    )
    
    stitch_tristrips: BoolProperty(
        name='Stitch Triangle Strips',
        description='If True, will stitch all triangle strips into a single strip per mesh.\n'
        'Which could help prevent crashes in some cases.',
        default=False,
    )
    
    export_tangents: BoolProperty(
        name='Export Tangents and Binormals',
        description='If True, will export tangents and binormals for the meshes.\n'
        'If False, will not export tangents.',
        default=True,
    )
    
    normals_as_tangents: BoolProperty(
        name='Export Real Normals as Tangents',
        description='If True, will use the normals as tangents for the meshes.\n'
        'This only exists for shaders that require it.',
        default=False,
    )
    
    normals_as_binormals: BoolProperty(
        name='Export Real Normals as Binormals',
        description='If True, will use the normals as binormals for the meshes.\n'
        'This only exists for shaders that require it.',
        default=False,
    )
    
    high_quality_colors: BoolProperty(
        name='Export 16-bit Colors',
        description='If True, will export 16 bit colors instead of 8 bit.',
        default=False,
    )
    
    high_precision_uvs: BoolProperty(
        name='Export High Precision UVs',
        description='If True, will export UVs as 32-bit floats instead of 16-bit half-floats.',
        default=False,
    )
    
    rename_content: BoolProperty(
        name='Rename Content',
        description='If True, will rename the content during export.',
        default=False,
    )
    
    source_name: StringProperty(
        name='Source Name',
        description='Name of the source content.',
        default='',
    )
    
    target_name: StringProperty(
        name='Target Name',
        description='Name of the target content.',
        default='',
    )
    
    round_precision: BoolProperty(
        name='Round Precision',
        description='If True, will round vertex attributes to reduce precision during export.',
        default=False,
    )
    
    rounding_threshold: FloatProperty(
        name='Rounding Threshold',
        description='Threshold for rounding vertex attributes during export.',
        default=0.0001,
    )
    
    def draw(self, context):
        layout = self.layout

        layout.label(text='Select a collection to export:')
        layout.prop_search(self, 'collection', bpy.data, 'collections')

        if self.collection:
            inject_row = layout.row()
            inject_row.prop(self, 'inject_to_xfbin')
            
            # Always enabled, grayed out
            tristrip_row = layout.row()
            tristrip_row.enabled = False
            tristrip_row.prop(self, "export_tristrips")
            
            layout.prop(self, "stitch_tristrips")
            
            layout.prop(self, 'export_tangents')
            
            if self.export_tangents:
                layout.prop(self, 'normals_as_tangents')
            
            layout.prop(self, 'high_precision_uvs')
            layout.prop(self, 'high_quality_colors')
            
            layout.prop(self, 'rename_content')
            if self.rename_content:
                box = layout.box()
                box.prop(self, 'source_name')
                box.prop(self, 'target_name')
            
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
        
        for key in export_settings:
            # add attribute
            setattr(self, key, export_settings[key])
        
        self.collection: bpy.types.Collection = bpy.data.collections[self.collection]

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
                                
        # before wriitng the xfbin, rename content if needed
        '''if self.rename_content and self.source_name and self.target_name:
            # rename everything in the xfbin including paths
            for page in self.xfbin.pages:
                for chunk in page.chunks:
                    chunk: NuccChunk
                    chunk.name = chunk.name.replace(self.source_name, self.target_name)
                    print(chunk.name)
                    chunk.filePath = chunk.filePath.replace(self.source_name, self.target_name)
                    print(chunk.filePath)
                    
                        
                for reference in page.chunk_references:
                    reference: NuccChunk
                    reference.name = reference.name.replace(self.source_name, self.target_name)
                    reference.filePath = reference.filePath.replace(self.source_name, self.target_name)'''
        # Write the xfbin
        write_xfbin_to_path(self.xfbin, self.filepath)
    
    
    def create_chunk(self, chunk_type: type, file_path: str, name: str) -> NuccChunk:
        if self.rename_content and self.source_name and self.target_name:
            file_path = file_path.replace(self.source_name, self.target_name)
            name = name.replace(self.source_name, self.target_name)
        return chunk_type(file_path, name)
    

    def make_clump(self, armature_obj: Object, context) -> NuccChunkClump:
        """Creates and returns a NuccChunkClump made from an Armature and its child meshes."""

        # Set the armature as the active object to be able to get its edit bones
        context.view_layer.objects.active = armature_obj

        armature: Armature = armature_obj.data
        meshes: List[Mesh] = [obj for obj in armature_obj.children if obj.type == 'MESH' and obj.name in context.view_layer.objects]

        clump_data: ClumpPropertyGroup = armature_obj.xfbin_clump_data

        # Remove the added " [C]" from the clump's name if it exists
        #clump = #NuccChunkClump(clump_data.path, armature.name[:-4] if armature.name.endswith(' [C]') else armature.name)
        clump = self.create_chunk(NuccChunkClump, clump_data.path, armature.name[:-4] if armature.name.endswith(' [C]') else armature.name)
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

            #model_chunks['None'] = None
            
            clump.model_chunks = list(model_chunks.values())

            # Add the model groups from the clump data
            clump.model_groups = list()
            clump.extra_groups = list()
            for group in clump_data.model_groups:
                group: ClumpModelGroupPropertyGroup
                g = ClumpModelGroup()

                g.flag0 = group.flag0
                g.flag1 = group.flag1
                g.unk = group.unk
                if self.rename_content and self.source_name and self.target_name:
                    g.model_chunks = [model_chunks[c.value.replace(self.source_name, self.target_name)] for c in group.models if c.value.replace(self.source_name, self.target_name) in model_chunks]
                else:
                    g.model_chunks = [model_chunks[c.value] for c in group.models if c.value in model_chunks]

                clump.model_groups.append(g)
            
            for group in clump_data.extra_groups:
                group: ClumpModelGroupPropertyGroup
                g = ClumpModelGroup()

                g.flag0 = group.flag0
                g.flag1 = group.flag1
                g.unk = group.unk
                if self.rename_content and self.source_name and self.target_name:
                    g.model_chunks = [model_chunks[c.value.replace(self.source_name, self.target_name)] for c in group.models if c.value.replace(self.source_name, self.target_name) in model_chunks]
                else:
                    g.model_chunks = [model_chunks[c.value] for c in group.models if c.value in model_chunks]

                clump.extra_groups.append(g)
            
        elif old_clump:
            #clump.model_chunks = old_clump.model_chunks
            clump.model_groups = old_clump.model_groups
            clump.extra_groups = old_clump.extra_groups
        else:
            self.operator.report({'ERROR_INVALID_INPUT'}, 'Could not export meshes. Please check the exporter options.')
            raise Exception('Failed to export.')

        return clump

    def make_coords(self, armature: Armature, clump: NuccChunkClump, context) -> List[NuccChunkCoord]:
        #bpy.ops.object.mode_set(mode='EDIT')

        coords: List[NuccChunkCoord] = list()
        

        def make_coord(bone: EditBone, coord_parent: CoordNode = None, parent_matrix: Matrix = Matrix.Identity(4)):
            #coord = NuccChunkCoord(clump.filePath, bone.name)
            coord = self.create_chunk(NuccChunkCoord, clump.filePath, bone.name)
            coord.node = CoordNode(coord)
            coord.has_props = True
            coord.has_data = True
            
            # Set up the node
            node = coord.node
            node.parent = coord_parent

            local_matrix: Matrix = parent_matrix.inverted() @ bone.matrix_local
            pos, rot, sca = local_matrix.decompose()  # Rotation should be converted from the matrix directly

            # Apply the scale signs if they exist
            scale_signs = bone.get('scale_signs')
            if scale_signs is not None:
                sca *= Vector(scale_signs)

            # Set the coordinates of the node
            node.position = pos_m_to_cm(pos)
            node.rotation = rot_from_blender(rot.to_euler('ZYX'))
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
                make_coord(c, node, bone.matrix_local)
        
        def make_coord_og(bone: EditBone, coord_parent: CoordNode = None, parent_matrix: Matrix = Matrix.Identity(4)):
            #coord = NuccChunkCoord(clump.filePath, bone.name)
            coord = self.create_chunk(NuccChunkCoord, clump.filePath, bone.name)
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
            elif bone.get('original_coords'):
                node.position = tuple(bone['original_coords'][0])
                node.rotation = tuple(bone['original_coords'][1])
                node.scale = tuple(bone['original_coords'][2])
            else:
                local_matrix: Matrix = parent_matrix.inverted() @ bone.matrix_local
                pos, rot, sca = local_matrix.decompose()  # Rotation should be converted from the matrix directly

                # Set the coordinates of the node
                node.position = pos_m_to_cm(pos) #tuple(pos) 
                node.rotation = rot_from_blender(rot.to_euler('ZYX'))
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
                make_coord_og(c, node, bone.matrix_local)

        # Iterate through the root bones to process their children in order
        if self.use_original_coords:
            for root_bone in [b for b in armature.bones if b.parent is None]:
                make_coord_og(root_bone)
        else:
            for root_bone in [b for b in armature.bones if b.parent is None]:
                make_coord(root_bone)

        for coord in coords:
            if coord.node.parent:
                coord.node.parent.children.append(coord.node)

        #bpy.ops.object.mode_set(mode='OBJECT')

        return coords
    

    def make_models(self, objects: List[Object], clump: NuccChunkClump, old_clump: NuccChunkClump, context) -> List[NuccChunkModel]:
        bpy.ops.object.mode_set(mode='OBJECT')

        model_chunks = list()
        texture_chunks_dict = {}

        if self.rename_content and self.source_name and self.target_name:
            coord_indices_dict = {
                name.replace(self.target_name, self.source_name): i
                for i, name in enumerate([c.name for c in clump.coord_chunks])
            }
            
        else:
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
            #chunk = NuccChunkModel(clump.filePath, obj.name)
            chunk = self.create_chunk(NuccChunkModel, clump.filePath, obj.name)
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
            if mesh_bone:
                bbox_corners = [mesh_bone.matrix_local.inverted() @ Vector(corner) for corner in obj.bound_box]
            else:
                bbox_corners = [Vector(corner) for corner in obj.bound_box]

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


            # Generate a mesh with modifiers applied, and put it into a bmesh
            mesh: Mesh = obj.evaluated_get(context.evaluated_depsgraph_get()).to_mesh()
            mesh.transform(obj.matrix_world)
            

            # Transform the mesh by the inverse of its bone's matrix, if it was not parented to it
            if mesh_bone and mesh_bone.get("matrix"):
                mesh.transform(Matrix(mesh_bone["matrix"]).inverted())
            elif mesh_bone:
                mesh.transform(mesh_bone.matrix_local.inverted())

            
            use_skinning = RiggingFlag.SKINNED in chunk.rigging_flag
            loop_data = extract_loop_data_numpy(obj, mesh, coord_indices_dict, max_influences=4, normals_as_tangents=self.normals_as_tangents)
            
            # Build structured vertex array from loop data
            positions = loop_data['positions']
            normals = loop_data['normals']
            tangents = loop_data['tangents']
            bitangents = np.cross(normals, tangents)
            uvs = loop_data['uvs']
            colors = loop_data['colors']
            bone_ids = loop_data['bone_ids']
            weights = loop_data['weights']
            loop_tri_indices = loop_data['loop_tri_indices']
            material_indices = loop_data['material_indices']
            
            # Create structured array for all loops
            num_uvs = len(uvs)
            dtype = make_vertex_dtype(num_uvs)
            num_loops = len(positions)
            structured = np.empty(num_loops, dtype=dtype)
            
            structured['position'] = positions
            structured['normal'] = normals
            structured['tangent'] = tangents
            structured['bitangent'] = bitangents
            
            for i, uv in enumerate(uvs):
                structured[f'uv{i}'] = uv
            
            if colors is not None:
                structured['color'] = colors
            else:
                self.high_quality_colors = False # no need to export high quality colors if there are no colors
                structured['color'][:] = 255 
            
            if use_skinning:
                structured['bone_ids'] = bone_ids
                structured['bone_weights'] = weights
            else:
                structured['bone_ids'][:] = (0, 0, 0, 0)
                structured['bone_weights'][:] = (0, 0, 0, 1)
            
            # Deduplicate vertices
            unique_verts, unique_tri_indices, _ = dedupe_vertices_structured(
                structured, loop_tri_indices, material_indices
            )
            
            # Now segment by material
            sorted_idx = np.argsort(material_indices)
            sorted_materials = material_indices[sorted_idx]
            sorted_triangles = unique_tri_indices[sorted_idx]
            
            # Find boundaries where material changes
            mat_change = np.where(np.diff(sorted_materials) != 0)[0] + 1
            
            # Split triangles by material
            triangle_groups = np.split(sorted_triangles, mat_change)
            material_groups = np.split(sorted_materials, mat_change)
            
            # Create NudMesh for each material
            for tri_group, mat_group in zip(triangle_groups, material_groups):
                mat_index = mat_group[0]  # All triangles in group have same material
                mat_name = mesh.materials[mat_index].name
                
                # Get unique vertex indices used by this material
                unique_vert_indices = np.unique(tri_group)
                
                # Remap triangle indices to be 0-based for this material
                remap = {old_idx: new_idx for new_idx, old_idx in enumerate(unique_vert_indices)}
                remapped_tris = np.vectorize(remap.get)(tri_group).reshape(-1, 3)
                
                # Extract vertices for this material
                mat_verts = unique_verts[unique_vert_indices]
                
                # Stripify if requested
                if self.export_tristrips:
                    faces = tristrip.stripify(remapped_tris.tolist(), self.stitch_tristrips)
                else:
                    faces = remapped_tris.tolist()
                
                if len(mat_verts) < 3:
                    self.operator.report({'WARNING'}, f'[NUD MESH] {obj.name}, mat {mat_name} has no valid faces and was skipped.')
                    continue
                
                # Create NudMesh
                mat_mesh = build_nud_mesh_from_verts(mat_verts, faces, num_uvs, use_skinning, 
                                                     export_tangents=self.export_tangents,
                                                     high_quality_colors=self.high_quality_colors,
                                                     high_precision_uvs=self.high_precision_uvs)
                if mat_mesh is None:
                    self.operator.report({'WARNING'}, f'[NUD MESH] {obj.name}, mat {mat_name} has no valid faces and was skipped.')
                    continue

                if not obj.data.materials:
                    self.operator.report({'WARNING'}, f'[NUD MESH] {obj.name} has no material and will be skipped.')
                    continue

                mat_slot = obj.data.materials[mat_name]
                mat, textures_to_process = self.make_xfbin_material(mat_slot, chunk.rigging_flag, clump, context)
                chunk.material_chunks.append(mat)
                mat_mesh.materials = self.make_nud_materials(obj, mat_slot, clump, context)
                texture_chunks_dict.update(textures_to_process)

                mesh_group.meshes.append(mat_mesh)



            model_chunks.append(chunk)

            #update the mesh object
            obj.update_tag()

        # process and add texture chunks
        for tex_chunk, texture in texture_chunks_dict.values():
            texture_chunk = self.make_texture(tex_chunk, texture)

        return model_chunks

    def make_modelhit(self, obj, clump, context):
        modelhit_data = obj.xfbin_modelhit_data
        #modelhit = NuccChunkModelHit(clump.filePath, obj.name[:-6] if obj.name.endswith('_[HIT]') else obj.name)
        modelhit = self.create_chunk(NuccChunkModelHit, clump.filePath, obj.name[:-6] if obj.name.endswith('_[HIT]') else obj.name)
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

    def make_xfbin_material(self, mat, flags: RiggingFlag, clump: NuccChunkClump, context) -> NuccChunkMaterial:
        pg = mat.xfbin_material_data

        #chunk = NuccChunkMaterial(clump.filePath, mat.name)
        chunk = self.create_chunk(NuccChunkMaterial, clump.filePath, mat.name)
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
        textures_to_process = {}
        for mattex in mat.xfbin_material_data.NUTextures:
            texture: XfbinTextureChunkPropertyGroup = bpy.context.scene.xfbin_texture_chunks_data.texture_chunks.get(mattex.name)
            
            texture_hash = hash(texture.name + texture.path)
            texture_chunk = textures_to_process.get(texture_hash)
            if not texture_chunk:
                #t = NuccChunkTexture(texture.path, texture.name)
                t = self.create_chunk(NuccChunkTexture, texture.path, texture.name)
                textures_to_process[texture_hash] = t, texture
            else:
                t = texture_chunk[0]
            
            g.texture_chunks.append(t)
        
        g2 = MaterialTextureGroup()
        #copy g to g2
        for attr, value in g.__dict__.items():
            setattr(g2, attr, value)
        chunk.texture_groups.append(g)
        
        if flags & RiggingFlag.OUTLINE and pg.texGroupsCount > 1:
            chunk.texture_groups.append(g2)
            pg.texGroupsCount = 2
        else:
            pg.texGroupsCount = 1
        
        
        return chunk, textures_to_process
    
    def make_texture(self, texture_chunk: NuccChunkTexture, texture: XfbinTextureChunkPropertyGroup):
        #Create a texture chunk
        if not texture.reference and self.export_textures:
            texture_chunk.has_data = True
            texture_chunk.has_props = True
            texture_chunk.nut = Nut()
            texture_chunk.nut.magic = 'NTP3'
            texture_chunk.nut.version = 0x100
            texture_chunk.nut.textures = [] 
            texture_chunk.nut.texture_count = 0

            if texture.textures:
                for tex in texture.textures:
                    tex: NutTexturePropertyGroup
                    image = tex.image
                    if image:
                        if image.packed_file:
                            image_data = image.packed_file.data
                        else:
                            image.pack()
                            image.source = 'FILE'
                            image_data = image.packed_file.data
                        
                        try:
                            nuttex: NutTexture = convert_texture(image_data, tex.target_format)
                            texture_chunk.nut.textures.append(nuttex)
                            texture_chunk.nut.texture_count += 1
                        except Exception as e:
                            print(e)
                            self.operator.report({'WARNING'}, f'Could not export texture {tex.name}. Unsupported texture format.')    
                            return None
                    else:
                        self.operator.report({'WARNING'}, f'Could not export texture {tex.name}. Make sure that the image is assigned to the texture.')
                        return None
            else:
                self.operator.report({'WARNING'}, f'Could not export texture {texture.name}. Make sure that the image is assigned to the texture.')
                return None

            if texture_chunk.nut.texture_count == 0:
                #discard the nut chunk if it has no textures
                return None
            
            #add texture to texture list
            self.xfbin.add_chunk_page(texture_chunk)
        
        return texture_chunk
    
    def make_dynamics(self, armature_obj: Object, clump: NuccChunkClump, context) -> NuccChunkDynamics:
        dynamics_data: DynamicsPropertyGroup = armature_obj.xfbin_dynamics_data
        clump_data: ClumpPropertyGroup = armature_obj.xfbin_clump_data
        #dynamics = NuccChunkDynamics(clump_data.path, clump_data.name)
        dynamics = self.create_chunk(NuccChunkDynamics, clump_data.path, clump_data.name)
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
            flag = 0
            if spring_group.ignore_animations:
                flag |= 1
            if spring_group.maintain_shape:
                flag |= 2
            
            d.shorts = [flag] * d.BonesCount
            
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

def extract_loop_data_numpy(mesh_obj, mesh, coord_indices_dict, max_influences=4, normals_as_tangents=False, high_quality_colors=False):
    mesh.calc_loop_triangles()
    
    mesh2 = mesh.copy()
    if mesh2.attributes.get("custom_normal"):
        mesh2.attributes.remove(mesh2.attributes["custom_normal"])

    
    num_loops = len(mesh.loops)
    num_verts = len(mesh.vertices)
    num_tris  = len(mesh.loop_triangles)

    # === Allocate NumPy arrays ===
    vertex_indices = np.empty(num_loops, dtype=np.int32)
    loop_normals   = np.empty((num_loops, 3), dtype=np.float32)
    positions      = np.empty((num_loops, 3), dtype=np.float32)
    tangents       = np.empty((num_loops, 3), dtype=np.float32)
    colors         = np.zeros((num_loops, 4), dtype=np.float32)
    uvs            = [np.zeros((num_loops, 2), dtype=np.float32) for _ in range(len(mesh.uv_layers))]

    mesh.loops.foreach_get("vertex_index", vertex_indices)
    mesh.loops.foreach_get("normal", loop_normals.ravel())

    for uv_index, uv_layer in enumerate(mesh.uv_layers):
        uv_layer.data.foreach_get("uv", uvs[uv_index].ravel())
        uvs[uv_index][:, 1] = 1 - uvs[uv_index][:, 1]  # Flip Y

    if mesh.color_attributes:
        # requires Blender 4.x 'color_srgb'
        mesh.color_attributes[0].data.foreach_get("color_srgb", colors.ravel())
        if not high_quality_colors:
            colors = (colors[:, :4] * 255).astype(np.uint8)

    # === Vertex positions (transformed) ===
    vert_positions = np.empty((num_verts, 3), dtype=np.float32)
    mesh.vertices.foreach_get("co", vert_positions.ravel())
    positions[:] = vert_positions[vertex_indices] * 100.0  # Scale to cm

    # === Tangents or "normals as tangents" ===
    if normals_as_tangents:
        vert_normals = np.empty((num_verts, 3), dtype=np.float32)
        mesh2.vertices.foreach_get("normal", vert_normals.ravel())
        tangents[:] = vert_normals[vertex_indices]
    else:
        mesh.loops.foreach_get("tangent", tangents.ravel())
    
    bpy.data.meshes.remove(mesh2)

    # === Process bone weights efficiently ===
    vertex_groups = mesh_obj.vertex_groups
    
    # First calculate weights per vertex
    vertex_bone_ids = np.zeros((num_verts, max_influences), dtype=">u4")
    vertex_weights = np.zeros((num_verts, max_influences), dtype=np.float32)
    
    for v_idx, vertex in enumerate(mesh.vertices):
        # Get valid bone influences for this vertex
        influences = []
        for group in vertex.groups:
            if group.weight > 0:
                group_name = vertex_groups[group.group].name
                if group_name in coord_indices_dict:
                    influences.append((coord_indices_dict[group_name], group.weight))
        
        if influences:
            # Sort by weight (descending) and limit influences
            influences.sort(key=lambda x: x[1], reverse=True)
            influences = influences[:max_influences]
            
            # Normalize weights
            total_weight = sum(weight for _, weight in influences)
            if total_weight > 0:
                for i, (bone_idx, weight) in enumerate(influences):
                    vertex_bone_ids[v_idx, i] = bone_idx
                    vertex_weights[v_idx, i] = weight / total_weight
            else:
                # Edge case: weights sum to 0
                vertex_weights[v_idx, max_influences-1] = 1.0
        else:
            # No valid influences - use default
            vertex_weights[v_idx, max_influences-1] = 1.0
    
    # Map vertex weights to loops for per-loop data
    bone_ids = vertex_bone_ids[vertex_indices]
    weights = vertex_weights[vertex_indices]

    # === Triangle index data ===
    loop_tri_indices = np.empty((num_tris, 3), dtype=np.uint32)
    material_indices = np.empty(num_tris, dtype=np.uint8)
    mesh.loop_triangles.foreach_get("loops", loop_tri_indices.ravel())
    mesh.loop_triangles.foreach_get("material_index", material_indices)

    return {
        "positions": positions,
        "normals": loop_normals,
        "tangents": tangents,
        "uvs": uvs,
        "colors": colors,
        "bone_ids": bone_ids,
        "weights": weights,
        "loop_tri_indices": loop_tri_indices,
        "material_indices": material_indices,
        "vertex_indices": vertex_indices
    }
    

def dedupe_vertices_structured(verts, tri_indices, material_indices):
    """
    verts: structured numpy array, shape (num_loops,)
    tri_indices: (num_tris, 3) int array referring to loop indices
    material_indices: (num_tris,) int array
    """

    raw = verts.view(np.void)  # shape (num_loops,)

    unique_raw, unique_index, inverse_map = np.unique(
        raw, return_index=True, return_inverse=True
    )

    unique_verts = verts[unique_index]

    unique_tris = inverse_map[tri_indices]

    return unique_verts, unique_tris, material_indices


def make_vertex_dtype(num_uvs):
    dtype = [
        ('position', 'f4', 3),
        ('normal', 'f4', 3),
        ('tangent', 'f4', 3),
        ('bitangent', 'f4', 3),
    ]
    for i in range(num_uvs):
        dtype.append((f'uv{i}', 'f4', 2))
    dtype += [
        ('color', 'u1', 4),
        ('bone_ids', 'u4', 4),
        ('bone_weights', 'f4', 4),
    ]
    return np.dtype(dtype)

def build_nud_mesh_from_verts(unique_verts, faces, num_uvs, use_skinning=True, export_tangents=False, high_quality_colors=False, high_precision_uvs=False):
    """Build a NudMesh from already-deduplicated vertices and faces."""
    if len(unique_verts) < 3:
        return None

    mesh = NudMesh()
    mesh.vertices = unique_verts
    mesh.faces = faces
    mesh.uv_type = 2
    if high_precision_uvs:
        mesh.uv_type |= 0x01
    if high_quality_colors:
        mesh.uv_type |= 0x04
    
    bone_type = 0x00
    face_flag = 0x00
    vertex_type = 0x01  # positions, normals
    if export_tangents:
        vertex_type |= 0x02  # tangents, bitangents
    if use_skinning:
        bone_type = 0x10  # bone IDs and weights
        face_flag = 0x04  # skinned faces


            
    
    mesh.vertex_type, mesh.bone_type, mesh.face_flag = (vertex_type, bone_type, face_flag)

    return mesh


def menu_func_export(self, context):
    self.layout.operator(ExportXfbin.bl_idname, text='XFBIN Model Container (.xfbin)')

