"""A bounded screen-space CPU rasterizer, not a GPU conformance model."""
from fractions import Fraction
import struct
import zlib

COLORS = {None: (233, 239, 240), "A": (22, 118, 124), "B": (224, 123, 45)}


def edge(a, b, p):
    return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])


def top_left(a, b):
    # y grows down; vertices are normalized to positive signed area.
    return b[1] < a[1] or (b[1] == a[1] and b[0] > a[0])


def validate(width, height, triangles):
    if type(width) is not int or type(height) is not int or not (1 <= width <= 32 and 1 <= height <= 32):
        raise ValueError("grid must be integer 1..32")
    ids = []
    for t in triangles:
        if t["id"] not in ("A", "B") or t["id"] in ids or len(t["vertices"]) != 3:
            raise ValueError("unique A/B triangle with exactly 3 vertices required")
        ids.append(t["id"])
        for x, y, z in t["vertices"]:
            if type(x) is not int or type(y) is not int or not (-32 <= x <= 32 and -32 <= y <= 32):
                raise ValueError("screen coordinate must be integer -32..32")
            if not isinstance(z, str) or not (0 <= Fraction(z) <= 1):
                raise ValueError("depth must be rational string in 0..1")


def render(width, height, triangles, mode="depth"):
    validate(width, height, triangles)
    if mode not in ("depth", "painter"):
        raise ValueError("unknown render mode")
    prepared = []
    for t in triangles:
        vertices = [(x, y, Fraction(z)) for x, y, z in t["vertices"]]
        area = edge(vertices[0], vertices[1], vertices[2])
        if area < 0:
            vertices[1], vertices[2] = vertices[2], vertices[1]
            area = -area
        prepared.append((t["id"], vertices, area))
    pixels = []
    for y in range(height):
        for x in range(width):
            p = (Fraction(2*x+1, 2), Fraction(2*y+1, 2))
            winner, depth, fragments = None, None, []
            for tid, v, area in prepared:
                if area == 0:
                    fragments.append({"triangle": tid, "covered": False, "reason": "degenerate-area-zero"})
                    continue
                edges = [edge(v[i], v[(i+1) % 3], p) for i in range(3)]
                ties = [top_left(v[i], v[(i+1) % 3]) for i in range(3)]
                covered = all(e > 0 or (e == 0 and tie) for e, tie in zip(edges, ties))
                fragment = {"triangle":tid, "covered":covered, "edges":[str(e) for e in edges], "edgeIncludedOnTie":ties}
                if covered:
                    weights = [edges[1]/area, edges[2]/area, edges[0]/area]
                    z = sum(w*vertex[2] for w, vertex in zip(weights, v))
                    passed = mode == "painter" or depth is None or z < depth
                    fragment.update(weights=[str(w) for w in weights], depthExact=str(z), depth=float(z), accepted=passed)
                    if passed:
                        winner, depth = tid, z
                else:
                    fragment["reason"] = "outside-or-exclusive-edge"
                fragments.append(fragment)
            pixels.append({"x":x,"y":y,"center":[str(p[0]),str(p[1])],"owner":winner,"depthExact":str(depth) if depth is not None else None,"depth":float(depth) if depth is not None else None,"rgb":list(COLORS[winner]),"fragments":fragments})
    return {"mode":mode,"width":width,"height":height,"pixels":pixels,"degenerateTriangles":[tid for tid,v,a in prepared if a == 0]}


def png(result):
    # RGB PNG, one byte-filter 0 per row; standard-library-only output encoding.
    w, h = result["width"], result["height"]
    raw = b"".join(b"\0" + bytes(c for p in result["pixels"][y*w:(y+1)*w] for c in p["rgb"]) for y in range(h))
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind+data) & 0xffffffff)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w,h,8,2,0,0,0)) + chunk(b"IDAT",zlib.compress(raw)) + chunk(b"IEND",b"")
