#!/usr/bin/env python3
"""ref_audit.py: reference audit before you move, rename, or delete a folder.

Scans every place that may hard-code the old path and reports file:line for each
hit. It only does the mechanical part. Sorting hits into "live file, must update"
and "history file, keep as is" is left to the model or to you.

Scan domains (all five, none optional unless a flag says so):
  1. Project tree under --root (default: current directory):
     *.md *.py *.sh *.gs *.json *.plist, skipping ._* files, node_modules and .git
  2. Claude Code settings: <root>/.claude/settings*.json and <claude-dir>/settings*.json
     (permission allowlists hard-code paths). Reported here only, not again in domain 1.
  3. Claude memory folder (default: <claude-dir>/projects/<encoded root>/memory). The name
     is derived from --root, but Claude Code names it after the folder you started it in. If
     that is not --root, or you are unsure, pass --memory-dir explicitly.
  4. <claude-dir>/commands symlinks: does the link target contain a string?
  5. Schedulers: ~/Library/LaunchAgents plists (com.apple* skipped), the user's
     crontab, and any extra config files given with --sync-config

Each string is also searched in its URL-encoded forms (space as %20, and fully
percent-encoded), because Markdown links often store paths that way.

Safety: output is only "path:line [stringN]". The matched line is never printed,
so a hit inside a credential-looking file leaks nothing to the terminal or to --out.

Usage:
    ref_audit.py STRING [STRING ...] [--root DIR] [--claude-dir DIR] [--memory-dir DIR]
                 [--launchd-dir DIR] [--sync-config FILE ...] [--no-gs] [--no-launchd]
                 [--out FILE]
    ref_audit.py --selftest

Exit codes:
  0  scan finished (whatever the hit count)
  2  I/O error, or bad arguments
  3  --root does not exist
Files are read with errors="replace", so a non-UTF-8 file never crashes the scan.
"""
import argparse
import datetime
import os
import re
import subprocess
import sys
from urllib.parse import quote

SCAN_EXTS = {".md", ".py", ".sh", ".gs", ".json", ".plist"}
PRUNE_DIRS = {"node_modules", ".git"}


# ---------- scan primitives ----------

def variants(s):
    """The string itself plus its URL-encoded forms. Markdown links usually encode
    only the space (%20); a browser copy encodes everything. Plain search misses both."""
    return {s, s.replace(" ", "%20"), quote(s, safe="/")}


def scan_lines(lines, strings):
    """Substring match per line, URL-encoded forms included.
    Returns [(line number, string index), ...]. Never returns line content."""
    expanded = [variants(s) for s in strings]
    hits = []
    for i, line in enumerate(lines, 1):
        for si, vs in enumerate(expanded):
            if any(v in line for v in vs):
                hits.append((i, si))
    return hits


def scan_file_lines(path, strings):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return scan_lines(f, strings)
    except OSError:
        return []


def scan_tree(strings, root, include_gs=True, skip_real=()):
    """Domain 1. Returns (file_hits, stats). Files whose real path is in skip_real are
    left to another domain (the settings files), so no hit is counted twice."""
    exts = SCAN_EXTS if include_gs else (SCAN_EXTS - {".gs"})
    file_hits = []
    stats = {"scanned": 0, "dot_skipped": 0, "pruned": 0}
    for cur, dirnames, filenames in os.walk(root):
        stats["pruned"] += sum(1 for d in dirnames if d in PRUNE_DIRS)
        dirnames[:] = [d for d in dirnames if d not in PRUNE_DIRS]
        for fn in filenames:
            if fn.startswith("._"):
                stats["dot_skipped"] += 1
                continue
            if os.path.splitext(fn)[1] not in exts:
                continue
            path = os.path.join(cur, fn)
            if os.path.realpath(path) in skip_real:
                continue
            stats["scanned"] += 1
            hits = scan_file_lines(path, strings)
            if hits:
                file_hits.append((path, hits))
    return file_hits, stats


def scan_settings(strings, settings_dirs):
    """Domain 2. settings.json and settings.local.json in each given .claude folder."""
    file_hits = []
    seen = set()
    for d in settings_dirs:
        for name in ("settings.json", "settings.local.json"):
            p = os.path.join(d, name)
            real = os.path.realpath(p)
            if real in seen or not os.path.exists(p):
                continue
            seen.add(real)
            hits = scan_file_lines(p, strings)
            if hits:
                file_hits.append((p, hits))
    return file_hits


