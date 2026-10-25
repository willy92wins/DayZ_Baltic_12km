"""Copy directory trees into an archive with robocopy and verify every file by SHA-256 on both sides.

Usage:  python secure_copy.py plan.json [--dry-run]

plan.json = {"dest_root": "E:\\...", "jobs": [{"name": "...", "src": "C:\\...", "dst": "rel\\path"}]}

Rules:
  * Reparse points (junctions, symlinks) are never followed nor copied; they are listed in the manifest.
  * A job destination must not exist beforehand: every archive is a fresh copy.
  * Verdict PASS only if robocopy exit code < 8, every source file exists at the destination with the
    same size and SHA-256, and the destination holds no extra files.
Writes <dest_root>/_manifests/<job>.json (per-file rel/size/sha256 + verdict) and <dest_root>/_manifests/summary.json.
"""
import concurrent.futures as cf
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

REPARSE = 0x400
CHUNK = 8 * 2**20
WORKERS = 8


def xp(path):
    path = os.path.abspath(path)
    return path if path.startswith("\\\\?\\") else "\\\\?\\" + path


def walk(root, exclude=()):
    files, reparse = [], []
    base = xp(root)
    skip = {e.lower() for e in exclude}
    stack = [base]
    while stack:
        d = stack.pop()
        with os.scandir(d) as it:
            for e in it:
                st = e.stat(follow_symlinks=False)
                rel = os.path.relpath(e.path, base)
                if (getattr(st, "st_file_attributes", 0) & REPARSE) or e.is_symlink():
                    reparse.append(rel)
                elif e.is_dir(follow_symlinks=False):
                    if rel.lower() not in skip:
                        stack.append(e.path)
                else:
                    files.append((rel, st.st_size))
    return files, reparse


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb", buffering=0) as f:
        while True:
            block = f.read(CHUNK)
            if not block:
                return h.hexdigest()
            h.update(block)


def log(fp, msg):
    line = time.strftime("%H:%M:%S ") + msg
    print(line, flush=True)
    fp.write(line + "\n")
    fp.flush()


def run_job(job, dest_root, manifests, progress):
    name, src = job["name"], job["src"]
    dst = os.path.join(dest_root, job["dst"])
    result = {"name": name, "src": src, "dst": dst, "started": time.strftime("%Y-%m-%dT%H:%M:%S")}
    if os.path.exists(xp(dst)):
        result.update(verdict="FAIL", reason="destination already exists")
        return result
    exclude = job.get("exclude", [])
    files, reparse = walk(src, exclude)
    result.update(files=len(files), bytes=sum(s for _, s in files), skipped_reparse_points=reparse,
                  excluded_dirs=exclude)
    log(progress, f"[{name}] census {len(files)} files, {result['bytes'] / 2**30:.3f} GiB, {len(reparse)} reparse skipped")

    os.makedirs(xp(dst), exist_ok=False)
    rlog = os.path.join(manifests, f"{name}.robocopy.log")
    cmd = ["robocopy", src, dst, "/E", "/XJ", "/COPY:DAT", "/DCOPY:DAT", "/R:2", "/W:2", "/MT:16",
           "/NP", "/NFL", "/NDL", f"/UNILOG:{rlog}"]
    if exclude:
        cmd += ["/XD"] + [os.path.join(src, e) for e in exclude]
    rc = subprocess.run(cmd, capture_output=True).returncode
    result["robocopy_rc"] = rc
    log(progress, f"[{name}] robocopy rc={rc}")

    def check(item):
        rel, size = item
        s, d = os.path.join(xp(src), rel), os.path.join(xp(dst), rel)
        if not os.path.isfile(d):
            return rel, size, None, "missing"
        if os.path.getsize(d) != size:
            return rel, size, None, "size"
        hs = sha256(s)
        return rel, size, hs, ("ok" if sha256(d) == hs else "hash")

    entries, bad = [], []
    done, t0 = 0, time.time()
    with cf.ThreadPoolExecutor(WORKERS) as pool:
        for rel, size, digest, status in pool.map(check, files, chunksize=16):
            done += 1
            if status == "ok":
                entries.append([rel, size, digest])
            else:
                bad.append([rel, size, status])
            if done % 5000 == 0:
                log(progress, f"[{name}] verified {done}/{len(files)} ({time.time() - t0:.0f}s)")

    retried = []
    for rel, size, status in bad:  # one direct re-copy attempt for each failing file
        s, d = os.path.join(xp(src), rel), os.path.join(xp(dst), rel)
        os.makedirs(os.path.dirname(d), exist_ok=True)
        shutil.copy2(s, d)
        hs = sha256(s)
        ok = os.path.getsize(d) == os.path.getsize(s) and sha256(d) == hs
        retried.append([rel, status, "fixed" if ok else "still_bad"])
        if ok:
            entries.append([rel, os.path.getsize(s), hs])
    still_bad = [r for r in retried if r[2] != "fixed"]

    dst_files, _ = walk(dst)
    src_set = {rel for rel, _ in files}
    extras = sorted(rel for rel, _ in dst_files if rel not in src_set)

    verdict = "PASS" if rc < 8 and not still_bad and not extras and len(entries) == len(files) else "FAIL"
    result.update(verdict=verdict, verified=len(entries), retried=retried, extras=extras[:200],
                  finished=time.strftime("%Y-%m-%dT%H:%M:%S"))
    entries.sort()
    with open(os.path.join(manifests, f"{name}.json"), "wb") as f:
        f.write(json.dumps({"job": result, "files": entries}, ensure_ascii=False).encode("utf-8"))
    log(progress, f"[{name}] {verdict}: verified {len(entries)}/{len(files)}, retried {len(retried)}, extras {len(extras)}")
    return result


def main():
    plan = json.load(open(sys.argv[1], encoding="utf-8"))
    dest_root = plan["dest_root"]
    if "--dry-run" in sys.argv:
        for job in plan["jobs"]:
            files, reparse = walk(job["src"], job.get("exclude", []))
            print(f"{sum(s for _, s in files) / 2**30:9.3f} GiB {len(files):8d} files  reparse={len(reparse):3d}  {job['name']}")
        return
    manifests = os.path.join(dest_root, "_manifests")
    os.makedirs(xp(manifests), exist_ok=True)
    with open(os.path.join(manifests, "progress.log"), "a", encoding="utf-8") as progress:
        results = [run_job(job, dest_root, manifests, progress) for job in plan["jobs"]]
    summary = {
        "dest_root": dest_root,
        "verdict": "PASS" if all(r.get("verdict") == "PASS" for r in results) else "FAIL",
        "jobs": [{k: r.get(k) for k in ("name", "verdict", "files", "verified", "bytes", "robocopy_rc", "reason")}
                 | {"skipped_reparse_points": len(r.get("skipped_reparse_points", [])), "extras": len(r.get("extras", []))}
                 for r in results],
    }
    with open(os.path.join(manifests, "summary.json"), "wb") as f:
        f.write(json.dumps(summary, indent=1, ensure_ascii=False).encode("utf-8"))
    print(json.dumps(summary, indent=1, ensure_ascii=False))
    sys.exit(0 if summary["verdict"] == "PASS" else 1)


if __name__ == "__main__":
    main()
