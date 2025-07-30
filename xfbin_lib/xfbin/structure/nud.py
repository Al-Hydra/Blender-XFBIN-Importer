from itertools import chain
from typing import List, Tuple

from .br.br_nud import *
import numpy as np

class Nud:
    name: str  # chunk name
    mesh_groups: List['NudMeshGroup']

    def init_data(self, name, br_nud: BrNud):
        self.name = name
        self.bounding_sphere = br_nud.boundingSphere

        self.mesh_groups = list()
        for br_mesh_group in br_nud.meshGroups:
            mesh_group = NudMeshGroup()
            mesh_group.init_data(br_mesh_group)
            self.mesh_groups.append(mesh_group)

    def get_bone_range(self) -> Tuple[int, int]:
        if not (self.mesh_groups and
                self.mesh_groups[0].meshes and
                self.mesh_groups[0].meshes[0].bone_type != NudBoneType.NoBones):
            return (0, 0)

        lower = 0xFF_FF
        higher = 0
        for mesh in [m for m in self.mesh_groups[0].meshes if m.vertices is not None and m.vertices.size > 0 and 'bone_ids' in m.vertices.dtype.names]:
            bone_ids = mesh.vertices['bone_ids']
            if bone_ids.size > 0:
                mesh_min = np.min(bone_ids)
                mesh_max = np.max(bone_ids)
                lower = min(lower, mesh_min)
                higher = max(higher, mesh_max)

        if lower > higher:
            return (0, 0)

        return (lower, higher)


class NudMeshGroup:
    name: str
    meshes: List['NudMesh']

    def init_data(self, br_mesh_group: BrNudMeshGroup):
        self.name = br_mesh_group.name
        self.bone_flags = br_mesh_group.boneFlags
        self.bounding_sphere = br_mesh_group.boundingSphere
        self.unk_values = br_mesh_group.unkValues

        self.meshes = list()
        for br_mesh in br_mesh_group.meshes:
            mesh = NudMesh()
            mesh.init_data(br_mesh)
            self.meshes.append(mesh)


class NudMesh:
    MAX_VERTICES = 32_767
    MAX_FACES = 16_383

    vertices: List['NudVertex']
    faces: List[Tuple[int, int, int]]
    materials: List['NudMaterial']

    vertex_type: NudVertexType
    bone_type: NudBoneType
    uv_type: NudUvType

    def init_data(self, br_mesh: BrNudMesh):
        self.add_vertices(br_mesh.vertices)
        self.add_faces(br_mesh.faces, br_mesh.faceSize)
        self.add_materials(br_mesh.materials)

        self.vertex_type = NudVertexType(br_mesh.vertexSize & 0x0F)
        self.bone_type = NudBoneType(br_mesh.vertexSize & 0xF0)
        self.uv_type = NudUvType(br_mesh.uvSize & 0x0F)
        self.face_flag = br_mesh.faceFlag

    def has_bones(self):
        #check if the numpy array has bone ids
        return self.vertices is not None and self.vertices.size > 0 and self.vertices["bone_ids"].any()

    def has_color(self):
        return self.vertices is not None and self.vertices.size > 0 and self.vertices["color"].any()

    def get_uv_channel_count(self):
        count = 0
        for i in range(4):
            field_name = f"uv{i}"
            if field_name in self.vertices.dtype.names:
                if np.any(self.vertices[field_name]):
                    count += 1
        return count

    def add_vertices(self, vertices: List[BrNudVertex]):
        self.vertices = list()
        for br_vertex in vertices:
            vertex = NudVertex()
            vertex.init_data(br_vertex)
            self.vertices.append(vertex)

    def add_faces(self, faces: List[int], faceSize: int):
        faces = iter(faces)

        if faceSize & 0x40:
            # 0x40 format does not have -1 indices nor changing directions
            self.faces = zip(faces, faces, faces)
            return

        self.faces = list()

        start_dir = 1
        f1 = next(faces)
        f2 = next(faces)
        face_dir = start_dir

        try:
            while True:
                f3 = next(faces)

                if f3 == -1:
                    f1 = next(faces)
                    f2 = next(faces)
                    face_dir = start_dir
                else:
                    face_dir = -face_dir

                    if f1 != f2 != f3:
                        if face_dir > 0:
                            self.faces.append((f3, f2, f1))
                        else:
                            self.faces.append((f2, f3, f1))
                    f1 = f2
                    f2 = f3
        except StopIteration:
            pass

    def add_materials(self, materials: List[BrNudMaterial]):
        self.materials = list()

        for br_material in materials:
            material = NudMaterial()
            material.init_data(br_material)
            self.materials.append(material)


class NudVertex:
    __slots__ = (
        "position", "normal", "bitangent", "tangent",
        "color", "uv", "bone_ids", "bone_weights"
    )

    def init_data(self, br_vertex: BrNudVertex):
        self.position = br_vertex.position
        self.normal = br_vertex.normals
        self.bitangent = br_vertex.biTangents if br_vertex.biTangents else None
        self.tangent = br_vertex.tangents if br_vertex.tangents else None

        self.color = tuple(map(lambda x: int(x), br_vertex.color)
                           ) if br_vertex.color else None
        self.uv = br_vertex.uv

        self.bone_ids = br_vertex.boneIds
        self.bone_weights = br_vertex.boneWeights

    def __eq__(self, other: 'NudVertex') -> bool:
        return (
            self.position == other.position and
            self.normal == other.normal and
            self.bitangent == other.bitangent and
            self.tangent == other.tangent and
            self.color == other.color and
            self.uv == other.uv and
            self.bone_ids == other.bone_ids and
            self.bone_weights == other.bone_weights
        )

    def __hash__(self) -> int:
        return hash((
            tuple(self.position),
            tuple(self.normal),
            tuple(self.bitangent),
            tuple(self.tangent),
            tuple(self.color),
            tuple(self.uv),  # assume self.uv is already a tuple of tuples
            tuple(self.bone_ids),
            tuple(self.bone_weights),
        ))


class NudMaterial:
    def init_data(self, material: BrNudMaterial):
        self.flags = material.flags

        self.sourceFactor = material.sourceFactor
        self.destFactor = material.destFactor

        self.alphaTest = material.alphaTest
        self.alphaFunction = material.alphaFunction

        self.refAlpha = material.refAlpha
        self.cullMode = material.cullMode
        self.unk1 = material.unk1
        self.unk2 = material.unk2

        self.zBufferOffset = material.zBufferOffset

        self.textures = list()
        for br_texture in material.textures:
            texture = NudMaterialTexture()
            texture.init_data(br_texture)
            self.textures.append(texture)

        self.properties = list()
        for br_property in [p for p in material.properties if p.name]:
            property = NudMaterialProperty()
            property.init_data(br_property)
            self.properties.append(property)


class NudMaterialTexture:
    def init_data(self, texture: BrNudMaterialTexture):
        self.baseID = texture.baseID
        self.groupID = texture.groupID
        self.subGroupID = texture.subGroupID
        self.textureID = texture.textureID
        self.mapMode = texture.mapMode

        self.wrapModeS = texture.wrapModeS
        self.wrapModeT = texture.wrapModeT
        self.minFilter = texture.minFilter
        self.magFilter = texture.magFilter
        self.mipDetail = texture.mipDetail
        self.unk1 = texture.unk1
        self.LOD = texture.LOD


class NudMaterialProperty:
    def init_data(self, property: BrNudMaterialProperty):
        self.name = property.name
        self.values: List[float] = property.values
