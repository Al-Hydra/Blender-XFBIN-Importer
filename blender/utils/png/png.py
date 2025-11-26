import struct
import sys
import zlib
import numpy as np
from zlib import crc32
from io import BytesIO
from . import pngdefilter

# ─────────────────────────────
# PNG Color Type Constants
# ─────────────────────────────

COLOR_TYPE_GRAYSCALE = 0
COLOR_TYPE_RGB = 2
COLOR_TYPE_INDEXED = 3
COLOR_TYPE_GRAYSCALE_ALPHA = 4
COLOR_TYPE_RGBA = 6

COLOR_TYPE_NAMES = {
    0: "Grayscale",
    2: "RGB",
    3: "Indexed",
    4: "Grayscale+Alpha",
    6: "RGBA"
}


# ─────────────────────────────
# Base structures
# ─────────────────────────────

class PNG:
    def __init__(self):
        self.Signature = b'\x89PNG\r\n\x1a\n'
        self.Chunks = []  # Keep for unknown/ancillary chunks
        
        # Direct attributes for common chunks
        self.IHDR = None
        self.PLTE = None
        self.IDAT = []  # Can have multiple IDAT chunks
        self.IEND = None
        self.tRNS = None

    def read(self, f: BytesIO):
        self.Signature = f.read(8)
        while True:
            data = f.read(4)
            if not data or len(data) < 4:
                break
            length = struct.unpack(">I", data)[0]
            ctype = f.read(4).decode("ascii")
            cdata = f.read(length)
            crc = struct.unpack(">I", f.read(4))[0]
            cls = globals().get(ctype, PNG_Chunk)
            chunk = cls()
            chunk.Type = ctype
            chunk.Length = length
            chunk.CRC = crc
            chunk.read(BytesIO(cdata), length)
            
            # Store in direct attributes for common chunks
            if isinstance(chunk, IHDR):
                self.IHDR = chunk
            elif isinstance(chunk, PLTE):
                self.PLTE = chunk
            elif isinstance(chunk, IDAT):
                self.IDAT.append(chunk)
            elif isinstance(chunk, IEND):
                self.IEND = chunk
            elif isinstance(chunk, tRNS):
                self.tRNS = chunk
            else:
                # Store unknown chunks in the list
                self.Chunks.append(chunk)

    def write(self, f: BytesIO):
        f.write(self.Signature)
        
        # Collect all chunks in proper order
        chunks_to_write = []
        if self.IHDR:
            chunks_to_write.append(self.IHDR)
        if self.PLTE:
            chunks_to_write.append(self.PLTE)
        if self.tRNS:
            chunks_to_write.append(self.tRNS)
        chunks_to_write.extend(self.IDAT)
        chunks_to_write.extend(self.Chunks)  # Other chunks
        if self.IEND:
            chunks_to_write.append(self.IEND)
        
        for chunk in chunks_to_write:
            cdata = BytesIO()
            chunk.write(cdata)
            payload = cdata.getvalue()
            f.write(struct.pack(">I", len(payload)))
            f.write(chunk.Type.encode("ascii"))
            f.write(payload)
            crc = crc32(chunk.Type.encode("ascii") + payload)
            f.write(struct.pack(">I", crc))
    
    def get_image_data(self):
        """Combine all IDAT chunks and decompress to get raw pixel data."""
        compressed = b"".join(chunk.ImageData for chunk in self.IDAT)
        return zlib.decompress(compressed)
    
    def get_rgba(self):
        """Convenience method to get RGBA pixel data from PNG."""
        if not self.IHDR:
            raise ValueError("PNG missing IHDR chunk")
        
        width, height = self.IHDR.Width, self.IHDR.Height
        color_type = self.IHDR.ColorType
        bit_depth = self.IHDR.BitDepth
        
        # Decompress image data
        decompressed = self.get_image_data()
        
        # Handle interlacing
        if self.IHDR.InterlaceMethod == 1:  # Adam7 interlacing
            #raw_pixels = deinterlace_adam7(decompressed, width, height, color_type, bit_depth)
            raw_pixels = pngdefilter.deinterlace_adam7(decompressed, width, height, color_type, bit_depth)
        else:  # No interlacing
            raw_pixels = pngdefilter.defilter_scanlines(decompressed, width, height, color_type, bit_depth)
        
        # Convert to RGBA
        return convert_to_rgba(raw_pixels, width, height, self.IHDR, self.PLTE, self.tRNS)


