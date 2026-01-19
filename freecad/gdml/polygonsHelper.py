from FreeCAD import Vector
from typing import List, Optional

# ---------- Helpers ----------
def polygon_area_signed(vecs):
    """Signed area of polygon given as list of FreeCAD.Vector.
       >0 for CCW, <0 for CW, 0 if degenerate."""
    area = 0.0
    n = len(vecs)
    for i in range(n):
        v0 = vecs[i]
        v1 = vecs[(i + 1) % n]
        area += v0.x * v1.y - v1.x * v0.y
    return 0.5 * area


def is_point_in_triangle(p, a, b, c, eps=1e-12):
    """Check if point p (Vector) is inside or on triangle (a,b,c) using barycentric test."""
    v0 = c - a
    v1 = b - a
    v2 = p - a

    dot00 = v0.x * v0.x + v0.y * v0.y
    dot01 = v0.x * v1.x + v0.y * v1.y
    dot02 = v0.x * v2.x + v0.y * v2.y
    dot11 = v1.x * v1.x + v1.y * v1.y
    dot12 = v1.x * v2.x + v1.y * v2.y

    denom = dot00 * dot11 - dot01 * dot01
    if abs(denom) < eps:
        return False  # Degenerate triangle

    inv_denom = 1.0 / denom
    u = (dot11 * dot02 - dot01 * dot12) * inv_denom
    v = (dot00 * dot12 - dot01 * dot02) * inv_denom
    w = 1.0 - u - v

    # Allow small negatives due to floating‑point rounding
    return (u >= -eps) and (v >= -eps) and (w >= -eps)


def is_convex(prev_v, curr_v, next_v, orientation_ccw, eps=1e-12):
    """
    Test if vertex curr_v is convex given neighbors prev_v and next_v.
    orientation_ccw: True if polygon is CCW, False if CW.
    All vectors are FreeCAD.Vector with z ~ 0.
    """
    v1 = curr_v - prev_v
    v2 = next_v - prev_v
    cross_z = v1.x * v2.y - v1.y * v2.x
    if orientation_ccw:
        return cross_z > eps
    else:
        return cross_z < -eps


# ---------- Main triangulation (returns triangles as Vectors) ----------

def triangulate_polygon_earclip(vecs):
    """
    Triangulate a simple polygon (possibly concave) using ear clipping.

    vecs: list of FreeCAD.Vector vertices, in order (CW or CCW), not repeated first/last.
          Assumed to lie in plane z=0 (XY plane).

    Returns:
        triangles: list of (v0, v1, v2) where each v* is a FreeCAD.Vector.
    Raises:
        ValueError if polygon is too small, degenerate, or appears not simple.
    """
    n = len(vecs)
    if n < 3:
        raise ValueError("Need at least 3 points to form a polygon")
    if n == 3:
        return [(vecs[0], vecs[1], vecs[2])]

    # Determine orientation from signed area
    area = polygon_area_signed(vecs)
    if abs(area) < 1e-16:
        raise ValueError("Degenerate polygon (area ~ 0)")
    orientation_ccw = (area > 0.0)

    # Work on a list of indices referencing vecs
    V = list(range(n))
    tri_indices = []

    max_iter = 5 * n * n
    iters = 0

    while len(V) > 3 and iters < max_iter:
        iters += 1
        ear_found = False

        for i in range(len(V)):
            i_prev = V[(i - 1) % len(V)]
            i_curr = V[i]
            i_next = V[(i + 1) % len(V)]

            p_prev = vecs[i_prev]
            p_curr = vecs[i_curr]
            p_next = vecs[i_next]

            # 1. convex corner?
            if not is_convex(p_prev, p_curr, p_next, orientation_ccw):
                continue

            # 2. no other vertex inside this ear?
            a, b, c = p_prev, p_curr, p_next
            ear_ok = True
            for j in V:
                if j in (i_prev, i_curr, i_next):
                    continue
                if is_point_in_triangle(vecs[j], a, b, c):
                    ear_ok = False
                    break

            if not ear_ok:
                continue

            # 3. ear found, clip it
            tri_indices.append((i_prev, i_curr, i_next))
            del V[i]
            ear_found = True
            break

        if not ear_found:
            raise ValueError(
                "No ear found; polygon may be self‑intersecting "
                "or numerically problematic"
            )

    if len(V) == 3:
        tri_indices.append((V[0], V[1], V[2]))
    elif len(V) > 3:
        raise ValueError("Ear clipping failed to reduce polygon to triangles")

    # Convert index triples to Vector triples
    triangles = [[vecs[i], vecs[j], vecs[k]] for (i, j, k) in tri_indices]
    return triangles




