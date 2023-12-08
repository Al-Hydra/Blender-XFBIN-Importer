from ...util import *
from .br_anm import *
from .br_anm_strm import *
from .br_nud import *
from .br_nut import *


class BrNuccChunk(BrStruct):
    name: str
    filePath: str
    data: bytearray
    version: int
    anmvalue: int


    # Only used when writing
    nuccChunk: 'NuccChunk'

    def __br_read__(self, br: 'BinaryReader', file_path, name, version, anmvalue) -> None:
        # When the BrNuccChunk is read, the init_data method of the BrNuccChunk type will be called,
        # which means that this method does not have to be overrided in each subclass
        self.filePath = file_path
        self.name = name
        self.version = version
        self.anmvalue = anmvalue
        #if self.version:# != 0x79 and self.version != 0x7A:
            #print(f"Chunk name: {self.name}, Version: {self.version}, other value: {self.anmvalue} type: {type(self).__qualname__}")


        self.init_data(br)

    def init_data(self, br: BinaryReader):
        # Store the data to be given to the NuccChunk instance later
        self.data = br.buffer()
        br.seek(0)

    def __br_write__(self, br: 'BinaryReader', chunkIndexDict: IterativeDict) -> None:
        # This should be used only when an override does not exist (i.e. don't call this manually)
        br.extend(self.nuccChunk.data)
        br.seek(len(self.nuccChunk.data), Whence.CUR)

        # Try to add the referenced chunks in the same order they were added
        # This should work fine unless some other chunk in this page (before this chunk) got modified
        # TODO: Maybe replace this with a better solution later
        chunkIndexDict.update_or_next(self.nuccChunk.chunks)

    @classmethod
    def get_br_nucc_type_from_str(cls, type_str: str) -> type:
        # Get the type from a string after capitalizing its first character and prepending "Br" to it
        type_name = "Br" + type_str[0].upper() + type_str[1:]
        result = globals().get(type_name, None)

        if result is None:
            # Create a new type and add it to the globals
            result = type(type_name, (cls,), {})
            globals()[type_name] = result

        return result

    @classmethod
    def create_from_nucc_type(cls, type_str, file_path, name, data, version, anmvalue) -> 'BrNuccChunk':
        # Read a BrNuccChunk struct from the data using the type and set the name and file path
        return BinaryReader(data, Endian.BIG).read_struct(cls.get_br_nucc_type_from_str(type_str), None, file_path, name, version, anmvalue)


class BrNuccChunkNull(BrNuccChunk):
    # Empty
    def __br_write__(self, br: 'BinaryReader', chunkIndexDict: IterativeDict):
        pass


class BrNuccChunkPage(BrNuccChunk):
    def init_data(self, br: BinaryReader):
        super().init_data(br)
        self.pageSize = br.read_uint32()
        self.referenceSize = br.read_uint32()

    def __br_write__(self, br: 'BinaryReader', chunkIndexDict: IterativeDict, chunkReferences: List):
        # Write the size of the dictionary, and add 1 for the index chunk after this chunk
        br.write_uint32(len(chunkIndexDict) + 1)
        br.write_uint32(len(chunkReferences))


class BrNuccChunkIndex(BrNuccChunk):
    # Does not exist
    pass


class BrNuccChunkTexture(BrNuccChunk):
    def init_data(self, br: BinaryReader):
        super().init_data(br)
        
        self.field00 = br.read_uint16()
        self.width = br.read_uint16()
        self.height = br.read_uint16()
        self.field06 = br.read_uint16()

        self.nutSize = br.read_uint32()

        try:
            self.nut_data = br.buffer()[br.pos(): br.pos() + self.nutSize]
            self.brNut = BinaryReader(
                self.nut_data, Endian.BIG).read_struct(BrNut)
        except:
            print(
                f'Failed to read chunk: {self.name} of type: {type(self).__qualname__}')
            self.brNut = None

        #br.seek(self.nutSize, Whence.CUR)

    def __br_write__(self, br: 'BinaryReader', chunkIndexDict: IterativeDict):

        br.write_uint16(0)  # Placeholder values
        br.write_uint16(
            self.nuccChunk.nut.textures[0].width if self.nuccChunk.nut.textures else 0)
        br.write_uint16(
            self.nuccChunk.nut.textures[0].height if self.nuccChunk.nut.textures else 0)
        br.write_uint16(0)

        with BinaryReader(endianness=Endian.BIG) as br_internal:
            br_internal.write_struct(BrNut(), self.nuccChunk.nut)

            # Write the nut size
            br.write_uint32(br_internal.size())
            # Write the nut data
            br.extend(br_internal.buffer())
            # Advance the position
            br.seek(br_internal.size(), Whence.CUR)


