from dataclasses import dataclass
from binary_reader.binary_reader import *


ambient_writer = BinaryReader(endianness=Endian.BIG, encoding='utf-8')  # Create a new BinaryReader (bytearray buffer is initialized automatically)


@dataclass
class Ambient(BrStruct):
    unk1: float
    unk2: float
    unk3: float
    unk4: float

    def __br_write__(self, ambient_writer: 'BinaryReader'):
        ambient_writer.write_float(self.unk1)
        ambient_writer.write_float(self.unk2)
        ambient_writer.write_float(self.unk3)
        ambient_writer.write_float(self.unk4)