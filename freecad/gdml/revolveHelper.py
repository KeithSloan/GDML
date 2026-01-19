
import math

# ---------- 2D helpers ----------

def polygon_centroid_xz(points):
    """Approximate centroid of a simple polygon in XZ plane (CCW or CW)."""
    n = len(points)
    if n == 0:
        raise ValueError("Empty polygon")
    if n == 1:
        return points[0]
    if n == 2:
        return (0.5*(points[0][0] + points[1][0]),
                0.5*(points[0][1] + points[1][1]))

    A = 0.0
    Cx = 0.0
    Cz = 0.0
    for (x0, z0), (x1, z1) in zip(points, points[1:] + points[:1]):
        cross = x0 * z1 - x1 * z0
        A += cross
        Cx += (x0 + x1) * cross
        Cz += (z0 + z1) * cross
    A *= 0.5
    if abs(A) < 1e-16:
        # Degenerate-ish; fallback to average
        x_mean = sum(p[0] for p in points) / n
        z_mean = sum(p[1] for p in points) / n
        return x_mean, z_mean

    Cx /= (6.0 * A)
    Cz /= (6.0 * A)
    return Cx, Cz


def edge_normal_2d(p0, p1):
    """
    2D outward normal (nx, nz) for edge p0->p1 in XZ plane,
    assuming polygon is CCW.
    """
    x0, z0 = p0
    x1, z1 = p1
    dx = x1 - x0
    dz = z1 - z0
    length = math.hypot(dx, dz)
    if length == 0.0:
        return 0.0, 0.0
    nx = dz / length
    nz = -dx / length
    return nx, nz


# ---------- Interior 3D point for the swept solid ----------

def interior_3d_point_from_profile(profile_xz, phi):
    """
    Given a 2D profile polygon in XZ (possibly concave), find a 3D point
    that lies in the interior of its solid of revolution.
    """
    if profile_xz[0] == profile_xz[-1]:
        pts = profile_xz[:-1]
    else:
        pts = profile_xz

    cx, cz = polygon_centroid_xz(pts)
    theta_mid = 0.5 * phi
    x_int = cx * math.cos(theta_mid)
    y_int = cx * math.sin(theta_mid)
    z_int = cz
    return x_int, y_int, z_int


# ---------- Classify each profile segment ----------

def classify_profile_edges(profile_xz, eps=1e-9):
    """
    For one closed polygon (possibly concave), revolved about Z by angle phi,
    determine for each 2D edge:

      - what 3D surface type it becomes: 'z_plane', 'cylinder', 'cone'
      - geometric parameters you may need (z_const, R, p0, p1, line normal)

    Returns:
      segments_info: list of dicts, one per segment
    """
    # Ensure closed
    if profile_xz[0] != profile_xz[-1]:
        pts = profile_xz + [profile_xz[0]]
    else:
        pts = list(profile_xz)

    segments_info = []

    # Precompute centroid for cone sign in 2D
    cx, cz = polygon_centroid_xz(pts[:-1])

    for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
        dx = x1 - x0
        dz = z1 - z0

        if abs(dz) < eps and abs(dx) > eps:
            # Horizontal edge -> plane z = z0
            z_const = z0
            # Implicit f = z - z_const

            segments_info.append({
                'type': 'z_plane',
                'z': z_const,
                'p0': (x0, z0),
                'p1': (x1, z1)
            })

        elif abs(dx) < eps and abs(dz) > eps:
            # Vertical edge -> cylinder radius |x0|
            x_const = x0
            R = abs(x_const)
            if R < eps:
                # Edge exactly on axis: special (often a plane through axis).
                # Handle as needed in your own code.
                continue

            segments_info.append({
                'type': 'cylinder',
                'R': R,
                'p0': (x0, z0),
                'p1': (x1, z1),
            })

        else:
            # Slanted edge -> cone (or plane through axis)
            # Use 2D geometry to determine which side is interior.
            nx, nz = edge_normal_2d((x0, z0), (x1, z1))

            segments_info.append({
                'type': 'cone',
                'p0': (x0, z0),
                'p1': (x1, z1),
                'nx_2d': nx,
                'nz_2d': nz
            })

    return segments_info


# ---------- Top-level: classify one closed polygon ----------

def classify_revolved_polygon(profile_xz, eps=1e-9):
    """
    Given a single closed polygon (possibly concave) in XZ (CCW) and a
    classify all surfaces for the corresponding
    solid of revolution.

    Returns:
      segments_info: list of dicts for each profile edge:
         - 'type': 'z_plane' | 'cylinder' | 'cone'
         - geometry params (z, R, p0,p1 or 2D line data)
    """
    segments_info = classify_profile_edges(profile_xz, eps=eps)
    return segments_info
'''
or each entry in `segments_info`:
  - If `type == 'z_plane'`:
    - You already know how to emit a `<plane>` with `z = info['z']`.
    - `inside_is_negative` tells you whether the “inside” side is `f(z) <= 0` (your “−” side) or `f(z) >= 0`.
  - If `type == 'cylinder'`:
    - Emit a `<cylinder>` of radius `R = info['R']` around the z‑axis.
    - `inside_is_negative` decides whether `r <= R` or `r >= R` is inside.
  - If `type == 'cone'`:
    - Use your own line‑segment‑to‑cone logic on `p0,p1`,


The region for that one polygon’s solid of revolution is simply:

- The intersection of **all** those half‑spaces (every segment’s surface + radial planes, if any), with the sign given by `inside_is_negative`.

That holds whether the polygon is convex or concave, as long as it’s a single, simple loop (no self‑intersections, no holes). 
'''