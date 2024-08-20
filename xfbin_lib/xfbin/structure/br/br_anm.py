from enum import IntEnum
from dataclasses import dataclass
from typing import List, Tuple, Dict, Union
from ...util import *

@dataclass
class BrAnmClump(BrStruct):
    def __br_read__(self, br: 'BinaryReader'):
        self.clump_index = br.read_uint32()

        self.bone_count = br.read_uint16()  # Including materials
        self.model_count = br.read_uint16()

        self.bones = br.read_uint32(self.bone_count)
        self.models = br.read_uint32(self.model_count)
    
    def __br_write__(self, br: 'BinaryReader'):
        br.write_uint32(self.clump_index)
        br.write_uint16(self.bone_count)
        br.write_uint16(self.model_count)

        for index in self.bones:
            br.write_uint32(index)
        
        for index in self.models:
            br.write_uint32(index)


class BrAnmCoordParent(BrStruct):
    def __br_read__(self, br: 'BinaryReader'):
        self.parent_clump_index = br.read_int16()
        self.parent_coord_index = br.read_uint16()

        self.child_clump_index = br.read_int16()
        self.child_coord_index = br.read_uint16()
    
    def __br_write__(self, br: 'BinaryReader'):
        br.write_int16(self.parent_clump_index)
        br.write_uint16(self.parent_coord_index)
        br.write_int16(self.child_clump_index)
        br.write_uint16(self.child_coord_index)


class AnmEntryFormat(IntEnum):
    BONE = 1
    CAMERA = 2
    MATERIAL = 4
    LIGHTDIRC = 5
    LIGHTPOINT = 6
    AMBIENT = 8


class AnmCurveFormat(IntEnum):
    FLOAT3 = 0x05  # location/scale
    INT1_FLOAT3 = 0x06  # location/scale (with keyframe)
    FLOAT3ALT = 0x08  # rotation
    INT1_FLOAT4 = 0x0A  # rotation quaternions (with keyframe)
    FLOAT1 = 0x0B  # "toggled"
    INT1_FLOAT1 = 0x0C  # camera / toggled
    SHORT1 = 0x0F  # "toggled"
    SHORT3 = 0x10  # scale
    SHORT4 = 0x11  # rotation quaternions
    BYTE3 = 0x14  # lightdirc
    FLOAT3ALT2 = 0x15  # scale
    FLOAT1ALT = 0x16  # lightdirc
    FLOAT1ALT2 = 0x18  # material
    SHORT1ALT = 29  # "toggled"


class BrAnmCurveHeader(BrStruct):
    def __br_read__(self, br: 'BinaryReader'):
        self.curve_index = br.read_uint16()  # Might be used for determining the order of curves
        self.curve_format = br.read_uint16()
        self.keyframe_count = br.read_uint16()
        self.curve_flags = br.read_int16()

    def __br_write__(self, br: 'BinaryReader'):
        br.write_uint16(self.curve_index)
        br.write_uint16(self.curve_format)
        br.write_uint16(self.keyframe_count)
        br.write_int16(self.curve_flags)


@dataclass
class Curve(BrStruct):
	curve_format: AnmCurveFormat
	keyframes: Union[Tuple[int], Tuple[float], Dict[int, float]]
	
	def __br_write__(self, anm_writer: 'BinaryReader'):
		if self.curve_format == AnmCurveFormat.INT1_FLOAT3 or self.curve_format == AnmCurveFormat.INT1_FLOAT1 or self.curve_format == AnmCurveFormat.INT1_FLOAT4:
			for frame, value in self.keyframes.items():
				anm_writer.write_int32(frame)
				anm_writer.write_float(value)
		
		if self.curve_format == AnmCurveFormat.SHORT4 or self.curve_format == AnmCurveFormat.SHORT3 or self.curve_format == AnmCurveFormat.SHORT1:
			for value in self.keyframes:
				anm_writer.write_int16(value)
		
		if self.curve_format == AnmCurveFormat.FLOAT3 or self.curve_format == AnmCurveFormat.FLOAT3ALT or self.curve_format == AnmCurveFormat.FLOAT1 or self.curve_format == AnmCurveFormat.FLOAT1ALT:
			for value in self.keyframes:
				anm_writer.write_float(value)
				
		if self.curve_format == AnmCurveFormat.BYTE3:
			for value in self.keyframes:
				anm_writer.write_uint8(int(value))


