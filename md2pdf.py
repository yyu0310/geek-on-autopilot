#!/usr/bin/env python3
"""md2pdf.py: Markdown to PDF converter with PingFang TC font QA (macOS).

Pipeline: pandoc (markdown+hard_line_breaks, reference docx) -> LibreOffice headless -> pdffonts check.

Subcommands:
  lint <file.md>
      Scan for known traps: numbered lists that start at a number other than 1
      with a non-blank line before them, and standalone images that carry a caption.
  convert <file.md> [--keep-docx] [--outdir DIR] [--strip] [--ref-docx PATH]
      MD -> DOCX (pandoc) -> PDF (soffice). --strip renders the whole document
      as one tall page and writes <name>_strip.pdf next to the normal PDF.
  wordcount <file.md> [--max N]
      Word-style count (each CJK character counts as one, each run of Latin
      letters or digits counts as one). Exits 4 when the count exceeds --max.
  --selftest
      Run the built-in tests. Everything happens inside a temporary folder.

Reference template lookup order:
  1. --ref-docx PATH
  2. environment variable MD2PDF_REF_DOCX
  3. reference_pingfang.docx in the same folder as this script

LibreOffice lookup order: environment variable MD2PDF_SOFFICE, the default
macOS app path, then `soffice` on PATH.

Exit codes:
  0  success
  2  external command (pandoc/soffice) failed or timed out
  3  input file missing or not a .md file
  4  hard gate failed (lint hit, PDF check failed, font QA still failing after all retries)
  5  missing dependency (pandoc, soffice, reference docx, or pdffonts)

Why the font QA exists: LibreOffice headless on macOS resolves CJK fonts
non-deterministically. The same docx converted several times in a row can come
out in different fonts, including handwriting and decorative ones, no matter
which font name the template specifies. The workaround is to convert several
times in parallel, inspect each PDF with pdffonts, and keep the first one whose
fonts all pass.
"""
import argparse
import concurrent.futures
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

VERSION = "1.3.0"

DEFAULT_REF_DOCX = str(Path(__file__).resolve().parent / "reference_pingfang.docx")
DEFAULT_SOFFICE_MAC = "/Applications/LibreOffice.app/Contents/MacOS/soffice"
DEFAULT_TIMEOUT = 120


def find_ref_docx(cli_value=None):
    """--ref-docx beats the MD2PDF_REF_DOCX env var, which beats the bundled template."""
    return cli_value or os.environ.get("MD2PDF_REF_DOCX") or DEFAULT_REF_DOCX


def find_soffice():
    env = os.environ.get("MD2PDF_SOFFICE")
    if env:
        return env
    if os.path.exists(DEFAULT_SOFFICE_MAC):
        return DEFAULT_SOFFICE_MAC
    return shutil.which("soffice") or DEFAULT_SOFFICE_MAC


# Each round starts BATCH_SIZE soffice processes in parallel, each with its own
# -env:UserInstallation profile so they don't fight over one profile lock. The first
# one that passes the font QA wins. At most MAX_BATCHES rounds are run.
#
# Measured pass rate for "every non-exempt font is PingFangTC" is low, about 5% per
# attempt, because LibreOffice draws fallback fonts from a wide pool. 20 rounds of 6
# attempts gives a 0.95^120 chance of total failure, well under 1%. Rerunning
# convert fixes the rare miss. If that is still too slow for you, the deterministic
# alternative is rendering through a browser engine with CSS font-family "PingFang TC".
BATCH_SIZE = 6
MAX_BATCHES = 20

ORDERED_LIST_RE = re.compile(r"^(\d+)\.(?:\s|$)")
# A line that holds exactly one image with non-empty alt text, optional {width=..} attributes
FIGURE_CAPTION_RE = re.compile(r"^!\[[^\]]+\]\([^)]*\)(\{[^}]*\})?\s*$")

# Whitelist used by convert. Only PingFang TC passes. HK, MO and SC variants share the
# PingFang family but use different glyph shapes, so the substring "pingfangtc" is the
# match and the other variants trigger a retry.
GOOD_FONT_PATTERNS = ["pingfangtc"]
# Fonts that always show up in pdffonts and are not CJK body fonts. They are excluded
# from the "every font must be PingFang TC" rule. Menlo is deliberately absent:
# when it appears, some symbol in the text has no PingFang TC glyph.
STRICT_EXEMPT_FONTS = ["liberation", "symbol", "applecoloremoji", "couriernewps"]

# Blacklist of known handwriting and decorative fonts. Always applied on top of the
# whitelist, and used alone when check_pdf_fonts gets no good_patterns. Copy new
# entries from real pdffonts output rather than from memory of a font's name.
BAD_FONT_PATTERNS = [
    "hanzipen", "kaiti", "xingkai", "baoli", "wawa",
    "yuppy", "hannotate", "weibei", "libian",
]

