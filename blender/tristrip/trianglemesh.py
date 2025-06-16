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

# modified from:

# http://techgame.net/projects/Runeblade/browser/trunk/RBRapier/RBRapier/Tools/Geometry/Analysis/TriangleMesh.py?rev=760

# original license:

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~ License
# ~
# - The RuneBlade Foundation library is intended to ease some
# - aspects of writing intricate Jabber, XML, and User Interface (wxPython, etc.)
# - applications, while providing the flexibility to modularly change the
# - architecture. Enjoy.
# ~
# ~ Copyright (C) 2002  TechGame Networks, LLC.
# ~
# ~ This library is free software; you can redistribute it and/or
# ~ modify it under the terms of the BSD style License as found in the
# ~ LICENSE file included with this distribution.
# ~
# ~ TechGame Networks, LLC can be reached at:
# ~ 3578 E. Hartsel Drive #211
# ~ Colorado Springs, Colorado, USA, 80920
# ~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~ Imports
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

import operator # itemgetter
from weakref import WeakSet
from collections import defaultdict

class Edge:
    __slots__ = ("verts", "faces", "__weakref__")  # for Edge

    def __init__(self, ev0, ev1):
        if ev0 == ev1:
            raise ValueError("Degenerate edge.")
        self.verts = (ev0, ev1)
        self.faces = WeakSet()

    def __repr__(self):
        return f"Edge{self.verts}"

    def __eq__(self, other):
        if not isinstance(other, Edge):
            return NotImplemented
        return self.verts == other.verts

    def __hash__(self):
        return hash(self.verts)


class Face:
    __slots__ = ("verts", "index", "adjacent_faces", "__weakref__")  # for Face

    def __init__(self, v0, v1, v2):
        if v0 == v1 or v1 == v2 or v2 == v0:
            raise ValueError("Degenerate face.")

        verts = (v0, v1, v2)
        min_index = verts.index(min(verts))
        self.verts = verts[min_index:] + verts[:min_index]

        self.index = None
        self.adjacent_faces = (WeakSet(), WeakSet(), WeakSet())

    def __repr__(self):
        return f"Face{self.verts}"

    def __eq__(self, other):
        if not isinstance(other, Face):
            return NotImplemented
        return self.verts == other.verts

    def __hash__(self):
        return hash(self.verts)

    def get_next_vertex(self, vi):
        idx = self.verts.index(vi)
        return self.verts[(idx + 1) % 3]

    def get_adjacent_faces(self, vi):
        idx = self.verts.index(vi)
        return self.adjacent_faces[idx]


class Mesh:
    __slots__ = ("_faces", "_edges", "faces")

    def __init__(self, faces=None, lock=True):
        self._faces = {}
        self._edges = {}
        if faces:
            for v0, v1, v2 in faces:
                self.add_face(v0, v1, v2)
            if lock:
                self.lock()

    def _add_edge(self, face, pv0, pv1):
        key = (pv0, pv1)
        edge = self._edges.get(key)
        if not edge:
            edge = Edge(pv0, pv1)
            self._edges[key] = edge
        edge.faces.add(face)

        # Try to find reverse edge
        other = self._edges.get((pv1, pv0))
        if other:
            pv2 = face.get_next_vertex(pv1)
            for of in other.faces:
                opv2 = of.get_next_vertex(pv0)
                face.get_adjacent_faces(pv2).add(of)
                of.get_adjacent_faces(opv2).add(face)

    def add_face(self, v0, v1, v2):
        face = Face(v0, v1, v2)
        verts = face.verts
        if verts in self._faces:
            return self._faces[verts]

        self._faces[verts] = face
        self._add_edge(face, v0, v1)
        self._add_edge(face, v1, v2)
        self._add_edge(face, v2, v0)
        return face

    def lock(self):
        """Sort and freeze the face list."""
        items = sorted(self._faces.items(), key=operator.itemgetter(0))
        self.faces = []
        for i, (_, face) in enumerate(items):
            face.index = i
            self.faces.append(face)
        del self._faces
        del self._edges

    def discard_face(self, face):
        """Remove a face from the mesh and clean up all adjacency references."""
        self.faces[face.index] = None
        for i, adj_set in enumerate(face.adjacent_faces):
            for other_face in list(adj_set):  # copy to avoid mutation during iteration
                try:
                    idx_in_other = other_face.verts.index(face.verts[(i + 2) % 3])
                    other_face.adjacent_faces[idx_in_other].discard(face)
                except (ValueError, IndexError):
                    pass  # Face already GC'd or not present


    def __repr__(self):
        if hasattr(self, "faces"):
            return f"Mesh(faces={[f.verts for f in self.faces if f]})"
        elif self._faces:
            return f"Mesh(faces={[verts for verts in sorted(self._faces)]}, lock=False)"
        else:
            return "Mesh()"

if __name__ == '__main__':
    import doctest
    doctest.testmod()
