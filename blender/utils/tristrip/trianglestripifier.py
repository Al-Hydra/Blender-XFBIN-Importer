import numpy as np

class TriangleStrip(object):
    """A heavily specialized oriented strip of faces."""

    def __init__(self, stripped_faces=None, faces=None, vertices=None, reversed_=False):
        self.faces = faces if faces is not None else []
        self.vertices = vertices if vertices is None else (np.array(vertices, dtype=np.int32) if not isinstance(vertices, np.ndarray) else vertices)
        self.reversed_ = reversed_
        self.stripped_faces = stripped_faces if stripped_faces is not None else set()

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

        # Use lists for efficient building, convert to numpy at end
        forward_verts = []
        backward_verts = []

        while next_face:
            self.stripped_faces.add(next_face.index)
            count += 1

            if count & 1:
                if forward:
                    pv0 = pv1
                    pv1 = next_face.get_next_vertex(pv0)
                    forward_verts.append(pv1)
                    self.faces.append(next_face)
                else:
                    pv0 = pv2
                    pv2 = next_face.get_next_vertex(pv1)
                    backward_verts.append(pv2)
                    self.faces.insert(0, next_face)
                    self.reversed_ = not self.reversed_
            else:
                if forward:
                    pv0 = pv2
                    pv2 = next_face.get_next_vertex(pv1)
                    forward_verts.append(pv2)
                    self.faces.append(next_face)
                else:
                    pv0 = pv1
                    pv1 = next_face.get_next_vertex(pv0)
                    backward_verts.append(pv1)
                    self.faces.insert(0, next_face)
                    self.reversed_ = not self.reversed_

            next_face = self.get_unstripped_adjacent_face(next_face, pv0)
        
        # Efficiently combine arrays
        if backward_verts or forward_verts:
            if isinstance(self.vertices, np.ndarray):
                base_verts = self.vertices.tolist()
            else:
                base_verts = list(self.vertices) if self.vertices else []
            self.vertices = np.array(backward_verts[::-1] + base_verts + forward_verts, dtype=np.int32)
        elif not isinstance(self.vertices, np.ndarray):
            self.vertices = np.array(self.vertices, dtype=np.int32)
        
        return count

    def build(self, start_vertex, start_face):
        self.faces.clear()
        self.reversed_ = False

        v0 = start_vertex
        v1 = start_face.get_next_vertex(v0)
        v2 = start_face.get_next_vertex(v1)

        self.stripped_faces.add(start_face.index)
        self.faces.append(start_face)
        self.vertices = [v0, v1, v2]  # Start as list for efficient building

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
        """Efficient deterministic sampling supporting both lists and sets."""
        if isinstance(population, (list, tuple)):
            n = len(population)
            if k >= n:
                return population
            step = (n - 1) / (k - 1) if k > 1 else 0
            return [population[int(i * step)] for i in range(k)]
        else:
            # For sets, convert only sampled portion
            pop_list = list(population)
            n = len(pop_list)
            if k >= n:
                return pop_list
            step = (n - 1) / (k - 1) if k > 1 else 0
            return [pop_list[int(i * step)] for i in range(k)]

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
            # Sample from sorted face list for deterministic results
            sorted_faces = sorted(unstripped_faces)
            face_indices = self.sample(sorted_faces, min(self.num_samples, len(unstripped_faces)))
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

            # Debug: print info about best experiment
            if len(unstripped_faces) > 9000:
                print(f"Iteration: {len(unstripped_faces)} unstripped faces, {len(experiments)} experiments tested, best score: {selector.best_score:.2f}, best has {len(best.strips)} strips covering {len(best.stripped_faces)} faces")

            unstripped_faces.difference_update(best.stripped_faces)

            # Apply result
            for strip in best.strips:
                all_strips.append(strip.get_strip())
                for face in strip.faces:
                    self.mesh.discard_face(face)

            selector = ExperimentSelector()  # Clear by replacing

        return all_strips