class BrNuccChunkDynamics(BrNuccChunk):
    def init_data(self, br: BinaryReader):
        super().init_data(br)

        self.SPGroupCount = br.read_uint16()
        self.ColSphereCount = br.read_uint16()

        # Chunk index of the clump of this model, but relative to this page
        self.clumpChunkIndex = br.read_uint32()

        self.SPGroup = br.read_struct(BrDynamics1, self.SPGroupCount)
        self.ColSphere = br.read_struct(BrDynamics2, self.ColSphereCount)

        # Read all shorts as a single tuple for now
        self.section1Shorts = br.read_uint16(
            sum(map(lambda x: x.BonesCount, self.SPGroup)))

    def __br_write__(self, br: 'BinaryReader', chunkIndexDict: IterativeDict):
        chunk = self.nuccChunk

        br.write_uint16(chunk.SPGroupCount)
        br.write_uint16(chunk.ColSphereCount)

        br.write_uint32(chunkIndexDict.get_or_next(chunk.clump_chunk))

        # Write the section 1 shorts while iterating over it
        br_sec1_shorts = BinaryReader(endianness=Endian.BIG)

        for sec1 in chunk.SPGroup:
            br.write_struct(BrDynamics1(), sec1)
            br_sec1_shorts.write_uint16(sec1.shorts)

        for sec2 in chunk.ColSphere:
            br.write_struct(BrDynamics2(), sec2)

        br.extend(br_sec1_shorts.buffer())
        br.seek(br_sec1_shorts.size(), Whence.CUR)


# Placeholder names for now
class BrDynamics1(BrStruct):
    def __br_read__(self, br: 'BinaryReader'):
        self.Bounciness = br.read_float()
        self.Elasticity = br.read_float()
        self.Stiffness = br.read_float()
        self.Movement = br.read_float()

        # Coord index in the clump's coord indices
        self.coordIndex = br.read_uint16()
        self.BonesCount = br.read_uint16()

    def __br_write__(self, br: 'BinaryReader', sec1: 'Dynamics1'):
        br.write_float(sec1.Bounciness)
        br.write_float(sec1.Elasticity)
        br.write_float(sec1.Stiffness)
        br.write_float(sec1.Movement)

        br.write_uint16(sec1.coord_index)
        br.write_uint16(len(sec1.shorts))


class BrDynamics2(BrStruct):
    def __br_read__(self, br: 'BinaryReader'):
        self.offset_x = br.read_float()
        self.offset_y = br.read_float()
        self.offset_z = br.read_float()
        self.scale_x = br.read_float()
        self.scale_y = br.read_float()
        self.scale_z = br.read_float()

        self.coordIndex = br.read_uint16()
        self.boolflag = br.read_uint16()

        self.negativeUnk = br.read_int16()
        br.read_uint16()

        self.attached_groups_count = 0
        self.attached_groups = 0

        self.attached_groups = list()
        if self.boolflag == 1:
            self.attached_groups_count = br.read_uint16()
            self.attached_groups = br.read_uint16(self.attached_groups_count)

    def __br_write__(self, br: 'BinaryReader', sec2: 'Dynamics2'):
        br.write_float(sec2.offset_x)
        br.write_float(sec2.offset_y)
        br.write_float(sec2.offset_z)
        br.write_float(sec2.scale_x)
        br.write_float(sec2.scale_y)
        br.write_float(sec2.scale_z)

        br.write_uint16(sec2.coord_index)
        br.write_uint16(sec2.attach_groups)
        br.write_int16(sec2.negative_unk)
        br.write_uint16(0)

        if sec2.attach_groups == 1:
            br.write_uint16(sec2.attached_groups_count)
            for g in sec2.attached_groups:
                br.write_uint16(g)


