from enum import IntEnum

from ...util import *


class BrAnmClump(BrStruct):
    def __br_read__(self, br: 'BinaryReader'):
        self.clump_index = br.read_uint32()

        self.bone_count = br.read_uint16()  # Including materials
        self.model_count = br.read_uint16()

        self.bones = br.read_uint32(self.bone_count)
        self.models = br.read_uint32(self.model_count)


class BrAnmCoordParent(BrStruct):
    def __br_read__(self, br: 'BinaryReader'):
        self.parent_clump_index = br.read_int16()
        self.parent_coord_index = br.read_uint16()

        self.child_clump_index = br.read_int16()
        self.child_coord_index = br.read_uint16()


class AnmEntryFormat(IntEnum):
    BONE = 1
    CAMERA = 2
    MATERIAL = 4
    LIGHTDIRC = 5
    LIGHTPOINT = 6
    AMBIENT = 8
    MORPH = 9


class AnmCurveFormat(IntEnum):
    FLOAT3 = 0x05  # vector3 no interpolation
    INT1_FLOAT3 = 0x06  # vector3 linear interpolation
    INT1_FLOAT3BEZIER = 0x07  # vector3 bezier interpolation
    FLOAT3ALT = 0x08  # rotation EULER no interpolation
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
    FLOAT3ALT3 = 0x1A # location no interp
    SHORT4ALT = 0x1B # rotation quaternions no interp


class AnmCurveType(IntEnum):
    VECTOR3FIXED = 5
    VECTOR3LINEAR = 6
    VECTOR3BEZIER = 7
    EULERXYZFIXED = 8
    EULERINTERPOLATE = 9
    QUATERNIONLINEAR = 10
    FLOATFIXED = 11
    FLOATLINEAR = 12
    VECTOR2FIXED = 13
    VECTOR2LINEAR = 14
    OPACITYI16TBL = 15
    SCALEI16TBL = 16
    QUATERNIONI16TBL = 17
    COLORRGBTBL = 20
    VECTOR3TBL = 21
    FLOATTBLNI = 22
    QUATERNIONTBL = 23
    FLOATTBL = 24
    VECTOR3I16LINEAR = 25
    VECTOR3TBL_NOINTERP = 26
    QUATERNIONI16TBL_NOINTERP = 27
    OPACITYI16TBL_NOINTERP = 29



class BrAnmCurveHeader(BrStruct):
    def __br_read__(self, br: 'BinaryReader'):
        self.curve_index = br.read_uint16()  # Might be used for determining the order of curves
        self.curve_format = br.read_uint16()
        self.keyframe_count = br.read_uint16()
        self.curve_flags = br.read_int16()

