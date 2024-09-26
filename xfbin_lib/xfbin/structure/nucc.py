from enum import IntFlag
from typing import Dict, Iterator, List, Optional, Set

from ..util import *
from .anm import AnmClump, AnmEntry
from .br.br_nucc import *
from .br.br_nud import *
from .br.br_nut import *
from .nud import Nud
from .nut import Nut


class NuccChunk:
    filePath: str
    name: str
    data: bytearray

    extension: str

    chunks: List['NuccChunk']

    def __init__(self, file_path, name, type_str = "NuccChunk"):
        self.extension = ''
        self.filePath = file_path
        self.name = name
        self.type = type_str

        self.has_data = False
        self.has_props = False
        self.chunks = list()

    def set_data(self, data: bytearray, chunks):
        self.data = data
        self.has_data = True

        self.chunks = [c for c in chunks if not isinstance(
            c, (NuccChunkPage, NuccChunkIndex))]

    def init_data(self, br_chunk: BrNuccChunk, chunk_list: List['NuccChunk'], chunk_indices: List[int], chunk_refs: List['ChunkReference'], initial_chunks: List['NuccChunk']):
        """Initializes the data of this `NuccChunk` from a `BrNuccChunk`, using a chunk list and a list of
        local page indices for properly setting references to other `NuccChunk`s
        """
        self.type = br_chunk.type
        self.version = br_chunk.version
        self.data = br_chunk.data
        #self.version = br_chunk.version
        self.has_data = True

        # Temporary way to store referenced chunks for rebuilding
        # TODO: Maybe replace this with a better solution later
        #self.chunks = [chunk_list[x]
        #               for x in chunk_indices if not isinstance(chunk_list[x], (NuccChunkPage, NuccChunkIndex))]
        self.chunks = initial_chunks

    def get_data(self, file_data_only: bool) -> bytearray:
        """Returns the data of this chunk when it was first read from the XFBIN as a buffer.\n
        If file_data_only is True, will return only the data contained in the formatted file of the chunk.
        (NTP3 .nut for nuccChunkTexture, NDP3 .nud for nuccChunkModel)
        """
        if file_data_only and hasattr(self, 'file_data'):
            return getattr(self, 'file_data')

        return self.data

    def to_dict(self) -> Dict[str, str]:
        d = dict()
        d['Name'] = self.name
        d['Type'] = NuccChunk.get_nucc_str_from_type(type(self))
        d['Path'] = self.filePath
        d['Version'] = hex(self.version)

        return d

    @classmethod
    def get_nucc_type_from_str(cls, type_str: str) -> type:
        type_name = type_str[0].upper() + type_str[1:]
        result = globals().get(type_name, None)

        if result is None:
            # Create a new type and add it to the globals
            result = type(type_name, (cls,), {})
            globals()[type_name] = result

        return result

    @classmethod
    def get_nucc_str_from_type(cls, nucc_type: type) -> str:
        return nucc_type.__name__[0].lower() + nucc_type.__name__[1:]

    @classmethod
    def get_nucc_str_short_from_type(cls, nucc_type: type) -> str:
        return cls.get_nucc_str_from_type(nucc_type)[len(NuccChunk.__qualname__):]

    @classmethod
    def create_from_nucc_type(cls, type_str, file_path, name) -> 'NuccChunk':
        return cls.get_nucc_type_from_str(type_str)(file_path, name, type_str)

    @classmethod
    def get_all_nucc_types(cls):
        # This will only return types with names that start with this class's name (but are not this class)
        return [n for (k, n) in globals() if k.startswith(cls.__qualname__) and len(k) > len(cls.__qualname__)]

    def __eq__(self, o: object) -> bool:
        # Treat NuccChunks as ChunkMaps:
        # ChunkMaps are only equal to other ChunkMaps that have the same type, file path, and name
        return isinstance(o, type(self)) and self.filePath == o.filePath and self.name == o.name

    def __hash__(self) -> int:
        # Just a simple hash calculation to allow NuccChunks to be put into a dictionary
        return hash(type(self).__qualname__) ^ hash(self.filePath) ^ hash(self.name)


class NuccChunkNull(NuccChunk):
    # Empty
    def __init__(self, file_path='', name='',type_str= "NuccChunkNull", version=0x79):
        super().__init__(file_path, name, type_str)
        self.has_props = True