class BrNuccChunkClump(BrNuccChunk):
    def init_data(self, br: BinaryReader):
        super().init_data(br)

        # 0 or 1 (?)
        self.field00 = br.read_uint32()

        self.coordCount = br.read_uint16()
        self.coordFlag0 = br.read_uint8()
        self.coordFlag1 = br.read_uint8()

        if self.field00 == 2:
            br.read_half_float(14) #it might be wise to check what these values are used for

        # Signed because root node's parent index is -1
        self.coordNodeParentsIndices = br.read_int16(self.coordCount)
        self.coordNodeIndices = br.read_uint32(self.coordCount)

        self.modelCount = br.read_uint16()
        self.modelFlag0 = br.read_uint8()
        self.modelFlag1 = br.read_uint8()

        # Padding (?)
        br.read_uint32()

        self.modelIndices = br.read_uint32(self.modelCount)

        self.modelGroups = list()
        while True:
            modelGroup: BrClumpModelGroup = br.read_struct(BrClumpModelGroup)

            if modelGroup.modelCount == -1 or br.eof():
                break

            self.modelGroups.append(modelGroup)

    def __br_write__(self, br: 'BinaryReader', chunkIndexDict: IterativeDict):
        br.write_uint32(self.nuccChunk.field00)

        br.write_uint16(len(self.nuccChunk.coord_chunks))
        br.write_uint8(self.nuccChunk.coord_flag0)
        br.write_uint8(self.nuccChunk.coord_flag1)

        # Enumerate the coord chunks because the parent indices are respective to the local coord indices list, not the page indices
        coord_chunks_dict = IterativeDict()
        coord_chunks_dict.update_or_next(self.nuccChunk.coord_chunks)

        coord_chunks = tuple(
            map(lambda x: chunkIndexDict.get_or_next(x), self.nuccChunk.coord_chunks))

        for coord in self.nuccChunk.coord_chunks:
            br.write_int16(
                coord_chunks_dict[coord.node.parent.chunk] if coord.node.parent else -1)

        br.write_uint32(coord_chunks)

        br.write_uint16(len(self.nuccChunk.model_chunks))
        br.write_uint8(self.nuccChunk.model_flag0)
        br.write_uint8(self.nuccChunk.model_flag0)

        # TODO: is this correct?
        br.write_uint32(0)

        br.write_uint32(
            tuple(map(lambda x: chunkIndexDict.get_or_next(x), self.nuccChunk.model_chunks)))

        for group in self.nuccChunk.model_groups:
            br.write_struct(BrClumpModelGroup(), group, chunkIndexDict)

        br.write_int16(-1)


class BrClumpModelGroup(BrStruct):
    def __br_read__(self, br: 'BinaryReader') -> None:
        self.modelCount = br.read_int16()

        if self.modelCount != -1 and not br.eof():
            self.flag0 = br.read_uint8()
            self.flag1 = br.read_uint8()

            # Seems to be some 4 signed 8 bit integers
            self.unk = br.read_int32()

            self.modelIndices = list()
            for _ in range(self.modelCount):
                # There might be -1 indices, but we're not sure what they're used for
                # Can be found in Storm 1 spc xfbins
                self.modelIndices.append(br.read_int32())

    def __br_write__(self, br: 'BinaryReader', model_group: 'ClumpModelGroup', chunkIndexDict: IterativeDict):
        br.write_uint16(len(model_group.model_chunks))

        br.write_uint8(model_group.flag0)
        br.write_uint8(model_group.flag1)

        br.write_int32(model_group.unk)

        br.write_int32(tuple(map(lambda x: chunkIndexDict.get_or_next(
            x) if x else -1, model_group.model_chunks)))


