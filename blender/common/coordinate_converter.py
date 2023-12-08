import math
from math import tan, atan, pi
from mathutils import Matrix, Quaternion, Euler, Vector
from typing import Tuple, List


def pos_cm_to_m(pos: Tuple[float, float, float]) -> Vector:
    # From centimeter to meter
    return Vector(pos) * 0.01


def pos_cm_to_m_tuple(pos: Tuple[float]) -> Tuple[float]:
    # From centimeter to meter
    return tuple(map(lambda x: x * 0.01, pos))


def pos_to_blender(pos) -> Vector:
    return Vector(pos)


def pos_scaled_to_blender(pos) -> Vector:
    return pos_cm_to_m(pos_to_blender(pos))


def rot_to_blender(rot):
    return Euler(tuple(map(lambda x: math.radians(x), rot)), 'ZYX')


def uv_to_blender(uv):
    return Vector((uv[0], 1.0 - uv[1]))


def frame_to_blender(frame):
    return frame * 0.01


def focal_to_blender(fov, sensor_width) -> float:
    return (sensor_width / 2) / tan(math.radians(fov) / 2)


def focal_from_blender(focal_length, sensor_width) -> float:
    return 2 * atan(0.5 * sensor_width / focal_length) * 180 / pi


def pos_m_to_cm(pos: Vector) -> Tuple[float, float, float]:
    # From meter to centimeter
    return (pos * 100)[:]


def pos_m_to_cm_tuple(pos: Tuple[float]) -> Tuple[float]:
    # From meter to centimeter
    return tuple(map(lambda x: x * 100, pos))


def pos_from_blender(pos: Vector) -> Tuple[float, float, float]:
    return pos[:]


def pos_scaled_from_blender(pos: Vector) -> Tuple[float, float, float]:
    return pos_from_blender(Vector(pos_m_to_cm(pos)))


def rot_from_blender(rot: Euler) -> Tuple[float, float, float]:
    return tuple(map(lambda x: math.degrees(x), rot))


def uv_from_blender(uv):
    return (uv[0], 1.0 - uv[1])


def frame_from_blender(frame):
    return frame * 100

def transform_location_to_blender(original_coords: Matrix, original_parent_coords: Vector, values: List[Vector], parent_exist: bool):

    head = original_coords

    parent_head = Vector()
    if parent_exist:
        parent_head = original_parent_coords

    loc,rot,sca = head.decompose()

    pre_mat = (
        Matrix.Translation(loc).inverted()
        @ rot.to_matrix().to_4x4().inverted()
    )

    post_mat = (
        rot.to_matrix().to_4x4()
        @ Matrix.Translation(loc)
    )

    values = list(map(lambda x: (pre_mat @ Matrix.Translation(pos_cm_to_m(x) - loc + parent_head) @ post_mat).to_translation(), values))

    return values

def transform_rotation_to_blender(rot: Quaternion, values: List[Quaternion]):

    values = list(map(lambda x: rot @ Quaternion([x[3],x[0],x[1],x[2]]).inverted(), values))

    return values