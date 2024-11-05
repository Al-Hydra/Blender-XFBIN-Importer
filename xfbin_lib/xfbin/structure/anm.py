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

class AnmMaterial:
    name: str
    chunk: 'NuccChunk'

    anm_entry: 'AnmEntry'

    def __init__(self):
        self.name = ''
        self.chunk = None
        self.anm_entry = None


class AnmModel:
    name: str
    chunk: 'NuccChunk'


class AnmClump:
    bones: List[AnmBone]
    models: List[AnmModel]
    materials: List[AnmMaterial]
    children: List[AnmBone]

    def init_data(self, br_anm_clump: BrAnmClump, chunk_refs: List['ChunkReference']):
        clump_ref = chunk_refs[br_anm_clump.clump_index]

        self.name = clump_ref.chunk.name
        self.chunk = clump_ref.chunk

        self.bones: List[AnmBone] = list()
        self.materials: List[AnmMaterial] = list()
        self.children: List[AnmBone] = list()
        
        
        for bone_ref in list(map(lambda x: chunk_refs[x], br_anm_clump.bones)):
            if bone_ref.chunk.to_dict().get('Type') == 'nuccChunkMaterial':
                material = AnmMaterial()
                material.name = bone_ref.name
                material.chunk = bone_ref.chunk
                
                self.materials.append(material)
            
            else:
                bone = AnmBone()
                bone.name = bone_ref.name
                bone.chunk = bone_ref.chunk

                self.bones.append(bone)
            
            self.children.append(bone)
            
    
        self.models: List[AnmModel] = list()

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
    # Coord
    UNKNOWN = -1
    LOCATION = 0
    ROTATION = -2
    ROTATION_EULER = 1
    ROTATION_QUATERNION = 2
    SCALE = 3
    TOGGLED = 4

    # Material
    U1_LOCATION = 5
    V1_LOCATION = 6
    U1_SCALE = 7
    V1_SCALE = 8
    U2_LOCATION = 9
    V2_LOCATION = 10
    U2_SCALE = 11
    V2_SCALE = 12
    BLEND = 13
    GLARE = 14
    ALPHA = 15
    CELSHADE = 16

    # Camera
    CAMERA = 17 # Field of View

    # Light
    COLOR = 18
    ENERGY = 19
    RADIUS = 20 # Shadow Soft Size
    CUTOFF = 21 # Cutoff Distance

class AnmCurve:
    data_path: AnmDataPath
    keyframes: List[AnmKeyframe]


