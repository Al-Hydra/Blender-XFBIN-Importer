from dataclasses import dataclass
from binary_reader.binary_reader import *


lightdirc_writer = BinaryReader(endianness=Endian.BIG, encoding='utf-8')  # Create a new BinaryReader (bytearray buffer is initialized automatically)


@dataclass
class LightDirc(BrStruct):
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

    def __br_write__(self, lightDirc_writer: 'BinaryReader'):
        lightDirc_writer.write_float(self.unk1)
        lightDirc_writer.write_float(self.unk2)
        lightDirc_writer.write_float(self.unk3)
        lightDirc_writer.write_float(self.unk4)
        lightDirc_writer.write_float(self.unk5)
        lightDirc_writer.write_float(self.unk6)
        lightDirc_writer.write_float(self.unk7)
        lightDirc_writer.write_float(self.unk8)
        lightDirc_writer.write_float(self.unk9)
        lightDirc_writer.write_float(self.unk10)
        lightDirc_writer.write_float(self.unk11)
        lightDirc_writer.write_float(self.unk12)
        lightDirc_writer.write_float(self.unk13)
        lightDirc_writer.write_float(self.unk14)
        lightDirc_writer.write_float(self.unk15)
        lightDirc_writer.write_float(self.unk16)