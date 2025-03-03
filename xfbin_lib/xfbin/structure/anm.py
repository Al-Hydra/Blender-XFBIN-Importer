from enum import IntEnum
from typing import List, Optional, Union

from .br.br_anm import *
import time

class AnmBone:
    name: str
    chunk: 'NuccChunk'

    parent: 'AnmBone'
    children: List['AnmBone']

    anm_entry: 'AnmEntry'

    def __init__(self):
        self.name = ''
        self.referenced_name = ''
        self.chunk = None
        self.parent = None
        self.children = list()
        self.curves = list()
class AnmMaterial:
    name: str
    chunk: 'NuccChunk'

    anm_entry: 'AnmEntry'

    def __init__(self):
        self.name = ''
        self.referenced_name = ''
        self.chunk = None
        self.curves = list()


class AnmModel:
    name: str
    referenced_name: str
    chunk: 'NuccChunk'
    


class AnmClump:
    bones: List[AnmBone]
    models: List[AnmModel]
    materials: List[AnmMaterial]
    children: List[AnmBone]

    def init_data(self, br_anm_clump: BrAnmClump, chunk_version, chunk_refs: List['ChunkReference'], initial_chunks):
        no_refs = False
        try:
            clump_ref = chunk_refs[br_anm_clump.clump_index]
        except:
            no_refs = True
        
        if no_refs:
            clump_ref = initial_chunks[br_anm_clump.clump_index]

            self.name = clump_ref.name
            self.referenced_name = clump_ref.name
            self.chunk = clump_ref

            self.bones: List[AnmBone] = list()
            self.materials: List[AnmMaterial] = list()
            self.children: List[AnmBone] = list()
            
            
            for bone_ref in list(map(lambda x: initial_chunks[x], br_anm_clump.bones)):
                if bone_ref.to_dict().get('Type') == 'nuccChunkMaterial':
                    material = AnmMaterial()
                    material.name = bone_ref.name
                    material.referenced_name = bone_ref.name
                    material.chunk = bone_ref
                    
                    
                    self.materials.append(material)
                
                else:
                    bone = AnmBone()
                    bone.name = bone_ref.name
                    bone.referenced_name = bone_ref.name
                    bone.chunk = bone_ref

                    self.bones.append(bone)
                
                self.children.append(bone_ref)
                
        
            self.models: List[AnmModel] = list()

            for model_ref in list(map(lambda x: initial_chunks[x], br_anm_clump.models)):
                model = AnmModel()
                model.name = model_ref.name
                model.referenced_name = model_ref.name
                model.chunk = model_ref
                self.models.append(model)
        
        else:
        
            clump_ref = chunk_refs[br_anm_clump.clump_index]

            self.name = clump_ref.chunk.name
            self.referenced_name = clump_ref.name
            self.chunk = clump_ref.chunk

            self.bones: List[AnmBone] = list()
            self.materials: List[AnmMaterial] = list()
            self.children: List[AnmBone] = list()
            
            
            for bone_ref in list(map(lambda x: chunk_refs[x], br_anm_clump.bones)):
                if bone_ref.chunk.to_dict().get('Type') == 'nuccChunkMaterial':
                    material = AnmMaterial()
                    material.name = bone_ref.chunk.name
                    material.referenced_name = bone_ref.name
                    material.chunk = bone_ref.chunk
                    
                    self.materials.append(material)
                
                else:
                    bone = AnmBone()
                    bone.name = bone_ref.chunk.name
                    bone.referenced_name = bone_ref.name
                    bone.chunk = bone_ref.chunk

                    self.bones.append(bone)
                
                self.children.append(bone_ref)
                
        
            self.models: List[AnmModel] = list()

            for model_ref in list(map(lambda x: chunk_refs[x], br_anm_clump.models)):
                model = AnmModel()
                model.name = model_ref.chunk.name
                model.referenced_name = model_ref.name
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
            clump_child = self.clump.children[br_anm_entry.bone_index]
            self.bone = self.clump.bones[br_anm_entry.bone_index]
            self.bone.anm_entry = self
            self.name = self.bone.name
            self.chunk = self.bone
        
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
        curves = list(zip(br_anm_entry.curve_headers, br_anm_entry.curves))

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
            self.bone.curves = self.curves = create_bone_curves(curves, frame_size)

                                     
        elif self.entry_format == AnmEntryFormat.CAMERA:
            self.curves = create_camera_curves(curves, frame_size)
        
        elif self.entry_format == AnmEntryFormat.LIGHTDIRC:
            self.curves = create_lightdirc_curves(curves, frame_size)
        
        elif self.entry_format == AnmEntryFormat.LIGHTPOINT:
            self.curves = create_lightpoint_curves(curves, frame_size)
        
        elif self.entry_format == AnmEntryFormat.AMBIENT:
            self.curves = create_ambient_curves(curves, frame_size)
        
        elif self.entry_format == AnmEntryFormat.MATERIAL:
            self.curves = create_material_curves(curves, frame_size)
            self.material.curves = self.curves
            

        else:
            print(f"Unknown entry format: {self.entry_format}")
            #self.curves = list()
        