class NuccChunkPage(NuccChunk):
    # Should not be used as a NuccChunk, except when writing
    def __init__(self, file_path='', name='Page0',type_str= "NuccChunkPage", version=0x79):
        super().__init__(file_path, name, type_str)
        self.has_props = True


class NuccChunkIndex(NuccChunk):
    # Does not exist
    def __init__(self, file_path='', name='index', type_str= "NuccChunkIndex", version=0x79):
        super().__init__(file_path, name, type_str)
        self.has_props = True


class NuccChunkTexture(NuccChunk):
    def __init__(self, file_path, name, type_str= "NuccChunkTexture", version=0x79):
        super().__init__(file_path, name, type_str)

        # Set these to None in case a texture is a reference only and isn't contained in the xfbin
        self.data = self.nut = None

    def init_data(self, br_chunk: BrNuccChunkTexture, chunk_list: List['NuccChunk'], chunk_indices: List[int], chunk_refs: List['ChunkReference'], initial_chunks: List['NuccChunk']):
        self.extension = '.nut'

        self.data = br_chunk.data
        #self.version = br_chunk.version
        self.has_data = True
        self.has_props = True

        self.width = br_chunk.width
        self.height = br_chunk.height

        self.nut = Nut()
        self.nut.init_data(br_chunk.brNut)


class NuccChunkDynamics(NuccChunk):
    def init_data(self, br_chunk: BrNuccChunkDynamics, chunk_list: List['NuccChunk'], chunk_indices: List[int], chunk_refs: List['ChunkReference'], initial_chunks: List['NuccChunk']):
        self.data = br_chunk.data
        #self.version = br_chunk.version
        self.has_data = True
        self.has_props = True
        self.extension = '.dynamics'

        self.SPGroupCount = br_chunk.SPGroupCount
        self.ColSphereCount = br_chunk.ColSphereCount
        self.clump_chunk: NuccChunkClump = chunk_list[chunk_indices[br_chunk.clumpChunkIndex]]
        # Make an iterator to give each Dynamics1 entry its own values
        sec1_shorts = iter(br_chunk.section1Shorts)

        self.SPGroup: List[Dynamics1] = list()
        for sec1 in br_chunk.SPGroup:
            d = Dynamics1()
            d.init_data(sec1, sec1_shorts)
            self.SPGroup.append(d)

        self.ColSphere: List[Dynamics2] = list()
        for sec2 in br_chunk.ColSphere:
            d = Dynamics2()
            d.init_data(sec2)
            self.ColSphere.append(d)


class Dynamics1:
    def __init__(self) -> None:
        self.name = ''
    def init_data(self, sec1: BrDynamics1, sec1_shorts: Iterator):
        self.Bounciness = sec1.Bounciness
        self.Elasticity = sec1.Elasticity
        self.Stiffness = sec1.Stiffness
        self.Movement = sec1.Movement
        self.coord_index = sec1.coordIndex
        self.BonesCount = sec1.BonesCount

        self.shorts = list()
        for _ in range(sec1.BonesCount):
            self.shorts.append(next(sec1_shorts))


class Dynamics2:
    def init_data(self, sec2: BrDynamics2):
        self.offset_x = sec2.offset_x
        self.offset_y = sec2.offset_y
        self.offset_z = sec2.offset_z
        self.scale_x = sec2.scale_x
        self.scale_y = sec2.scale_y
        self.scale_z = sec2.scale_z
        self.coord_index = sec2.coordIndex
        self.attach_groups = sec2.boolflag
        # Should always be -1, but let's store it just in case
        self.negative_unk = sec2.negativeUnk

        self.attached_groups_count = sec2.attached_groups_count
        self.attached_groups = sec2.attached_groups