def scan_memory(strings, memdir):
    """Domain 3. Every .md file in the memory folder."""
    file_hits = []
    if memdir and os.path.isdir(memdir):
        for fn in sorted(os.listdir(memdir)):
            if fn.startswith("._") or not fn.endswith(".md"):
                continue
            p = os.path.join(memdir, fn)
            hits = scan_file_lines(p, strings)
            if hits:
                file_hits.append((p, hits))
    return file_hits


def scan_commands(strings, cmddir):
    """Domain 4. Does a symlink's target path contain a string? A dangling link still
    has a readable target string, so it is reported too. Returns [(name, target)]."""
    hits = []
    if os.path.isdir(cmddir):
        for name in sorted(os.listdir(cmddir)):
            p = os.path.join(cmddir, name)
            if os.path.islink(p):
                try:
                    target = os.readlink(p)
                except OSError:
                    continue
                if any(v in target for s in strings for v in variants(s)):
                    hits.append((name, target))
    return hits


def scan_schedulers(strings, launchd_dir, sync_configs, crontab_text=""):
    """Domain 5. Returns (file_hits, cron_hits). cron_hits are line numbers within
    the crontab text, which has no file path."""
    file_hits = []
    if launchd_dir and os.path.isdir(launchd_dir):
        for fn in sorted(os.listdir(launchd_dir)):
            if fn.startswith("com.apple") or not fn.endswith(".plist"):
                continue
            p = os.path.join(launchd_dir, fn)
            hits = scan_file_lines(p, strings)
            if hits:
                file_hits.append((p, hits))
    for p in sync_configs:
        if os.path.exists(p):
            hits = scan_file_lines(p, strings)
            if hits:
                file_hits.append((p, hits))
    cron_hits = scan_lines(crontab_text.splitlines(), strings) if crontab_text else []
    return file_hits, cron_hits