class BrAnmEntry(BrStruct):
    def __br_read__(self, br: 'BinaryReader'):
        self.clump_index = br.read_int16()
        self.bone_index = br.read_uint16()

        self.entry_format = br.read_uint16()
        self.curve_count = br.read_uint16()

        self.curve_headers = br.read_struct(BrAnmCurveHeader, self.curve_count)

        self.curves = list()

        curve_readers = {
            AnmCurveType.VECTOR3FIXED: self.read_vector3fixed,
            AnmCurveType.VECTOR3LINEAR: self.read_vector3linear,
            AnmCurveType.VECTOR3BEZIER: self.read_vector3bezier,
            AnmCurveType.EULERXYZFIXED: self.read_eulerxyzfixed,
            AnmCurveType.EULERINTERPOLATE: self.read_eulerinterpolate,
            AnmCurveType.QUATERNIONLINEAR: self.read_quaternionlinear,
            AnmCurveType.FLOATFIXED: self.read_floatfixed,
            AnmCurveType.FLOATLINEAR: self.read_floatlinear,
            AnmCurveType.VECTOR2FIXED: self.read_vector2fixed,
            AnmCurveType.VECTOR2LINEAR: self.read_vector2linear,
            AnmCurveType.OPACITYI16TBL: self.read_opacityi16tbl,
            AnmCurveType.SCALEI16TBL: self.read_scalei16tbl,
            AnmCurveType.QUATERNIONI16TBL: self.read_quaternioni16tbl,
            AnmCurveType.COLORRGBTBL: self.read_colorrgbtbl,
            AnmCurveType.VECTOR3TBL: self.read_vector3tbl,
            AnmCurveType.FLOATTBLNI: self.read_floattblni,
            AnmCurveType.QUATERNIONTBL: self.read_quaterniontbl,
            AnmCurveType.FLOATTBL: self.read_floattbl,
            AnmCurveType.VECTOR3I16LINEAR: self.read_vector3i16linear,
            AnmCurveType.VECTOR3TBL_NOINTERP: self.read_vector3tbl_nointerp,
            AnmCurveType.QUATERNIONI16TBL_NOINTERP: self.read_quaternioni16tbl_nointerp,
            AnmCurveType.OPACITYI16TBL_NOINTERP: self.read_opacityi16tbl_nointerp,
        }

        for header in self.curve_headers:
            curve = [None] * header.keyframe_count
            reader = curve_readers.get(header.curve_format)
            if reader:
                reader(br, header, curve)
            else:
                print(f'NuccChunkAnm: Unsupported curve format {header.curve_format}')
            br.align_pos(4)
            self.curves.append(curve)

    def read_vector3fixed(self, br, header, curve):
        for i in range(header.keyframe_count):
            curve[i] = br.read_float(3)

    def read_vector3linear(self, br, header, curve):
        for i in range(header.keyframe_count):
            curve[i] = (br.read_int32(), *br.read_float(3))

    def read_vector3bezier(self, br, header, curve):
        for i in range(header.keyframe_count):
            curve[i] = (br.read_int32(), *br.read_float(3))

    def read_eulerxyzfixed(self, br, header, curve):
        for i in range(header.keyframe_count):
            curve[i] = br.read_float(3)

    def read_eulerinterpolate(self, br, header, curve):
        for i in range(header.keyframe_count):
            curve[i] = br.read_float(3)

    def read_quaternionlinear(self, br, header, curve):
        for i in range(header.keyframe_count):
            curve[i] = (br.read_int32(), *br.read_float(4))

    def read_floatfixed(self, br, header, curve):
        for i in range(header.keyframe_count):
            curve[i] = br.read_float(1)

    def read_floatlinear(self, br, header, curve):
        for i in range(header.keyframe_count):
            curve[i] = (br.read_int32(), br.read_float())

    def read_vector2fixed(self, br, header, curve):
        for i in range(header.keyframe_count):
            curve[i] = br.read_int16(1)

    def read_vector2linear(self, br, header, curve):
        for i in range(header.keyframe_count):
            curve[i] = br.read_int16(3)

    def read_opacityi16tbl(self, br, header, curve):
        for i in range(header.keyframe_count):
            curve[i] = br.read_int16(1)

    def read_scalei16tbl(self, br, header, curve):
        for i in range(header.keyframe_count):
            curve[i] = br.read_int16(3)

    def read_quaternioni16tbl(self, br, header, curve):
        for i in range(header.keyframe_count):
            curve[i] = br.read_int16(4)

    def read_colorrgbtbl(self, br, header, curve):
        for i in range(header.keyframe_count):
            curve[i] = br.read_uint8(3)

    def read_vector3tbl(self, br, header, curve):
        for i in range(header.keyframe_count):
            curve[i] = br.read_float(3)

    def read_floattblni(self, br, header, curve):
        for i in range(header.keyframe_count):
            curve[i] = br.read_float(1)

    def read_quaterniontbl(self, br, header, curve):
        for i in range(header.keyframe_count):
            curve[i] = br.read_float(4)

    def read_floattbl(self, br, header, curve):
        for i in range(header.keyframe_count):
            curve[i] = br.read_float(1)

    def read_vector3i16linear(self, br, header, curve):
        for i in range(header.keyframe_count):
            curve[i] = (br.read_int16(), *br.read_float(3))

    def read_vector3tbl_nointerp(self, br, header, curve):
        for i in range(header.keyframe_count):
            curve[i] = br.read_float(3)

    def read_quaternioni16tbl_nointerp(self, br, header, curve):
        for i in range(header.keyframe_count):
            curve[i] = br.read_int16(4)

    def read_opacityi16tbl_nointerp(self, br, header, curve):
        for i in range(header.keyframe_count):
            curve[i] = br.read_int16(1)