class NuccChunkClump(NuccChunk):

    def init_data(self, br_chunk: BrNuccChunkClump, chunk_list: List['NuccChunk'], chunk_indices: List[int], chunk_refs: List['ChunkReference'], initial_chunks: List['NuccChunk']):

        self.data = br_chunk.data
        #self.version = br_chunk.version
        self.has_data = True
        self.has_props = True

        #print('Clump chunk: ', self.name)

        self.field00 = br_chunk.field00

        self.coord_flag0 = br_chunk.coordFlag0
        self.coord_flag1 = br_chunk.coordFlag1

        self.bounding_box = br_chunk.bounding_box if self.field00 == 2 else [0, 0, 0, 0, 0, 0]

        self.model_flag0 = br_chunk.modelFlag0
        self.model_flag1 = br_chunk.modelFlag1

        # Get the coord chunks
        self.coord_chunks: List[NuccChunkCoord] = list()
        for i in br_chunk.coordNodeIndices:
            self.coord_chunks.append(chunk_list[chunk_indices[i]])

        # Setup the coord node hierarchy
        self.root_nodes: List[CoordNode] = list()
        for i, j in zip(range(len(self.coord_chunks)), br_chunk.coordNodeParentsIndices):
            if j == -1:
                #print('Root node name: ', self.coord_chunks[i].node.name)
                #print(f"j: {j}")
                # There could be multiple root nodes: add all of them
                self.root_nodes.append(self.coord_chunks[i].node)
            else:
                #print('Child node name: ', self.coord_chunks[i].node.name)
                #print('Parent node name: ', self.coord_chunks[j].node.name)
                # Set the node's parent and add the node to its parent's children
                self.coord_chunks[i].node.parent = self.coord_chunks[j].node
                self.coord_chunks[j].node.children.append(
                    self.coord_chunks[i].node)

        # Get the model chunks
        self.model_chunks: List[NuccChunkModel] = list()
        for i in br_chunk.modelIndices:
            model: NuccChunkModel = chunk_list[chunk_indices[i]]
            self.model_chunks.append(model)

            # There are other types of chunks that can be used as models (Billboard for example)
            if isinstance(model, NuccChunkModel):
                # Set the model chunk's respective coord
                if model.coord_index != -1:
                    model.coord_chunk = self.coord_chunks[model.coord_index]

        # Initialize the model groups
        self.model_groups: List[ClumpModelGroup] = list()
        for model_group in br_chunk.modelGroups:
            self.model_groups.append(ClumpModelGroup())
            self.model_groups[-1].init_data(model_group,
                                            self.coord_chunks, chunk_list, chunk_indices)

    def clear_non_model_chunks(self, model_list: bool = True, model_groups: bool = True, none_refs: bool = False) -> int:
        """Removes all chunks that are not NuccChunkModel from the model list and model groups of this clump, based on the arguments.\n
        If none_refs is True, will also remove "None" entries.\n
        Returns the number of chunks removed, including duplicates.
        """

        org_count = len(self.model_chunks) + \
            sum(list(map(lambda x: len(x.model_chunks), self.model_groups)))

        if model_list:
            self.model_chunks = [x for x in self.model_chunks if isinstance(
                x, NuccChunkModel) or ((x is None) if (not none_refs) else False)]

        if model_groups:
            for group in self.model_groups:
                group.model_chunks = [x for x in group.model_chunks if isinstance(
                    x, NuccChunkModel) or ((x is None) if (not none_refs) else False)]

        return org_count - (len(self.model_chunks) + sum(list(map(lambda x: len(x.model_chunks), self.model_groups))))


class ClumpModelGroup:
    def __init__(self) -> None:
        self.model_chunks: List[NuccChunkModel] = list()

    def init_data(self, model_group: BrClumpModelGroup, coord_chunks: List['NuccChunkCoord'], chunk_list: List['NuccChunk'], chunk_indices: List[int]):
        self.flag0 = model_group.flag0
        self.flag1 = model_group.flag1
        self.unk = model_group.unk

        self.model_chunks: List[NuccChunkModel] = list(
            map(lambda x: chunk_list[chunk_indices[x]] if x != -1 else None, model_group.modelIndices))
        
        for chunk in self.model_chunks:
            # Set the model chunk's respective coord
            if chunk and chunk.coord_index != -1:
                chunk.coord_chunk = coord_chunks[chunk.coord_index]

    def __iter__(self):
        return iter(self.model_chunks)


class NuccChunkCoord(NuccChunk):
    def init_data(self, br_chunk: BrNuccChunkCoord, chunk_list: List['NuccChunk'], chunk_indices: List[int], chunk_refs: List['ChunkReference'], initial_chunks: List['NuccChunk']):
        self.data = br_chunk.data
        #self.version = br_chunk.version
        self.has_data = True
        self.has_props = True

        # Pass a reference to the chunk itself for accessing it later
        self.node = CoordNode(self)
        self.node.init_data(br_chunk)


