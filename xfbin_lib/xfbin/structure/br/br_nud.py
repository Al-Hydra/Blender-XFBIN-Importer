from enum import IntFlag
from typing import List, Tuple

from ...util import *


# Based on Smash Forge Nud implementation
# https://github.com/jam1garner/Smash-Forge/blob/master/Smash%20Forge/Filetypes/Models/Nuds/NUD.cs
class BrNud(BrStruct):
    def __br_read__(self, br: BinaryReader) -> None:
        self.magic = br.read_str(4)

        if self.magic != 'NDP3':
            raise Exception('Invalid NUD magic.')

        self.fileSize = br.read_uint32()
        self.version = br.read_uint16()

        self.meshGroupCount = br.read_uint16()

        # Bone indices in the clump's coords array
        self.boneStart = br.read_uint16()
        self.boneEnd = br.read_uint16()

        self.polyClumpStart = br.read_uint32() + 0x30
        self.polyClumpSize = br.read_uint32()

        self.vertClumpStart = self.polyClumpStart + self.polyClumpSize
        self.vertClumpSize = br.read_uint32()

        self.vertAddClumpStart = self.vertClumpStart + self.vertClumpSize
        self.vertAddClumpSize = br.read_uint32()

        self.nameStart = self.vertAddClumpStart + self.vertAddClumpSize

        self.boundingSphere = br.read_float(4)

        self.meshGroups: Tuple[BrNudMeshGroup] = br.read_struct(
            BrNudMeshGroup, self.meshGroupCount, self)

        for g in self.meshGroups:
            g.meshes = br.read_struct(BrNudMesh, g.meshCount, self)

    def __br_write__(self, br: 'BinaryReader', nud: 'Nud'):
        buffers = NudBuffers()
        with BinaryReader(endianness=Endian.BIG) as br_internal:
            mesh_group_count = len(nud.mesh_groups)
            mesh_count = sum(map(lambda x: len(x.meshes), nud.mesh_groups))
            for mesh_group in nud.mesh_groups:
                br_internal.write_struct(
                    BrNudMeshGroup(), mesh_group, buffers, mesh_group_count, mesh_count)

            # Write the mesh and material buffers
            br_internal.extend(buffers.meshes.buffer())
            br_internal.extend(buffers.materials.buffer())

            # Align and seek to end
            br_internal.align(0x10)
            br_internal.seek(0, Whence.END)

            # Copy the buffer to add to the main buffer later
            mesh_groups_buffer = br_internal.buffer()

        # Write the header
        br.write_str('NDP3')
        br.write_uint32(0)  # Size with header
        br.write_uint16(0x0200)  # Version

        # Mesh group count
        br.write_uint16(len(nud.mesh_groups))

        # The bone IDs are actually global across all models in an xfbin page, but these values should be valid
        # as they would break JoJo xfbins otherwise
        # Start and end bone indices
        br.write_uint16(nud.get_bone_range())

        br.write_uint32(len(mesh_groups_buffer))  # polyClumpStart
        br.write_uint32(0)  # polyClumpSize
        br.write_uint32(0)  # vertClumpSize
        br.write_uint32(0)  # vertAddClumpSize

        # Bounding sphere affects if some meshes appear at all (tested with Storm 1 eyes)
        br.write_float(nud.bounding_sphere)

        # Write the mesh groups buffer
        br.extend(mesh_groups_buffer)
        br.seek(0, Whence.END)

        # Write each of the remaining buffers
        for i, br_other in enumerate(buffers):
            br.extend(br_other.buffer())

            if i < 3:
                # Write the sizes for polyClump, vertClump, and vertAddClump, after aligning the main buffer
                with br.seek_to(0x10 + (4 * (i + 1))):
                    br.write_uint32(br_other.size() + br.align(0x10))

        br.seek(0, Whence.END)

        # Write file size
        with br.seek_to(0x4):
            br.write_uint32(br.size())