class PNG_Chunk:
    def __init__(self):
        self.Length = 0
        self.Type = ""
        self.CRC = 0

    def read(self, f: BytesIO, length: int):
        self.Data = f.read(length)

    def write(self, f: BytesIO):
        if hasattr(self, "Data"):
            f.write(self.Data)


# ─────────────────────────────
# Common chunk definitions
# ─────────────────────────────

class IHDR(PNG_Chunk):
    def __init__(self):
        super().__init__()
        self.Type = "IHDR"
        self.Width = 0
        self.Height = 0
        self.BitDepth = 8
        self.ColorType = 6
        self.CompressionMethod = 0
        self.FilterMethod = 0
        self.InterlaceMethod = 0

    def read(self, f: BytesIO, length: int):
        (
            self.Width,
            self.Height,
            self.BitDepth,
            self.ColorType,
            self.CompressionMethod,
            self.FilterMethod,
            self.InterlaceMethod,
        ) = struct.unpack(">IIBBBBB", f.read(13))

    def write(self, f: BytesIO):
        f.write(struct.pack(
            ">IIBBBBB",
            self.Width,
            self.Height,
            self.BitDepth,
            self.ColorType,
            self.CompressionMethod,
            self.FilterMethod,
            self.InterlaceMethod
        ))


class IDAT(PNG_Chunk):
    def __init__(self):
        super().__init__()
        self.Type = "IDAT"
        self.ImageData = b""

    def read(self, f: BytesIO, length: int):
        self.ImageData = f.read(length)

    def write(self, f: BytesIO):
        f.write(self.ImageData)


class IEND(PNG_Chunk):
    def __init__(self):
        super().__init__()
        self.Type = "IEND"

    def read(self, f: BytesIO, length: int):
        f.read(length)

    def write(self, f: BytesIO):
        pass


class PLTE(PNG_Chunk):
    """Palette chunk for indexed color images"""
    def __init__(self):
        super().__init__()
        self.Type = "PLTE"
        self.Palette = []

    def read(self, f: BytesIO, length: int):
        # Each entry is 3 bytes (RGB)
        data = f.read(length)
        # Use NumPy for fast reading
        palette_array = np.frombuffer(data, dtype=np.uint8).reshape(-1, 3)
        self.Palette = [tuple(row) for row in palette_array]

    def write(self, f: BytesIO):
        # Convert to NumPy array and write as bytes
        if self.Palette:
            palette_array = np.array(self.Palette, dtype=np.uint8)
            f.write(palette_array.tobytes())


class tRNS(PNG_Chunk):
    """Transparency chunk"""
    def __init__(self):
        super().__init__()
        self.Type = "tRNS"
        self.TransparencyData = b""
        self.ColorType = None

    def read(self, f: BytesIO, length: int):
        self.TransparencyData = f.read(length)

    def write(self, f: BytesIO):
        f.write(self.TransparencyData)


def deinterlace_adam7(data, width, height, color_type, bit_depth):
    """Deinterlace Adam7 interlaced PNG data.
    
    Adam7 interlacing divides the image into 7 passes with specific patterns.
    """
    bpp = get_bytes_per_pixel(color_type, bit_depth)
    # Adam7 pass parameters: (x_start, y_start, x_step, y_step)
    adam7_passes = [
        (0, 0, 8, 8),  # Pass 1: 1/64 of image
        (4, 0, 8, 8),  # Pass 2
        (0, 4, 4, 8),  # Pass 3
        (2, 0, 4, 4),  # Pass 4
        (0, 2, 2, 4),  # Pass 5
        (1, 0, 2, 2),  # Pass 6
        (0, 1, 1, 2),  # Pass 7: every other row
    ]
    
    # Output buffer
    stride = width * bpp
    output = np.zeros(height * stride, dtype=np.uint8)
    
    data_offset = 0
    for pass_idx, (x_start, y_start, x_step, y_step) in enumerate(adam7_passes):
        # Calculate pass dimensions
        pass_width = (width - x_start + x_step - 1) // x_step
        pass_height = (height - y_start + y_step - 1) // y_step
        
        if pass_width == 0 or pass_height == 0:
            continue
        
        # Calculate pass data size
        pass_stride = get_scanline_bytes(pass_width, color_type, bit_depth)
        pass_size = pass_height * (pass_stride + 1)  # +1 for filter byte per scanline
        
        # Extract and defilter this pass
        pass_data = data[data_offset:data_offset + pass_size]
        if len(pass_data) < pass_size:
            break
        
        defiltered = defilter_scanlines(pass_data, pass_width, pass_height, color_type, bit_depth)
        defiltered_array = np.frombuffer(defiltered, dtype=np.uint8).reshape(pass_height, pass_stride)
        
        # Place pixels in output image according to Adam7 pattern
        for y in range(pass_height):
            out_y = y_start + y * y_step
            if out_y >= height:
                break
            for x in range(pass_width):
                out_x = x_start + x * x_step
                if out_x >= width:
                    break
                # Copy pixel (bpp bytes)
                src_offset = x * bpp
                dst_offset = out_y * stride + out_x * bpp
                output[dst_offset:dst_offset + bpp] = defiltered_array[y, src_offset:src_offset + bpp]
        
        data_offset += pass_size
    
    return output.tobytes()