class AnmEntry:
    name: str
    chunk: 'NuccChunk'

    clump: Optional[AnmClump]
    bone: Optional[AnmBone]
    material: Optional[AnmMaterial]

    def init_data(self, br_anm_entry: BrAnmEntry, frame_size: int, clumps: List[AnmClump], other_entry_chunks: List['NuccChunk']):
        
        if br_anm_entry.entry_format == AnmEntryFormat.BONE:
            self.clump: AnmClump = clumps[br_anm_entry.clump_index]
            self.bone = self.clump.bones[br_anm_entry.bone_index]
            self.bone.anm_entry = self
            self.name = self.bone.name
            self.chunk = self.bone.chunk
        
        elif br_anm_entry.entry_format == AnmEntryFormat.MATERIAL:
            self.clump: AnmClump = clumps[br_anm_entry.clump_index]


            # Combine the bone and materials
            bone_materials = self.clump.bones + self.clump.materials


            self.material = bone_materials[br_anm_entry.bone_index]
            self.material.anm_entry = self
            self.name = self.material.name
            self.chunk = self.material.chunk
        
        elif br_anm_entry.clump_index == -1:

            self.clump = None

            chunk = other_entry_chunks[br_anm_entry.bone_index]
            self.bone = None
            self.name = chunk.name
            self.chunk = chunk


        self.entry_format = br_anm_entry.entry_format

        
    

        # Sort the curves based on curve index (might not actually be necessary)
        curves = sorted(zip(br_anm_entry.curve_headers, br_anm_entry.curves), key=lambda x: x[0].curve_index)

        self.curves = list()
        
        self.material_indices = {0: "U0_LocX", 1: "V0_LocY", 2: "U1_LocX", 3: "V1_LocY", 4: "U2_LocX", 5: "V2_LocY", 6: "U3_LocX", 7: "V3_LocY",
                                 8: "U0_ScaleX", 9: "V0_ScaleY", 10: "U1_ScaleX", 11: "V1_ScaleY", 12: "BlendRate1", 13: "BlendRate2", 14: "Falloff", 15: "Glare",
                                 16: "Alpha", 17: "OutlineID", 18: "U2_ScaleX", 19: "V2_ScaleY", 20: "U3_ScaleX", 21: "V3_ScaleY", 22: "unknown"}
        
        self.material_curves = {"U0_LocX": [],
                                "V0_LocY": [],
                                "U1_LocX": [],
                                "V1_LocY": [],
                                "U2_LocX": [],
                                "V2_LocY": [],
                                "U3_LocX": [],
                                "V3_LocY": [],
                                "U0_ScaleX": [],
                                "V0_ScaleY": [],
                                "U1_ScaleX": [],
                                "V1_ScaleY": [],
                                "BlendRate1": [],
                                "BlendRate2": [],
                                "Falloff": [],
                                "Glare": [],
                                "Alpha": [],
                                "OutlineID" : [],
                                "U2_ScaleX": [],
                                "V2_ScaleY": [],
                                "U3_ScaleX": [],
                                "V3_ScaleY": [],
                                "unknown": []}
        
        
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
        
        elif self.entry_format == AnmEntryFormat.LIGHTDIRC:
            for i, cur in enumerate(('color', 'energy', 'rotation')):
                curve = create_anm_curve(AnmDataPath[cur.upper()], curves[i][0].curve_format,
                                         curves[i][1], frame_size) if i < len(curves) else None
                self.curves.append(curve)
                setattr(self, f'{cur}_curve', curve)
        
        elif self.entry_format == AnmEntryFormat.LIGHTPOINT:
            for i, cur in enumerate(('color', 'energy', 'location', 'radius', 'cutoff')):
                curve = create_anm_curve(AnmDataPath[cur.upper()], curves[i][0].curve_format,
                                         curves[i][1], frame_size) if i < len(curves) else None
                self.curves.append(curve)
                setattr(self, f'{cur}_curve', curve)
        
        elif self.entry_format == AnmEntryFormat.AMBIENT:
            for i, cur in enumerate(('color', 'energy')):
                curve = create_anm_curve(AnmDataPath[cur.upper()], curves[i][0].curve_format,
                                         curves[i][1], frame_size) if i < len(curves) else None
                if curve and cur == 'color':
                    for kf in curve.keyframes:
                        # We need to add an alpha value of 1 to the color curve
                        color_value = list(kf.value) 
                        color_value.append(1.0)
                        kf.value = tuple(color_value)  
                self.curves.append(curve)
                setattr(self, f'{cur}_curve', curve)


        elif self.entry_format == AnmEntryFormat.MATERIAL:
            # We have to handle the material curve differently since we need to skip some curves
            material_curve_indices = (0, 1, 8, 9, 2, 3, 10, 11, 12, 14, 16, 4)

            for i, cur in enumerate(('u1_location', 'v1_location', 'u1_scale', 'v1_scale', 'u2_location', 'v2_location', 'u2_scale', 'v2_scale',
                                        'blend', 'glare', 'alpha', 'celshade')):
                curve = create_anm_curve(AnmDataPath[cur.upper()], curves[material_curve_indices[i]][0].curve_format,
                                        curves[material_curve_indices[i]][1], frame_size) if i < len(curves) else None
                self.curves.append(curve)
                setattr(self, f'{cur}_curve', curve)
            

        else:
            self.curves = list(map(lambda c: create_anm_curve(
                AnmDataPath.UNKNOWN, c[0].curve_format, c[1], frame_size), curves))
        

    


