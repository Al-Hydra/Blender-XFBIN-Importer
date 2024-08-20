from dataclasses import dataclass
from binary_reader.binary_reader import *


Lightpoint_writer = BinaryReader(endianness=Endian.BIG, encoding='utf-8')  # Create a new BinaryReader (bytearray buffer is initialized automatically)


@dataclass
class LightPoint(BrStruct):
    unk1: float
    unk2: float
    unk3: float
    unk4: float
    unk5: float
    unk6: float
    unk7: float
    unk8: float
    unk9: float
    unk10: float
    unk11: float
    unk12: float
    unk13: float
    unk14: float
    unk15: float
    unk16: float

    def __br_write__(self, lightPoint_writer: 'BinaryReader'):
        lightPoint_writer.write_float(self.unk1)
        lightPoint_writer.write_float(self.unk2)
        lightPoint_writer.write_float(self.unk3)
        lightPoint_writer.write_float(self.unk4)
        lightPoint_writer.write_float(self.unk5)
        lightPoint_writer.write_float(self.unk6)
        lightPoint_writer.write_float(self.unk7)
        lightPoint_writer.write_float(self.unk8)
        lightPoint_writer.write_float(self.unk9)
        lightPoint_writer.write_float(self.unk10)
        lightPoint_writer.write_float(self.unk11)
        lightPoint_writer.write_float(self.unk12)
        lightPoint_writer.write_float(self.unk13)
        lightPoint_writer.write_float(self.unk14)
        lightPoint_writer.write_float(self.unk15)
        lightPoint_writer.write_float(self.unk16)