TRAILING_BACKSLASH_RE = re.compile(r"\\\n")


def log(msg):
    print(f"[md2pdf] {msg}", flush=True)


def path_hint(tool):
    """Extra hint for exit 5. Claude Code's shell PATH often lacks /opt/homebrew/bin,
    so a tool can be installed and still not be found."""
    for d in ("/opt/homebrew/bin", "/usr/local/bin"):
        if os.path.exists(os.path.join(d, tool)):
            return (f" (it is installed in {d} but not on PATH: "
                    f"run export PATH=\"{d}:$PATH\" and retry)")
    return ""


def check_md_file(path):
    """Return exit code 3 or None when the file is fine."""
    if not os.path.isfile(path):
        log(f"ERROR: file not found: {path}")
        return 3
    if not path.endswith(".md"):
        log(f"ERROR: not a .md file: {path}")
        return 3
    return None


def cmd_lint(path):
    err = check_md_file(path)
    if err:
        return err

    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()

    hits = []
    for i, line in enumerate(lines):
        m = ORDERED_LIST_RE.match(line)
        if not m:
            continue
        if int(m.group(1)) == 1:
            continue
        if i == 0:
            continue  # no previous line to judge
        if lines[i - 1].strip() != "":
            hits.append((i + 1, line[:60]))

    # A standalone image with alt text becomes a Figure in pandoc. Its caption uses the
    # "Image Caption" style, which the template gives no CJK font, so font QA can fail
    # on every attempt.
    fig_hits = []
    in_fence = False
    for i, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or not FIGURE_CAPTION_RE.match(line):
            continue
        prev_blank = i == 0 or lines[i - 1].strip() == ""
        next_blank = i == len(lines) - 1 or lines[i + 1].strip() == ""
        if prev_blank and next_blank:
            fig_hits.append((i + 1, line[:60]))

    if hits:
        log("Known trap: numbered list starts at a number other than 1 and the previous "
            "line is not blank, pandoc may renumber it. Lines:")
        for lineno, snippet in hits:
            print(f"{lineno}: {snippet}")
    if fig_hits:
        log("Known trap: standalone image with a caption in the alt text. The caption "
            "style has no CJK font and font QA can fail every attempt. Fix: write the "
            "caption as a normal text line and put ![](path) on the very next line, "
            "with no blank line between. Lines:")
        for lineno, snippet in fig_hits:
            print(f"{lineno}: {snippet}")
    if hits or fig_hits:
        return 4

    log("lint passed: no known traps found")
    return 0


CJK_PUNCT = "，。：「」？、；！"


def cmd_wordcount(path, max_words=None):
    """Word-style count: CJK characters and full-width punctuation count one each,
    each run of Latin letters or digits counts as one word."""
    err = check_md_file(path)
    if err:
        return err

    with open(path, encoding="utf-8") as f:
        text = f.read()

    cjk = sum(1 for ch in text if "一" <= ch <= "鿿" or ch in CJK_PUNCT)
    words = len(re.findall(r"[A-Za-z0-9]+", text))
    total = cjk + words

    log(f"Word count: {total} (CJK characters and punctuation {cjk} + Latin/digit words {words})")
    if max_words is not None and total > max_words:
        log(f"ERROR: over the limit of {max_words} (by {total - max_words})")
        return 4
    return 0


def strip_trailing_hard_breaks(text):
    """Remove manual trailing backslash line breaks. convert already applies pandoc
    markdown+hard_line_breaks, so a leftover backslash would produce a second break
    and an extra blank line."""
    return TRAILING_BACKSLASH_RE.sub("\n", text)


def check_pdf_fonts(pdf_path, pdffonts=None, good_patterns=None, bad_patterns=None):
    """Return (ok, suspect_fonts, all_fonts).

    Whitelist mode (good_patterns given, used by convert): ok is True only when
    at least one embedded font matches good_patterns, no font matches
    BAD_FONT_PATTERNS, and every font outside STRICT_EXEMPT_FONTS matches
    good_patterns. suspect_fonts lists the non-Latin fonts for logging.

    Blacklist mode (default): ok is True when no font matches bad_patterns
    (BAD_FONT_PATTERNS by default)."""
    pdffonts = pdffonts or shutil.which("pdffonts")
    r = subprocess.run([pdffonts, pdf_path], capture_output=True, text=True)
    all_fonts = []
    for line in r.stdout.splitlines()[2:]:  # first two lines are the header and the rule
        line = line.strip()
        if not line:
            continue
        all_fonts.append(line.split()[0])

    if good_patterns is not None:
        has_good = any(any(pat in f.lower() for pat in good_patterns) for f in all_fonts)
        has_bad = any(any(pat in f.lower() for pat in BAD_FONT_PATTERNS) for f in all_fonts)
        rest = [f for f in all_fonts if not any(e in f.lower() for e in STRICT_EXEMPT_FONTS)]
        all_good = all(any(pat in f.lower() for pat in good_patterns) for f in rest)
        ok = has_good and not has_bad and all_good
        if ok:
            return True, [], all_fonts
        non_cjk = ["liberationserif", "liberationsans", "symbol"]
        suspect = [f for f in all_fonts if not any(n in f.lower() for n in non_cjk)]
        return False, (suspect or all_fonts), all_fonts

    bad_patterns = bad_patterns if bad_patterns is not None else BAD_FONT_PATTERNS
    bad_fonts = [f for f in all_fonts if any(pat in f.lower() for pat in bad_patterns)]
    return (len(bad_fonts) == 0, bad_fonts, all_fonts)