class BrNuccChunkModel(BrNuccChunk):
    def init_data(self, br: BinaryReader):
        super().init_data(br)
        #print(self.version)
        if self.version > 0x73 and self.version < 0x76:
            self.field00 = br.read_uint16()
            # Affects if the model is correctly rigged to its bones or not
            self.riggingFlag = br.read_uint16()

            self.attributes = br.read_uint16()

            br.read_uint16()

            self.clumpIndex = br.read_uint32()
            self.hitIndex = br.read_uint32()
            self.meshBoneIndex = br.read_uint32()

            self.nudSize = br.read_uint32()

            self.lightCategoryFlag = br.read_uint16()
            self.renderLayer = br.read_uint8()
            self.lightModeID = br.read_uint8()
            
        else:
            #print("mesh version: " + str(self.version))
            self.field00 = br.read_uint16()
            # Affects if the model is correctly rigged to its bones or not
            self.riggingFlag = br.read_uint16()

            self.attributes = br.read_uint16()

            self.renderLayer = br.read_uint8()
            self.lightModeID = br.read_uint8()
            if self.version > 0x73:
                self.lightCategoryFlag = br.read_uint32()
            else:
                self.lightCategoryFlag = 0

            self.clumpIndex = br.read_uint32()
            self.hitIndex = br.read_uint32()
            self.meshBoneIndex = br.read_uint32()

            self.nudSize = br.read_uint32()

        if self.attributes & 0x04:
            self.boundingBox = br.read_float(6)
        
        self.nud_pos = br.pos()
        self.nud_data = br.read_bytes(self.nudSize)
        self.brNud = BinaryReader(self.nud_data, Endian.BIG).read_struct(BrNud)

        self.materialCount = br.read_uint16()
        self.materialIndices = br.read_uint32(self.materialCount)

    def __br_write__(self, br: 'BinaryReader', chunkIndexDict: IterativeDict):
        br.write_uint16(1)  # Can be 0 sometimes, should test more

        br.write_uint8(0)  # Padding for flag in next byte
        br.write_uint8(int(self.nuccChunk.rigging_flag))

        br.write_uint16(self.nuccChunk.model_attributes)

        br.write_uint8(self.nuccChunk.render_layer)
        br.write_uint8(self.nuccChunk.light_mode_id)

        br.write_uint32(self.nuccChunk.light_category)
        
        br.write_uint32(chunkIndexDict.get_or_next(self.nuccChunk.clump_chunk))
        br.write_uint32(chunkIndexDict.get_or_next(self.nuccChunk.hit_chunk))

        # Index of the mesh bone of this model in the clump
        # This might be shared by multiple models
        br.write_uint32(
            self.nuccChunk.coord_index if self.nuccChunk.coord_index != -1 else 0)

        # Write the BrNud using the NuccChunk's NUD
        with BinaryReader(endianness=Endian.BIG) as br_internal:
            br_internal.write_struct(BrNud(), self.nuccChunk.nud)

            # Write NUD size
            br.write_uint32(br_internal.size())

            # Write the flag1 floats, if they exist
            br.write_float(self.nuccChunk.bounding_box)

            # Write NUD buffer
            br.extend(br_internal.buffer())
            br.seek(br_internal.size(), Whence.CUR)

        # Write material chunk count
        br.write_uint16(len(self.nuccChunk.material_chunks))

        # Write the material chunk indices
        br.write_uint32(tuple(
            map(lambda x: chunkIndexDict.get_or_next(x), self.nuccChunk.material_chunks)))


class BrNuccChunkMaterial(BrNuccChunk):
    def init_data(self, br: BinaryReader):
        super().init_data(br)

        self.groupCount = br.read_uint16()

        # 0xFE in Storm 1, 0xCD in JoJo and Storm 4. Should actually find out what it does
        self.alpha = br.read_uint16()

        self.glare = br.read_float()

        self.flags = br.read_uint32()
        
        if self.flags & 0x01:
            self.UV0 = br.read_float(4)
        if self.flags & 0x02:
            self.UV1 = br.read_float(4)
        if self.flags & 0x04:
            self.UV2 = br.read_float(4)
        if self.flags & 0x08:
            self.UV3 = br.read_float(4)
        if self.flags & 0x10:
            self.BlendRate = br.read_float()
            self.BlendType = br.read_float()
        if self.flags & 0x20:
            self.fallOff = br.read_float()
        if self.flags & 0x40:
            self.outlineID = br.read_float()


        self.textureGroups = br.read_struct(
            BrMaterialTextureGroup, self.groupCount)

    def __br_write__(self, br: 'BinaryReader', chunkIndexDict: IterativeDict):
        br.write_uint16(len(self.nuccChunk.texture_groups))

        br.write_uint16(self.nuccChunk.alpha)

        br.write_float(self.nuccChunk.glare)

        br.write_uint32(self.nuccChunk.flags)

        if self.nuccChunk.flags & 0x01:
            br.write_float(self.nuccChunk.UV0)
        if self.nuccChunk.flags & 0x02:
            br.write_float(self.nuccChunk.UV1)
        if self.nuccChunk.flags & 0x04:
            br.write_float(self.nuccChunk.UV2)
        if self.nuccChunk.flags & 0x08:
            br.write_float(self.nuccChunk.UV3)
        if self.nuccChunk.flags & 0x10:
            br.write_float(self.nuccChunk.BlendRate)
            br.write_float(self.nuccChunk.BlendType)
        if self.nuccChunk.flags & 0x20:
            br.write_float(self.nuccChunk.fallOff)
        if self.nuccChunk.flags & 0x40:
            br.write_float(self.nuccChunk.outlineID)
        

        for group in self.nuccChunk.texture_groups:
            br.write_struct(BrMaterialTextureGroup(), group, chunkIndexDict)


