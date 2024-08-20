from enum import IntEnum
from typing import List, Optional, Union

from .br.br_anm import *


class AnmBone:
    name: str
    chunk: 'NuccChunk'

    parent: 'AnmBone'
    children: List['AnmBone']

    anm_entry: 'AnmEntry'

    def __init__(self):
        self.name = ''
        self.chunk = None
        self.parent = None
        self.children = list()
        self.anm_entry = None


class AnmModel:
    name: str
    chunk: 'NuccChunk'


class AnmClump:
    bones: List[AnmBone]
    models: List[AnmModel]

    def init_data(self, br_anm_clump: BrAnmClump, chunk_refs: List['ChunkReference']):
        clump_ref = chunk_refs[br_anm_clump.clump_index]

        self.name = clump_ref.chunk.name
        self.chunk = clump_ref.chunk

        self.bones = list()
        for bone_ref in list(map(lambda x: chunk_refs[x], br_anm_clump.bones)):
            bone = AnmBone()
            bone.name = bone_ref.name
            bone.chunk = bone_ref.chunk
            self.bones.append(bone)

        self.models = list()
        for model_ref in list(map(lambda x: chunk_refs[x], br_anm_clump.models)):
            model = AnmModel()
            model.name = model_ref.name
            model.chunk = model_ref.chunk
            self.models.append(model)


class AnmKeyframe:
    frame: int
    value: Union[int, float]

    def __init__(self, frame, value):
        self.frame = frame
        self.value = value


class AnmDataPath(IntEnum):
    UNKNOWN = -1

    LOCATION = 0
    ROTATION = -2
    ROTATION_EULER = 1
    ROTATION_QUATERNION = 2
    SCALE = 3
    TOGGLED = 4

    # Proper name not yet decided
    CAMERA = 5


class AnmCurve:
    data_path: AnmDataPath
    keyframes: List[AnmKeyframe]


class AnmEntry:
    name: str
    chunk: 'NuccChunk'

    clump: Optional[AnmClump]
    bone: Optional[AnmBone]

    def init_data(self, br_anm_entry: BrAnmEntry, frame_size: int, clumps: List[AnmClump], other_entry_chunks: List['NuccChunk']):
        if br_anm_entry.clump_index != -1:
            self.clump: AnmClump = clumps[br_anm_entry.clump_index]

            # Set up this entry's name and chunk, and set the bone's entry
            self.bone = self.clump.bones[br_anm_entry.bone_index]
            self.bone.anm_entry = self
            self.name = self.bone.name
            self.chunk = self.bone.chunk
        else:
            self.clump = None

            chunk = other_entry_chunks[br_anm_entry.bone_index]
            self.bone = None
            self.name = chunk.name
            self.chunk = chunk

        self.entry_format = br_anm_entry.entry_format

        # Sort the curves based on curve index (might not actually be necessary)
        curves = sorted(zip(br_anm_entry.curve_headers, br_anm_entry.curves), key=lambda x: x[0].curve_index)

        self.curves = list()
        if self.entry_format == AnmEntryFormat.BONE:
            for i, cur in enumerate(('location', 'rotation', 'scale', 'toggled')):
                curve = create_anm_curve(AnmDataPath[cur.upper()], curves[i][0].curve_format,
                                         curves[i][1], frame_size) if i < len(curves) else None
                self.curves.append(curve)
                setattr(self, f'{cur}_curve', curve)

        elif self.entry_format == AnmEntryFormat.CAMERA:
            for i, cur in enumerate(('location', 'rotation', 'camera')):
                curve = create_anm_curve(AnmDataPath[cur.upper()], curves[i][0].curve_format,
                                         curves[i][1], frame_size) if i < len(curves) else None
                self.curves.append(curve)
                setattr(self, f'{cur}_curve', curve)

        else:
            self.curves = list(map(lambda c: create_anm_curve(
                AnmDataPath.UNKNOWN, c[0].curve_format, c[1], frame_size), curves))