def run_soffice_once(soffice, docx_path, timeout):
    """One soffice conversion with its own profile and output folder, so parallel runs
    don't share a profile lock or overwrite each other. Returns (candidate_pdf or None,
    out_dir). The caller removes out_dir."""
    profile_dir = tempfile.mkdtemp(prefix="md2pdf_profile_")
    out_dir = tempfile.mkdtemp(prefix="md2pdf_out_")
    try:
        r = subprocess.run(
            [soffice, "--headless", f"-env:UserInstallation=file://{profile_dir}",
             "--convert-to", "pdf", docx_path, "--outdir", out_dir],
            capture_output=True, text=True, timeout=timeout,
        )
    except (subprocess.TimeoutExpired, OSError):
        # OSError: the soffice path is invalid. TimeoutExpired: this run hung.
        # Both count as a failed attempt so the outer loop can continue.
        r = None
    finally:
        shutil.rmtree(profile_dir, ignore_errors=True)

    basename = os.path.basename(docx_path)[: -len(".docx")]
    candidate = os.path.join(out_dir, basename + ".pdf")
    if r is not None and r.returncode == 0 and os.path.isfile(candidate) and os.path.getsize(candidate) > 0:
        return candidate, out_dir
    return None, out_dir


def pick_good_pdf(docx_path, soffice, pdffonts, timeout,
                  batch_size=BATCH_SIZE, max_batches=MAX_BATCHES):
    """Run batch_size soffice conversions in parallel, keep the first that passes the
    font QA and delete the rest. If none pass, start another round, up to max_batches.
    Returns (winner_pdf or None, winner_out_dir or None, total_attempts)."""
    total_attempts = 0
    for batch_num in range(1, max_batches + 1):
        log(f"Step 2/2: soffice batch {batch_num}/{max_batches} ({batch_size} in parallel)")
        with concurrent.futures.ThreadPoolExecutor(max_workers=batch_size) as ex:
            results = list(ex.map(
                lambda _: run_soffice_once(soffice, docx_path, timeout), range(batch_size)
            ))

        winner, winner_out_dir = None, None
        for candidate, out_dir in results:
            total_attempts += 1
            if candidate is None:
                log(f"  attempt {total_attempts}: soffice failed or timed out, discarded")
                shutil.rmtree(out_dir, ignore_errors=True)
                continue
            ok, bad_fonts, all_fonts = check_pdf_fonts(
                candidate, pdffonts=pdffonts, good_patterns=GOOD_FONT_PATTERNS
            )
            verdict = "pass" if ok else f"FAIL, fonts outside the whitelist: {bad_fonts}"
            log(f"  attempt {total_attempts}: {all_fonts} | {verdict}")
            if ok and winner is None:
                winner, winner_out_dir = candidate, out_dir
            else:
                shutil.rmtree(out_dir, ignore_errors=True)

        if winner:
            return winner, winner_out_dir, total_attempts

    return None, None, total_attempts


STRIP_PROBE_IN = 200      # probe page height in inches. PDF pages top out near 200 in (14400 pt)
STRIP_BOTTOM_IN = 0.5     # bottom margin in inches, must match pgMar bottom in set_docx_page_height


def set_docx_page_height(docx_path, height_in):
    """Set the docx page to Letter width and the given height in inches, with 0.5 in
    top and bottom margins and 1 in side margins. pandoc's sectPr usually has no
    pgSz, so it is added. Existing pgSz and pgMar are removed first, so the call is
    repeatable."""
    tmp_path = docx_path + ".tmp"
    with zipfile.ZipFile(docx_path) as zin, zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/document.xml":
                x = data.decode("utf-8")
                x = re.sub(r"<w:pgSz[^>]*/>", "", x)
                x = re.sub(r"<w:pgMar[^>]*/>", "", x)
                pg = (f'<w:pgSz w:w="12240" w:h="{int(height_in * 1440)}"/>'
                      '<w:pgMar w:top="720" w:right="1440" w:bottom="720" w:left="1440" '
                      'w:header="360" w:footer="360" w:gutter="0"/>')
                idx = x.rfind("</w:sectPr>")
                if idx < 0:
                    raise ValueError("no sectPr found in docx")
                x = x[:idx] + pg + x[idx:]
                data = x.encode("utf-8")
            zout.writestr(item, data)
    os.replace(tmp_path, docx_path)