class CoordNode:
    parent: Optional['CoordNode']
    children: List['CoordNode']

    def __init__(self, chunk: NuccChunkCoord):
        self.chunk = chunk

        self.name = chunk.name
        self.parent = None
        self.children = list()

        self.position = (0.0,) * 3
        self.rotation = (0.0,) * 3
        self.scale = (1.0,) * 3
        self.matrix = None
        self.opacity = 1.0
        self.flags = 0

    def init_data(self, coord: BrNuccChunkCoord):
        self.position = coord.position
        self.rotation = coord.rotation
        self.scale = coord.scale
        self.opacity = coord.opacity
        self.flags = coord.flags

    def get_children_recursive(self) -> List['CoordNode']:
        result = list()

        for child in self.children:
            result.extend(child.get_children_recursive())

        return result

    def copy_from(self, other: 'CoordNode'):
        """Copies the contents of another node into this node without changing the parenting relations."""

        self.position = other.position
        self.rotation = other.rotation
        self.scale = other.scale
        self.opacity = other.opacity
        self.flags = other.flags


class NuccChunkModel(NuccChunk):
    def init_data(self, br_chunk: BrNuccChunkModel, chunk_list: List['NuccChunk'], chunk_indices: List[int], chunk_refs: List['ChunkReference'], initial_chunks: List['NuccChunk']):
        self.extension = '.nud'

        self.data = br_chunk.data
        #self.version = br_chunk.version
        self.has_data = True
        self.has_props = True

        # Store the rigging flag to use when writing, if the rigging flag was not specified while exporting
        self.rigging_flag = RiggingFlag(br_chunk.riggingFlag)

        self.model_attributes = br_chunk.attributes
        self.render_layer = br_chunk.renderLayer #render layers are different in each game

        self.light_mode_id = br_chunk.lightModeID
        self.light_category = br_chunk.lightCategoryFlag

        self.bounding_box = br_chunk.boundingBox if self.model_attributes & 0x04 else tuple()

        # Reference to the clump chunk of this page
        self.clump_chunk = chunk_list[chunk_indices[br_chunk.clumpIndex]]

        # Reference to the ModelHit chunk of this model
        self.hit_chunk = chunk_list[chunk_indices[br_chunk.hitIndex]]
        # This will be set later in the clump, using the index
        self.coord_chunk: Optional[NuccChunkCoord] = None

        # This should be set again when creating a new instance, instead of getting it from the clump when writing
        self.coord_index = br_chunk.meshBoneIndex

        #self.file_data = br_chunk.nud_data

        # Create a Nud from the BrNud
        self.nud = Nud()
        self.nud.init_data(self.name, br_chunk.brNud)

        # Get the material chunks
        self.material_chunks: List[NuccChunkMaterial] = list()
        for i in br_chunk.materialIndices:
            self.material_chunks.append(chunk_list[chunk_indices[i]])

    def copy_from(self, other: 'NuccChunkModel'):
        """Copies the contents of another chunk to this chunk (shallow copy).\n
        Used for modifying a chunk without losing its original reference inside other chunks.
        """

        if hasattr(other, 'data'):
            self.data = other.data

        self.extension = other.extension

        self.rigging_flag = other.rigging_flag
        self.material_flags = other.material_flags
        self.flag1_floats = other.flag1_floats

        self.clump_chunk = other.clump_chunk

        if other.hit_chunk and not isinstance(other.hit_chunk, NuccChunkNull):
            self.hit_chunk = other.hit_chunk
        self.coord_chunk = other.coord_chunk
        self.coord_index = other.coord_index

        self.nud = other.nud
        self.material_chunks = other.material_chunks


class RiggingFlag(IntFlag):
    NULL = 0x0

    UNSKINNED = 0x01  # Storm eyes and JoJo teeth
    SKINNED = 0x02  # JoJo eyes
    OUTLINE = 0x04

    # Storm 4 and JoJo use these two combined for most models (in addition to the previous flags)
    BLUR = 0x10
    SHADOW = 0x20