class NudBuffers:
    def __init__(self):
        self.meshes = BinaryReader(endianness=Endian.BIG)
        self.materials = BinaryReader(endianness=Endian.BIG)
        self.polyClump = BinaryReader(endianness=Endian.BIG)
        self.vertClump = BinaryReader(endianness=Endian.BIG)
        self.vertAddClump = BinaryReader(endianness=Endian.BIG)
        self.names = BinaryReader(endianness=Endian.BIG)

    def __iter__(self):
        # Only include these 4 buffers, as the first 2 will be merged with the mesh group buffer
        return iter([self.polyClump, self.vertClump, self.vertAddClump, self.names])


class BrNudMeshGroup(BrStruct):
    meshes: List['BrNudMesh']

    def __br_read__(self, br: BinaryReader, nud: BrNud) -> None:
        self.boundingSphere = br.read_float(8)
        self.nameStart = br.read_uint32()

        with br.seek_to(self.nameStart + nud.nameStart):
            try:
                self.name = br.read_str()
            except:
                self.name = 'Unknown'

        self.unk = br.read_uint16()
        self.boneFlags = br.read_uint16()
        self.singleBind = br.read_uint16()
        self.meshCount = br.read_uint16()

        self.positionb = br.read_uint32()

    def __br_write__(self, br: 'BinaryReader', mesh_group: 'NudMeshGroup', buffers: NudBuffers, mesh_groups_count, mesh_count):
        # Bounding sphere
        br.write_float(mesh_group.bounding_sphere)

        # Name start in names buffer
        br.write_uint32(buffers.names.size())

        # Write the name
        buffers.names.align(0x10)
        buffers.names.write_str(mesh_group.name, True)

        br.write_uint16(0)
        br.write_uint16(mesh_group.bone_flags)
        br.write_int16(-1)
        br.write_int16(len(mesh_group.meshes))

        # Start offset of mesh info
        br.write_uint32(buffers.meshes.size() + 0x30 +
                        (mesh_groups_count * 0x30))

        # Write each mesh in this group
        for mesh in mesh_group.meshes:
            buffers.meshes.write_struct(
                BrNudMesh(), mesh, buffers, mesh_groups_count, mesh_count)


