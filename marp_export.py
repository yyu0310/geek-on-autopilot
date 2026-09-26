#!/usr/bin/env python3
# marp_export.py: QA check, PDF export and verification for Marp decks.
"""
Wraps the /marp-export pipeline (QA check, npx marp-cli export, verification)
into one small CLI. Standard library only.

Subcommands:
  qa <file.md>                      Scan for draft markers and missing local images
  export <file.md> [--timeout 300]  Export a PDF with npx @marp-team/marp-cli
  verify <file.md>                  Check the sibling .pdf exists, is non-empty
                                    and is not older than the .md

Exit codes:
  0  success
  2  external command (npx) failed or timed out
  3  input file missing or not a .md file
  4  hard gate FAIL (QA found problems, or verify failed)
  5  environment missing (npx not found)

--selftest runs the built-in tests in a temp folder. The real npx export is
not part of the selftest because it needs network access on first run.
"""
import argparse
import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

VERSION = "1.1.0"
DEFAULT_TIMEOUT = 300

# Draft markers: TODO / FIXME / TBD / XXX as whole words, and the full-width
# bracket 【 used as a "fill me in" placeholder.
DRAFT_RE = re.compile(r"\b(?:TODO|FIXME|TBD|XXX)\b|【")
IMG_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
TITLE_SUFFIX_RE = re.compile(r'^(.*?)\s+(?:"[^"]*"|\'[^\']*\')$')


def log(msg):
    print(f"[marp_export] {msg}", flush=True)


def check_md_file(path):
    if not os.path.isfile(path):
        log(f"ERROR: file not found: {path}")
        return 3
    if not path.endswith(".md"):
        log(f"ERROR: not a .md file: {path}")
        return 3
    return None


def _extract_img_url(raw):
    """`pic.png "title"` -> `pic.png`. Strips a trailing quoted title, keeps spaces in the path."""
    raw = raw.strip()
    m = TITLE_SUFFIX_RE.match(raw)
    return m.group(1).strip() if m else raw


def find_npx():
    """Return (npx_path, bin_dir) or (None, None). Falls back to common Homebrew and nvm locations."""
    found = shutil.which("npx")
    if found:
        return found, os.path.dirname(found)
    candidates = ["/opt/homebrew/bin/npx", "/usr/local/bin/npx"]
    candidates += sorted(glob.glob(os.path.expanduser("~/.nvm/versions/node/*/bin/npx")), reverse=True)
    for c in candidates:
        if os.path.isfile(c) and os.access(c, os.X_OK):
            return c, os.path.dirname(c)
    return None, None


def cmd_qa(path):
    err = check_md_file(path)
    if err:
        return err

    md_dir = os.path.dirname(os.path.abspath(path))
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()

    fail = False

    # QA-1: draft markers
    draft_hits = [(i + 1, line) for i, line in enumerate(lines) if DRAFT_RE.search(line)]
    if draft_hits:
        fail = True
        log("QA-1 FAIL: draft markers found (TODO, FIXME, TBD, XXX, 【)")
        for lineno, line in draft_hits:
            print(f"{lineno}: {line}")
    else:
        log("QA-1 PASS: no draft markers")

    # QA-2: local image references exist
    missing = []
    remote = []
    for i, line in enumerate(lines):
        for m in IMG_RE.finditer(line):
            url = _extract_img_url(m.group(1))
            if url.startswith("http://") or url.startswith("https://"):
                remote.append((i + 1, url))
                continue
            img_path = url if os.path.isabs(url) else os.path.join(md_dir, url)
            if not os.path.isfile(img_path):
                missing.append((i + 1, url))

    for lineno, url in remote:
        log(f"WARN: line {lineno} remote image not checked: {url}")

    if missing:
        fail = True
        log("QA-2 FAIL: missing image files")
        for lineno, url in missing:
            print(f"{lineno}: {url}")
    else:
        log("QA-2 PASS: all local image references exist")

    return 4 if fail else 0


