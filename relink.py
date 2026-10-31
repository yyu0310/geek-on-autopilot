#!/usr/bin/env python3
"""relink.py: repair broken Markdown relative links after a folder move or rename.

Why it exists: when a move changes folder depth (a subfolder moves up or down a
level, or a folder is renamed and then moved back), plain string replacement cannot
get the number of ../ right. This script recomputes the relative paths.

It repairs both kinds of breakage:
  1. Links from other files to the moved thing: the link points at the old location,
     so it is rewritten to the new location.
  2. Links from the moved files to the outside: the file changed location, so its
     relative links no longer resolve. The old location is used to find what each
     link originally pointed at, and the path is recomputed from the new location.
A link is changed only if it is broken now and resolves after the change. Links that
already work, and links that stay broken, are left alone (the latter are listed in the
report). The original style is kept: <...> links keep spaces, bare links use %20.

Usage:
    relink.py --root DIR --map "OLD_ABS=NEW_ABS" [--map ...] [--also FILE ...] [--dry-run]
    relink.py --root DIR --check       report broken links only, change nothing
    relink.py --selftest

Exit codes:
  0  success (with --check: zero broken links)
  3  --root does not exist
  4  --check found broken links
"""
import argparse
import os
import pathlib
import re
import sys
import tempfile
import urllib.parse

LINK = re.compile(r"\]\((<)?([^)>\n]+?)(>)?\)")
SKIP = re.compile(r"^(https?:|mailto:|#|vscode:|file:)")


SKIP_DIRS = {"node_modules", ".git"}


def files_under(root, also=()):
    out = [p for p in root.rglob("*.md")
           if not p.name.startswith("._") and not (SKIP_DIRS & set(p.relative_to(root).parts))]
    return out + [pathlib.Path(a) for a in also]


def read_md(path):
    """Read as UTF-8; bytes that are not valid are replaced, so a stray binary file cannot crash the run."""
    return path.read_text(encoding="utf-8", errors="replace")


def remap(path, maps):
    """If an absolute path sits under an old folder, return the matching path under the new one."""
    for old, new in maps:
        try:
            return new / path.relative_to(old)
        except ValueError:
            continue
    return None


def unmap(path, maps):
    """Reverse of remap: from a new location back to the old one (for files that were moved)."""
    return remap(path, [(n, o) for o, n in maps])


def fix_file(f, maps, dry):
    s = read_md(f)
    fixed, still = 0, []

    def sub(m):
        nonlocal fixed
        lt, u, gt = m.group(1), m.group(2), m.group(3)
        if SKIP.match(u):
            return m.group(0)
        raw = urllib.parse.unquote(u)
        path, hashpart, frag = raw.partition("#")
        if not path or (f.parent / path).exists():
            return m.group(0)
        target = pathlib.Path(os.path.normpath(f.parent / path))
        new = remap(target, maps)
        if new is None or not new.exists():  # case 2: the file itself moved, read the link from its old location
            old_dir = unmap(f.parent, maps)
            if old_dir is not None:
                t2 = pathlib.Path(os.path.normpath(old_dir / path))
                new = remap(t2, maps) or t2
        if new is None or not new.exists():
            still.append(raw)
            return m.group(0)
        rel = os.path.relpath(new, f.parent)
        if not lt:
            rel = rel.replace(" ", "%20")
        fixed += 1
        return "](" + (lt or "") + rel + (hashpart + frag if frag else "") + (gt or "") + ")"

    out = LINK.sub(sub, s)
    if fixed and not dry:
        f.write_text(out, encoding="utf-8")
    return fixed, still


def run(root, maps, also=(), dry=False, check=False):
    total, broken = 0, []
    for f in files_under(root, also):
        if check:
            for m in LINK.finditer(read_md(f)):
                u = m.group(2)
                path = urllib.parse.unquote(u).split("#")[0]
                if not SKIP.match(u) and path and not (f.parent / path).exists():
                    broken.append((str(f), path))
            continue
        n, still = fix_file(f, maps, dry)
        if n:
            print(f"{'[dry run] ' if dry else ''}fixed {n} links: {f}")
        total += n
        broken += [(str(f), x) for x in still]
    return total, broken


