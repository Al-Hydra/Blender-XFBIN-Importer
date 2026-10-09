"""Pure-Python fallback for blockCompressor.pyd, used where the compiled module can't load (Linux/macOS).

Decompression (used when importing / viewing textures) is implemented; DXT compression (only used
when exporting edited textures back to XFBIN) is not, and raises a clear error instead.
"""
import struct


def _rgb565(c):
    r, g, b = (c >> 11) & 31, (c >> 5) & 63, c & 31
    return (r << 3 | r >> 2, g << 2 | g >> 4, b << 3 | b >> 2)


def _color_block(blk, out, x0, y0, width, height, dxt1):
    c0, c1, bits = struct.unpack_from("<HHI", blk, 0)
    p0, p1 = _rgb565(c0), _rgb565(c1)
    if c0 > c1 or not dxt1:
        p2 = tuple((2 * a + b) // 3 for a, b in zip(p0, p1))
        p3 = tuple((a + 2 * b) // 3 for a, b in zip(p0, p1))
        pal = [p0 + (255,), p1 + (255,), p2 + (255,), p3 + (255,)]
    else:
        p2 = tuple((a + b) // 2 for a, b in zip(p0, p1))
        pal = [p0 + (255,), p1 + (255,), p2 + (255,), (0, 0, 0, 0)]
    for j in range(4):
        y = y0 + j
        if y >= height:
            break
        for i in range(4):
            x = x0 + i
            if x >= width:
                continue
            idx = (bits >> (2 * (j * 4 + i))) & 3
            o = (y * width + x) * 4
            out[o:o + 4] = bytes(pal[idx])


def _blocks(data, width, height, size):
    bw, bh = (width + 3) // 4, (height + 3) // 4
    for by in range(bh):
        for bx in range(bw):
            off = (by * bw + bx) * size
            yield bx * 4, by * 4, data[off:off + size]


def decompress_dxt1(data, width, height):
    out = bytearray(width * height * 4)
    for x0, y0, blk in _blocks(data, width, height, 8):
        _color_block(blk, out, x0, y0, width, height, True)
    return bytes(out)


def decompress_dxt3(data, width, height):
    out = bytearray(width * height * 4)
    for x0, y0, blk in _blocks(data, width, height, 16):
        _color_block(blk[8:], out, x0, y0, width, height, False)
        alpha = int.from_bytes(blk[:8], "little")
        for j in range(4):
            for i in range(4):
                x, y = x0 + i, y0 + j
                if x < width and y < height:
                    a = (alpha >> (4 * (j * 4 + i))) & 15
                    out[(y * width + x) * 4 + 3] = a * 17
    return bytes(out)


def decompress_dxt5(data, width, height):
    out = bytearray(width * height * 4)
    for x0, y0, blk in _blocks(data, width, height, 16):
        _color_block(blk[8:], out, x0, y0, width, height, False)
        a0, a1 = blk[0], blk[1]
        if a0 > a1:
            pal = [a0, a1] + [((7 - k) * a0 + k * a1) // 7 for k in range(1, 7)]
        else:
            pal = [a0, a1] + [((5 - k) * a0 + k * a1) // 5 for k in range(1, 5)] + [0, 255]
        bits = int.from_bytes(blk[2:8], "little")
        for j in range(4):
            for i in range(4):
                x, y = x0 + i, y0 + j
                if x < width and y < height:
                    out[(y * width + x) * 4 + 3] = pal[(bits >> (3 * (j * 4 + i))) & 7]
    return bytes(out)


def _no_compress(*_):
    raise NotImplementedError("DXT compression needs the Windows blockCompressor.pyd; exporting "
                              "edited textures is not available on this platform")


compress_dxt1 = compress_dxt3 = compress_dxt5 = _no_compress
