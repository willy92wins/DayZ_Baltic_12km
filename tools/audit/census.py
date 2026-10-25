"""Size census of directory trees without following reparse points (junctions/symlinks)."""
import os
import sys
import json

REPARSE = 0x400


def census(root):
    files = 0
    total = 0
    reparse = []
    stack = [root]
    while stack:
        d = stack.pop()
        try:
            it = os.scandir(d)
        except OSError as e:
            reparse.append({"path": d, "error": str(e)})
            continue
        with it:
            for e in it:
                st = e.stat(follow_symlinks=False)
                if getattr(st, "st_file_attributes", 0) & REPARSE or e.is_symlink():
                    reparse.append({"path": e.path})
                    continue
                if e.is_dir(follow_symlinks=False):
                    stack.append(e.path)
                else:
                    files += 1
                    total += st.st_size
    return {"root": root, "files": files, "bytes": total, "gib": round(total / 2**30, 3), "reparse_points": reparse}


if __name__ == "__main__":
    out = [census(p) for p in sys.argv[1:]]
    print(json.dumps(out, indent=1, ensure_ascii=False))