def create_bone_curves(curves,frame_size):
    bone_curves = {0: "location",
                   1: "rotation_quaternion",
                   2: "scale",
                   3: "opacity",
                   11: "rotation_euler",}
    
    #this is done to differentiate between euler and quaternion curves
    
    eulers = {AnmCurveType.EULERXYZFIXED: 10, AnmCurveType.EULERINTERPOLATE: 10}
    
    curves_list = []

    for curve in curves:
        anm_curve = AnmCurve()
        anm_curve.data_path = bone_curves[curve[0].curve_index + eulers.get(curve[0].curve_format, 0)]
        anm_curve.keyframes = create_curve_keyframes(frame_size, curve[0], curve[1])
        
        curves_list.append(anm_curve)
    
    return curves_list

def create_camera_curves(curves,frame_size):
    camera_curves = {0: "location",
                     1: "rotation_quaternion",
                     2: "data.lens"}
    
    curves_list = []

    for curve in curves:
        anm_curve = AnmCurve()
        anm_curve.data_path = camera_curves[curve[0].curve_index]
        anm_curve.keyframes = create_curve_keyframes(frame_size, curve[0], curve[1])
        
        curves_list.append(anm_curve)
    
    return curves_list

def create_lightdirc_curves(curves,frame_size):
    lightdirc_curves = {0: "color",
                        1: "energy",
                        2: "rotation"}
    
    curves_list = []

    for curve in curves:
        anm_curve = AnmCurve()
        anm_curve.data_path = lightdirc_curves[curve[0].curve_index]
        anm_curve.keyframes = create_curve_keyframes(frame_size, curve[0], curve[1])
        
        curves_list.append(anm_curve)
    
    return curves_list

def create_lightpoint_curves(curves,frame_size):
    lightpoint_curves = {0: "color",
                         1: "energy",
                         2: "location",
                         3: "radius",
                         4: "cutoff"}
    
    curves_list = []

    for curve in curves:
        anm_curve = AnmCurve()
        anm_curve.data_path = lightpoint_curves[curve[0].curve_index]
        anm_curve.keyframes = create_curve_keyframes(frame_size, curve[0], curve[1])
        
        curves_list.append(anm_curve)
    
    return curves_list

def create_ambient_curves(curves,frame_size):
    ambient_curves = {0: "color",
                      1: "energy"}
    
    curves_list = []

    for curve in curves:
        anm_curve = AnmCurve()
        anm_curve.data_path = ambient_curves[curve[0].curve_index]
        anm_curve.keyframes = create_curve_keyframes(frame_size, curve[0], curve[1])
        
        curves_list.append(anm_curve)
    
    return curves_list