def cmd_export(path, timeout=DEFAULT_TIMEOUT):
    err = check_md_file(path)
    if err:
        return err

    npx, bin_dir = find_npx()
    if npx is None:
        log("ERROR: npx not found. Install Node.js (brew install node, or nvm install --lts)")
        return 5

    abspath = os.path.abspath(path)
    md_dir = os.path.dirname(abspath)
    basename = os.path.basename(abspath)[: -len(".md")]

    env = dict(os.environ)
    env["PATH"] = bin_dir + os.pathsep + env.get("PATH", "")

    log(f"exporting {basename}.md -> {basename}.pdf with npx @marp-team/marp-cli (cwd={md_dir})")
    try:
        # --no-stdin plus stdin=DEVNULL: marp-cli hangs waiting on stdin otherwise.
        r = subprocess.run(
            [npx, "--yes", "@marp-team/marp-cli@latest", f"{basename}.md",
             "--pdf", "--allow-local-files", "--no-stdin", "-o", f"{basename}.pdf"],
            cwd=md_dir, capture_output=True, text=True, timeout=timeout,
            stdin=subprocess.DEVNULL, env=env,
        )
    except subprocess.TimeoutExpired:
        log(f"ERROR: npx timed out after {timeout}s")
        return 2
    if r.returncode != 0:
        log(f"ERROR: npx failed (returncode={r.returncode})")
        tail = "\n".join(r.stderr.splitlines()[-30:])
        print(tail, file=sys.stderr)
        return 2

    log(f"export command finished: {basename}.pdf")
    return 0


def cmd_verify(path):
    err = check_md_file(path)
    if err:
        return err

    abspath = os.path.abspath(path)
    pdf_path = abspath[: -len(".md")] + ".pdf"
    md_mtime = os.path.getmtime(abspath)

    ok = True

    exists = os.path.isfile(pdf_path)
    log(f"{'OK  ' if exists else 'FAIL'} PDF exists: {pdf_path}")
    ok = ok and exists

    if exists:
        size = os.path.getsize(pdf_path)
        size_ok = size > 0
        log(f"{'OK  ' if size_ok else 'FAIL'} PDF size > 0 ({size} bytes)")
        ok = ok and size_ok

        pdf_mtime = os.path.getmtime(pdf_path)
        mtime_ok = pdf_mtime >= md_mtime
        log(f"{'OK  ' if mtime_ok else 'FAIL'} PDF mtime >= md mtime")
        ok = ok and mtime_ok
    else:
        log("FAIL PDF size > 0 (skipped, file missing)")
        log("FAIL PDF mtime >= md mtime (skipped, file missing)")

    if ok:
        size = os.path.getsize(pdf_path)
        log(f"PDF: {pdf_path} ({size} bytes)")
        return 0
    return 4