def defilter_scanlines(raw, width, height, color_type, bit_depth):
    """Remove PNG filters using NumPy.

    Optimizations:
    - Vectorized Sub filter using cumsum along width axis
    - Minimal Python loops for dependent filters
    - Reusable buffers to avoid allocations
    """
    raw = np.frombuffer(raw, dtype=np.uint8)
    bpp = get_bytes_per_pixel(color_type, bit_depth)
    stride = get_scanline_bytes(width, color_type, bit_depth)
    
    # Work buffers (int16 for safe intermediate arithmetic without overflow)
    prev_line = np.zeros(stride, dtype=np.int16)
    line_buffer = np.empty(stride, dtype=np.int16)
    recon_buffer = np.empty(stride, dtype=np.int16)
    
    # Create 2D views once (they'll be updated in-place) - only for non-packed pixels
    # For packed pixels (bit_depth < 8), we work with bytes directly
    use_2d = (bit_depth >= 8) and (stride == width * bpp)
    if use_2d and width > 1:
        line_2d = line_buffer.reshape(width, bpp)
        prev_2d = prev_line.reshape(width, bpp)
        recon_2d = recon_buffer.reshape(width, bpp)
    
    # Output buffer
    out = np.empty((height, stride), dtype=np.uint8)

    i = 0
    for y in range(height):
        filter_type = raw[i]
        i += 1
        line_buffer[:] = raw[i:i+stride]
        i += stride

        if filter_type == 0:  # None
            recon_buffer[:] = line_buffer

        elif filter_type == 1:  # Sub
            # Sub: each byte adds the corresponding byte bpp positions to its left
            recon_buffer[:bpp] = line_buffer[:bpp]
            # Process in chunks of bpp for better cache locality
            for j in range(bpp, stride):
                recon_buffer[j] = (line_buffer[j] + recon_buffer[j - bpp]) & 0xFF

        elif filter_type == 2:  # Up
            recon_buffer[:] = (line_buffer + prev_line) & 0xFF

        elif filter_type == 3:  # Average
            if not use_2d:
                # Byte-level processing for packed pixels
                recon_buffer[:bpp] = (line_buffer[:bpp] + (prev_line[:bpp] >> 1)) & 0xFF
                for j in range(bpp, stride):
                    avg = (recon_buffer[j - bpp] + prev_line[j]) >> 1
                    recon_buffer[j] = (line_buffer[j] + avg) & 0xFF
            else:
                recon_2d[0, :] = (line_2d[0, :] + (prev_2d[0, :] >> 1)) & 0xFF
                for x in range(1, width):
                    recon_2d[x, :] = (line_2d[x, :] + ((recon_2d[x - 1, :] + prev_2d[x, :]) >> 1)) & 0xFF

        elif filter_type == 4:  # Paeth
            if not use_2d:
                # Byte-level processing for packed pixels
                recon_buffer[:bpp] = (line_buffer[:bpp] + prev_line[:bpp]) & 0xFF
                for j in range(bpp, stride):
                    a = recon_buffer[j - bpp]
                    b = prev_line[j]
                    c = prev_line[j - bpp]
                    p = a + b - c
                    pa = p - a if p >= a else a - p
                    pb = p - b if p >= b else b - p
                    pc = p - c if p >= c else c - p
                    pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                    recon_buffer[j] = (line_buffer[j] + pr) & 0xFF
            else:
                recon_2d[0, :] = (line_2d[0, :] + prev_2d[0, :]) & 0xFF
                for k in range(bpp):
                    seg = line_2d[:, k]
                    prev_seg = prev_2d[:, k]
                    recon_seg = recon_2d[:, k]
                    a_prev = recon_seg[0]
                    prev_c_prev = prev_seg[0]
                    for x in range(1, width):
                        a = a_prev
                        b = prev_seg[x]
                        c = prev_c_prev
                        p = a + b - c
                        pa = p - a if p >= a else a - p
                        pb = p - b if p >= b else b - p
                        pc = p - c if p >= c else c - p
                        pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                        val = (seg[x] + pr) & 0xFF
                        recon_seg[x] = val
                        a_prev = val
                        prev_c_prev = b
                        prev_c_prev = b

        else:  # Unknown filter
            recon_buffer[:] = line_buffer

        out[y] = recon_buffer.astype(np.uint8)
        prev_line[:] = recon_buffer

    return out.tobytes()