def read_crontab():
    """Text of `crontab -l`, or "" when there is none or crontab is unavailable."""
    try:
        r = subprocess.run(["crontab", "-l"], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return ""
    return r.stdout if r.returncode == 0 else ""


def encode_project_dir(abs_root):
    """Claude Code names a project's folder under <claude-dir>/projects by replacing
    every non-alphanumeric character of its absolute path with a dash. If your version
    differs, pass --memory-dir."""
    return re.sub(r"[^A-Za-z0-9]", "-", abs_root)


# ---------- report assembly ----------

def render_domain(num, title, file_hits, extra_lines=None):
    """path:line format. Returns (output lines, file count, hit count)."""
    lines = [f"\n## {num}. {title}"]
    if not file_hits:
        lines.append("no hits")
        return lines, 0, 0
    files = 0
    total_hits = 0
    for path, h in file_hits:
        if not h:
            continue
        files += 1
        for line_no, si in h:
            lines.append(f"{path}:{line_no} [string{si + 1}]")
            total_hits += 1
        lines.append(f"  subtotal: {len(h)}")
    lines.append(f"domain total: {files} files, {total_hits} hits")
    return lines, files, total_hits


def render_symlinks(num, title, sym_hits):
    lines = [f"\n## {num}. {title}"]
    if not sym_hits:
        lines.append("no hits")
        return lines, 0, 0
    for name, target in sym_hits:
        lines.append(f"{name} -> {target}")
    lines.append(f"domain total: {len(sym_hits)} links")
    return lines, len(sym_hits), len(sym_hits)


def build_report(strings, root, claude_dir, memdir, launchd_dir, sync_configs,
                 crontab_text="", include_gs=True, include_launchd=True):
    """Assemble the five domains. Returns (output lines, total files, total hits)."""
    out = []
    total_files = 0
    total_hits = 0

    settings_dirs = [os.path.join(root, ".claude"), claude_dir]
    settings_real = {os.path.realpath(os.path.join(d, n)) for d in settings_dirs
                     for n in ("settings.json", "settings.local.json")}
    d1, stats = scan_tree(strings, root, include_gs, skip_real=settings_real)
    lines, f, h = render_domain(1, "Project tree", d1)
    lines.append(f"(scan stats: compared {stats['scanned']} files; skipped {stats['dot_skipped']} "
                 f"._ files, pruned {stats['pruned']} node_modules/.git folders)")
    out += lines
    total_files += f
    total_hits += h

    lines, f, h = render_domain(2, "Claude settings", scan_settings(strings, settings_dirs))
    out += lines
    total_files += f
    total_hits += h

    lines, f, h = render_domain(3, "Claude memory", scan_memory(strings, memdir))
    out += lines
    total_files += f
    total_hits += h

    lines, f, h = render_symlinks(4, "commands symlinks",
                                  scan_commands(strings, os.path.join(claude_dir, "commands")))
    out += lines
    total_files += f
    total_hits += h

    if include_launchd:
        file_hits, cron_hits = scan_schedulers(strings, launchd_dir, sync_configs, crontab_text)
        lines, f, h = render_domain(5, "launchd, cron, sync configs", file_hits)
        if cron_hits:
            lines = [x for x in lines if x != "no hits"]
            for line_no, si in cron_hits:
                lines.append(f"crontab:{line_no} [string{si + 1}]")
            lines.append(f"crontab total: {len(cron_hits)} hits")
            h += len(cron_hits)
            f += 1
        out += lines
        total_files += f
        total_hits += h
    else:
        out += ["\n## 5. launchd, cron, sync configs", "(skipped by --no-launchd)"]

    return out, total_files, total_hits


def render_full_report(strings, **kwargs):
    """Add the timestamp header and the totals footer."""
    out_lines, total_files, total_hits = build_report(strings, **kwargs)
    header = f"=== ref-audit {datetime.datetime.now():%Y-%m-%d %H:%M} | strings: {', '.join(strings)} ==="
    footer = f"\n=== total hits: {total_files} files, {total_hits} hits ==="
    return [header] + out_lines + [footer], total_files, total_hits


def write_lines(path, lines):
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


# ---------- CLI ----------

def parse_args(argv):
    p = argparse.ArgumentParser(
        prog="ref_audit.py",
        description="Reference audit: find every hard-coded reference to a path before it moves")
    p.add_argument("strings", nargs="*", metavar="STRING",
                   help="strings to find; for a rename give both the old and the new name")
    p.add_argument("--root", default=".", help="project root to scan (default: current directory)")
    p.add_argument("--claude-dir", default=os.path.expanduser("~/.claude"),
                   help="Claude Code config folder (default: ~/.claude)")
    p.add_argument("--memory-dir", help="Claude memory folder (default: derived from --root)")
    p.add_argument("--launchd-dir", default=os.path.expanduser("~/Library/LaunchAgents"),
                   help="launchd agents folder (default: ~/Library/LaunchAgents)")
    p.add_argument("--sync-config", action="append", default=[], metavar="FILE",
                   help="extra config file that may hard-code paths; repeatable")
    p.add_argument("--no-gs", action="store_true", help="skip .gs files in the project tree")
    p.add_argument("--no-launchd", action="store_true", help="skip the launchd, cron and sync-config domain")
    p.add_argument("--out", metavar="FILE", help="also write the report to this file (your choice of location)")
    p.add_argument("--selftest", action="store_true",
                   help="run the built-in tests in a temporary folder, no real files touched")
    args = p.parse_args(argv)
    if not args.selftest:
        if not args.strings:
            p.error("at least one string is required")
        if any(s == "" for s in args.strings):
            p.error("a string must not be empty")
    return args


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.selftest:
        return run_selftest()

    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        print(f"ERROR: scan root does not exist: {root}")
        return 3
    claude_dir = os.path.abspath(args.claude_dir)
    memdir = args.memory_dir or os.path.join(claude_dir, "projects", encode_project_dir(root), "memory")

    try:
        full, _, _ = render_full_report(
            args.strings, root=root, claude_dir=claude_dir, memdir=memdir,
            launchd_dir=args.launchd_dir, sync_configs=args.sync_config,
            crontab_text="" if args.no_launchd else read_crontab(),
            include_gs=not args.no_gs, include_launchd=not args.no_launchd)
    except OSError as e:
        print(f"ERROR: I/O error: {e}")
        return 2

    for line in full:
        print(line)

    if args.out:
        try:
            write_lines(args.out, full)
        except OSError as e:
            print(f"ERROR: could not write --out file: {e}")
            return 2
    return 0


# ---------- selftest ----------

def run_selftest():
    import tempfile
    import shutil

    tmp = tempfile.mkdtemp(prefix="ref_audit_selftest_")
    results = []

    def check(cond, label):
        results.append(bool(cond))
        print(f"[{'PASS' if cond else 'FAIL'}] {label}")

    try:
        root = os.path.join(tmp, "proj root")
        claude_dir = os.path.join(tmp, "dotclaude")
        memdir = os.path.join(tmp, "memory")
        cmddir = os.path.join(claude_dir, "commands")
        launchd_dir = os.path.join(tmp, "LaunchAgents")
        for d in (root, claude_dir, memdir, cmddir, launchd_dir):
            os.makedirs(d, exist_ok=True)
        cron = "0 * * * * /bin/sh /x/目標字串A/run.sh\n# note\n"

        # Chinese path with a space
        zh_dir = os.path.join(root, "我的 專案")
        os.makedirs(zh_dir, exist_ok=True)
        with open(os.path.join(zh_dir, "筆記.md"), "w", encoding="utf-8") as f:
            f.write("第一行\n這裡有 目標字串A 出現\n")

        # two strings on one line
        multi_dir = os.path.join(root, "multi")
        os.makedirs(multi_dir, exist_ok=True)
        with open(os.path.join(multi_dir, "a.md"), "w", encoding="utf-8") as f:
            f.write("目標字串A 與 目標字串B 同一行\n")

        # non-UTF-8 file
        with open(os.path.join(root, "bad.md"), "wb") as f:
            f.write(b"\xff\xfe\x00invalid utf8 \x80\x81 \xffbytes\n")

        # node_modules and .git are pruned
        nm_dir = os.path.join(root, "pkg", "node_modules")
        os.makedirs(nm_dir, exist_ok=True)
        with open(os.path.join(nm_dir, "x.md"), "w", encoding="utf-8") as f:
            f.write("目標字串A\n")
        git_dir = os.path.join(root, ".git")
        os.makedirs(git_dir, exist_ok=True)
        with open(os.path.join(git_dir, "hook.sh"), "w", encoding="utf-8") as f:
            f.write("目標字串A\n")

        # ._ prefix is skipped
        with open(os.path.join(root, "._ghost.md"), "w", encoding="utf-8") as f:
            f.write("目標字串A\n")

        # .gs file (for --no-gs)
        with open(os.path.join(root, "script.gs"), "w", encoding="utf-8") as f:
            f.write("目標字串A\n")

        # project settings and user settings
        proj_claude = os.path.join(root, ".claude")
        os.makedirs(proj_claude, exist_ok=True)
        with open(os.path.join(proj_claude, "settings.json"), "w", encoding="utf-8") as f:
            f.write('{"path": "目標字串A"}\n')
        with open(os.path.join(claude_dir, "settings.local.json"), "w", encoding="utf-8") as f:
            f.write('{"allow": ["Read(目標字串A/**)"]}\n')

        # memory
        with open(os.path.join(memdir, "note.md"), "w", encoding="utf-8") as f:
            f.write("記得 目標字串A\n")

        # symlinks: one dangling whose target string matches, one healthy that does not
        good_target = os.path.join(root, "real.md")
        with open(good_target, "w", encoding="utf-8") as f:
            f.write("ok\n")
        os.symlink(os.path.join(root, "目標字串A-not-exist.md"), os.path.join(cmddir, "broken.md"))
        os.symlink(good_target, os.path.join(cmddir, "fine.md"))

        # launchd plist, com.apple plist, sync config
        with open(os.path.join(launchd_dir, "com.mine.job.plist"), "w", encoding="utf-8") as f:
            f.write("<plist>目標字串A</plist>\n")
        with open(os.path.join(launchd_dir, "com.apple.skip.plist"), "w", encoding="utf-8") as f:
            f.write("目標字串A\n")
        sync_cfg = os.path.join(tmp, "sync_config.json")
        with open(sync_cfg, "w", encoding="utf-8") as f:
            f.write('{"x":"目標字串A"}\n')

        strings = ["目標字串A", "目標字串B"]
        kw = dict(root=root, claude_dir=claude_dir, memdir=memdir, launchd_dir=launchd_dir,
                  sync_configs=[sync_cfg], crontab_text=cron)

        out, files_n, hits_n = build_report(strings, include_gs=True, include_launchd=True, **kw)
        text = "\n".join(out)

        check("我的 專案" in text and "筆記.md" in text, "Chinese path with a space is matched")
        check("[string1]" in text and "[string2]" in text and "multi" in text, "two strings on one line are listed once each")
        check(True, "non-UTF-8 file read without raising (reaching this line proves it)")
        check("/node_modules/" not in text, "no hits inside node_modules (only the stats line mentions pruning)")
        check("scan stats:" in text and "skipped 1 ._ files" in text, "stats line reports the skipped count")
        check("._ghost" not in text, "._ files are skipped")
        check(f"{sync_cfg}:1" in text, "extra sync config is matched")
        check("com.apple.skip" not in text, "launchd skips com.apple* plists")
        check("broken.md -> " in text, "dangling symlink does not crash and its target is reported")
        check("fine.md" not in text, "healthy symlink whose target lacks the string is not reported")
        check("hook.sh" not in text, ".git folder is pruned")
        check(os.path.join(proj_claude, "settings.json") + ":1" in text
              and os.path.join(claude_dir, "settings.local.json") + ":1" in text,
              "project and user settings files are both scanned")
        check(text.count(os.path.join(proj_claude, "settings.json") + ":1") == 1,
              "a settings file under the root is reported once (domain 2), not again in domain 1")
        check("crontab:1 [string1]" in text and "crontab:2" not in text, "crontab hit reports the line number only")
        check("目標字串A 出現" not in text and "invalid utf8" not in text, "report never prints matched line content")

        out_nogs, _, _ = build_report(strings, include_gs=False, include_launchd=True, **kw)
        text_nogs = "\n".join(out_nogs)
        check("script.gs" not in text_nogs, "--no-gs: .gs files have no hits")
        check("script.gs" in text, "without --no-gs: .gs files are hit (control)")

        out_nold, _, _ = build_report(strings, include_gs=True, include_launchd=False, **kw)
        text_nold = "\n".join(out_nold)
        check("skipped by --no-launchd" in text_nold and sync_cfg not in text_nold and "crontab:" not in text_nold,
              "--no-launchd skips the whole domain, cron included")

        # --out matches what is printed
        full, _, _ = render_full_report(strings, **kw)
        out_file = os.path.join(tmp, "report.txt")
        write_lines(out_file, full)
        with open(out_file, encoding="utf-8") as f:
            written = f.read()
        check(written == "\n".join(full) + "\n", "--out content equals the assembled report")

        # URL-encoded variants: %20-only and fully encoded, one hit per line even if both appear
        enc_dir = os.path.join(tmp, "enc")
        os.makedirs(enc_dir, exist_ok=True)
        s = "舊 資料夾/子夾"
        cases = [
            ("space.md", "[a](舊%20資料夾/子夾/x.md)\n"),
            ("full.md", f"[b]({quote(s, safe='/')}/x.md)\n"),
            ("raw.md", "舊 資料夾/子夾\n"),
            ("both.md", "舊 資料夾/子夾 與 舊%20資料夾/子夾\n"),
            ("miss.md", "舊%20資料夾/別的夾\n"),
        ]
        for fn, content in cases:
            with open(os.path.join(enc_dir, fn), "w", encoding="utf-8") as f:
                f.write(content)
        enc_hits, _ = scan_tree([s], enc_dir)
        got = {os.path.basename(p): len(h) for p, h in enc_hits}
        check(got == {"space.md": 1, "full.md": 1, "raw.md": 1, "both.md": 1},
              f"URL-encoded variants are matched, one hit per line (got {sorted(got.items())})")
        os.symlink(os.path.join(tmp, "舊%20資料夾/子夾/x.md"), os.path.join(cmddir, "enc.md"))
        check([n for n, _ in scan_commands([s], cmddir)] == ["enc.md"], "symlink target in %20 form is matched")

        # CLI behaviour through main()
        import contextlib
        import io
        saved = os.getcwd()
        quiet = io.StringIO()
        with contextlib.redirect_stdout(quiet), contextlib.redirect_stderr(quiet):
            try:
                os.chdir(zh_dir)
                rc_default = main(["目標字串A", "--claude-dir", claude_dir, "--memory-dir", memdir,
                                   "--launchd-dir", launchd_dir, "--no-launchd"])
            finally:
                os.chdir(saved)
            rc_missing = main(["x", "--root", os.path.join(tmp, "no such dir")])
            try:
                main(["x", ""])
                empty_code = None
            except SystemExit as e:
                empty_code = e.code
            rc_out = main(["目標字串A", "--root", root, "--claude-dir", claude_dir, "--memory-dir", memdir,
                           "--no-launchd", "--out", os.path.join(tmp, "no_such_dir", "r.txt")])
        check(rc_default == 0, "main() with the default root (current directory) exits 0")
        check("筆記.md" in quiet.getvalue(), "default root really is the current directory (hit inside it is listed)")
        check(rc_missing == 3, "missing --root exits 3")
        check(empty_code == 2, "empty string argument is rejected with exit 2")
        check(rc_out == 2, "unwritable --out exits 2")
        check(encode_project_dir("/home/u/My Proj") == "-home-u-My-Proj", "memory folder name encoding")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    passed = sum(results)
    print(f"\nselftest result: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
