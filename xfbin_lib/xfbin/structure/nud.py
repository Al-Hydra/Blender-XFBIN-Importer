from itertools import chain
from typing import List, Tuple

from .br.br_nud import *


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
        for mesh in [m for m in self.mesh_groups[0].meshes if m.vertices and m.vertices[0].bone_ids]:
            lower = min(lower, min(
                chain(*map(lambda x: x.bone_ids, mesh.vertices))))
            higher = max(higher, max(
                chain(*map(lambda x: x.bone_ids, mesh.vertices))))

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
        return bool(self.vertices and self.vertices[0].bone_ids)

    def has_color(self):
        return bool(self.vertices and self.vertices[0].color)

    def get_uv_channel_count(self):
        return len(self.vertices[0].uv) if bool(self.vertices and self.vertices[0].uv) else 0

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
    position: Tuple[float, float, float]
    normal: Tuple[float, float, float]
    bitangent: Tuple[float, float, float]
    tangent: Tuple[float, float, float]

    color: Tuple[int, int, int, int]
    uv: List[Tuple[float, float]]

    bone_ids: Tuple[int, int, int, int]
    bone_weights: Tuple[float, float, float, float]

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

    def __eq__(self, o: 'NudVertex') -> bool:
        return all(map(lambda x, y: x == y, self.position, o.position)) \
            and all(map(lambda x, y: x == y, self.normal, o.normal)) \
            and all(map(lambda x, y: all(map(lambda a, b: a == b, x, y)), self.uv, o.uv)) \
            and all(map(lambda x, y: x == y, self.tangent, o.tangent)) \
            and all(map(lambda x, y: x == y, self.bitangent, o.bitangent)) \
            and all(map(lambda x, y: x == y, self.color, o.color)) \
            and all(map(lambda x, y: x == y, self.bone_ids, o.bone_ids)) \
            and all(map(lambda x, y: x == y, self.bone_weights, o.bone_weights))

    def __hash__(self) -> int:
        return hash(tuple(self.position)) ^ hash(tuple(self.normal)) ^ hash(tuple(self.color)) ^ hash(tuple(self.uv))


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
        self.unk0 = texture.unk0
        self.mapMode = texture.mapMode

        self.wrapModeS = texture.wrapModeS
        self.wrapModeT = texture.wrapModeT
        self.minFilter = texture.minFilter
        self.magFilter = texture.magFilter
        self.mipDetail = texture.mipDetail
        self.unk1 = texture.unk1
        self.unk2 = texture.unk2


class NudMaterialProperty:
    def init_data(self, property: BrNudMaterialProperty):
        self.name = property.name
        self.values: List[float] = property.values
