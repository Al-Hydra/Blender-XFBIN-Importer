"""A wrapper for TriangleStripifier and some utility functions, for
stripification of sets of triangles, stitching and unstitching strips,
and triangulation of strips."""

# ***** BEGIN LICENSE BLOCK *****
#
# Copyright (c) 2007-2012, Python File Format Interface
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#
#    * Redistributions in binary form must reproduce the above
#      copyright notice, this list of conditions and the following
#      disclaimer in the documentation and/or other materials provided
#      with the distribution.
#
#    * Neither the name of the Python File Format Interface
#      project nor the names of its contributors may be used to endorse
#      or promote products derived from this software without specific
#      prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# ***** END LICENSE BLOCK *****


from .trianglestripifier import TriangleStripifier
from .trianglemesh import Mesh
import numpy as np
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor
import itertools
from time import perf_counter
from typing import List
from collections import defaultdict
def triangulate(strips):
    """A generator for iterating over the faces in a set of
    strips. Degenerate triangles in strips are discarded.

    >>> triangulate([[1, 0, 1, 2, 3, 4, 5, 6]])
    [(0, 2, 1), (1, 2, 3), (2, 4, 3), (3, 4, 5), (4, 6, 5)]
    """

    triangles = []

    for strip in strips:
        if len(strip) < 3: continue # skip empty strips
        # make list copy incase input data does not like slice notation
        strip_list = list(strip)
        # flips the order of verts in every other tri
        flip = False
        for i in range(0, len(strip_list)-2):
            flip = not flip
            t0, t1, t2 = strip_list[i:i+3]
            # skip degenerate tri
            if t0 == t1 or t1 == t2 or t2 == t0: continue
            # append tri in correct order
            triangles.append((t0, t1, t2) if flip else (t0, t2, t1))

    return triangles


def stripify(triangles, stitchstrips = False):
    """Converts triangles into a list of strips.

    If stitchstrips is True, then everything is wrapped in a single strip using
    degenerate triangles.

    """

    strips = []
    # build a mesh from triangles
    mesh = Mesh()
    for face in triangles:
        try:
            mesh.add_face(*face)
        except ValueError:
            # degenerate face
            pass
    mesh.lock()

    # calculate the strip
    stripifier = TriangleStripifier(mesh)
    strips = stripifier.find_all_strips()

    # stitch the strips if needed
    if stitchstrips:            
        return [stitch_strips(strips)]
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


def unstitch_strip(strip):
    """Revert stitched strip back to a set of strips without stitches."""
    strips = []
    currentstrip = []
    i = 0
    while i < len(strip)-1:
        winding = i & 1
        currentstrip.append(strip[i])
        if strip[i] == strip[i+1]:
            # stitch detected, add current strip to list of strips
            strips.append(currentstrip)
            # and start a new one, taking into account winding
            if winding == 1:
                currentstrip = []
            else:
                currentstrip = [strip[i+1]]
        i += 1
    # add last part
    currentstrip.extend(strip[i:])
    strips.append(currentstrip)
    # sanitize strips
    for strip in strips:
        while len(strip) >= 3 and strip[0] == strip[1] == strip[2]:
            strip.pop(0)
            strip.pop(0)
    return [strip for strip in strips if len(strip) > 3 or (len(strip) == 3 and strip[0] != strip[1])]

if __name__=='__main__':
    import doctest
    doctest.testmod()
