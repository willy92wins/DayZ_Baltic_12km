"""Read and write Terrain Builder's editable WRP (0WZD) as exported by DayZ Tools.

Layout (BI wiki "Wrp File Format - 8WVR", section 0WZD; as read by tools/narva/inspect_wrp.py):
  '0WZD', u32 texture grid x, u32 texture grid z, u32 terrain grid x, u32 terrain grid z, f32 texture cell size
  f32 heights[terrain z][terrain x]   (row 0 = south)
  u16 material index[texture z][texture x]
  u32 material count, then per material: (u32 length, bytes)* terminated by u32 0
  objects: f32 matrix[12] (3x3 rotation, then position x, y, z), u32 id, u32 name length, name bytes
  terminator: f32 matrix[12], u32 id, u32 0
"""
import struct

import numpy as np


def read(path):
    b = open(path, "rb").read()
    magic, tx, tz, nx, nz, cell = struct.unpack_from("<4s4If", b)
    assert magic == b"0WZD", magic
    o = 24
    heights = np.frombuffer(b, dtype="<f4", count=nx * nz, offset=o).reshape(nz, nx)
    o += nx * nz * 4
    mat_start = o
    o += tx * tz * 2
    n = struct.unpack_from("<I", b, o)[0]
    o += 4
    for _ in range(n):
        while True:
            length = struct.unpack_from("<I", b, o)[0]
            o += 4
            if not length:
                break
            o += length
    obj_start = o
    objects = []
    while True:
        start = o
        matrix = struct.unpack_from("<12f", b, o)
        o += 48
        ident, length = struct.unpack_from("<2I", b, o)
        o += 8
        if not length:
            terminator = b[start:o]
            break
        raw = b[o:o + length]
        o += length
        objects.append({"matrix": list(matrix), "id": ident, "raw_name": raw, "name": raw.decode("ascii").rstrip("\0"),
                        "bytes": b[start:o]})
    assert o == len(b), ("trailing bytes", o, len(b))
    return {"header": b[:24], "dims": (tx, tz, nx, nz, cell), "heights": heights, "materials": b[mat_start:obj_start],
            "objects": objects, "terminator": terminator, "size": len(b)}


def object_record(matrix, ident, raw_name):
    return struct.pack("<12f", *matrix) + struct.pack("<2I", ident, len(raw_name)) + raw_name


def write(path, header, heights, materials, object_records, terminator):
    nz, nx = heights.shape
    assert struct.unpack_from("<4s4If", header)[3:5] == (nx, nz)
    with open(path, "wb") as f:
        f.write(header)
        f.write(np.ascontiguousarray(heights, dtype="<f4").tobytes())
        f.write(materials)
        for rec in object_records:
            f.write(rec)
        f.write(terminator)
