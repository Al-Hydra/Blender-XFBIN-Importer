"""A general purpose stripifier, based on NvTriStrip (http://developer.nvidia.com/)

Credit for porting NvTriStrip to Python goes to the RuneBlade Foundation
library:
http://techgame.net/projects/Runeblade/browser/trunk/RBRapier/RBRapier/Tools/Geometry/Analysis/TriangleStripifier.py?rev=760

The algorithm of this stripifier is an improved version of the RuneBlade
Foundation / NVidia stripifier; it makes no assumptions about the
underlying geometry whatsoever and is intended to produce valid
output in all circumstances.
"""

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

import itertools
import random # choice

from .trianglemesh import Face, Mesh
import numpy as np

class TriangleStrip(object):
    """A heavily specialized oriented strip of faces."""

    def __init__(self, stripped_faces=None, faces=None, vertices=None, reversed_=False):
        self.faces = faces if faces is not None else []
        self.vertices = np.empty(0, dtype=np.int32) if vertices is None else np.array(vertices, dtype=np.int32)
        self.reversed_ = reversed_
        self.stripped_faces = stripped_faces if stripped_faces is not None else set()

    def __repr__(self):
        return (f"TriangleStrip(stripped_faces={repr(self.stripped_faces)}, "
                f"faces={repr(self.faces)}, vertices={self.vertices.tolist()}, reversed_={repr(self.reversed_)})")

    def get_unstripped_adjacent_face(self, face, vi):
        for otherface in face.get_adjacent_faces(vi):
            if otherface.index not in self.stripped_faces:
                return otherface

    def traverse_faces(self, start_vertex, start_face, forward):
        count = 0
        pv0 = start_vertex
        pv1 = start_face.get_next_vertex(pv0)
        pv2 = start_face.get_next_vertex(pv1)
        next_face = self.get_unstripped_adjacent_face(start_face, pv0)

        while next_face:
            self.stripped_faces.add(next_face.index)
            count += 1

            if count & 1:
                if forward:
                    pv0 = pv1
                    pv1 = next_face.get_next_vertex(pv0)
                    self.vertices = np.append(self.vertices, pv1)
                    self.faces.append(next_face)
                else:
                    pv0 = pv2
                    pv2 = next_face.get_next_vertex(pv1)
                    self.vertices = np.insert(self.vertices, 0, pv2)
                    self.faces.insert(0, next_face)
                    self.reversed_ = not self.reversed_
            else:
                if forward:
                    pv0 = pv2
                    pv2 = next_face.get_next_vertex(pv1)
                    self.vertices = np.append(self.vertices, pv2)
                    self.faces.append(next_face)
                else:
                    pv0 = pv1
                    pv1 = next_face.get_next_vertex(pv0)
                    self.vertices = np.insert(self.vertices, 0, pv1)
                    self.faces.insert(0, next_face)
                    self.reversed_ = not self.reversed_

            next_face = self.get_unstripped_adjacent_face(next_face, pv0)
        return count

    def build(self, start_vertex, start_face):
        self.faces.clear()
        self.vertices = np.empty(0, dtype=np.int32)
        self.reversed_ = False

        v0 = start_vertex
        v1 = start_face.get_next_vertex(v0)
        v2 = start_face.get_next_vertex(v1)

        self.stripped_faces.add(start_face.index)
        self.faces.append(start_face)
        self.vertices = np.array([v0, v1, v2], dtype=np.int32)

        self.traverse_faces(v0, start_face, True)
        return self.traverse_faces(v2, start_face, False)

    def get_strip(self):
        if self.reversed_:
            if len(self.vertices) & 1:
                return self.vertices[::-1].tolist()
            elif len(self.vertices) == 4:
                return [self.vertices[0], self.vertices[2], self.vertices[1], self.vertices[3]]
            else:
                return [self.vertices[0]] + self.vertices.tolist()
        else:
            return self.vertices.tolist()

