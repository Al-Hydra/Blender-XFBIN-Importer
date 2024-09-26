from enum import IntEnum
from typing import List, Optional, Union

from .br.br_anm import *


class AnmClumpChild:
    name: str
    chunk: 'NuccChunk'

    parent: 'AnmClumpChild'
    children: List['AnmClumpChild']

    anm_entry: 'AnmEntry'

    def __init__(self):
        self.name = ''
        self.type = ""
        self.chunk = None
        self.parent = None
        self.children = list()
        self.anm_entry = None


class AnmModel:
    name: str
    chunk: 'NuccChunk'


class AnmClump:
    bones: List[AnmClumpChild]
    models: List[AnmModel]

    def init_data(self, br_anm_clump: BrAnmClump, chunk_refs: List['ChunkReference'], initial_page_chunks: List['NuccChunk']):
        #if clump not in chunk_refs, then it's in initial_page_chunks
        is_ref = True
        if br_anm_clump.clump_index < len(chunk_refs):
            clump_ref = chunk_refs[br_anm_clump.clump_index]
        else:
            clump_ref = initial_page_chunks[br_anm_clump.clump_index]
            is_ref = False
        #print(f"{BrAnmClump.__name__} clump_ref: {clump_ref}")

        if is_ref:
            self.name = clump_ref.chunk.name

            self.chunk = clump_ref.chunk
        else:
            self.name = clump_ref.name
            self.chunk = clump_ref

        self.children = list()
        for child_ref in list(map(lambda x: chunk_refs[x], br_anm_clump.bones)):
            child = AnmClumpChild()
            child.name = child_ref.name
            child.type = child_ref.chunk.type
            child.chunk = child_ref.chunk
            self.children.append(child)

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
    bone: Optional[AnmClumpChild]

    def init_data(self, br_anm_entry: BrAnmEntry, frame_size: int, clumps: List[AnmClump], other_entry_chunks: List['NuccChunk']):
        if br_anm_entry.clump_index != -1:
            self.clump: AnmClump = clumps[br_anm_entry.clump_index]

            # Set up this entry's name and chunk, and set the bone's entry
            self.child = self.clump.children[br_anm_entry.bone_index]
            self.child.anm_entry = self
            self.name = self.child.name
            self.chunk = self.child.chunk
            self.type = self.child.type
        else:
            self.clump = None

            chunk = other_entry_chunks[br_anm_entry.bone_index]
            self.bone = None
            self.name = chunk.name
            self.chunk = chunk
            self.type = chunk.type

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

        elif curve_format == AnmCurveFormat.SHORT4 or curve_format == AnmCurveFormat.SHORT4ALT:
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
        
        elif curve_format == AnmCurveFormat.SHORT1ALT:
            curve.keyframes = list(map(lambda i, v: AnmKeyframe(frame_size * i, v),
                                       range(len(curve_values)), curve_values))
        
        elif curve_format == AnmCurveFormat.INT1_FLOAT1:
            curve.keyframes = list(map(lambda kv: AnmKeyframe(kv[0], kv[1:]), curve_values))

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
