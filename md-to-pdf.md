Convert a Markdown file to PDF with the PingFang TC font. Everything runs locally, so it's safe for confidential documents.

Usage:
- `/md-to-pdf` converts the .md file currently open in the IDE
- `/md-to-pdf /path/to/file.md` converts the .md file at that path

Setup: `md2pdf.py` and `reference_pingfang.docx` live in the repo root and must stay in the same folder. The script finds the template next to itself. To use another template, pass `--ref-docx PATH` or set `MD2PDF_REF_DOCX`. The commands below assume you run them from the repo root. Otherwise use the full path to `md2pdf.py`.

Prerequisites:
- pandoc: `brew install pandoc`
- LibreOffice: `brew install --cask libreoffice`
- poppler, for the `pdffonts` font check: `brew install poppler`
- PingFang TC ships with macOS

Steps:

1. Confirm the target path. Use the path the user gave, or the file open in the IDE.

2. Run lint:

```bash
python3 md2pdf.py lint "<file.md>"
```

Exit 4 means a known trap was found. List the line numbers and let the user decide whether to fix them before converting. Lint checks two things. A numbered list that starts above 1 needs a blank line before every such item, though pitfall 8 covers a catch. A standalone `![caption](path)` needs the fix in pitfall 3.

3. Convert:

```bash
python3 md2pdf.py convert "<file.md>"
```

The PDF lands next to the source file. Add `--strip` for one continuous page with no page breaks, which keeps tables from splitting. It writes `<name>_strip.pdf` and keeps the normal PDF. Add `--keep-docx` to keep the intermediate file, and `--outdir DIR` to write elsewhere.

4. If the document has a word limit, run `python3 md2pdf.py wordcount "<file.md>" --max N` before converting. Exit 4 means over the limit.

5. Report the script output as is. Exit codes:
- 0 success
- 2 pandoc or LibreOffice failed, and the .docx is kept for debugging
- 3 the file doesn't exist or isn't a .md file
- 4 hard gate failed, from lint, wordcount, the PDF check, or font QA that kept failing
- 5 a dependency is missing, see pitfall 5 first

Known pitfalls:

1. **LibreOffice picks CJK fonts at random on macOS.** The same docx can come out in a different font on each run, and the template's font name doesn't matter. The script converts several copies in parallel, checks each with `pdffonts`, and keeps the first one where every font is PingFang TC, retrying up to 20 rounds. It takes about 15 seconds on average and up to about 45 seconds in the worst case. Don't switch to a manual conversion. Verify with `pdffonts file.pdf` if you ever convert by hand, and redo it when the fonts are wrong.

2. **A single Enter is a line break.** The script calls `pandoc -f markdown+hard_line_breaks`, and it strips trailing backslashes from a temporary copy first so old files don't get double breaks. The original file is never modified.

3. **Don't put a caption in `![caption](path)` on its own line.** Pandoc turns it into a Figure and the caption gets the Image Caption style, which has no CJK font. Font QA then fails on every attempt. Write the caption as a normal text line and put `![](path){width=85%}` on the very next line with no blank line between. Image paths resolve from the current working directory, so `cd` to the .md folder first.

4. **Paired `$` signs are read as LaTeX math.** Text like `$AAPL and $MSFT` becomes italic serif math with a fallback font, and font QA fails every round. Escape each one as `\$` in a scratch copy, for example `sed -i '' 's/\$/\\$/g'`. The PDF looks the same and the original stays untouched. To confirm the cause, run `unzip -p file.docx word/document.xml | grep -o '<m:oMath>' | wc -l`. A result above 0 means math was detected.

5. **Exit 5 is often a PATH problem.** Claude Code's shell frequently lacks `/opt/homebrew/bin`, so tools that are installed look missing. Run `export PATH="/opt/homebrew/bin:$PATH"` and retry. Only treat the tool as missing if `ls /opt/homebrew/bin` doesn't list it.

6. **Symbols that PingFang TC lacks drag in Menlo.** LibreOffice falls back to Menlo-Regular for a glyph PingFang TC doesn't have, and every attempt then fails the font check, even ones where the body font is right. A flag symbol such as `⚑` (U+2691) triggers it. The signature is `Menlo-Regular` in the suspect fonts of nearly every failed attempt. Find the odd character, remove or replace it in a scratch copy, and convert again. Emoji with a variant selector such as `⚠️` use AppleColorEmoji and are exempt.

7. **Font QA expects CJK text.** The check accepts only PingFang TC. A document with no CJK text at all falls back to Liberation Serif, and list bullets use the Symbol font, so `convert` burns all 120 attempts and exits 4. This tool is built for Chinese and mixed Chinese and English documents. For English-only files, run plain `pandoc` and LibreOffice without the font check.

8. **The blank-line fix for numbered lists can backfire.** Adding blank lines makes pandoc read the whole list as loose. In this template, items 2 and up can then render as deeper-indented sublists with large gaps between items. It happens most with text you quote verbatim that already carries its own numbers, like a pasted prompt. That text doesn't need list semantics. Escape the period in each number as `N\.` so pandoc treats the lines as plain text, then check the numbering with `pdftotext -layout`.

Self-check: `python3 md2pdf.py --selftest` runs the built-in tests inside a temporary folder.