class BrMaterialTextureGroup(BrStruct):
    def __br_read__(self, br: 'BinaryReader'):
        self.textureCount = br.read_int16()
        br.read_uint16()

        # Probably a flag
        self.unk = br.read_int32()

        self.textureIndices = br.read_uint32(self.textureCount)

    def __br_write__(self, br: 'BinaryReader', texture_group: 'MaterialTextureGroup', chunkIndexDict: IterativeDict):
        br.write_uint16(len(texture_group.texture_chunks))
        br.write_uint16(0)

        # Can be safely set to 0
        br.write_int32(texture_group.unk)

        # Write the texture chunk indices
        br.write_uint32(tuple(
            map(lambda x: chunkIndexDict.get_or_next(x), texture_group.texture_chunks)))


class BrNuccChunkCoord(BrNuccChunk):
    def init_data(self, br: BinaryReader):
        super().init_data(br)

        self.position = br.read_float(3)
        self.rotation = br.read_float(3)  # Rotation is in euler
        self.scale = br.read_float(3)
        self.unkFloat = br.read_float()   # Might be part of scale
        if self.version > 0x66:
            self.unkShort = br.read_uint16()  # Not always 0
        else:
            self.unkShort = 0

    def __br_write__(self, br: 'BinaryReader', chunkIndexDict: IterativeDict):
        node = self.nuccChunk.node

        br.write_float(node.position)
        br.write_float(node.rotation)
        br.write_float(node.scale)
        br.write_float(node.unkFloat)
        br.write_uint16(node.unkShort)


class BrNuccChunkModelHit(BrNuccChunk):
    def init_data(self, br: BinaryReader):
        super().init_data(br)
        self.mesh_count = br.read_uint32()
        self.total_vertex_size = br.read_uint32()  # multiplied by 3
        self.vertex_sections = br.read_struct(BrModelHit, self.mesh_count, self.version)

    def __br_write__(self, br: 'BinaryReader', chunkIndexDict: IterativeDict):
        br.write_uint32(self.nuccChunk.mesh_count)

        br.write_uint32(self.nuccChunk.total_vertex_size)

        for hit in self.nuccChunk.vertex_sections:
            br.write_struct(BrModelHit(), hit)


class BrModelHit(BrStruct):
    def __br_read__(self, br: 'BinaryReader', version):

        self.mesh_vertex_size = br.read_uint32()
        self.unk_count = br.read_uint8()
        self.flags = br.read_uint8(3)

        if version == 0x7A:
            br.seek(8, 1)
        
        self.vertex_count = self.mesh_vertex_size * 3
        self.mesh_vertices = [br.read_float(3)
                              for i in range(self.vertex_count)]

    def __br_write__(self, br: 'BinaryReader', hit: 'ModelHit'):
        br.write_uint32(hit.mesh_vertex_size)
        br.write_uint8(hit.unk_count)
        br.write_uint8(hit.flags)
        for vertices in hit.mesh_vertices:
            br.write_float(vertices)


class BrNuccChunkBillboard(BrNuccChunk):
    def init_data(self, br: BinaryReader):
        super().init_data(br)
        self.data = br.read_uint8(len(br.buffer()))

    def __br_write__(self, br: 'BinaryReader', chunkIndexDict: IterativeDict):
        br.write_uint8(self.nuccChunk.data)

