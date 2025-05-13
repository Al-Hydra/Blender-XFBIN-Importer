from dataclasses import dataclass
from binary_reader.binary_reader import *


cam_writer = BinaryReader(endianness=Endian.BIG, encoding='utf-8')  # Create a new BinaryReader (bytearray buffer is initialized automatically)


@dataclass
class Camera(BrStruct):
    unk: int
    fov: float

    def __br_write__(self, cam_writer: 'BinaryReader'):
        cam_writer.write_int32(self.unk)
        cam_writer.write_float(self.fov)