class BrAnmEntry(BrStruct):
    def __br_read__(self, br: 'BinaryReader'):
        self.clump_index = br.read_int16()
        self.bone_index = br.read_uint16()

        self.entry_format = br.read_uint16()
        self.curve_count = br.read_uint16()

        self.curve_headers = br.read_struct(BrAnmCurveHeader, self.curve_count)

        self.curves = list()
        for header in self.curve_headers:
            # Some mini optimizations
            curve = [None] * header.keyframe_count

            # More mini optimizations that make the code a lot less readable
            if header.curve_format == AnmCurveFormat.FLOAT3:  # 0x05
                for i in range(header.keyframe_count):
                    curve[i] = br.read_float(3)

            elif header.curve_format == AnmCurveFormat.INT1_FLOAT3:  # 0x06
                for i in range(header.keyframe_count):
                    curve[i] = (br.read_int32(), *br.read_float(3))

            elif header.curve_format == AnmCurveFormat.FLOAT3ALT:  # 0x08
                for i in range(header.keyframe_count):
                    curve[i] = br.read_float(3)

            elif header.curve_format == AnmCurveFormat.INT1_FLOAT4:  # 0x0A
                for i in range(header.keyframe_count):
                    curve[i] = (br.read_int32(), *br.read_float(4))

            elif header.curve_format == AnmCurveFormat.FLOAT1:  # 0x0B
                for i in range(header.keyframe_count):
                    curve[i] = br.read_float(1)

            elif header.curve_format == AnmCurveFormat.INT1_FLOAT1:  # 0x0C
                for i in range(header.keyframe_count):
                    curve[i] = (br.read_int32(), br.read_float())

            elif header.curve_format == AnmCurveFormat.SHORT1:  # 0x0F
                for i in range(header.keyframe_count):
                    curve[i] = br.read_int16(1)

            elif header.curve_format == AnmCurveFormat.SHORT3:  # 0x10
                for i in range(header.keyframe_count):
                    curve[i] = br.read_int16(3)

            elif header.curve_format == AnmCurveFormat.SHORT4:  # 0x11
                for i in range(header.keyframe_count):
                    curve[i] = br.read_int16(4)

            elif header.curve_format == AnmCurveFormat.BYTE3:  # 0x14
                for i in range(header.keyframe_count):
                    curve[i] = br.read_int8(3)

            elif header.curve_format == AnmCurveFormat.FLOAT3ALT2:  # 0x15
                for i in range(header.keyframe_count):
                    curve[i] = br.read_float(3)

            elif header.curve_format == AnmCurveFormat.FLOAT1ALT:  # 0x16
                for i in range(header.keyframe_count):
                    curve[i] = br.read_float(1)

            elif header.curve_format == AnmCurveFormat.FLOAT1ALT2:  # 0x18
                for i in range(header.keyframe_count):
                    curve[i] = br.read_float(1)

            else:
                print(f'NuccChunkAnm: Unsupported curve format {header.curve_format}')

            br.align_pos(4)

            self.curves.append(curve)
    
    def __br_write__(self, br: 'BinaryReader'):
        br.write_int16(self.clump_index)
        br.write_uint16(self.bone_index)
        br.write_uint16(self.entry_format)
        br.write_uint16(self.curve_count)

        for header in self.curve_headers:
            br.write_struct(header)
        
        for curve in self.curves:
            br.write_struct(curve)
        

'''
anm_writer = BinaryReader(endianness=Endian.BIG, encoding='utf-8')  # Create a new BinaryReader (bytearray buffer is initialized automatically)


"""class AnmDataPath(IntEnum):
	UNKNOWN = -1

	LOCATION = 6
	LOCATION_NOKEY = 8
	ROTATION = -2
	ROTATION_EULER = 1
	ROTATION_QUATERNION = 17
	SCALE = 5
	TOGGLED = 11

	# Proper name not yet decided
	CAMERA = 10"""


@dataclass
class Anm(BrStruct):
	anm_length: int
	frame_size: int
	entry_count: int
	loop: bool
	clump_count: int
	other_entry_count: int
	coord_count: int

	clumps: List[Clump]
	coord_parents: CoordParent
	entries: List[Entry]

	def __br_write__(self, anm_writer: 'BinaryReader'):
		anm_writer.write_uint32(self.anm_length * 100)
		anm_writer.write_uint32(self.frame_size * 100)
		anm_writer.write_uint16(self.entry_count)
		anm_writer.write_uint16(int(self.loop))
		anm_writer.write_uint16(self.clump_count)
		anm_writer.write_uint16(self.other_entry_count)
		anm_writer.write_uint32(self.coord_count)

		for clump in self.clumps:
			anm_writer.write_struct(clump)
		if self.other_entry_count > 0:
			g = 0
			for other_index in range(0,self.other_entry_count):
				g += 1
				anm_writer.write_uint32(g)
		anm_writer.write_struct(self.coord_parents)

		for entry in self.entries:
			anm_writer.write_struct(entry)

'''