from weakref import WeakSet
import operator
class Edge:
    __slots__ = ("verts", "faces", "__weakref__")  # for Edge

    def __init__(self, ev0, ev1):
        if ev0 == ev1:
            raise ValueError("Degenerate edge.")
        self.verts = (ev0, ev1)
        self.faces = WeakSet()

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
        if self.faces[face.index] is None:
            return  # Face already discarded
        self.faces[face.index] = None
        for i, adj_set in enumerate(face.adjacent_faces):
            for other_face in list(adj_set):  # copy to avoid mutation during iteration
                try:
                    idx_in_other = other_face.verts.index(face.verts[(i + 2) % 3])
                    other_face.adjacent_faces[idx_in_other].discard(face)
                except (ValueError, IndexError):
                    pass  # Face already GC'd or not present