class BrNudMesh(BrStruct):
    def __br_read__(self, br: BinaryReader, nud: BrNud) -> None:
        self.polyClumpStart = br.read_uint32() + nud.polyClumpStart
        self.vertClumpStart = br.read_uint32() + nud.vertClumpStart
        self.vertAddClumpStart = br.read_uint32() + nud.vertAddClumpStart

        self.vertexCount = br.read_uint16()
        self.vertexSize = br.read_uint8()
        self.uvSize = br.read_uint8()

        self.texProps = br.read_uint32(4)

        self.faceCount = br.read_uint16()
        self.faceSize = br.read_uint8()
        self.faceFlag = br.read_uint8()
        br.seek(0xC, Whence.CUR)

        # Faces
        with br.seek_to(self.polyClumpStart):
            self.faces = br.read_int16(self.faceCount)

        # UV + Vertices
        with br.seek_to(self.vertClumpStart):
            boneType = self.vertexSize & 0xF0
            vertexType = self.vertexSize & 0x0F

            colors = list()
            uvs = list()
            if boneType > 0:
                uvCount = self.uvSize >> 4
                uvType = self.uvSize & 0x0F

                for i in range(self.vertexCount):
                    if uvType == NudUvType.Null:
                        colors.append(tuple())
                    elif uvType == NudUvType.Byte:
                        colors.append(br.read_uint8(4))
                    elif uvType == NudUvType.HalfFloat:
                        colors.append(
                            list(map(lambda x: int(x * 255), br.read_half_float(4))))

                    uvs.append(list())
                    for _ in range(uvCount):
                        uvs[i].append(br.read_half_float(2))

                br.seek(self.vertAddClumpStart)

            self.vertices = br.read_struct(
                BrNudVertex, self.vertexCount, vertexType, boneType, self.uvSize)

            if boneType > 0:
                for i in range(self.vertexCount):
                    self.vertices[i].color = colors[i]
                    self.vertices[i].uv = uvs[i]

        # Materials
        i = 0
        self.materials: List[BrNudMaterial] = list()
        while i < 4 and self.texProps[i] != 0:
            with br.seek_to(self.texProps[i]):
                self.materials.append(br.read_struct(
                    BrNudMaterial, None, self, nud.nameStart))
            i += 1

    def __br_write__(self, br: 'BinaryReader', mesh: 'NudMesh', buffers: NudBuffers, mesh_groups_count, mesh_count):
        # Set the formats we're going to use
        vertex_type = mesh.vertex_type
        bone_type = mesh.bone_type if mesh.has_bones() else NudBoneType.NoBones
        uv_type = mesh.uv_type if mesh.has_color() else NudUvType.Null

        br.write_uint32(buffers.polyClump.size())
        br.write_uint32(buffers.vertClump.size())
        br.write_uint32(buffers.vertAddClump.size() if bone_type else 0)

        br.write_uint16(len(mesh.vertices))

        # Write vertex size
        br.write_uint8(vertex_type | bone_type)

        # Write UV and vertex color format
        br.write_uint8((mesh.get_uv_channel_count() << 4) | uv_type)

        # Write materials
        tex_props = [0] * 4
        for i, material in enumerate(mesh.materials[:4]):
            tex_props[i] = buffers.materials.size() + 0x30 + \
                (mesh_groups_count * 0x30) + (mesh_count * 0x30)
            buffers.materials.write_struct(BrNudMaterial(), material, buffers)

        # Write material offsets
        for tex_prop in tex_props:
            br.write_uint32(tex_prop)

        # Write face count and format
        br.write_uint16((len(mesh.faces) * 4) - 1)

        # Unlike the usual 0x04 and 0x40 formats, CC2 NUDs only support strips (0x04) but this flag is always 0
        br.write_uint8(0)
        br.write_uint8(mesh.face_flag)

        # Padding
        br.write_uint32([0] * 3)

        # Write faces
        for face in mesh.faces[:-1]:
            buffers.polyClump.write_int16((face[2], face[0], face[1]))
            buffers.polyClump.write_int16(-1)

        # Write the last triangle (without the -1)
        buffers.polyClump.write_int16(
            (mesh.faces[-1][2], mesh.faces[-1][0], mesh.faces[-1][1]))

        # Write UV + vertices
        vertex_br = buffers.vertClump
        if bone_type != NudBoneType.NoBones:
            vertex_br = buffers.vertAddClump
            for vertex in mesh.vertices:
                if uv_type == NudUvType.Byte:
                    buffers.vertClump.write_uint8(vertex.color)
                elif uv_type == NudUvType.HalfFloat:
                    buffers.vertClump.write_half_float(
                        tuple(map(lambda x: x / 255, vertex.color)))

                for uv in vertex.uv:
                    buffers.vertClump.write_half_float(uv)

        for vertex in mesh.vertices:
            vertex_br.write_struct(BrNudVertex(), vertex,
                                   vertex_type, bone_type, uv_type)

        buffers.vertAddClump.align(4)


class NudVertexType(IntFlag):
    NoNormals = 0
    NormalsFloat = 1
    Unknown = 2
    NormalsTanBiTanFloat = 3
    NormalsHalfFloat = 6
    NormalsTanBiTanHalfFloat = 7


class NudBoneType(IntFlag):
    NoBones = 0
    Float = 0x10
    HalfFloat = 0x20
    Byte = 0x40


class NudUvType(IntFlag):
    Null = 0
    Byte = 2
    HalfFloat = 4