def selftest():
    results = []

    def check(cond, label):
        results.append(bool(cond))
        print(f"[{'PASS' if cond else 'FAIL'}] {label}")

    import contextlib
    import io
    with tempfile.TemporaryDirectory() as d:
        d = pathlib.Path(d)
        (d / "docs/01 筆記本").mkdir(parents=True)
        (d / "docs/02 assets").mkdir(parents=True)
        (d / "docs/02 assets/清單.md").write_text("x")
        (d / "board.md").write_text("[a](docs/01%20筆記本/摘要.md) [b](<docs/01 筆記本/摘要.md#section-2>) [x](https://e.com) [ok](docs/02%20assets/清單.md)")
        (d / "docs/01 筆記本/摘要.md").write_text("[清單](<../02 assets/清單.md>) [壞](<../不存在.md>)")
        # simulate the move: docs/01 筆記本 -> 新/筆記本 (depth changes)
        (d / "新").mkdir()
        os.rename(d / "docs/01 筆記本", d / "新/筆記本")
        maps = [((d / "docs/01 筆記本").resolve(), (d / "新/筆記本").resolve())]

        # dry run first: reports but writes nothing
        before = (d / "board.md").read_text()
        with contextlib.redirect_stdout(io.StringIO()):
            n_dry, _ = run(d.resolve(), maps, dry=True)
        check(n_dry == 3 and (d / "board.md").read_text() == before, "dry run counts 3 fixes and writes nothing")

        with contextlib.redirect_stdout(io.StringIO()):
            n, still = run(d.resolve(), maps)
        board = (d / "board.md").read_text()
        law = (d / "新/筆記本/摘要.md").read_text()
        check("[a](新/筆記本/摘要.md)" in board and "[b](<新/筆記本/摘要.md#section-2>)" in board,
              "case 1: links to the moved folder are rewritten, <> keeps spaces, bare form uses %20, fragment kept")
        check("[x](https://e.com)" in board and "[ok](docs/02%20assets/清單.md)" in board,
              "external links and links that already work are untouched")
        check("[清單](<../../docs/02 assets/清單.md>)" in law, "case 2: outgoing link of the moved file is recomputed")
        check(n == 3, f"fixed count is 3 (got {n})")
        check([x[1] for x in still] == ["../不存在.md"], "a link that stays broken is reported, not changed")
        _, broken = run(d.resolve(), maps, check=True)
        check([b[1] for b in broken] == ["../不存在.md"], "--check lists the one remaining broken link")
        with contextlib.redirect_stdout(io.StringIO()):
            n2, _ = run(d.resolve(), maps)
        check(n2 == 0, "a second run changes nothing")

        # robustness: node_modules and .git skipped, non-UTF-8 file does not crash, bad --map is an argument error
        (d / "docs/node_modules/pkg").mkdir(parents=True)
        (d / "docs/node_modules/pkg/R.md").write_text("[x](missing-in-vendor.md)")
        (d / "docs/binary.md").write_bytes(b"\xff\xfe bad bytes [y](nowhere.md)")
        with contextlib.redirect_stdout(io.StringIO()):
            _, broken2 = run((d / "docs").resolve(), maps, check=True)
        names = [b[0] for b in broken2]
        check(not any("node_modules" in n for n in names), "files under node_modules are not scanned")
        check(any(n.endswith("binary.md") for n in names), "a file with invalid UTF-8 is read with replacement, not a crash")
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                main(["--root", str(d), "--map", "abc"])
            map_code = None
        except SystemExit as e:
            map_code = e.code
        check(map_code == 2, "--map without = is refused with exit 2")

        # CLI exit codes
        with contextlib.redirect_stdout(io.StringIO()):
            rc_missing = main(["--root", str(d / "nope")])
            rc_check = main(["--root", str(d), "--check"])
            rc_clean = main(["--root", str(d / "docs/02 assets"), "--check"])
        check(rc_missing == 3, "missing --root exits 3")
        check(rc_check == 4, "--check with a broken link exits 4")
        check(rc_clean == 0, "--check on a clean folder exits 0")

    passed = sum(results)
    print(f"\nselftest result: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description="Repair broken Markdown relative links after a folder move")
    ap.add_argument("--root", help="folder to scan (default: current directory)")
    ap.add_argument("--map", action="append", default=[], help='"OLD_ABS=NEW_ABS", repeatable')
    ap.add_argument("--also", nargs="*", default=[], help="extra files outside --root to fix")
    ap.add_argument("--dry-run", action="store_true", help="show what would change, write nothing")
    ap.add_argument("--check", action="store_true", help="report broken links only")
    ap.add_argument("--selftest", action="store_true", help="run the built-in tests in a temporary folder")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    root = pathlib.Path(a.root or ".").resolve()
    if not root.exists():
        print(f"ERROR: root does not exist: {root}")
        return 3
    for m in a.map:
        if "=" not in m or not all(m.split("=", 1)):
            ap.error(f'--map needs "OLD_ABS=NEW_ABS", got: {m!r}')
    maps = [tuple(pathlib.Path(x).resolve() for x in m.split("=", 1)) for m in a.map]
    n, broken = run(root, maps, a.also, a.dry_run, a.check)
    if not a.check:
        print(f"fixed {n} links in total")
    print(f"still broken: {len(broken)}" + (":" if broken else ""))
    for f, p in broken[:50]:
        print(f"  {f} -> {p}")
    return 4 if (a.check and broken) else 0


if __name__ == "__main__":
    sys.exit(main())