class BrNuccChunkModelPrimitiveBatch(BrNuccChunk):
    def init_data(self, br: BinaryReader):
        super().init_data(br)
        self.clump_index = br.read_uint32()
        self.material_index = br.read_uint32()
        self.primitive_vertex_chunk_index = br.read_uint32()
        self.unk1 = br.read_uint32()
        self.mesh_count = br.read_uint16()
        self.unk2 = br.read_uint16()
        self.unk3 = br.read_uint64(2)
        self.shader_id = br.read_uint32()
        self.unk4 = br.read_uint64()
        self.unk5 = br.read_float()

        self.meshes = br.read_struct(BrPrimitiveBatchMesh, self.mesh_count)


class BrPrimitiveBatchMesh(BrStruct):
    def __br_read__(self, br: BinaryReader):
        self.bone_index = br.read_uint32()
        self.vertex_count = br.read_uint32()
        br.read_uint32()


class BrNuccChunkPrimitiveVertex(BrNuccChunk):
    def init_data(self, br: BinaryReader):
        super().init_data(br)

        self.unk = br.read_uint64()
        self.vertex_size = br.read_uint32()
        self.vertex_count = br.read_uint32()

        if self.vertex_size == 48:
            self.vertices = br.read_struct(BrPrimitiveVertex48, self.vertex_count)
        elif self.vertex_size == 64:
            self.vertices = br.read_struct(BrPrimitiveVertex64, self.vertex_count)


class BrPrimitiveVertex64(BrStruct):
    def __br_read__(self, br: BinaryReader):
        self.position = br.read_float(3)
        br.seek(4, 1)
        self.normal = br.read_float(3)
        br.seek(4, 1)
        self.color = br.read_float(4)
        self.uv = br.read_float(2)
        br.seek(8, 1)


class BrPrimitiveVertex48(BrStruct):
    def __br_read__(self, br: BinaryReader):
        self.position = br.read_float(3)
        br.seek(4, 1)
        self.normal = br.read_float(3)
        br.seek(4, 1)
        self.color = (1.0, 1.0, 1.0, 1.0)
        self.uv = br.read_float(2)
        br.seek(8, 1)


class BrNuccChunkParticles(BrNuccChunk):
    def init_data(self, br: BinaryReader):
        super().init_data(br)


class BrNuccChunkAnm(BrNuccChunk):
    def init_data(self, br: BinaryReader):
        super().init_data(br)

        self.frame_count = br.read_uint32()
        self.frame_size = br.read_uint32()  # Usually 100 (0x64)

        self.entry_count = br.read_uint16()
        self.loop_flag = br.read_uint16() # Whether the animation is looped
        self.clump_count = br.read_uint16()
        self.other_entry_count = br.read_uint16()  # Other entries have a clump index of -1
        self.other_index_count = br.read_uint16()

        self.coord_count = br.read_uint16()

        self.clumps = br.read_struct(BrAnmClump, self.clump_count)
        self.other_entry_indices = br.read_uint32(self.other_entry_count + self.other_index_count)  # Chunk indices for Camera, LightDirc, etc
        self.coord_parents = br.read_struct(BrAnmCoordParent, self.coord_count)

        self.entries = br.read_struct(BrAnmEntry, self.entry_count)

class BrNuccChunkAnmStrm(BrNuccChunk):
    def init_data(self, br: BinaryReader):
        super().init_data(br)
        
        self.AnmLength = br.read_uint32()
        self.FrameSize = br.read_uint32()
        self.FrameCount = br.read_uint16()
        self.isLooped = br.read_uint16()
        self.ClumpCount = br.read_uint16()
        self.OtherEntryCount = br.read_uint16()
        self.CoordCount = br.read_uint32()

        self.Clumps = br.read_struct(BrStrmClump, self.ClumpCount)

        self.OtherEntryIndices = br.read_uint32(self.OtherEntryCount)

        self.CoordParents = br.read_struct(BrAnmCoordParent, self.CoordCount)

        self.FrameInfo = br.read_struct(BrStrmFrameInfo, self.FrameCount)


class BrNuccChunkAnmStrmFrame(BrNuccChunk):
    def init_data(self, br: BinaryReader,):
        super().init_data(br)

        self.Frame = br.read_uint32()
        self.EntryCount = br.read_uint16()
        self.Unk = br.read_uint16()
        self.Entries = br.read_struct(BrStrmEntry, self.EntryCount)


class BrNuccChunkCamera(BrNuccChunk):
    def init_data(self, br: BinaryReader):
        super().init_data(br)

        self.unk = br.read_uint32()
        self.fov = br.read_float()