def create_anm_curve(data_path: AnmDataPath, curve_format: AnmCurveFormat, curve_values, frame_size) -> AnmCurve:
    curve = AnmCurve()
    curve.data_path = data_path
    curve.keyframes = None

    if data_path == AnmDataPath.LOCATION:
        if AnmCurveFormat(curve_format).name.startswith('FLOAT3'):
            curve.keyframes = list(map(lambda i, v: AnmKeyframe(frame_size * i, v),
                                       range(len(curve_values)), curve_values))

        elif curve_format == AnmCurveFormat.INT1_FLOAT3:
            curve.keyframes = list(map(lambda kv: AnmKeyframe(kv[0], kv[1:]), curve_values))

    # Treat euler/quaternion as one, but set the correct data path according to the format
    if data_path == AnmDataPath.ROTATION:
        if AnmCurveFormat(curve_format).name.startswith('FLOAT3'):
            curve.data_path = AnmDataPath.ROTATION_EULER
            curve.keyframes = list(map(lambda i, v: AnmKeyframe(frame_size * i, v),
                                       range(len(curve_values)), curve_values))

        elif curve_format == AnmCurveFormat.INT1_FLOAT4:
            curve.data_path = AnmDataPath.ROTATION_QUATERNION
            curve.keyframes = list(map(lambda kv: AnmKeyframe(kv[0], kv[1:]), curve_values))

        elif curve_format == AnmCurveFormat.SHORT4:
            curve.data_path = AnmDataPath.ROTATION_QUATERNION
            curve.keyframes = list(map(lambda i, v: AnmKeyframe(
                frame_size * i, tuple(map(lambda x: x / 0x8000, v))), range(len(curve_values)), curve_values))

    elif data_path == AnmDataPath.SCALE:
        if AnmCurveFormat(curve_format).name.startswith('FLOAT3'):
            curve.keyframes = list(map(lambda i, v: AnmKeyframe(frame_size * i, v),
                                       range(len(curve_values)), curve_values))

        elif curve_format == AnmCurveFormat.INT1_FLOAT3:
            curve.keyframes = list(map(lambda kv: AnmKeyframe(kv[0], kv[1:]), curve_values))

        elif curve_format == AnmCurveFormat.SHORT3:
            curve.keyframes = list(map(lambda i, v: AnmKeyframe(
                frame_size * i, tuple(map(lambda x: x / 0x1000, v))), range(len(curve_values)), curve_values))

    elif data_path == AnmDataPath.TOGGLED:
        if curve_format == AnmCurveFormat.FLOAT1:
            curve.keyframes = list(map(lambda i, v: AnmKeyframe(frame_size * i, v),
                                       range(len(curve_values)), curve_values))

        elif curve_format == AnmCurveFormat.SHORT1:
            curve.keyframes = list(map(lambda i, v: AnmKeyframe(
                frame_size * i, tuple(map(lambda x: x / 0x8000, v))), range(len(curve_values)), curve_values))

    elif data_path == AnmDataPath.CAMERA:
        if curve_format == AnmCurveFormat.INT1_FLOAT1:
            curve.keyframes = list(map(lambda kv: AnmKeyframe(kv[0], kv[1:]), curve_values))

    elif data_path == AnmDataPath.UNKNOWN:
        curve.keyframes = list(map(lambda i, v: AnmKeyframe(frame_size * i, v), range(len(curve_values)), curve_values))

    if curve.keyframes is None:
        raise Exception(
            f'nuccChunkAnm: Unexpected curve format ({AnmCurveFormat(curve_format).name}) for curve with data path {AnmDataPath(data_path).name}')

    if len(curve.keyframes) and curve.keyframes[-1].frame == -1:
        # Remove the last keyframe (with frame -1) until we're sure of its usage
        curve.keyframes.pop()

    return curve