def create_material_curves(curves,frame_size):
    material_curves = {0: "U0_LocX",
                       1: "V0_LocY",
                       2: "U1_LocX",
                       3: "V1_LocY",
                       4: "U2_LocX",
                       5: "V2_LocY",
                       6: "U3_LocX",
                       7: "V3_LocY",
                       8: "U0_ScaleX",
                       9: "V0_ScaleY",
                       10: "U1_ScaleX",
                       11: "V1_ScaleY",
                       12: "BlendRate1",
                       13: "BlendRate2",
                       14: "Falloff",
                       15: "Glare",
                       16: "Alpha",
                       17: "OutlineID",
                       18: "U2_ScaleX",
                       19: "V2_ScaleY",
                       20: "U3_ScaleX",
                       21: "V3_ScaleY",
                       22: "unknown"}
    
    curves_list = []

    for curve in curves:
        anm_curve = AnmCurve()
        anm_curve.data_path = material_curves.get(curve[0].curve_index, "unknown")
        anm_curve.keyframes = create_curve_keyframes(frame_size, curve[0], curve[1])
        
        curves_list.append(anm_curve)
    
    return curves_list

def create_curve_keyframes(frame_size, curve, curve_frames):
    curve_to_convert = {AnmCurveType.VECTOR3FIXED: convert_vector3fixed,
                        AnmCurveType.VECTOR3LINEAR: convert_vector3linear,
                        AnmCurveType.VECTOR3BEZIER: convert_vector3bezier,
                        AnmCurveType.EULERXYZFIXED: convert_eulerxyzfixed,
                        AnmCurveType.EULERINTERPOLATE: convert_eulerinterpolate,
                        AnmCurveType.QUATERNIONLINEAR: convert_quaternionlinear,
                        AnmCurveType.FLOATFIXED: convert_floatfixed,
                        AnmCurveType.FLOATLINEAR: convert_floatlinear,
                        AnmCurveType.VECTOR2FIXED: convert_vector2fixed,
                        AnmCurveType.VECTOR2LINEAR: convert_vector2linear,
                        AnmCurveType.OPACITYI16TBL: convert_opacityi16tbl,
                        AnmCurveType.SCALEI16TBL: convert_scalei16tbl,
                        AnmCurveType.QUATERNIONI16TBL: convert_quaternioni16tbl,
                        AnmCurveType.COLORRGBTBL: convert_colorrgbtbl,
                        AnmCurveType.VECTOR3TBL: convert_vector3tbl,
                        AnmCurveType.FLOATTBLNI: convert_floattblni,
                        AnmCurveType.QUATERNIONTBL: convert_quaterniontbl,
                        AnmCurveType.FLOATTBL: convert_floattbl,
                        AnmCurveType.VECTOR3I16LINEAR: convert_vector3i16linear,
                        AnmCurveType.VECTOR3TBL_NOINTERP: convert_vector3tbl_nointerp,
                        AnmCurveType.QUATERNIONI16TBL_NOINTERP: convert_quaternioni16tbl_nointerp,
                        AnmCurveType.OPACITYI16TBL_NOINTERP: convert_opacityi16tbl_nointerp}
    
    keyframes = list(curve_to_convert[curve.curve_format](frame_size, curve.keyframe_count, curve_frames))
        
    return keyframes


def convert_vector3fixed(frame_size, keyframe_count, curve_frames):
    for i in range(keyframe_count):
        yield AnmKeyframe(frame_size * i, curve_frames[i])
    

def convert_vector3linear(frame_size, keyframe_count, curve_frames):
    for i in range(keyframe_count):
        yield AnmKeyframe(curve_frames[i][0], curve_frames[i][1:])

def convert_vector3bezier(frame_size, keyframe_count, curve_frames):
    for i in range(keyframe_count):
        yield AnmKeyframe(curve_frames[i][0], curve_frames[i][1:])