def get_bytes_per_pixel(color_type, bit_depth):
    """Calculate bytes per pixel for PNG filtering based on color type and bit depth.
    
    Returns the number of bytes per pixel used during the filtering step.
    For bit depths < 8, returns 1 (sub-byte pixels are packed).
    """
    # Map: (color_type, bit_depth) -> bytes per pixel
    # For filtering, sub-byte formats use 1 byte per pixel
    if color_type == COLOR_TYPE_GRAYSCALE:
        return max(1, bit_depth // 8)
    elif color_type == COLOR_TYPE_RGB:
        return 3 * max(1, bit_depth // 8)
    elif color_type == COLOR_TYPE_INDEXED:
        return 1  # Always 1 byte per pixel for indexed
    elif color_type == COLOR_TYPE_GRAYSCALE_ALPHA:
        return 2 * max(1, bit_depth // 8)
    elif color_type == COLOR_TYPE_RGBA:
        return 4 * max(1, bit_depth // 8)
    else:
        raise ValueError(f"Unknown color type: {color_type}")


def get_scanline_bytes(width, color_type, bit_depth):
    """Calculate the number of bytes in a scanline for filtering.
    
    For bit depths < 8, pixels are packed and we need to calculate actual byte width.
    """
    if bit_depth < 8 and color_type in (COLOR_TYPE_GRAYSCALE, COLOR_TYPE_INDEXED):
        # Packed pixels - calculate bytes needed
        bits_per_scanline = width * bit_depth
        return (bits_per_scanline + 7) // 8  # Round up to nearest byte
    else:
        # Normal case
        bpp = get_bytes_per_pixel(color_type, bit_depth)
        return width * bpp


def unpack_bits(data, width, height, bit_depth, scale_to_8bit=True):
    """Unpack sub-byte pixels to full bytes using NumPy vectorization (for bit depths 1, 2, 4)
    
    Args:
        data: Raw pixel data
        width: Image width in pixels
        height: Image height in pixels
        bit_depth: Bits per pixel (1, 2, 4, or 8)
        scale_to_8bit: If True, scale values to 0-255 range (for grayscale).
                       If False, keep raw values (for indexed colors)
    """
    if bit_depth == 8:
        return data
    
    data = np.frombuffer(data, dtype=np.uint8)
    
    # Calculate parameters
    pixels_per_byte = 8 // bit_depth
    mask = (1 << bit_depth) - 1
    total_pixels = width * height
    
    # Pre-allocate result array
    result = np.zeros(total_pixels, dtype=np.uint8)
    
    # Vectorized bit unpacking
    if bit_depth == 1:
        # Special case for 1-bit: very efficient
        shifts = np.array([7, 6, 5, 4, 3, 2, 1, 0], dtype=np.uint8)
        pixel_idx = 0
        for byte_val in data:
            remaining = min(8, total_pixels - pixel_idx)
            vals = (byte_val >> shifts[:remaining]) & 1
            result[pixel_idx:pixel_idx + remaining] = vals * 255 if scale_to_8bit else vals
            pixel_idx += remaining
            if pixel_idx >= total_pixels:
                break
    elif bit_depth == 2:
        # 2-bit: 4 pixels per byte
        shifts = np.array([6, 4, 2, 0], dtype=np.uint8)
        pixel_idx = 0
        for byte_val in data:
            remaining = min(4, total_pixels - pixel_idx)
            vals = (byte_val >> shifts[:remaining]) & 3
            result[pixel_idx:pixel_idx + remaining] = (vals * 255) // 3 if scale_to_8bit else vals
            pixel_idx += remaining
            if pixel_idx >= total_pixels:
                break
    elif bit_depth == 4:
        # 4-bit: 2 pixels per byte
        high_nibbles = (data >> 4) & 0x0F
        low_nibbles = data & 0x0F
        # Interleave high and low nibbles
        unpacked = np.empty(len(data) * 2, dtype=np.uint8)
        unpacked[0::2] = high_nibbles
        unpacked[1::2] = low_nibbles
        # Scale to 8-bit or keep raw values
        if scale_to_8bit:
            result = ((unpacked[:total_pixels].astype(np.uint16) * 255) // 15).astype(np.uint8)
        else:
            result = unpacked[:total_pixels]
        return result.tobytes()
    
    return result.tobytes()


def _grayscale_to_rgba(raw_pixels, width, height, bit_depth, trns=None):
    """Convert grayscale PNG to RGBA"""
    # Convert to 8-bit grayscale
    if bit_depth == 16:
        data = np.frombuffer(raw_pixels, dtype='>u2')
        gray = (data >> 8).astype(np.uint8)
    elif bit_depth < 8:
        gray = np.frombuffer(unpack_bits(raw_pixels, width, height, bit_depth), dtype=np.uint8)
    else:
        gray = np.frombuffer(raw_pixels, dtype=np.uint8)
    
    # Build RGBA (grayscale in RGB channels, opaque alpha)
    rgba = np.empty((len(gray), 4), dtype=np.uint8)
    rgba[:, :3] = gray[:, np.newaxis]  # Broadcast to R, G, B in one operation
    rgba[:, 3] = 255   # A
    
    # Apply transparency if tRNS chunk exists
    if trns and len(trns.TransparencyData) >= 2:
        trns_gray = struct.unpack(">H", trns.TransparencyData[:2])[0]
        if bit_depth < 8:
            trns_gray = (trns_gray * 255) // ((1 << bit_depth) - 1)
        elif bit_depth == 16:
            trns_gray = trns_gray >> 8
        rgba[gray == trns_gray, 3] = 0
    
    return rgba.tobytes()


def _rgb_to_rgba(raw_pixels, bit_depth, trns=None):
    """Convert RGB PNG to RGBA"""
    # Convert to 8-bit RGB
    if bit_depth == 16:
        data = np.frombuffer(raw_pixels, dtype='>u2')
        rgb = (data >> 8).astype(np.uint8).reshape(-1, 3)
    else:
        rgb = np.frombuffer(raw_pixels, dtype=np.uint8).reshape(-1, 3)
    
    # Build RGBA with opaque alpha
    rgba = np.empty((rgb.shape[0], 4), dtype=np.uint8)
    rgba[:, :3] = rgb
    rgba[:, 3] = 255
    
    # Apply transparency if tRNS chunk exists
    if trns and len(trns.TransparencyData) >= 6:
        trns_rgb = np.array(struct.unpack(">HHH", trns.TransparencyData[:6]), dtype=np.uint16)
        if bit_depth == 16:
            trns_rgb = (trns_rgb >> 8).astype(np.uint8)
        else:
            trns_rgb = trns_rgb.astype(np.uint8)
        mask = np.all(rgb == trns_rgb, axis=1)
        rgba[mask, 3] = 0
    
    return rgba.tobytes()


def _indexed_to_rgba(raw_pixels, width, height, bit_depth, plte, trns=None):
    """Convert indexed/palette PNG to RGBA"""
    # Unpack indices - keep raw values, don't scale to 8-bit
    if bit_depth < 8:
        indices = np.frombuffer(unpack_bits(raw_pixels, width, height, bit_depth, scale_to_8bit=False), dtype=np.uint8)
    else:
        indices = np.frombuffer(raw_pixels, dtype=np.uint8)
    
    if not plte or not plte.Palette:
        raise ValueError("PLTE chunk required for indexed color PNG")
    
    # Build RGBA palette directly
    palette_len = len(plte.Palette)
    palette_rgba = np.empty((palette_len, 4), dtype=np.uint8)
    palette_rgba[:, :3] = plte.Palette  # NumPy handles list of tuples efficiently
    palette_rgba[:, 3] = 255  # Default opaque
    
    # Apply transparency from tRNS chunk if present
    if trns:
        trns_data = np.frombuffer(trns.TransparencyData, dtype=np.uint8)
        palette_rgba[:len(trns_data), 3] = trns_data
    
    # Direct palette lookup - much faster!
    # Clip indices to prevent index out of bounds
    indices = np.clip(indices, 0, len(palette_rgba) - 1)
    rgba = palette_rgba[indices]
    
    return rgba.tobytes()


def _grayscale_alpha_to_rgba(raw_pixels, bit_depth):
    """Convert grayscale+alpha PNG to RGBA"""
    # Convert to 8-bit GA
    if bit_depth == 16:
        data = np.frombuffer(raw_pixels, dtype='>u2')
        ga = (data >> 8).astype(np.uint8).reshape(-1, 2)
    else:
        ga = np.frombuffer(raw_pixels, dtype=np.uint8).reshape(-1, 2)
    
    # Build RGBA (grayscale in RGB channels, preserve alpha)
    rgba = np.empty((ga.shape[0], 4), dtype=np.uint8)
    rgba[:, :3] = ga[:, 0:1]  # Broadcast grayscale to R, G, B
    rgba[:, 3] = ga[:, 1]  # A
    
    return rgba.tobytes()


def _rgba_normalize(raw_pixels, bit_depth):
    """Normalize RGBA PNG to 8-bit"""
    if bit_depth == 16:
        # 16-bit RGBA - take high bytes
        data = np.frombuffer(raw_pixels, dtype='>u2')
        rgba = (data >> 8).astype(np.uint8)
        return rgba.tobytes()
    return raw_pixels


def convert_to_rgba(raw_pixels, width, height, ihdr, plte=None, trns=None):
    """Convert any PNG color type to RGBA.
    
    Dispatches to specialized conversion functions based on color type.
    All formats are converted to 8-bit RGBA.
    """
    color_type = ihdr.ColorType
    bit_depth = ihdr.BitDepth
    
    if color_type == COLOR_TYPE_GRAYSCALE:
        return _grayscale_to_rgba(raw_pixels, width, height, bit_depth, trns)
    elif color_type == COLOR_TYPE_RGB:
        return _rgb_to_rgba(raw_pixels, bit_depth, trns)
    elif color_type == COLOR_TYPE_INDEXED:
        return _indexed_to_rgba(raw_pixels, width, height, bit_depth, plte, trns)
    elif color_type == COLOR_TYPE_GRAYSCALE_ALPHA:
        return _grayscale_alpha_to_rgba(raw_pixels, bit_depth)
    elif color_type == COLOR_TYPE_RGBA:
        return _rgba_normalize(raw_pixels, bit_depth)
    else:
        raise ValueError(f"Unsupported color type: {color_type}")

def read_png(data: bytearray):
    png = PNG()
    with BytesIO(data) as f:
        png.read(f)
    return png

# ─────────────────────────────
# Example usage with your PNG class
# ─────────────────────────────
if __name__ == "__main__":
    from PIL import Image
    from time import perf_counter
    path = r"C:\Users\Hydra\Downloads\Ds2\cf_m_body_MT_CT.png"
    
    with open(path, "rb") as f:
        png = PNG()
        png.read(BytesIO(f.read()))

    start_time = perf_counter()
    # Display PNG info
    width, height = png.IHDR.Width, png.IHDR.Height
    color_type_name = COLOR_TYPE_NAMES.get(png.IHDR.ColorType, "Unknown")
    print(f"PNG: {width}x{height}, {color_type_name} (ColorType={png.IHDR.ColorType}), BitDepth={png.IHDR.BitDepth}")

    # Get RGBA pixel data using convenience method
    rgba_pixels = png.get_rgba()
    end_time = perf_counter()
    print(f"Converted to RGBA in {end_time - start_time:.4f} seconds.")
    # Convert to PIL image for preview
    img = Image.frombytes("RGBA", (width, height), rgba_pixels)
    img.show()