def create_anm_curve(data_path: AnmDataPath, curve_format: AnmCurveFormat, curve_values ,frame_size: int) -> AnmCurve:
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

        if AnmCurveFormat(curve_format).name.startswith('SHORT4'):
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
        elif curve_format == AnmCurveFormat.FLOAT1ALT:
            curve.keyframes = list(map(lambda i, v: AnmKeyframe(frame_size * i, v),
                                        range(len(curve_values)), curve_values))
        elif curve_format == AnmCurveFormat.INT1_FLOAT1:
            curve.keyframes = list(map(lambda kv: AnmKeyframe(kv[0], kv[1:]), curve_values))

        elif curve_format == AnmCurveFormat.SHORT1:
            curve.keyframes = list(map(lambda i, v: AnmKeyframe(
                frame_size * i, tuple(map(lambda x: x / 0x8000, v))), range(len(curve_values)), curve_values))
    

    elif data_path == AnmDataPath.U1_LOCATION:
        if curve_format == AnmCurveFormat.FLOAT1:
            curve.keyframes = list(map(lambda i, v: AnmKeyframe(frame_size * i, v),
                                       range(len(curve_values)), curve_values))
        elif curve_format == AnmCurveFormat.FLOAT1ALT:
            curve.keyframes = list(map(lambda i, v: AnmKeyframe(frame_size * i, v),
                                       range(len(curve_values)), curve_values))
        elif curve_format == AnmCurveFormat.FLOAT1ALT2:
            curve.keyframes = list(map(lambda i, v: AnmKeyframe(frame_size * i, v),
                                       range(len(curve_values)), curve_values))
            
        elif curve_format == AnmCurveFormat.INT1_FLOAT1:
            curve.keyframes = list(map(lambda kv: AnmKeyframe(kv[0], kv[1:]), curve_values))
            
    elif data_path == AnmDataPath.V1_LOCATION:
        if curve_format == AnmCurveFormat.FLOAT1:
            curve.keyframes = list(map(lambda i, v: AnmKeyframe(frame_size * i, v),
                                       range(len(curve_values)), curve_values))
        elif curve_format == AnmCurveFormat.FLOAT1ALT:
            curve.keyframes = list(map(lambda i, v: AnmKeyframe(frame_size * i, v),
                                       range(len(curve_values)), curve_values))
        
        elif curve_format == AnmCurveFormat.FLOAT1ALT2:
            curve.keyframes = list(map(lambda i, v: AnmKeyframe(frame_size * i, v),
                                        range(len(curve_values)), curve_values))
            
        elif curve_format == AnmCurveFormat.INT1_FLOAT1:
            curve.keyframes = list(map(lambda kv: AnmKeyframe(kv[0], kv[1:]), curve_values))
        
    elif data_path == AnmDataPath.U1_SCALE:
        if curve_format == AnmCurveFormat.FLOAT1:
            curve.keyframes = list(map(lambda i, v: AnmKeyframe(frame_size * i, v),
                                       range(len(curve_values)), curve_values))
        elif curve_format == AnmCurveFormat.FLOAT1ALT:
            curve.keyframes = list(map(lambda i, v: AnmKeyframe(frame_size * i, v),
                                       range(len(curve_values)), curve_values))
        elif curve_format == AnmCurveFormat.FLOAT1ALT2:
            curve.keyframes = list(map(lambda i, v: AnmKeyframe(frame_size * i, v),
                                       range(len(curve_values)), curve_values))
        elif curve_format == AnmCurveFormat.INT1_FLOAT1:
            curve.keyframes = list(map(lambda kv: AnmKeyframe(kv[0], kv[1:]), curve_values))
    
    elif data_path == AnmDataPath.V1_SCALE:
        if curve_format == AnmCurveFormat.FLOAT1:
            curve.keyframes = list(map(lambda i, v: AnmKeyframe(frame_size * i, v),
                                       range(len(curve_values)), curve_values))
        elif curve_format == AnmCurveFormat.FLOAT1ALT:
            curve.keyframes = list(map(lambda i, v: AnmKeyframe(frame_size * i, v),
                                       range(len(curve_values)), curve_values))
        elif curve_format == AnmCurveFormat.FLOAT1ALT2:
            curve.keyframes = list(map(lambda i, v: AnmKeyframe(frame_size * i, v),
                                       range(len(curve_values)), curve_values))
        elif curve_format == AnmCurveFormat.INT1_FLOAT1:
            curve.keyframes = list(map(lambda kv: AnmKeyframe(kv[0], kv[1:]), curve_values))
    
    elif data_path == AnmDataPath.U2_LOCATION:
        if curve_format == AnmCurveFormat.FLOAT1:
            curve.keyframes = list(map(lambda i, v: AnmKeyframe(frame_size * i, v),
                                       range(len(curve_values)), curve_values))
        elif curve_format == AnmCurveFormat.FLOAT1ALT:
            curve.keyframes = list(map(lambda i, v: AnmKeyframe(frame_size * i, v),
                                       range(len(curve_values)), curve_values))
        elif curve_format == AnmCurveFormat.FLOAT1ALT2:
            curve.keyframes = list(map(lambda i, v: AnmKeyframe(frame_size * i, v),
                                       range(len(curve_values)), curve_values))
        elif curve_format == AnmCurveFormat.INT1_FLOAT1:
            curve.keyframes = list(map(lambda kv: AnmKeyframe(kv[0], kv[1:]), curve_values))
    
    elif data_path == AnmDataPath.V2_LOCATION:
        if curve_format == AnmCurveFormat.FLOAT1:
            curve.keyframes = list(map(lambda i, v: AnmKeyframe(frame_size * i, v),
                                       range(len(curve_values)), curve_values))
        elif curve_format == AnmCurveFormat.FLOAT1ALT:
            curve.keyframes = list(map(lambda i, v: AnmKeyframe(frame_size * i, v),
                                       range(len(curve_values)), curve_values))
        elif curve_format == AnmCurveFormat.FLOAT1ALT2:
            curve.keyframes = list(map(lambda i, v: AnmKeyframe(frame_size * i, v),
                                       range(len(curve_values)), curve_values))
        elif curve_format == AnmCurveFormat.INT1_FLOAT1:
            curve.keyframes = list(map(lambda kv: AnmKeyframe(kv[0], kv[1:]), curve_values))
    
    elif data_path == AnmDataPath.U2_SCALE:
        if curve_format == AnmCurveFormat.FLOAT1:
            curve.keyframes = list(map(lambda i, v: AnmKeyframe(frame_size * i, v),
                                       range(len(curve_values)), curve_values))
        elif curve_format == AnmCurveFormat.FLOAT1ALT:
            curve.keyframes = list(map(lambda i, v: AnmKeyframe(frame_size * i, v),
                                       range(len(curve_values)), curve_values))
        elif curve_format == AnmCurveFormat.FLOAT1ALT2:
            curve.keyframes = list(map(lambda i, v: AnmKeyframe(frame_size * i, v),
                                       range(len(curve_values)), curve_values))
        elif curve_format == AnmCurveFormat.INT1_FLOAT1:
            curve.keyframes = list(map(lambda kv: AnmKeyframe(kv[0], kv[1:]), curve_values))
    
    elif data_path == AnmDataPath.V2_SCALE:
        if curve_format == AnmCurveFormat.FLOAT1:
            curve.keyframes = list(map(lambda i, v: AnmKeyframe(frame_size * i, v),
                                       range(len(curve_values)), curve_values))
        elif curve_format == AnmCurveFormat.FLOAT1ALT:
            curve.keyframes = list(map(lambda i, v: AnmKeyframe(frame_size * i, v),
                                       range(len(curve_values)), curve_values))
        elif curve_format == AnmCurveFormat.FLOAT1ALT2:
            curve.keyframes = list(map(lambda i, v: AnmKeyframe(frame_size * i, v),
                                       range(len(curve_values)), curve_values))
        elif curve_format == AnmCurveFormat.INT1_FLOAT1:
            curve.keyframes = list(map(lambda kv: AnmKeyframe(kv[0], kv[1:]), curve_values))
    
    elif data_path == AnmDataPath.BLEND:
        if curve_format == AnmCurveFormat.FLOAT1:
            curve.keyframes = list(map(lambda i, v: AnmKeyframe(frame_size * i, v),
                                       range(len(curve_values)), curve_values))
        elif curve_format == AnmCurveFormat.FLOAT1ALT:
            curve.keyframes = list(map(lambda i, v: AnmKeyframe(frame_size * i, v),
                                       range(len(curve_values)), curve_values))
        elif curve_format == AnmCurveFormat.FLOAT1ALT2:
            curve.keyframes = list(map(lambda i, v: AnmKeyframe(frame_size * i, v),
                                       range(len(curve_values)), curve_values))
        elif curve_format == AnmCurveFormat.INT1_FLOAT1:
            curve.keyframes = list(map(lambda kv: AnmKeyframe(kv[0], kv[1:]), curve_values))

    elif data_path == AnmDataPath.GLARE:
        if curve_format == AnmCurveFormat.FLOAT1:
            curve.keyframes = list(map(lambda i, v: AnmKeyframe(frame_size * i, v),
                                       range(len(curve_values)), curve_values))
        elif curve_format == AnmCurveFormat.FLOAT1ALT:
            curve.keyframes = list(map(lambda i, v: AnmKeyframe(frame_size * i, v),
                                       range(len(curve_values)), curve_values))
        elif curve_format == AnmCurveFormat.FLOAT1ALT2:
            curve.keyframes = list(map(lambda i, v: AnmKeyframe(frame_size * i, v),
                                       range(len(curve_values)), curve_values))
        elif curve_format == AnmCurveFormat.INT1_FLOAT1:
            curve.keyframes = list(map(lambda kv: AnmKeyframe(kv[0], kv[1:]), curve_values))
    
    elif data_path == AnmDataPath.ALPHA:
        if curve_format == AnmCurveFormat.FLOAT1:
            curve.keyframes = list(map(lambda i, v: AnmKeyframe(frame_size * i, v),
                                       range(len(curve_values)), curve_values))
        elif curve_format == AnmCurveFormat.FLOAT1ALT:
            curve.keyframes = list(map(lambda i, v: AnmKeyframe(frame_size * i, v),
                                       range(len(curve_values)), curve_values))
        elif curve_format == AnmCurveFormat.FLOAT1ALT2:
            curve.keyframes = list(map(lambda i, v: AnmKeyframe(frame_size * i, v),
                                       range(len(curve_values)), curve_values))
        elif curve_format == AnmCurveFormat.INT1_FLOAT1:
            curve.keyframes = list(map(lambda kv: AnmKeyframe(kv[0], kv[1:]), curve_values))
    
    elif data_path == AnmDataPath.CELSHADE:
        if curve_format == AnmCurveFormat.FLOAT1:
            curve.keyframes = list(map(lambda i, v: AnmKeyframe(frame_size * i, v),
                                       range(len(curve_values)), curve_values))
        elif curve_format == AnmCurveFormat.FLOAT1ALT:
            curve.keyframes = list(map(lambda i, v: AnmKeyframe(frame_size * i, v),
                                       range(len(curve_values)), curve_values))
        elif curve_format == AnmCurveFormat.FLOAT1ALT2:
            curve.keyframes = list(map(lambda i, v: AnmKeyframe(frame_size * i, v),
                                       range(len(curve_values)), curve_values))
        elif curve_format == AnmCurveFormat.INT1_FLOAT1:
            curve.keyframes = list(map(lambda kv: AnmKeyframe(kv[0], kv[1:]), curve_values))


    elif data_path == AnmDataPath.CAMERA:
        if curve_format == AnmCurveFormat.INT1_FLOAT1:
            curve.keyframes = list(map(lambda kv: AnmKeyframe(kv[0], kv[1:]), curve_values))

    elif data_path == AnmDataPath.COLOR:
        if curve_format == AnmCurveFormat.BYTE3:
            # in a tuple of 3 values for v, only divide the last 2 values by 255 but not the first value
            curve.keyframes = list(map(lambda i, v: AnmKeyframe(frame_size * i, tuple(map(lambda x: float(x) / 255.0, v))),
                                       range(len(curve_values)), curve_values))

    elif data_path == AnmDataPath.ENERGY:
        if curve_format == AnmCurveFormat.FLOAT1ALT:
            curve.keyframes = list(map(lambda i, v: AnmKeyframe(frame_size * i, v),
                                       range(len(curve_values)), curve_values))
            
    elif data_path == AnmDataPath.RADIUS:
        if curve_format == AnmCurveFormat.FLOAT1ALT:
            curve.keyframes = list(map(lambda i, v: AnmKeyframe(frame_size * i, v),
                                       range(len(curve_values)), curve_values))
            
    elif data_path == AnmDataPath.CUTOFF:
        if curve_format == AnmCurveFormat.FLOAT1ALT:
            curve.keyframes = list(map(lambda i, v: AnmKeyframe(frame_size * i, v),
                                       range(len(curve_values)), curve_values))

    elif data_path == AnmDataPath.UNKNOWN:
        curve.keyframes = list(map(lambda i, v: AnmKeyframe(frame_size * i, v), range(len(curve_values)), curve_values))

    if curve.keyframes is None:
        raise Exception(
            f'nuccChunkAnm: Unexpected curve format ({AnmCurveFormat(curve_format).name}) for curve with data path {AnmDataPath(data_path).name}')

    if len(curve.keyframes) and curve.keyframes[-1].frame == -1: # Remove the last keyframe
        curve.keyframes.pop()

    return curve