def run_selftest():
    results = []

    def check(name, cond):
        results.append((name, cond))
        log(f"[{'PASS' if cond else 'FAIL'}] {name}")

    def write(path, text):
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)

    with tempfile.TemporaryDirectory(prefix="marp_export selftest ") as tmp:
        # qa: draft markers
        draft_md = os.path.join(tmp, "draft.md")
        write(draft_md, "# Title\n\n【fill in】 content\n")
        check("qa 【 marker -> exit 4", cmd_qa(draft_md) == 4)

        todo_md = os.path.join(tmp, "todo.md")
        write(todo_md, "# Title\n\nTODO: add chart\n")
        check("qa TODO marker -> exit 4", cmd_qa(todo_md) == 4)

        word_md = os.path.join(tmp, "word.md")
        write(word_md, "# Title\n\nThe mastodon slide is fine\n")
        check("qa 'mastodon' is not a TODO hit -> exit 0", cmd_qa(word_md) == 0)

        # qa: missing image
        missing_md = os.path.join(tmp, "missing_img.md")
        write(missing_md, "# Title\n\n![alt](assets/not_exist.png)\n")
        check("qa missing image -> exit 4", cmd_qa(missing_md) == 4)

        # qa: existing image, ![bg fit] syntax, remote image not checked
        os.makedirs(os.path.join(tmp, "assets"), exist_ok=True)
        with open(os.path.join(tmp, "assets", "ok.png"), "wb") as f:
            f.write(b"\x89PNG fake")
        mixed_md = os.path.join(tmp, "mixed.md")
        write(
            mixed_md,
            "# Title\n\n"
            "![alt](assets/ok.png)\n\n"
            "![bg fit](assets/ok.png)\n\n"
            "![remote](https://example.com/pic.png)\n",
        )
        check("qa local image + ![bg fit] + remote image -> exit 0", cmd_qa(mixed_md) == 0)

        # qa: image path with spaces and a title suffix
        os.makedirs(os.path.join(tmp, "my assets"), exist_ok=True)
        with open(os.path.join(tmp, "my assets", "pic one.png"), "wb") as f:
            f.write(b"\x89PNG fake")
        space_md = os.path.join(tmp, "space_img.md")
        write(space_md, '# Title\n\n![alt](my assets/pic one.png "caption")\n')
        check("qa image path with spaces and title suffix -> exit 0", cmd_qa(space_md) == 0)

        # qa: no images
        no_img_md = os.path.join(tmp, "no_img.md")
        write(no_img_md, "# Title\n\nPlain text, no images\n")
        check("qa deck without images -> exit 0", cmd_qa(no_img_md) == 0)

        # exit 3: missing file or non-.md
        check("qa missing file -> exit 3", cmd_qa(os.path.join(tmp, "nope.md")) == 3)
        not_md = os.path.join(tmp, "file.txt")
        write(not_md, "x")
        check("qa non-.md -> exit 3", cmd_qa(not_md) == 3)
        check("export non-.md -> exit 3", cmd_export(not_md) == 3)
        check("export missing file -> exit 3", cmd_export(os.path.join(tmp, "nope.md")) == 3)
        check("verify non-.md -> exit 3", cmd_verify(not_md) == 3)

        # verify: three FAIL modes and one PASS
        v_md = os.path.join(tmp, "verify_target.md")
        write(v_md, "# Title\n")
        check("verify PDF missing -> exit 4", cmd_verify(v_md) == 4)

        v_pdf = os.path.join(tmp, "verify_target.pdf")
        with open(v_pdf, "wb"):
            pass
        check("verify PDF size 0 -> exit 4", cmd_verify(v_md) == 4)

        with open(v_pdf, "wb") as f:
            f.write(b"%PDF-1.4 fake")
        now = time.time()
        os.utime(v_pdf, (now - 100, now - 100))
        os.utime(v_md, (now, now))
        check("verify PDF older than md -> exit 4", cmd_verify(v_md) == 4)

        os.utime(v_pdf, (now + 100, now + 100))
        check("verify all pass -> exit 0", cmd_verify(v_md) == 0)

    log("[SKIP] real npx export is a manual check (first run downloads the package)")

    passed = sum(1 for _, c in results if c)
    total = len(results)
    log(f"selftest result: {passed}/{total} passed")
    return 0 if passed == total else 1


def main():
    parser = argparse.ArgumentParser(prog="marp_export.py", description="Marp deck QA, PDF export and verification")
    parser.add_argument("--selftest", action="store_true", help="run the built-in self test")
    sub = parser.add_subparsers(dest="command")

    p_qa = sub.add_parser("qa", help="scan for draft markers and missing images")
    p_qa.add_argument("file")

    p_export = sub.add_parser("export", help="export a PDF with npx marp-cli")
    p_export.add_argument("file")
    p_export.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)

    p_verify = sub.add_parser("verify", help="check the PDF exists, is non-empty and is fresh")
    p_verify.add_argument("file")

    args = parser.parse_args()

    if args.selftest:
        sys.exit(run_selftest())

    if args.command == "qa":
        sys.exit(cmd_qa(args.file))
    elif args.command == "export":
        sys.exit(cmd_export(args.file, timeout=args.timeout))
    elif args.command == "verify":
        sys.exit(cmd_verify(args.file))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