def _poppler_tool(name, pdffonts):
    """pdfinfo and pdftoppm ship with pdffonts in poppler, so prefer the same folder."""
    sibling = os.path.join(os.path.dirname(pdffonts), name)
    return sibling if os.path.exists(sibling) else (shutil.which(name) or name)


def pdf_page_count(pdf_path, pdffonts):
    r = subprocess.run([_poppler_tool("pdfinfo", pdffonts), pdf_path], capture_output=True, text=True)
    m = re.search(r"^Pages:\s+(\d+)", r.stdout, flags=re.M)
    return int(m.group(1)) if m else -1


def measure_content_height_in(pdf_path, pdffonts, dpi=20):
    """Render page 1 to a grayscale PGM, find the last row that has ink (pixel < 245)
    and return its distance from the top of the page in inches."""
    r = subprocess.run([_poppler_tool("pdftoppm", pdffonts), "-r", str(dpi), "-gray", "-f", "1", "-l", "1", pdf_path],
                       capture_output=True)
    data = r.stdout
    m = re.match(rb"P5\s+(\d+)\s+(\d+)\s+(\d+)\s", data)  # exactly one whitespace byte, then raw pixels
    if not m:
        return None
    width, height = int(m.group(1)), int(m.group(2))
    pixels = data[m.end():]
    last = 0
    for row in range(height):
        line = pixels[row * width:(row + 1) * width]
        if line and min(line) < 245:
            last = row
    return (last + 1) / dpi


def strip_convert(docx_path, soffice, pdffonts, timeout):
    """Single-page version. Lay out once on a very tall page to measure the content
    height, then lay out again at content height plus the bottom margin, through the
    normal font QA. Returns (winner_pdf, winner_out_dir, total_attempts, error or None)."""
    set_docx_page_height(docx_path, STRIP_PROBE_IN)
    probe, probe_dir = run_soffice_once(soffice, docx_path, timeout)
    if probe is None:
        shutil.rmtree(probe_dir, ignore_errors=True)
        return None, None, 0, "probe layout failed (soffice produced no PDF)"
    pages = pdf_page_count(probe, pdffonts)
    content_in = measure_content_height_in(probe, pdffonts)
    shutil.rmtree(probe_dir, ignore_errors=True)
    if pages != 1 or content_in is None:
        return None, None, 0, (f"content is taller than {STRIP_PROBE_IN} in "
                               f"(probe produced {pages} pages), use the paginated version")
    height_in = content_in * 1.005 + STRIP_BOTTOM_IN + 0.1  # small slack, grows 5% below if a font swap overflows
    log(f"strip: probe content height {content_in:.1f} in, final page height {height_in:.1f} in")
    total = 0
    for _ in range(3):
        set_docx_page_height(docx_path, height_in)
        winner, winner_dir, n = pick_good_pdf(docx_path, soffice, pdffonts, timeout)
        total += n
        if winner is None:
            return None, None, total, None
        if pdf_page_count(winner, pdffonts) == 1:
            return winner, winner_dir, total, None
        # A different font gave slightly taller lines and spilled onto page 2: add 5%
        shutil.rmtree(winner_dir, ignore_errors=True)
        height_in *= 1.05
        log(f"strip: overflowed to page 2, raising page height 5% to {height_in:.1f} in")
    return None, None, total, "still more than one page after 3 re-layouts"


