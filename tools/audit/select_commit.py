"""Select text files to commit from git status: untracked + modified, size-capped, binaries and foreign dirs excluded.

Writes:
  commit-paths.nul   NUL-separated pathspec list for `git add --pathspec-from-file --pathspec-file-nul`
  commit-select.json summary (included/excluded by reason, largest exclusions, secret-scan hits)
"""
import collections
import json
import os
import re
import subprocess
import sys

REPO = sys.argv[1]
OUT = sys.argv[2]
CAP = 2 * 2**20  # 2 MiB per text file
EXCLUDED_PREFIXES = ("diagnostics/",)  # marked foreign in the V29 LIVE-STATE
BINARY_EXT = {
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff", ".npz", ".npy",
    ".wrp", ".pbo", ".paa", ".p3d", ".nm", ".zip", ".7z", ".rar", ".exe", ".dll", ".pdf",
    ".v4w", ".v4d", ".dbf", ".shp", ".shx", ".mdmp", ".dmp", ".bin", ".pak", ".ebo", ".bisign",
    ".bikey", ".ogg", ".wss", ".lip", ".rtm", ".pyc", ".sqlite", ".db", ".gpkg", ".pbf", ".nc",
}
SECRET = re.compile(
    r"(?i)(lease_token|session_token|auth_token|access_token|bearer\s+[a-z0-9\-_.=]{20,}|sk-[a-z0-9]{20,}"
    r"|ghp_[a-z0-9]{30,}|github_pat_|xox[bpa]-|password\s*[:=]|steamid|765611\d{11}|activeuser)"
)


def status_entries():
    raw = subprocess.run(
        ["git", "-C", REPO, "status", "--porcelain=v1", "-z", "-uall"],
        capture_output=True, check=True,
    ).stdout.decode("utf-8")
    parts = raw.split("\0")
    i = 0
    while i < len(parts):
        p = parts[i]
        if not p:
            i += 1
            continue
        code, path = p[:2], p[3:]
        if code[0] in "RC":  # rename/copy carries the source path next
            i += 1
        yield code, path
        i += 1


def is_binary(full):
    with open(full, "rb") as f:
        head = f.read(65536)
    if b"\0" in head:
        return True
    try:
        head.decode("utf-8")
    except UnicodeDecodeError as e:
        # tolerate a multibyte sequence cut at the 64 KiB boundary
        if e.start < len(head) - 4:
            try:
                head.decode("cp1252")
            except UnicodeDecodeError:
                return True
    return False


def main():
    include, excluded = [], collections.defaultdict(list)
    for code, path in status_entries():
        full = os.path.join(REPO, path)
        if code.strip() == "D" or not os.path.isfile(full):
            excluded["not_a_file_or_deleted"].append((path, 0))
            continue
        size = os.path.getsize(full)
        ext = os.path.splitext(path)[1].lower()
        if path.startswith(EXCLUDED_PREFIXES):
            excluded["foreign_dir"].append((path, size))
        elif ext in BINARY_EXT:
            excluded["binary_ext"].append((path, size))
        elif size > CAP:
            excluded["text_over_cap"].append((path, size))
        elif is_binary(full):
            excluded["binary_sniff"].append((path, size))
        else:
            include.append((path, size, code))

    # Account identifiers stay out of git history; the files keep their original bytes in the external checkpoint.
    steam = re.compile(r"7656119\d{10}")
    kept = []
    for item in include:
        with open(os.path.join(REPO, item[0]), "r", encoding="utf-8", errors="replace") as f:
            if steam.search(f.read()):
                excluded["contains_steamid"].append((item[0], item[1]))
                continue
        kept.append(item)
    include = kept

    hits = []
    for path, size, _ in include:
        try:
            with open(os.path.join(REPO, path), "r", encoding="utf-8", errors="replace") as f:
                for n, line in enumerate(f, 1):
                    m = SECRET.search(line)
                    if m:
                        hits.append({"path": path, "line": n, "match": m.group(0)[:40], "text": line.strip()[:160]})
        except OSError:
            pass

    by_dir = collections.Counter()
    by_dir_bytes = collections.Counter()
    for path, size, _ in include:
        top = path.split("/")[0]
        by_dir[top] += 1
        by_dir_bytes[top] += size
    summary = {
        "included_files": len(include),
        "included_bytes": sum(s for _, s, _ in include),
        "included_by_top_dir": {k: [by_dir[k], by_dir_bytes[k]] for k in sorted(by_dir)},
        "modified_tracked": [p for p, _, c in include if c.strip() != "??"],
        "excluded_counts": {k: [len(v), sum(s for _, s in v)] for k, v in excluded.items()},
        "excluded_text_over_cap": sorted(excluded["text_over_cap"], key=lambda x: -x[1])[:40],
        "excluded_binary_ext_by_ext": dict(collections.Counter(os.path.splitext(p)[1].lower() for p, _ in excluded["binary_ext"])),
        "excluded_binary_sniff": excluded["binary_sniff"][:40],
        "excluded_foreign": [p for p, _ in excluded["foreign_dir"]],
        "excluded_contains_steamid": [p for p, _ in excluded["contains_steamid"]],
        "secret_scan_hits": hits[:200],
        "secret_scan_hit_count": len(hits),
    }
    with open(os.path.join(OUT, "commit-paths.nul"), "wb") as f:
        f.write(b"\0".join(p.encode("utf-8") for p, _, _ in include) + b"\0")
    with open(os.path.join(OUT, "commit-select.json"), "wb") as f:
        f.write(json.dumps(summary, indent=1, ensure_ascii=False).encode("utf-8"))
    print(json.dumps({k: summary[k] for k in ("included_files", "included_bytes", "included_by_top_dir", "excluded_counts", "secret_scan_hit_count")}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
