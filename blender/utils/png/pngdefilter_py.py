"""Pure-Python fallback for pngdefilter.pyd, used where the compiled module can't load (Linux/macOS).

defilter_scanlines: undo PNG per-scanline filters -> raw pixel rows (no filter bytes).
deinterlace_adam7:  same for Adam7-interlaced data, reassembled into a full image.
"""

_CHANNELS = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}


def _bits_per_pixel(color_type, bit_depth):
    return _CHANNELS[color_type] * bit_depth


def _row_bytes(width, color_type, bit_depth):
    return (width * _bits_per_pixel(color_type, bit_depth) + 7) // 8


def _unfilter(data, offset, width, height, color_type, bit_depth):
    """Unfilter `height` rows starting at data[offset]; returns (pixels, new_offset)."""
    stride = _row_bytes(width, color_type, bit_depth)
    bpp = max(1, _bits_per_pixel(color_type, bit_depth) // 8)
    out = bytearray(stride * height)
    prev = bytearray(stride)
    pos = offset
    for y in range(height):
        ftype = data[pos]
        line = bytearray(data[pos + 1:pos + 1 + stride])
        pos += 1 + stride
        if ftype == 1:      # Sub
            for i in range(bpp, stride):
                line[i] = (line[i] + line[i - bpp]) & 0xFF
        elif ftype == 2:    # Up
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif ftype == 3:    # Average
            for i in range(stride):
                left = line[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + ((left + prev[i]) >> 1)) & 0xFF
        elif ftype == 4:    # Paeth
            for i in range(stride):
                a = line[i - bpp] if i >= bpp else 0
                b = prev[i]
                c = prev[i - bpp] if i >= bpp else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pred = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pred) & 0xFF
        out[y * stride:(y + 1) * stride] = line
        prev = line
    return bytes(out), pos


def defilter_scanlines(raw, width, height, color_type, bit_depth):
    return _unfilter(raw, 0, width, height, color_type, bit_depth)[0]


_ADAM7 = [(0, 0, 8, 8), (4, 0, 8, 8), (0, 4, 4, 8), (2, 0, 4, 4), (0, 2, 2, 4), (1, 0, 2, 2),
          (0, 1, 1, 2)]


def deinterlace_adam7(data, width, height, color_type, bit_depth):
    if bit_depth < 8:
        raise NotImplementedError("Adam7 with sub-byte bit depths is not supported")
    bpp = _bits_per_pixel(color_type, bit_depth) // 8
    stride = width * bpp
    out = bytearray(stride * height)
    pos = 0
    for x0, y0, dx, dy in _ADAM7:
        pw = (width - x0 + dx - 1) // dx
        ph = (height - y0 + dy - 1) // dy
        if pw <= 0 or ph <= 0:
            continue
        pix, pos = _unfilter(data, pos, pw, ph, color_type, bit_depth)
        for j in range(ph):
            y = y0 + j * dy
            for i in range(pw):
                x = x0 + i * dx
                src = (j * pw + i) * bpp
                dst = y * stride + x * bpp
                out[dst:dst + bpp] = pix[src:src + bpp]
    return bytes(out)