def cmd_convert(path, keep_docx=False, outdir=None, ref_docx=None, soffice=None,
                pdffonts=None, timeout=DEFAULT_TIMEOUT, strip=False):
    ref_docx = find_ref_docx(ref_docx)
    soffice = soffice or find_soffice()
    pdffonts = pdffonts or shutil.which("pdffonts")

    err = check_md_file(path)
    if err:
        return err

    if shutil.which("pandoc") is None:
        log("ERROR: pandoc not found, install with: brew install pandoc" + path_hint("pandoc"))
        return 5
    if not os.path.exists(soffice):
        log(f"ERROR: LibreOffice not found ({soffice}), install with: brew install --cask libreoffice"
            " (or set MD2PDF_SOFFICE)")
        return 5
    if not os.path.exists(ref_docx):
        log(f"ERROR: reference docx not found: {ref_docx} (pass --ref-docx or set MD2PDF_REF_DOCX)")
        return 5
    if not pdffonts or not os.path.exists(pdffonts):
        log("ERROR: pdffonts not found (needed for the font QA), install with: brew install poppler"
            + path_hint("pdffonts"))
        return 5

    path = os.path.abspath(path)
    basename = os.path.basename(path)[: -len(".md")]
    out_dir = os.path.abspath(outdir) if outdir else os.path.dirname(path)
    os.makedirs(out_dir, exist_ok=True)

    docx_path = os.path.join(out_dir, basename + ".docx")
    pdf_path = os.path.join(out_dir, basename + ("_strip.pdf" if strip else ".pdf"))

    with open(path, encoding="utf-8") as f:
        src_text = f.read()
    tmp_md_path = os.path.join(os.path.dirname(path), f".{basename}__md2pdf_tmp__.md")
    with open(tmp_md_path, "w", encoding="utf-8") as f:
        f.write(strip_trailing_hard_breaks(src_text))

    try:
        log(f"Step 1/2: pandoc {path} -> {docx_path} (markdown+hard_line_breaks: a single Enter is a line break)")
        try:
            r = subprocess.run(
                ["pandoc", "-f", "markdown+hard_line_breaks", tmp_md_path,
                 f"--reference-doc={ref_docx}", "-o", docx_path],
                capture_output=True, text=True, timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            log(f"ERROR: pandoc timed out ({timeout}s)")
            return 2
        if r.returncode != 0:
            log(f"ERROR: pandoc failed (returncode={r.returncode})")
            print(r.stderr, file=sys.stderr)
            return 2
    finally:
        os.remove(tmp_md_path)

    if strip:
        winner, winner_out_dir, total_attempts, strip_err = strip_convert(docx_path, soffice, pdffonts, timeout)
        if strip_err:
            log(f"FAIL: strip version failed: {strip_err}. Kept {docx_path}")
            return 4
    else:
        winner, winner_out_dir, total_attempts = pick_good_pdf(docx_path, soffice, pdffonts, timeout)
    if winner is None:
        log(f"FAIL: {MAX_BATCHES} rounds and {total_attempts} attempts never produced a PDF "
            f"where every font is PingFang TC. Kept {docx_path}. "
            "If every attempt lists Menlo, a symbol in the text has no PingFang TC glyph: "
            "remove or replace it in a scratch copy. "
            "If the text has paired $ signs, escape them as \\$ (pandoc reads $...$ as math). "
            "Otherwise just rerun convert.")
        return 4

    shutil.move(winner, pdf_path)
    shutil.rmtree(winner_out_dir, ignore_errors=True)

    size = os.path.getsize(pdf_path)
    if keep_docx:
        log(f"Kept intermediate file: {docx_path}")
    else:
        os.remove(docx_path)

    log(f"PDF: {pdf_path} ({size} bytes)")
    return 0


def run_selftest():
    results = []

    def check(name, cond):
        results.append((name, cond))
        log(f"[{'PASS' if cond else 'FAIL'}] {name}")

    with tempfile.TemporaryDirectory(prefix="md2pdf test with spaces ") as tmp:
        def write(name, text):
            p = os.path.join(tmp, name)
            with open(p, "w", encoding="utf-8") as f:
                f.write(text)
            return p

        def fake_pdffonts(name, font_names):
            """A shell script that prints a fixed pdffonts-style table."""
            lines = ["#!/bin/sh", "echo 'name type encoding emb sub uni object ID'",
                     "echo '--- --- --- --- --- --- ---'"]
            lines += [f"echo '{n} TrueType WinAnsi yes yes yes 20 0'" for n in font_names]
            fp = write(name, "\n".join(lines) + "\n")
            os.chmod(fp, 0o755)
            return fp

        missing = lambda n: os.path.join(tmp, n)  # a path that does not exist

        # lint: numbered lists
        check("lint hit (4. with no blank line before) -> exit 4",
              cmd_lint(write("hit.md", "first line\n4. item\n")) == 4)
        check("lint clean (4. with blank line before) -> exit 0",
              cmd_lint(write("ok1.md", "first line\n\n4. item\n")) == 0)
        check("lint clean (list starts at 1.) -> exit 0",
              cmd_lint(write("ok2.md", "first line\n1. item\n")) == 0)

        # lint: standalone captioned image hits; empty alt, same-paragraph caption, code fence do not
        check("lint hit (standalone image with caption) -> exit 4",
              cmd_lint(write("fig_hit.md", "before\n\n![Figure 1 survival rate](assets/a.png){width=100%}\n\nafter\n")) == 4)
        check("lint clean (empty alt) -> exit 0",
              cmd_lint(write("fig_empty.md", "before\n\n![](assets/a.png){width=100%}\n\nafter\n")) == 0)
        check("lint clean (caption in same paragraph as image) -> exit 0",
              cmd_lint(write("fig_same.md", "before\n\n**Figure 1**\n![](assets/a.png){width=100%}\n\nafter\n")) == 0)
        check("lint clean (example inside a code fence) -> exit 0",
              cmd_lint(write("fig_fence.md", "example:\n\n```\n\n![caption](a.png)\n\n```\n")) == 0)

        # set_docx_page_height: adds pgSz when missing, repeat calls keep one pair
        mini = os.path.join(tmp, "mini.docx")
        with zipfile.ZipFile(mini, "w") as z:
            z.writestr("word/document.xml",
                       "<w:document><w:body><w:p/><w:sectPr><w:footnotePr/></w:sectPr></w:body></w:document>")
        set_docx_page_height(mini, 100)
        set_docx_page_height(mini, 50)
        with zipfile.ZipFile(mini) as z:
            mx = z.read("word/document.xml").decode("utf-8")
        check("set_docx_page_height: one pgSz and one pgMar, height from the last call",
              mx.count("<w:pgSz") == 1 and f'w:h="{50 * 1440}"' in mx and mx.count("<w:pgMar") == 1)

        # exit 3
        check("lint missing file -> exit 3", cmd_lint(missing("not_exist.md")) == 3)
        not_md = write("file.txt", "x")
        check("lint non-.md -> exit 3", cmd_lint(not_md) == 3)
        check("convert non-.md -> exit 3", cmd_convert(not_md) == 3)
        check("convert missing file -> exit 3", cmd_convert(missing("nope.md")) == 3)

        # exit 5 via injected fake tools (nothing real is touched)
        valid_md = write("mixed 中文 name.md", "# Title\n\n內容 content\n")
        check("reference docx missing (injected) -> exit 5",
              cmd_convert(valid_md, ref_docx=missing("no_such_ref.docx")) == 5)
        check("soffice missing (injected) -> exit 5",
              cmd_convert(valid_md, soffice=missing("no_such_soffice")) == 5)
        check("pdffonts missing (injected) -> exit 5",
              cmd_convert(valid_md, pdffonts=missing("no_such_pdffonts")) == 5)

        # reference docx resolution order
        saved_env = os.environ.pop("MD2PDF_REF_DOCX", None)
        try:
            check("ref docx default sits next to the script",
                  find_ref_docx() == str(Path(__file__).resolve().parent / "reference_pingfang.docx"))
            os.environ["MD2PDF_REF_DOCX"] = "/env/ref.docx"
            check("ref docx: env var overrides the default", find_ref_docx() == "/env/ref.docx")
            check("ref docx: argument overrides the env var", find_ref_docx("/arg/ref.docx") == "/arg/ref.docx")
        finally:
            os.environ.pop("MD2PDF_REF_DOCX", None)
            if saved_env is not None:
                os.environ["MD2PDF_REF_DOCX"] = saved_env

        # wordcount: 3 CJK characters + 1 Latin word = 4
        wc_md = write("wc.md", "中文字 test\n")
        check("wordcount without --max -> exit 0", cmd_wordcount(wc_md) == 0)
        check("wordcount under --max (4 <= 10) -> exit 0", cmd_wordcount(wc_md, max_words=10) == 0)
        check("wordcount over --max (4 > 2) -> exit 4", cmd_wordcount(wc_md, max_words=2) == 4)
        check("wordcount missing file -> exit 3", cmd_wordcount(missing("nope.md")) == 3)

        # trailing backslash cleanup
        check("strip_trailing_hard_breaks removes trailing backslashes",
              strip_trailing_hard_breaks("line one\\\nline two\n") == "line one\nline two\n")
        check("strip_trailing_hard_breaks leaves normal text alone",
              strip_trailing_hard_breaks("plain paragraph.\n") == "plain paragraph.\n")

        # check_pdf_fonts against fake pdffonts output
        fake_pdf = write("fake.pdf", "")
        fp_bad = fake_pdffonts("fp_bad.sh", ["BAAAAA+HanziPenSC-W3", "CAAAAA+LiberationSerif"])
        ok, bad, allf = check_pdf_fonts(fake_pdf, pdffonts=fp_bad)
        check("blacklist mode flags HanziPenSC", not ok and "BAAAAA+HanziPenSC-W3" in bad)
        check("check_pdf_fonts returns the full font list (2)", len(allf) == 2)

        fp_wawa = fake_pdffonts("fp_wawa.sh", ["BAAAAA+DFWaWaTC-W5"])
        ok, bad, _ = check_pdf_fonts(fake_pdf, pdffonts=fp_wawa)
        check("blacklist mode flags DFWaWaTC-W5", not ok and "BAAAAA+DFWaWaTC-W5" in bad)

        fp_song = fake_pdffonts("fp_song.sh", ["BAAAAA+STSongti-TC-Regular"])
        ok, bad, _ = check_pdf_fonts(fake_pdf, pdffonts=fp_song)
        check("blacklist mode accepts STSongti-TC", ok and bad == [])

        fp_pf = fake_pdffonts("fp_pf.sh", ["BAAAAA+PingFangTC-Regular", "CAAAAA+LiberationSerif"])
        ok, bad, _ = check_pdf_fonts(fake_pdf, pdffonts=fp_pf, good_patterns=GOOD_FONT_PATTERNS)
        check("whitelist mode: PingFangTC-Regular passes", ok and bad == [])
        ok, bad, _ = check_pdf_fonts(fake_pdf, pdffonts=fp_song, good_patterns=GOOD_FONT_PATTERNS)
        check("whitelist mode: STSongti-TC fails", not ok and "BAAAAA+STSongti-TC-Regular" in bad)

        for variant, expect_pass in [("PingFangTC-Regular", True), ("PingFangHK-Regular", False),
                                     ("PingFangMO-Regular", False), ("PingFangSC-Regular", False)]:
            fp = fake_pdffonts(f"fp_{variant}.sh", [f"BAAAAA+{variant}", "CAAAAA+LiberationSerif"])
            okv, badv, _ = check_pdf_fonts(fake_pdf, pdffonts=fp, good_patterns=GOOD_FONT_PATTERNS)
            check(f"whitelist is TC only: {variant} {'passes' if expect_pass else 'is rejected'}",
                  okv == expect_pass and (badv == [] if expect_pass else f"BAAAAA+{variant}" in badv))

        fp_mixed = fake_pdffonts("fp_mixed.sh", ["BAAAAA+PingFangTC-Regular", "CAAAAA+DFWaWaTC-W5"])
        ok, bad, _ = check_pdf_fonts(fake_pdf, pdffonts=fp_mixed, good_patterns=GOOD_FONT_PATTERNS)
        check("whitelist mode: PingFangTC mixed with DFWaWaTC is rejected",
              not ok and "CAAAAA+DFWaWaTC-W5" in bad)

        # strict rule: an unknown font mixed with PingFangTC must fail, exempt fonts must not
        for unknown in ["LiGothicMed", "FZLTTHB--B51-0", "STYuanti-TC-Regular", "Menlo-Regular"]:
            fp = fake_pdffonts(f"fp_strict_{unknown}.sh",
                               ["BAAAAA+PingFangTC-Regular", "CAAAAA+LiberationSerif", "DAAAAA+Symbol",
                                f"EAAAAA+{unknown}"])
            ok, bad, _ = check_pdf_fonts(fake_pdf, pdffonts=fp, good_patterns=GOOD_FONT_PATTERNS)
            check(f"strict: PingFangTC mixed with {unknown} is rejected", not ok and f"EAAAAA+{unknown}" in bad)

        fp_ex = fake_pdffonts("fp_exempt.sh",
                              ["BAAAAA+PingFangTC-Regular", "CAAAAA+PingFangTC-Semibold",
                               "DAAAAA+LiberationSerif-Italic", "EAAAAA+Symbol",
                               "FAAAAA+AppleColorEmoji", "GAAAAA+CourierNewPS-BoldMT"])
        ok, bad, _ = check_pdf_fonts(fake_pdf, pdffonts=fp_ex, good_patterns=GOOD_FONT_PATTERNS)
        check("strict: PingFangTC plus exempt fonts (Liberation, Symbol, emoji, Courier) passes",
              ok and bad == [])

        # PATH hint
        expect_hint = os.path.exists("/opt/homebrew/bin/pandoc") or os.path.exists("/usr/local/bin/pandoc")
        check("path_hint: hint iff pandoc lives in a Homebrew folder", bool(path_hint("pandoc")) == expect_hint)
        check("path_hint: unknown tool gives an empty string", path_hint("__no_such_tool_md2pdf__") == "")

        # retry cap: a soffice path that always fails must stop after max_batches rounds
        fake_docx = write("fake.docx", "")
        t0 = time.monotonic()
        w, w_dir, n = pick_good_pdf(fake_docx, missing("no_such_soffice"), fp_song, timeout=5, max_batches=2)
        elapsed = time.monotonic() - t0
        check("retry cap: all-failing soffice returns None", w is None and w_dir is None)
        check("retry cap: stops after max_batches rounds (returns within 10 s)", elapsed < 10)
        check("retry cap: attempts = batch_size x max_batches", n == BATCH_SIZE * 2)

        # real conversions, only when every dependency is present
        soffice, ref, pf = find_soffice(), find_ref_docx(), shutil.which("pdffonts")
        if shutil.which("pandoc") and os.path.exists(soffice) and os.path.exists(ref) and pf:
            stem = os.path.join(tmp, "mixed 中文 name")
            code = cmd_convert(valid_md)
            check("real convert -> exit 0", code == 0)
            check("real convert: PDF exists and is non-empty",
                  os.path.isfile(stem + ".pdf") and os.path.getsize(stem + ".pdf") > 0)
            _, _, real_fonts = check_pdf_fonts(stem + ".pdf", pdffonts=pf)
            check("real convert: CJK font is PingFang TC (HK, MO, SC do not count)",
                  any("pingfangtc" in f.lower() for f in real_fonts)
                  and not any(v in f.lower() for f in real_fonts for v in ("pingfanghk", "pingfangmo", "pingfangsc")))
            check("real convert: intermediate .docx removed", not os.path.exists(stem + ".docx"))
            check("real convert: temporary md removed",
                  not any(n.startswith(".") and n.endswith("__md2pdf_tmp__.md") for n in os.listdir(tmp)))

            check("--keep-docx -> exit 0", cmd_convert(valid_md, keep_docx=True) == 0)
            check("--keep-docx keeps the .docx", os.path.exists(stem + ".docx"))

            lb_md = write("linebreak.md", "第一行 line one\n第二行 line two\n")
            code = cmd_convert(lb_md, keep_docx=True)
            with zipfile.ZipFile(os.path.join(tmp, "linebreak.docx")) as z:
                doc_xml = z.read("word/document.xml").decode("utf-8")
            check("single Enter becomes a hard break (<w:br/>)", code == 0 and "<w:br" in doc_xml)

            strip_md = write("strip test.md",
                             "# Title\n\n" + "\n\n".join(f"Paragraph {i}，這段內容用來把頁面撐高。 " * 3
                                                       for i in range(60)) + "\n")
            code = cmd_convert(strip_md, strip=True)
            strip_pdf = os.path.join(tmp, "strip test_strip.pdf")
            check("--strip -> exit 0", code == 0)
            check("--strip writes _strip.pdf and leaves no .docx",
                  os.path.isfile(strip_pdf) and not os.path.exists(os.path.join(tmp, "strip test.docx")))
            check("--strip output is exactly 1 page", pdf_page_count(strip_pdf, pf) == 1)
            _, _, strip_fonts = check_pdf_fonts(strip_pdf, pdffonts=pf)
            check("--strip font is still PingFang TC", any("pingfangtc" in f.lower() for f in strip_fonts))
        else:
            log("[SKIP] real conversion tests: pandoc, soffice, reference docx or pdffonts is missing")

    passed = sum(1 for _, c in results if c)
    total = len(results)
    log(f"selftest result: {passed}/{total} passed")
    return 0 if passed == total else 1


def main():
    parser = argparse.ArgumentParser(prog="md2pdf.py", description="Markdown to PDF converter (PingFang TC)")
    parser.add_argument("--selftest", action="store_true", help="run the built-in tests in a temporary folder")
    parser.add_argument("--version", action="version", version=f"md2pdf {VERSION}")
    sub = parser.add_subparsers(dest="command")

    p_lint = sub.add_parser("lint", help="scan for known Markdown traps")
    p_lint.add_argument("file")

    p_conv = sub.add_parser("convert", help="MD -> DOCX -> PDF")
    p_conv.add_argument("file")
    p_conv.add_argument("--keep-docx", action="store_true", help="keep the intermediate .docx")
    p_conv.add_argument("--strip", action="store_true",
                        help="single tall page, no page breaks; writes <name>_strip.pdf")
    p_conv.add_argument("--outdir", default=None, help="output folder (default: next to the .md)")
    p_conv.add_argument("--ref-docx", default=None,
                        help="reference docx (default: $MD2PDF_REF_DOCX, else reference_pingfang.docx next to this script)")

    p_wc = sub.add_parser("wordcount", help="Word-style count, --max sets a hard limit")
    p_wc.add_argument("file")
    p_wc.add_argument("--max", type=int, default=None)

    args = parser.parse_args()

    if args.selftest:
        sys.exit(run_selftest())

    if args.command == "lint":
        sys.exit(cmd_lint(args.file))
    elif args.command == "convert":
        sys.exit(cmd_convert(args.file, keep_docx=args.keep_docx, outdir=args.outdir,
                             ref_docx=args.ref_docx, strip=args.strip))
    elif args.command == "wordcount":
        sys.exit(cmd_wordcount(args.file, max_words=args.max))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