class NuccChunkMaterial(NuccChunk):
    def __init__(self, file_path, name, type_str= "NuccChunkMaterial"):
        super().__init__(file_path, name, type_str)
        self.alpha = 0
        self.glare = 0
        self.flags = 0
        self.UV0 = [0,0,0,0]
        self.UV1 = [0,0,0,0]
        self.UV2 = [0,0,0,0]
        self.UV3 = [0,0,0,0]
        self.BlendRate = 0
        self.BlendType = 0
        self.Misc0 = 0
        self.Misc1 = 0
        
        self.texture_groups: List[MaterialTextureGroup] = list()
    def init_data(self, br_chunk: BrNuccChunkMaterial, chunk_list: List['NuccChunk'], chunk_indices: List[int], chunk_refs: List['ChunkReference'], initial_chunks: List['NuccChunk']):
        self.data = br_chunk.data
        #self.version = br_chunk.version
        self.has_data = True
        self.has_props = True

        self.alpha = br_chunk.alpha
        self.glare = br_chunk.glare

        self.flags = br_chunk.flags
        if br_chunk.flags & 0x01:
            self.UV0 = br_chunk.UV0
        if br_chunk.flags & 0x02:
            self.UV1 = br_chunk.UV1
        if br_chunk.flags & 0x04:
            self.UV2 = br_chunk.UV2
        if br_chunk.flags & 0x08:
            self.UV3 = br_chunk.UV3
        if br_chunk.flags & 0x10:
            self.BlendRate = br_chunk.BlendRate
            self.BlendType = br_chunk.BlendType
        if br_chunk.flags & 0x20:
            self.fallOff = br_chunk.fallOff
        if br_chunk.flags & 0x40:
            self.outlineID = br_chunk.outlineID
        
        self.texture_groups: List[MaterialTextureGroup] = list()
        for group in br_chunk.textureGroups:
            g = MaterialTextureGroup()
            g.init_data(group, chunk_list, chunk_indices)
            self.texture_groups.append(g)

    def __iter__(self):
        all_textures: Set[NuccChunkTexture] = set()

        for group in self.texture_groups:
            all_textures.update(group.texture_chunks)

        return iter(all_textures)


class MaterialTextureGroup:
    def init_data(self, texture_group: BrMaterialTextureGroup, chunk_list: List['NuccChunk'], chunk_indices: List[int]):
        self.unk = texture_group.unk

        self.texture_chunks: List[NuccChunkTexture] = list()
        for index in texture_group.textureIndices:
            self.texture_chunks.append(chunk_list[chunk_indices[index]])

    def __iter__(self):
        return iter(self.texture_chunks)


class NuccChunkAnmStrm(BrNuccChunk):
    def init_data(self, br_chunk: BrNuccChunkAnmStrm, chunk_list: List['NuccChunk'], chunk_indices: List[int], chunk_refs: List['ChunkReference'], initial_chunks: List['NuccChunk']):
        
        self.data = br_chunk.data
        #self.version = br_chunk.version
        self.has_data = True
        self.has_props = False

        self.anm_length = br_chunk.AnmLength
        self.frame_size = br_chunk.FrameSize
        self.loop_anm = br_chunk.isLooped
        self.clump_count = br_chunk.ClumpCount
        self.other_entry_count = br_chunk.OtherEntryCount
        self.coord_count = br_chunk.CoordCount

        self.clumps: List[AnmClump] = list()
        self.other_entry_indices = br_chunk.OtherEntryIndices
        self.coord_parents = br_chunk.CoordParents
        self.frames = []


class NuccChunkModelHit(NuccChunk):
    def init_data(self, br_chunk: BrNuccChunkModelHit, chunk_list: List['NuccChunk'], chunk_indices: List[int], chunk_refs: List['ChunkReference'], initial_chunks: List['NuccChunk']):
        self.data = br_chunk.data
        #self.version = br_chunk.version
        self.has_data = True
        self.has_props = True
        self.extension = '.modelhit'

        self.mesh_count = br_chunk.mesh_count
        self.total_vertex_size = br_chunk.total_vertex_size

        self.vertex_sections: List[ModelHit] = list()
        for hit in br_chunk.vertex_sections:
            h = ModelHit()
            h.init_data(hit)
            self.vertex_sections.append(h)


class ModelHit:
    def init_data(self, hit: BrModelHit):
        self.mesh_vertex_size = hit.mesh_vertex_size
        self.unk_count = hit.unk_count
        self.flags = hit.flags
        self.vertex_count = hit.mesh_vertex_size * 3
        self.mesh_vertices = hit.mesh_vertices


class NuccChunkBillboard(NuccChunk):
    def init_data(self, br_chunk: BrNuccChunkBillboard, chunk_list: List['NuccChunk'], chunk_indices: List[int], chunk_refs: List['ChunkReference'], initial_chunks: List['NuccChunk']):
        self.data = br_chunk.data
        #self.version = br_chunk.version


