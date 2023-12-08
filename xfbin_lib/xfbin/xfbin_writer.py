from .structure.br.br_xfbin import *
from .structure.xfbin import Xfbin
from .util import *


def write_xfbin(xfbin: Xfbin) -> bytearray:
    """Writes an XFBIN object to memory and returns a bytearray.
    :param xfbin: Xfbin object
    :return: A bytearray containing the written xfbin
    """

    br = BinaryReader(endianness=Endian.BIG)

    # Everything will be handled by the BrXfbin
    br.write_struct(BrXfbin(), xfbin)

    return br.buffer()


def write_xfbin_to_path(xfbin: Xfbin, path: str) -> None:
    file = write_xfbin(xfbin)
    with open(path, 'wb') as f:
        f.write(file)