class Experiment:
    __slots__ = ("stripped_faces", "start_vertex", "start_face", "strips")

    def __init__(self, start_vertex, start_face):
        self.stripped_faces = set()
        self.start_vertex = start_vertex
        self.start_face = start_face
        self.strips = []

    def build(self):
        """Build main strip and then attempt to grow adjacent strips."""
        main_strip = TriangleStrip(stripped_faces=self.stripped_faces)
        main_strip.build(self.start_vertex, self.start_face)
        self.strips.append(main_strip)

        num_faces = len(main_strip.faces)
        if num_faces == 0:
            return

        # Pick central face(s) for adjacency growth
        idx = num_faces >> 1
        fallback = {1: [0], 2: [0, 1], 3: [0, 1, 2], 4: [idx, idx + 1]}
        candidates = fallback.get(num_faces, [idx, idx + 1])

        for face_index in candidates:
            self.build_adjacent(main_strip, face_index)

    def build_adjacent(self, strip, face_index):
        """Attempt to grow a new strip adjacent to the current strip."""
        if face_index >= len(strip.faces) - 1:
            return False  # out of bounds

        face = strip.faces[face_index]
        opp_vert = strip.vertices[face_index + 1]
        other_face = strip.get_unstripped_adjacent_face(face, opp_vert)
        if not other_face:
            return False

        # Determine winding
        winding = strip.reversed_ ^ bool(face_index & 1)

        other_strip = TriangleStrip(stripped_faces=self.stripped_faces)
        start_vert = strip.vertices[face_index] if winding else strip.vertices[face_index + 2]
        new_index = other_strip.build(start_vert, other_face)

        self.strips.append(other_strip)

        new_len = len(other_strip.faces)
        if new_len == 0:
            return True  # early exit, nothing to build further

        if new_index > (new_len >> 1):
            self.build_adjacent(other_strip, new_index - 1)
        elif new_index < new_len - 1:
            self.build_adjacent(other_strip, new_index + 1)

        return True

class ExperimentSelector:
    __slots__ = ("best_score", "best_experiment")

    def __init__(self):
        self.clear()

    def update(self, experiment):
        """Update best experiment based on average face count per strip."""
        strips = experiment.strips
        if not strips:
            return  # avoid divide-by-zero

        # Precompute values
        total_faces = sum(len(s.faces) for s in strips)
        score = total_faces / len(strips)

        if score > self.best_score:
            self.best_score = score
            self.best_experiment = experiment

    def clear(self):
        self.best_score = float("-inf")
        self.best_experiment = None

class TriangleStripifier:
    __slots__ = ("num_samples", "mesh")

    def __init__(self, mesh):
        self.num_samples = 10
        self.mesh = mesh

    @staticmethod
    def sample(population, k):
        """Efficient deterministic sampling without list allocation."""
        n = len(population)
        if k >= n:
            return population
        step = (n - 1) / (k - 1) if k > 1 else 0
        return [population[int(i * step)] for i in range(k)]

    def find_all_strips(self):
        """Efficient triangle strip generation from a mesh."""
        if not getattr(self.mesh, "faces", None):
            return []

        all_strips = []
        selector = ExperimentSelector()
        mesh_faces = self.mesh.faces
        unstripped_faces = {i for i, f in enumerate(mesh_faces) if f}
        experiments = []

        while unstripped_faces:
            face_list = list(unstripped_faces)
            face_indices = self.sample(face_list, min(self.num_samples, len(unstripped_faces)))
            experiments.clear()

            # Collect candidate experiments
            for face_idx in face_indices:
                face = mesh_faces[face_idx]
                if face is None:
                    continue
                verts = face.verts
                experiments.extend(Experiment(v, face) for v in verts)

            # Evaluate experiments
            for experiment in experiments:
                experiment.build()
                selector.update(experiment)

            best = selector.best_experiment
            if best is None:
                break

            unstripped_faces.difference_update(best.stripped_faces)

            # Apply result
            for strip in best.strips:
                all_strips.append(strip.get_strip())
                for face in strip.faces:
                    self.mesh.discard_face(face)

            selector = ExperimentSelector()  # Clear by replacing

        return all_strips


if __name__=='__main__':
    import doctest
    doctest.testmod()
