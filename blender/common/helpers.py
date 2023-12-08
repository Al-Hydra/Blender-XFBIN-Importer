import array
import struct

import bpy

XFBIN_TEXTURES_OBJ = '#XFBIN Textures'
XFBIN_ANMS_OBJ = '#XFBIN Animations'

XFBIN_DYNAMICS_OBJ = '#XFBIN Dynamics'

def hex_str_to_int(val: str) -> int:
    return int(val.replace(' ', ''), 16)


def int_to_hex_str(val: int, size: int) -> str:
    # Format the value into a hex string and split it into chunks of 2
    str_val = f'{val:0{size*2}X}'
    return ' '.join([str_val[i: i + 2] for i in range(0, len(str_val), 2)])


def format_hex_str(value: str, size: int):
    try:
        val = hex_str_to_int(value)
    except:
        pass
    else:
        return int_to_hex_str(val, size)
