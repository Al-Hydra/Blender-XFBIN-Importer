from ...util import *
from enum import IntEnum
from .br_anm import *
class BrStrmClump(BrStruct):
    def __br_read__(self, br: 'BinaryReader'):
        self.ClumpIndex = br.read_uint32()
        self.BoneMaterialCount = br.read_uint16()
        self.ModelCount = br.read_uint16()
        self.BoneMaterialIndices = br.read_uint32(self.BoneMaterialCount)
        self.ModelIndices = br.read_uint32(self.ModelCount)
        self.Unk = br.read_uint32(self.ModelCount)


class BrStrmFrameInfo(BrStruct):
    def __br_read__(self, br: 'BinaryReader'):
        self.Offset = br.read_uint32() 
        self.Frame = br.read_uint32()


class AnmStrmCurveType(IntEnum):
    CAMERA = 0x07
    BONE = 0x0F
    MATERIAL = 0xFFFF


class BrStrmEntry(BrStruct):
    def __br_read__(self, br: 'BinaryReader'):
        
        self.ClumpIndex = br.read_int16()
        self.BoneIndex = br.read_int16()
        self.EntryType = br.read_uint16()
        self.EntryLength = br.read_uint16()
        
        if self.EntryType == AnmEntryFormat.BONE:
            self.Entry = br.read_struct(BrStrmEntryBone)
        
        elif self.EntryType == AnmEntryFormat.CAMERA:
            self.Entry = br.read_struct(BrStrmEntryCamera)
        
        elif self.EntryType == AnmEntryFormat.MATERIAL:
            self.Entry = br.read_struct(BrStrmEntryMaterial)

        elif self.EntryType == AnmEntryFormat.LIGHTDIRC:
            self.Entry = br.read_struct(BrStrmEntryLightDirc)
        
        elif self.EntryType == AnmEntryFormat.LIGHTPOINT:
            self.Entry = br.read_struct(BrStrmEntryLightPoint)
        
        elif self.EntryType == AnmEntryFormat.AMBIENT:
            self.Entry = br.read_struct(BrStrmEntryAmbient)

        else:
            print(f'Unknown entry type: {self.EntryType}')
            self.EntryData = br.read_bytes(self.EntryLength)                


class BrStrmEntryBone(BrStruct):
    def __br_read__(self, br: 'BinaryReader'):
        self.CurveType = br.read_uint32()
        self.Position = br.read_float(3)
        self.Rotation = br.read_float(4)
        self.Scale = br.read_float(3)
        self.Opacity = br.read_float() #Needs to be checked


class BrStrmEntryCamera(BrStruct):
    def __br_read__(self, br: 'BinaryReader'):
        self.CurveType = br.read_uint32()
        self.Position = br.read_float(3)
        self.Rotation = br.read_float(4)
        self.CameraFOV = br.read_float()
        self.Scale = br.read_float(3)


class BrStrmEntryMaterial(BrStruct):
    def __br_read__(self, br: 'BinaryReader'):
        self.CurveType = br.read_uint32()
        self.AmbientColor = br.read_float(16)


class BrStrmEntryLightDirc(BrStruct):
    def __br_read__(self, br):
        self.CurveType = br.read_uint32()
        self.LightColor = br.read_float(3)
        self.LightIntensity = br.read_float()
        self.LightDirection = br.read_float(4)


class BrStrmEntryLightPoint(BrStruct):
    def __br_read__(self, br: 'BinaryReader'):
        self.CurveType = br.read_uint32()
        self.LightColor = br.read_float(3)
        self.LightPosition = br.read_float(3)
        self.LightIntensity = br.read_float()
        self.LightRange = br.read_float()
        self.LightFalloff = br.read_float()

class BrStrmEntryAmbient(BrStruct):
    def __br_read__(self, br: 'BinaryReader'):
        self.CurveType = br.read_uint32()
        self.AmbientColor = br.read_float(4)