def convert_eulerxyzfixed(frame_size, keyframe_count, curve_frames):
    for i in range(keyframe_count):
        yield AnmKeyframe(frame_size * i, curve_frames[i])

def convert_eulerinterpolate(frame_size, keyframe_count, curve_frames):
    for i in range(keyframe_count):
        yield AnmKeyframe(curve_frames[i][0], curve_frames[i][1:])

def convert_quaternionlinear(frame_size, keyframe_count, curve_frames):
    for i in range(keyframe_count):
        yield AnmKeyframe(curve_frames[i][0], curve_frames[i][1:])

def convert_floatfixed(frame_size, keyframe_count, curve_frames):
    for i in range(keyframe_count):
        yield AnmKeyframe(frame_size * i, curve_frames[i])

def convert_floatlinear(frame_size, keyframe_count, curve_frames):
    for i in range(keyframe_count):
        yield AnmKeyframe(frame_size * i, curve_frames[i])

def convert_vector2fixed(frame_size, keyframe_count, curve_frames):
    for i in range(keyframe_count):
        yield AnmKeyframe(frame_size * i, curve_frames[i])

def convert_vector2linear(frame_size, keyframe_count, curve_frames):
    for i in range(keyframe_count):
        yield AnmKeyframe(i, curve_frames[i])

def convert_opacityi16tbl(frame_size, keyframe_count, curve_frames):
    for i in range(keyframe_count):
        yield AnmKeyframe(frame_size * i, list(map(lambda x: x / 0x8000, curve_frames[i])))

def convert_scalei16tbl(frame_size, keyframe_count, curve_frames):
    for i in range(keyframe_count):
        yield AnmKeyframe(frame_size * i, list(map(lambda x: x / 0x1000, curve_frames[i])))

def convert_quaternioni16tbl(frame_size, keyframe_count, curve_frames):
    for i in range(keyframe_count):
        yield AnmKeyframe(frame_size * i, list(map(lambda x: x / 0x8000, curve_frames[i])))

def convert_colorrgbtbl(frame_size, keyframe_count, curve_frames):
    for i in range(keyframe_count):
        yield AnmKeyframe(frame_size * i, list(map(lambda x: x / 0xff, curve_frames[i])))

def convert_vector3tbl(frame_size, keyframe_count, curve_frames):
    for i in range(keyframe_count):
        yield AnmKeyframe(frame_size * i, curve_frames[i])

def convert_floattblni(frame_size, keyframe_count, curve_frames):
    for i in range(keyframe_count):
        yield AnmKeyframe(frame_size * i, curve_frames[i])

def convert_quaterniontbl(frame_size, keyframe_count, curve_frames):
    for i in range(keyframe_count):
        yield AnmKeyframe(frame_size * i, curve_frames[i])

def convert_floattbl(frame_size, keyframe_count, curve_frames):
    for i in range(keyframe_count):
        yield AnmKeyframe(frame_size * i, curve_frames[i])

def convert_vector3i16linear(frame_size, keyframe_count, curve_frames):
    for i in range(keyframe_count):
        yield AnmKeyframe(curve_frames[i][0], list(map(lambda x: x / 0x8000, curve_frames[i][1:])))

def convert_vector3tbl_nointerp(frame_size, keyframe_count, curve_frames):
    for i in range(keyframe_count):
        yield AnmKeyframe(frame_size * i, curve_frames[i])

def convert_quaternioni16tbl_nointerp(frame_size, keyframe_count, curve_frames):
    for i in range(keyframe_count):
        yield AnmKeyframe(frame_size * i, list(map(lambda x: x / 0x8000, curve_frames[i])))

def convert_opacityi16tbl_nointerp(frame_size, keyframe_count, curve_frames):
    for i in range(keyframe_count):
        yield AnmKeyframe(frame_size * i, list(map(lambda x: x / 0x8000, curve_frames[i])))
        
