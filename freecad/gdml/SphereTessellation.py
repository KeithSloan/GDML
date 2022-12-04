from FreeCAD import Vector
from math import sqrt


class SphereTessellation:
    def __init__(self):
        self.n_vertices = 0
        self.n_faces = 0
        self.n_edges = 0
        self.vertices = []
        self.faces = []

        self._edge_walk = 0
        self._start = []
        self._end = []
        self._midpoint = []

    def search_midpoint(self, index_start, index_end):
        """
        create a vertex on the sphere at the midpoint of vertexes
        with indexes index_start, index_end
        returns: the index of the newly created vertex
        """
        for i in range(self._edge_walk):
            if (
                self._start[i] == index_start and self._end[i] == index_end
            ) or (self._start[i] == index_end and self._end[i] == index_start):

                res = self._midpoint[i]

                # update the arrays
                self._start[i] = self._start[self._edge_walk - 1]
                self._end[i] = self._end[self._edge_walk - 1]
                self._midpoint[i] = self._midpoint[self._edge_walk - 1]
                self._edge_walk -= 1

                return res

        # vertex not in the list, so we add it
        self._start[self._edge_walk] = index_start
        self._end[self._edge_walk] = index_end
        self._midpoint[self._edge_walk] = self.n_vertices

        # create new vertex
        vmid = (self.vertices[index_start] + self.vertices[index_end]) / 2.0
        vmid.normalize()
        self.vertices.append(vmid)

        self.n_vertices += 1
        self._edge_walk += 1

        return self._midpoint[self._edge_walk - 1]

    def subdivide(self):
        self._edge_walk = 0
        self.n_edges = 2 * self.n_vertices + 3 * self.n_faces

        self._start = [0] * self.n_edges
        self._end = [0] * self.n_edges
        self._midpoint = [0] * self.n_edges

        faces_old = self.faces[:]
        self.faces = []

        for f in faces_old:
            a = f[0]
            b = f[1]
            c = f[2]

            ab_midpoint = self.search_midpoint(b, a)
            bc_midpoint = self.search_midpoint(c, b)
            ca_midpoint = self.search_midpoint(a, c)

            self.faces.append([a, ab_midpoint, ca_midpoint])
            self.faces.append([ca_midpoint, ab_midpoint, bc_midpoint])
            self.faces.append([ca_midpoint, bc_midpoint, c])
            self.faces.append([ab_midpoint, b, bc_midpoint])

        self.n_faces = len(self.faces)

    def tessellate(self, ndiv):
        for i in range(ndiv):
            self.subdivide()

        return self.faces, self.vertices

    def output_sphere(self, filename):

        fd = open(filename, "w")
        ##fd.write(f'OFF\n{self.n_vertices} {self.n_faces} {self.n_edges}\n')
        for v in self.vertices:
            fd.write(f"{v.x} {v.y} {v.z}\n")
        ##for f in self.faces:
        ##    fd.write(f'{f[0]} {f[1]} {f[2]}\n')

    def faceCenters(self, normalize=False):
        centers = []
        for f in self.faces:
            c = (
                self.vertices[f[0]] + self.vertices[f[1]] + self.vertices[f[2]]
            ) / 3
            if normalize:
                c.normalize()
            centers.append(c)
        return centers


class TetraTessellation(SphereTessellation):
    def __init__(self):
        super().__init__()
        sqrt3 = 1 / sqrt(3.0)
        self.vertices = [
            Vector(sqrt3, sqrt3, sqrt3),
            Vector(-sqrt3, -sqrt3, sqrt3),
            Vector(-sqrt3, sqrt3, -sqrt3),
            Vector(sqrt3, -sqrt3, -sqrt3),
        ]

        self.faces = [[0, 2, 1], [0, 1, 3], [2, 3, 1], [3, 2, 0]]

        self.n_vertices = 4
        self.n_faces = 4
        self.n_edges = 6


class OctahedronTessellation(SphereTessellation):
    def __init__(self):
        super().__init__()
        self.vertices = [
            Vector(0.0, 0.0, -1.0),
            Vector(1.0, 0.0, 0.0),
            Vector(0.0, -1.0, 0.0),
            Vector(-1.0, 0.0, 0.0),
            Vector(0.0, 1.0, 0.0),
            Vector(0.0, 0.0, 1.0),
        ]

        self.faces = [
            [0, 1, 2],
            [0, 2, 3],
            [0, 3, 4],
            [0, 4, 1],
            [5, 2, 1],
            [5, 3, 2],
            [5, 4, 3],
            [5, 1, 4],
        ]

        self.n_vertices = 6
        self.n_faces = 8
        self.n_edges = 12


class IcosahedronTesselltion(SphereTessellation):
    def __init__(self):
        super().__init__()
        t = (1 + sqrt(5)) / 2
        tau = t / sqrt(1 + t * t)
        one = 1 / sqrt(1 + t * t)

        self.vertices = [
            Vector(tau, one, 0.0),
            Vector(-tau, one, 0.0),
            Vector(-tau, -one, 0.0),
            Vector(tau, -one, 0.0),
            Vector(one, 0.0, tau),
            Vector(one, 0.0, -tau),
            Vector(-one, 0.0, -tau),
            Vector(-one, 0.0, tau),
            Vector(0.0, tau, one),
            Vector(0.0, -tau, one),
            Vector(0.0, -tau, -one),
            Vector(0.0, tau, -one),
        ]

        self.faces = [
            [4, 8, 7],
            [4, 7, 9],
            [5, 6, 11],
            [5, 10, 6],
            [0, 4, 3],
            [0, 3, 5],
            [2, 7, 1],
            [2, 1, 6],
            [8, 0, 11],
            [8, 11, 1],
            [9, 10, 3],
            [9, 2, 10],
            [8, 4, 0],
            [11, 0, 5],
            [4, 9, 3],
            [5, 3, 10],
            [7, 8, 1],
            [6, 1, 11],
            [7, 2, 9],
            [6, 10, 2],
        ]

        self.n_vertices = 12
        self.n_faces = 20
        self.n_edges = 30


#    if sys.argv[1] == "-t":
#        tesselator = TetraTessellation()
#    if sys.argv[1] == "-o":
#        tesselator = OctahedronTessellation()
#    if sys.argv[1] == "-i":
#        tesselator = IcosahedronTesselltion()

#    nsub = int(sys.argv[2])
#    for i in range(nsub):
#        tesselator.subdivide()

#    tesselator.output_sphere(sys.argv[3])