class BrNudVertex(BrStruct):
    def __br_read__(self, br: BinaryReader, vertexType, boneType, uvSize) -> None:
        self.position = br.read_float(3)
        self.normals = None
        self.biTangents = None
        self.tangents = None

        self.color = None
        self.uv = None

        self.boneIds = None
        self.boneWeights = None

        if vertexType == NudVertexType.NoNormals:
            br.read_float()
        elif vertexType == NudVertexType.NormalsFloat:
            br.read_float()
            self.normals = br.read_float(3)
            br.read_float()
        elif vertexType == NudVertexType.Unknown:
            self.normals = br.read_float(3)
            br.read_float()
            br.read_float(3)
            br.read_float(3)
            br.read_float(3)
        elif vertexType == NudVertexType.NormalsTanBiTanFloat:
            br.read_float()
            self.normals = br.read_float(3)
            br.read_float()
            self.biTangents = br.read_float(4)
            self.tangents = br.read_float(4)
        elif vertexType == NudVertexType.NormalsHalfFloat:
            self.normals = br.read_half_float(3)
            br.read_half_float()
        elif vertexType == NudVertexType.NormalsTanBiTanHalfFloat:
            self.normals = br.read_half_float(3)
            br.read_half_float()
            self.biTangents = br.read_half_float(4)
            self.tangents = br.read_half_float(4)
        else:
            raise Exception(f'Unsupported vertex type: {vertexType}')

        if boneType == NudBoneType.NoBones:
            if uvSize >= 18:
                self.color = br.read_uint8(4)

            self.uv = list()
            for _ in range(uvSize >> 4):
                self.uv.append(br.read_half_float(2))
        elif boneType == NudBoneType.Float:
            self.boneIds = br.read_uint32(4)
            self.boneWeights = br.read_float(4)
        elif boneType == NudBoneType.HalfFloat:
            self.boneIds = br.read_uint16(4)
            self.boneWeights = br.read_half_float(4)
        elif boneType == NudBoneType.Byte:
            self.boneIds = br.read_uint8(4)
            self.boneWeights = list(
                map(lambda x: float(x) / 255, br.read_uint8(4)))
        else:
            raise Exception(f'Unsupported bone type: {boneType}')

    def __br_write__(self, br: 'BinaryReader', vertex: 'NudVertex', vertexType: NudVertexType, boneType: NudBoneType, uvType: int):
        br.write_float(vertex.position)

        if vertexType == NudVertexType.NoNormals:
            br.write_float(1.0)
        elif vertexType == NudVertexType.NormalsFloat:
            br.write_float(1.0)
            br.write_float(vertex.normal)
            br.write_float(1.0)
        elif vertexType == NudVertexType.Unknown:
            br.write_float(vertex.normal)
            br.write_float(1.0)
            br.write_float([1] * 3)
            br.write_float([1] * 3)
            br.write_float([1] * 3)
        elif vertexType == NudVertexType.NormalsTanBiTanFloat:
            br.write_float(1.0)
            br.write_float(vertex.normal if vertex.normal else [0] * 3)
            br.write_float(1.0)
            br.write_float(vertex.bitangent[:3]
                           if vertex.bitangent else [0] * 3)
            br.write_float(0)
            br.write_float(vertex.tangent[:3] if vertex.tangent else [0] * 3)
            br.write_float(0)
        elif vertexType == NudVertexType.NormalsHalfFloat:
            br.write_half_float(vertex.normal)
            br.write_half_float(1.0)
        elif vertexType == NudVertexType.NormalsTanBiTanHalfFloat:
            br.write_half_float(vertex.normal)
            br.write_half_float(1.0)
            br.write_half_float(vertex.bitangent[:3])
            br.write_half_float(0)
            br.write_half_float(vertex.tangent[:3])
            br.write_half_float(0)
        else:
            raise Exception(f'Unsupported vertex type: {vertexType}')

        if boneType == NudBoneType.NoBones:
            if uvType:
                br.write_uint8(vertex.color)

            for uv in vertex.uv:
                br.write_half_float(uv)
        elif boneType == NudBoneType.Float:
            br.write_uint32(vertex.bone_ids)
            br.write_float(vertex.bone_weights)
        elif boneType == NudBoneType.HalfFloat:
            br.write_uint16(vertex.bone_ids)
            br.write_half_float(vertex.bone_weights)
        elif boneType == NudBoneType.Byte:
            br.write_uint8(vertex.bone_ids)
            br.write_float(
                tuple(map(lambda x: int(x * 255), vertex.bone_weights)))


