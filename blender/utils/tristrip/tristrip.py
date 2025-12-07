from .trianglestripifier import TriangleStripifier
from .trianglemesh import Mesh
import numpy as np
import sys
from pathlib import Path

# Try to load Rust implementation directly
_rust_tristrip = None
_USE_RUST = False

try:
    rust_lib_path = Path(__file__).parent / "tristrip_rust"# / "target" / "release"
    if rust_lib_path.exists():
        sys.path.insert(0, str(rust_lib_path))
        import tristrip_rust
        _rust_tristrip = tristrip_rust
        _USE_RUST = True
        sys.path.pop(0)
except ImportError:
    pass

def stripify(triangles, stitchstrips = False):
    """Converts triangles into a list of strips.

    If stitchstrips is True, then everything is wrapped in a single strip using
    degenerate triangles.
    
    This function will automatically use the optimized Rust implementation if
    available, otherwise it falls back to the Python implementation.
    """
    
    # Use Rust implementation if available (10-100x faster)
    if _USE_RUST and _rust_tristrip is not None:
        result = _rust_tristrip.stripify(triangles, stitchstrips)
        return result
    
    # Fall back to Python implementation
    
    # Fall back to Python implementation
    strips = []
    # build a mesh from triangles
    mesh = Mesh()
    face_count = 0
    for face in triangles:
        try:
            mesh.add_face(*face)
            face_count += 1
        except ValueError:
            # degenerate face
            pass
    mesh.lock()

    # calculate the strip
    stripifier = TriangleStripifier(mesh)
    strips = stripifier.find_all_strips()

    # stitch the strips if needed
    if stitchstrips:            
        result = stitch_strips(strips)
        return [result]
    else:
        return strips

class OrientedStrip:
    """Optimized version with NumPy array support and stitching logic."""
    __slots__ = ("vertices", "reversed")

    def __init__(self, strip):
        if isinstance(strip, (list, tuple)):
            self.vertices = np.array(strip, dtype=np.int32)
            self.reversed = False
            self._compactify()
        elif isinstance(strip, OrientedStrip):
            self.vertices = np.copy(strip.vertices)
            self.reversed = strip.reversed
        else:
            raise TypeError("expected list or OrientedStrip")

    def _compactify(self):
        if self.vertices.size < 3:
            raise ValueError("Strip must have at least one non-degenerate face")

        while self.vertices[0] == self.vertices[1]:
            self.vertices = self.vertices[1:]
            self.reversed ^= True
            if self.vertices.size < 3:
                raise ValueError("Invalid strip")

        while self.vertices[-1] == self.vertices[-2]:
            self.vertices = self.vertices[:-1]
            if self.vertices.size < 3:
                raise ValueError("Invalid strip")

    def reverse(self):
        self.vertices = self.vertices[::-1]
        if self.vertices.size & 1:
            self.reversed ^= True

    def get_num_stitches(self, other) -> int:
        has_common = self.vertices[-1] == other.vertices[0]
        same_winding = (self.reversed == other.reversed) if self.vertices.size % 2 == 0 else (self.reversed != other.reversed)
        if has_common:
            return 0 if same_winding else 1
        else:
            return 2 if same_winding else 3

    def __add__(self, other):
        result = OrientedStrip(self)
        stitches = self.get_num_stitches(other)
        extra = []

        if stitches >= 1:
            extra.append(self.vertices[-1])
        if stitches >= 2:
            extra.append(other.vertices[0])
        if stitches >= 3:
            extra.append(other.vertices[0])

        result.vertices = np.concatenate([result.vertices, np.array(extra, dtype=np.int32), other.vertices])
        return result

    def __iter__(self):
        if self.reversed:
            yield int(self.vertices[0])
        for v in self.vertices:
            yield int(v)

def stitch_strips(strips):
    """Greedy stitching with minimal index count and NumPy support."""
    if not strips:
        return []

    class ExperimentSelector:
        __slots__ = ("best_pair", "best_index", "best_score")

        def __init__(self):
            self.best_pair = None
            self.best_index = -1
            self.best_score = float("inf")

        def try_pair(self, index, base, candidate):
            cost = base.get_num_stitches(candidate)
            if cost >= 4:
                return False
            score = cost * 1000 + candidate.vertices.size
            if score < self.best_score:
                self.best_score = score
                self.best_pair = (base, candidate)
                self.best_index = index
                return cost == 0
            return False

    ostrips = []
    for strip in strips:
        if len(strip) >= 3:
            o = OrientedStrip(strip)
            r = OrientedStrip(strip)
            r.reverse()
            ostrips.append((o, r))

    if not ostrips:
        return []

    result = ostrips.pop()[0]

    while ostrips:
        selector = ExperimentSelector()

        for i, (fwd, rev) in enumerate(ostrips):
            if selector.try_pair(i, result, fwd): break
            if selector.try_pair(i, fwd, result): break
            if selector.try_pair(i, result, rev): break
            if selector.try_pair(i, rev, result): break
            if selector.best_score == 0: break

        if selector.best_pair:
            result = selector.best_pair[0] + selector.best_pair[1]
            ostrips.pop(selector.best_index)
        else:
            break

    final = np.fromiter(result, dtype=np.int32)
    if final.size >= 2 and final[0] == final[1] and (final.size % 2 == 0):
        final = final[1:][::-1]
    return final.tolist()
