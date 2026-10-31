#!/usr/bin/env python3
"""docx_pdf.py: DOCX to PDF conversion and QA CLI, v1.0.0.

Wraps the fixed QA pipeline of /docx-gen (LibreOffice headless plus a font check
with automatic retries) into one command. Generating the .docx itself is not
scripted: every document differs, so the model writes the JavaScript each time.
This file only covers the mechanical part that always repeats: lint the generator
script, convert to PDF, check the page, retry on bad fonts.

The font check is borrowed from md2pdf.py (check_pdf_fonts, BAD_FONT_PATTERNS,
find_soffice), which must sit in the same folder as this script. Background:
LibreOffice headless on macOS resolves CJK fonts non-deterministically. Converting
the same file several times in a row can land on different fonts, including
handwriting and decorative ones, so the script converts again until the fonts pass.

Subcommands:
  lint <file.js>                                  scan for a known trap: italics: true
  convert <file.docx> [--outdir DIR] [--remove-docx]
                                                  DOCX to PDF (soffice headless + font QA retries)

Exit codes:
  0  success
  2  external command (soffice) failed or timed out
  3  input file missing or wrong extension
  4  hard gate failed (lint hit, PDF missing or empty, font QA still failing after all retries)
  5  missing dependency (soffice or pdffonts)

--selftest runs the built-in tests in a temporary folder and prints PASS/FAIL per test.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from md2pdf import check_pdf_fonts, BAD_FONT_PATTERNS, find_soffice  # noqa: E402

VERSION = "1.0.0"
DEFAULT_TIMEOUT = 120
MAX_FONT_RETRIES = 6

# Why italics are banned: when any run in a docx-js document has italics: true, even a
# pure Latin one, LibreOffice headless swaps the CJK fonts of the whole document for
# decorative ones such as STXingkai. The effect is document-wide and deterministic, not
# random: converting again does not help. Without any italics the document goes
# back to the normal "random but fixable by converting again" behavior.
ITALICS_RE = re.compile(r"italics\s*:\s*true")


def log(msg):
    print(f"[docx_pdf] {msg}", flush=True)


def check_docx_file(path):
    if not os.path.isfile(path):
        log(f"ERROR: file not found: {path}")
        return 3
    if not path.endswith(".docx"):
        log(f"ERROR: not a .docx file: {path}")
        return 3
    return None


def cmd_lint(path):
    if not os.path.isfile(path):
        log(f"ERROR: file not found: {path}")
        return 3
    if not path.endswith(".js"):
        log(f"ERROR: not a .js file: {path}")
        return 3

    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()

    hits = [(i + 1, line.strip()[:60]) for i, line in enumerate(lines) if ITALICS_RE.search(line)]
    if hits:
        log("known trap found (italics: true makes LibreOffice swap the CJK fonts of the whole document for decorative ones):")
        for lineno, snippet in hits:
            print(f"{lineno}: {snippet}")
        return 4

    log("lint passed: no italics: true found")
    return 0


def cmd_convert(path, keep_docx=True, outdir=None, soffice=None, pdffonts=None,
                timeout=DEFAULT_TIMEOUT, max_font_retries=MAX_FONT_RETRIES):
    soffice = soffice or find_soffice()
    pdffonts = pdffonts or shutil.which("pdffonts")

    err = check_docx_file(path)
    if err:
        return err

    if not os.path.exists(soffice):
        log(f"ERROR: LibreOffice not found ({soffice}). Install: brew install --cask libreoffice (or set MD2PDF_SOFFICE)")
        return 5
    if not pdffonts or not os.path.exists(pdffonts):
        log("ERROR: pdffonts not found (the font QA needs it). Install: brew install poppler")
        return 5

    path = os.path.abspath(path)
    basename = os.path.basename(path)[: -len(".docx")]
    out_dir = os.path.abspath(outdir) if outdir else os.path.dirname(path)
    os.makedirs(out_dir, exist_ok=True)
    pdf_path = os.path.join(out_dir, basename + ".pdf")

    for attempt in range(1, max_font_retries + 1):
        log(f"soffice {path} -> PDF ({out_dir}), attempt {attempt}/{max_font_retries}")
        try:
            r = subprocess.run(
                [soffice, "--headless", "--convert-to", "pdf", path, "--outdir", out_dir],
                capture_output=True, text=True, timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            log(f"ERROR: soffice timed out ({timeout}s)")
            return 2
        if r.returncode != 0:
            log(f"ERROR: soffice failed (returncode={r.returncode})")
            print(r.stderr, file=sys.stderr)
            return 2

        if not os.path.isfile(pdf_path) or os.path.getsize(pdf_path) == 0:
            log("FAIL: PDF check failed (missing or size 0)")
            return 4

        ok, bad_fonts, all_fonts = check_pdf_fonts(pdf_path, pdffonts=pdffonts)
        log(f"font QA: {all_fonts}")
        if ok:
            break
        log(f"WARNING: bad fonts detected {bad_fonts} (LibreOffice font matching is random), converting again")
    else:
        log(f"FAIL: bad fonts {bad_fonts} still present after {max_font_retries} attempts")
        return 4

    size = os.path.getsize(pdf_path)
    if not keep_docx:
        os.remove(path)
        log(f"removed intermediate file: {path}")

    log(f"PDF: {pdf_path} ({size} bytes)")
    return 0


def run_selftest():
    results = []

    def check(name, cond):
        results.append((name, cond))
        log(f"[{'PASS' if cond else 'FAIL'}] {name}")

    here = os.path.dirname(os.path.abspath(__file__))
    with tempfile.TemporaryDirectory(prefix="docx_pdf 測試 空格 ") as tmp:
        not_docx = os.path.join(tmp, "file.txt")
        with open(not_docx, "w", encoding="utf-8") as f:
            f.write("x")
        check("convert on a non-.docx -> exit 3", cmd_convert(not_docx) == 3)
        check("convert on a missing file -> exit 3", cmd_convert(os.path.join(tmp, "nope.docx")) == 3)

        # lint
        check("lint on a missing file -> exit 3", cmd_lint(os.path.join(tmp, "nope.js")) == 3)
        check("lint on a non-.js -> exit 3", cmd_lint(not_docx) == 3)

        hit_js = os.path.join(tmp, "hit.js")
        with open(hit_js, "w", encoding="utf-8") as f:
            f.write("makeRun('x', { color: '0000FF', italics: true }),\n")
        check("lint hit on italics: true -> exit 4", cmd_lint(hit_js) == 4)

        ok_js = os.path.join(tmp, "ok.js")
        with open(ok_js, "w", encoding="utf-8") as f:
            f.write("makeRun('x', { color: '0000FF', underline: {} }),\n")
        check("lint clean -> exit 0", cmd_lint(ok_js) == 0)

        # missing dependency: inject fake paths, a fake .docx is enough because the environment check runs first
        fake_docx = os.path.join(tmp, "fake.docx")
        with open(fake_docx, "wb") as f:
            f.write(b"PK\x03\x04")
        code = cmd_convert(fake_docx, soffice="/tmp/docx_pdf-selftest-不存在的假soffice")
        check("soffice missing (injected fake path) -> exit 5", code == 5)
        code = cmd_convert(fake_docx, pdffonts="/tmp/docx_pdf-selftest-不存在的假pdffonts")
        check("pdffonts missing (injected fake path) -> exit 5", code == 5)

        check("md2pdf.BAD_FONT_PATTERNS imported", len(BAD_FONT_PATTERNS) > 0)

        # real conversion: only when the tools are installed and a .docx exists in docx-gen-tools/workspace
        ws = os.path.join(here, "docx-gen-tools", "workspace")
        real_docx = sorted(os.path.join(ws, n) for n in os.listdir(ws) if n.endswith(".docx")) if os.path.isdir(ws) else []
        soffice = find_soffice()
        if os.path.exists(soffice) and shutil.which("pdffonts") and real_docx:
            dst = os.path.join(tmp, "真轉換 測試.docx")
            shutil.copy(real_docx[0], dst)
            code = cmd_convert(dst)
            pdf_out = os.path.join(tmp, "真轉換 測試.pdf")
            check("real conversion -> exit 0", code == 0)
            check("real conversion PDF exists and is not empty", os.path.isfile(pdf_out) and os.path.getsize(pdf_out) > 0)
        else:
            log("[SKIP] real conversion test (LibreOffice or pdffonts missing, or no .docx in docx-gen-tools/workspace/)")

    passed = sum(1 for _, c in results if c)
    total = len(results)
    log(f"selftest result: {passed}/{total} passed")
    return 0 if passed == total else 1


def main():
    parser = argparse.ArgumentParser(prog="docx_pdf.py", description="DOCX to PDF conversion with font QA")
    parser.add_argument("--selftest", action="store_true", help="run the built-in tests in a temporary folder")
    sub = parser.add_subparsers(dest="command")

    p_lint = sub.add_parser("lint", help="scan a generator script for the italics: true trap")
    p_lint.add_argument("file")

    p_conv = sub.add_parser("convert", help="DOCX to PDF (soffice headless + font QA retries)")
    p_conv.add_argument("file")
    p_conv.add_argument("--outdir", default=None)
    p_conv.add_argument("--remove-docx", action="store_true", help="delete the source .docx after a successful conversion (default: keep)")

    args = parser.parse_args()

    if args.selftest:
        sys.exit(run_selftest())

    if args.command == "lint":
        sys.exit(cmd_lint(args.file))
    elif args.command == "convert":
        sys.exit(cmd_convert(args.file, keep_docx=not args.remove_docx, outdir=args.outdir))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