class NuccChunkModelPrimitiveBatch(NuccChunk):
    def init_data(self, br_chunk: BrNuccChunkModelPrimitiveBatch, chunk_list: List['NuccChunk'], chunk_indices: List[int], chunk_refs: List['ChunkReference'], initial_chunks: List['NuccChunk']):
        self.data = br_chunk.data
        #self.version = br_chunk.version
        self.has_data = True
        self.has_props = True
        self.extension = '.modelprimitivebatch'

        self.clump_chunk = chunk_list[chunk_indices[br_chunk.clump_index]]
        self.coord_index = -1
        self.material_chunk: NuccChunkMaterial = chunk_list[chunk_indices[br_chunk.material_index]]
        self.primitive_vertex_chunk = chunk_list[chunk_indices[br_chunk.primitive_vertex_chunk_index]]
        self.shader_id = br_chunk.shader_id

        self.meshes = [PrimitiveBatchMesh(m.bone_index, m.vertex_count) for m in br_chunk.meshes]

class PrimitiveBatchMesh:
    def __init__(self, parent_bone = None, count = 0):
        self.parent_bone = parent_bone
        self.vertex_count = count


class NuccChunkPrimitiveVertex(NuccChunk):
    def init_data(self, br_chunk: BrNuccChunkPrimitiveVertex, chunk_list: List['NuccChunk'], chunk_indices: List[int], chunk_refs: List['ChunkReference'], initial_chunks: List['NuccChunk']):
        self.data = br_chunk.data
        #self.version = br_chunk.version
        self.has_data = True
        self.has_props = True
        self.extension = '.primitivevertex'

        self.vertex_count = br_chunk.vertex_count
        self.vertices: List[PrimitiveVertex] = list()
        self.vertices = [PrimitiveVertex(v.position, v.normal, v.color, v.uv) for v in br_chunk.vertices]


class PrimitiveVertex:
    def __init__(self, position, normal, color, uv):
        self.position = position
        self.normal = normal
        self.color = color
        self.uv = uv


class NuccChunkAnm(NuccChunk):
    def init_data(self, br_chunk: BrNuccChunkAnm, chunk_list: List['NuccChunk'], chunk_indices: List[int], chunk_refs: List['ChunkReference'], initial_chunks: List['NuccChunk']):
        self.data = br_chunk.data
        self.has_data = True
        self.has_props = False

        self.frame_count = br_chunk.frame_count
        self.frame_size = br_chunk.frame_size
        self.loop_flag = br_chunk.loop_flag

        #print(f"{br_chunk.name}")

        # Set up the clumps
        self.clumps: List[AnmClump] = list()
        for br_anm_clump in br_chunk.clumps:
            anm_clump = AnmClump()
            anm_clump.init_data(br_anm_clump, chunk_refs, initial_chunks)
            self.clumps.append(anm_clump)


        self.coord_parents: List[BrAnmCoordParent] = br_chunk.coord_parents
        # Set up the child-parent relations in AnmBones
        for p in self.coord_parents:
            if -1 in [p.parent_clump_index, p.parent_coord_index, p.child_clump_index, p.child_coord_index]:
                continue
            
            p: BrAnmCoordParent
            parent = self.clumps[p.parent_clump_index].children[p.parent_coord_index]
            child = self.clumps[p.child_clump_index].children[p.child_coord_index]
            child.parent = parent
            parent.children.append(child)

        other_entry_chunks = list(map(lambda x: chunk_list[chunk_indices[x]], br_chunk.other_entry_indices))

        # Set up the animation entries/bones
        self.entries: List[AnmEntry] = [None] * len(br_chunk.entries)
        for i, br_entry in enumerate(br_chunk.entries):
            entry = self.entries[i] = AnmEntry()
            entry.init_data(br_entry, self.frame_size, self.clumps, other_entry_chunks)

        # Get the "other" entries from the entry list
        self.other_entries = [e for e in self.entries if e.clump is None]

class NuccChunkCamera(NuccChunk):
    def init_data(self, br_chunk: BrNuccChunkCamera, chunk_list: List['NuccChunk'], chunk_indices: List[int], chunk_refs: List['ChunkReference'], initial_chunks: List['NuccChunk']):
        self.data = br_chunk.data
        self.has_data = True
        self.has_props = False
        self.extension = '.camera'

        self.fov = br_chunk.fov