# ------------------------------------------------------------
# Assumptions about your Vector class:
#   - has __eq__(self, other)
#   - has __sub__(self, other)
#   - has __add__(self, other)
#   - has cross(self, other) -> Vector (3D cross product)
#   - attributes .x, .y, .z (z will be 0 for all polygon vertices)
#
# Below I include:
#   1) Ear-clipping triangulation using Vector
#   2) Convex decomposition (triangulate + greedy merging)
# ------------------------------------------------------------

# =========================
# Basic geometry helpers
# =========================

def cross_z(o: Vector, a: Vector, b: Vector) -> float:
    """
    Oriented 2D cross product using the z-component of 3D cross:
    returns z-component of (a - o) x (b - o).
    > 0 → OAB is CCW in the x-y plane.
    """
    oa = a - o
    ob = b - o
    return (oa.cross(ob)).z


def is_convex_polygon(poly: List[Vector]) -> bool:
    """
    Check if a simple polygon (CCW) is convex.
    For a CCW polygon, all consecutive edge cross products must be >= 0.
    """
    n = len(poly)
    if n < 3:
        return False

    for i in range(n):
        a = poly[i]
        b = poly[(i + 1) % n]
        c = poly[(i + 2) % n]
        cr = cross_z(a, b, c)
        if cr < 0:
            return False
    return True


def inner_outer(polygon):
    ''' given a polygon (set of vertexes) in the x-z plane
    return two sets of vertexes, an outer one and an inner one
    Find minz, maxz. All vertexes on the inside have one or more edges to their right.
    All vertexes on the outer have one or more edges to their left

    Assumption: the vertexes are already arranged in CCW in the x-z plane
    '''

    minz = min([v.z for v in polygon])
    maxz = max([v.z for v in polygon])

    istart = 0
    for i, v in enumerate(polygon):
        if v.z == minz:
            istart = i
            break

    n = len(polygon)
    outer = []
    # find the outer vertexes. Since the polygon is arranged in CCW as we
    # climb from minz, we are climbing on the outside
    for i in range(istart, istart+n, 1):
        v = polygon[i % n]
        if v.z < maxz:
            outer.append(v)
        else:
            outer.append(v)
            break

    istart = 0
    for i, v in enumerate(polygon):
        if v.z == maxz:
            istart = i
            break

    # find the inner vertexes. Since the polygon is arranged in CCW as we
    # descend from maxz, we are descending on the inside
    # note that both outer an inner polygon share the minz and maxz vertexes
    inner = []
    for i in range(istart, istart+n, 1):
        v = polygon[i % n]
        if v.z > minz:
            inner.append(v)
        else:
            inner.append(v)
            break

    return inner, outer


def convex_hull(verts):
    '''
    My first attempt at returning the convex hull of a a polygon: Note we already have a CCW polygon,
    the points are NOT arbitrary points in space.
    :returns: a list of lists of vertexes, The first list is the convex hull, the remaining lists are edge
    triangle vertexes that have been removed from the hull
    '''

    done = False
    len_previous = len(verts)
    n = len(verts)
    hull = [i for i in range(n)]  # indexes of vertexes that make up the hull. We start with all polygon vertexes
    clipped_triangles = []
    while True:
        iremoved = []
        for i in range(n):
            iprev = (i-1) % n
            inext = (i+1) % n
            v1 = verts[hull[i]] - verts[hull[iprev]]
            v2 = verts[hull[inext]] -verts[hull[i]]
            if (v1.cross(v2)).z < 0:
                iremoved.append(hull[i])
                clipped_triangle = [hull[iprev], hull[i], hull[inext]]
                clipped_triangles.append(clipped_triangle)
        for i in iremoved:
            hull.remove(i)
        if len(hull) == n:
            break
        n = len(hull)

    return [hull, clipped_triangles]