class BrNudMaterial(BrStruct):
    def __br_read__(self, br: BinaryReader, mesh: BrNudMesh, nameStart: int) -> None:
        self.flags = br.read_uint32()
        br.read_uint32()

        self.sourceFactor = br.read_uint16()
        self.textureCount = br.read_uint16()
        self.destFactor = br.read_uint16()

        self.alphaTest = br.read_uint8()
        self.alphaFunction = br.read_uint8()

        self.refAlpha = br.read_uint16()
        self.cullMode = br.read_uint16()
        self.unk1 = br.read_float()  # Always 0 (?)
        self.unk2 = br.read_float()  # Usually 0, sometimes 1 (in Storm 1 eyes)
        self.zBufferOffset = br.read_int32()

        # Read texture proprties
        self.textures = br.read_struct(BrNudMaterialTexture, self.textureCount)

        # Read material properties
        self.properties: List[BrNudMaterialProperty] = list()
        while True:
            matAttPos = br.pos()
            prop = br.read_struct(BrNudMaterialProperty, None, nameStart)

            # if not (prop.valueCount == prop.nameStart == 0):
            self.properties.append(prop)

            if prop.matAttSize == 0:
                break

            br.seek(matAttPos + prop.matAttSize)

    def __br_write__(self, br: 'BinaryReader', material: 'NudMaterial', buffers: NudBuffers):
        br.write_uint32(material.flags)
        br.write_uint32(0)

        br.write_uint16(material.sourceFactor)
        br.write_uint16(len(material.textures))
        br.write_uint16(material.destFactor)

        br.write_uint8(material.alphaTest)
        br.write_uint8(material.alphaFunction)

        br.write_uint16(material.refAlpha)
        br.write_uint16(material.cullMode)
        br.write_float(material.unk1)
        br.write_float(material.unk2)
        br.write_int32(material.zBufferOffset)

        # Write texture properties
        for texture in material.textures:
            br.write_struct(BrNudMaterialTexture(), texture)

        # Write material properties
        if material.properties:
            for i, property in enumerate(material.properties):
                br.write_struct(BrNudMaterialProperty(), property,
                                buffers, i == (len(material.properties) - 1))
        else:
            br.write_uint32([0] * 4)  # One "empty" entry


class BrNudMaterialTexture(BrStruct):
    def __br_read__(self, br: BinaryReader) -> None:
        # This is not the hash, because that does not exist in CC2 NUDs.
        # Apparently, 0 makes it completely ignore the NUT texture, while -1 makes it use it
        self.unk0 = br.read_int32()
        br.read_uint32()

        br.read_uint16()
        self.mapMode = br.read_uint16()

        self.wrapModeS = br.read_uint8()
        self.wrapModeT = br.read_uint8()
        self.minFilter = br.read_uint8()
        self.magFilter = br.read_uint8()
        self.mipDetail = br.read_uint8()
        self.unk1 = br.read_uint8()

        br.read_uint32()
        self.unk2 = br.read_uint16()

    def __br_write__(self, br: 'BinaryReader', texture: 'NudMaterialTexture') -> None:
        br.write_int32(texture.unk0)
        br.write_uint32(0)

        br.write_uint16(0)
        br.write_uint16(texture.mapMode)

        br.write_uint8(texture.wrapModeS)
        br.write_uint8(texture.wrapModeT)
        br.write_uint8(texture.minFilter)
        br.write_uint8(texture.magFilter)
        br.write_uint8(texture.mipDetail)
        br.write_uint8(texture.unk1)

        br.write_uint32(0)
        br.write_uint16(texture.unk2)


class BrNudMaterialProperty(BrStruct):
    def __br_read__(self, br: BinaryReader, nameStart) -> None:
        self.matAttSize = br.read_uint32()
        self.nameStart = br.read_uint32()

        br.read_uint8(3)
        self.valueCount = br.read_uint8()
        br.read_uint32()

        # A material name should never be the first name, as the mesh group should have a name before it
        self.name = ''
        if self.nameStart != 0:
            with br.seek_to(nameStart + self.nameStart):
                self.name = br.read_str()

        self.values = list()
        if self.valueCount != 0:
            self.values = list(br.read_float(self.valueCount))
            self.values.extend([float()] * (4 - self.valueCount))

    def __br_write__(self, br: 'BinaryReader', property: 'NudMaterialProperty', buffers: NudBuffers, is_last):
        # Align the strings first
        buffers.names.align(0x10)

        br.write_uint32(0 if is_last else 0x10 +
                        (4 * len(property.values)))  # matAttSize
        br.write_uint32(buffers.names.size())  # nameStart

        buffers.names.write_str(property.name, True)

        br.write_uint8([0] * 3)
        br.write_uint8(len(property.values))
        br.write_uint32(0)

        # Write the values
        br.write_float(property.values)
