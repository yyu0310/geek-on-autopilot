---
name: docx-gen
description: Write a Word document with code for full control over fonts, colors, and tables, then export a clean PDF.
---

Write a Word document with per-paragraph control (different fonts and colors, tables) and export it as a PDF. The library underneath is dolanmiu/docx (npm). It costs more tokens than converting Markdown, and what you get in return is control over every run of text.

Usage:
- `/docx-gen <what you need>`: describe the content and layout of the document, and the PDF is generated directly

## Setup

`docx_pdf.py` lives in the repo root, next to `md2pdf.py`, which it imports for the font check. Keep the two files in the same folder. The generator scripts live in `docx-gen-tools/workspace/`. Run this once:

```bash
cd docx-gen-tools && npm install
```

`docx-gen-tools/workspace/example_qa_test.js` is a verified, complete example with tables, mixed formatting, and CJK text. Copy its structure for a new document and change the content. The setup command assumes you start in the repo root. Otherwise, use the full path to it. After that, every command below runs from `docx-gen-tools/workspace/`, which is why the script is reached as `../../docx_pdf.py`.

## Steps

1. **Write a `<name>.js` script in `docx-gen-tools/workspace/`.** It has to live in this folder, or `require('docx')` can't resolve. Don't open another folder. Every rule below comes from a trap hit in real conversions.

   - Pass every `TextRun` `font` as an object `{ ascii, eastAsia, hAnsi }` with the same font name in all three keys, never a plain string. A plain string sets only the Latin font, and Chinese text falls to whatever LibreOffice guesses.
   - Give the `Document` constructor `styles.default.document.run.font` and the `run.font` of `heading1`, `heading2`, and `title`, all with the same font object. Headings resolve through their own style path and don't inherit the font of a `TextRun`.
   - **Never use `italics: true` anywhere in the document.** If any run sets italics, even a pure English one, LibreOffice headless swaps all the CJK fonts of the document for decorative faces such as Xingkai. The failure is deterministic: converting again doesn't help. For an italic look in Chinese or English, use underline `underline: {}` or a color.
   - Any table with two or more columns needs `columnWidths` (an array) on the `Table` constructor. Setting `width` only on each `TableCell` isn't enough: LibreOffice renders the whole table as a collapsed black block and the data disappears.
   - Header shading uses `shading: { type: ShadingType.CLEAR, fill: 'COLORCODE' }`. Never `SOLID`, which turns the cell black.
   - Generate repeated content (table rows, lists) with a for loop instead of writing each item out. It saves tokens and nothing gets missed in an edit.

2. **Run it:**

   ```bash
   cd docx-gen-tools/workspace && node <name>.js
   ```

3. **Lint.** A mechanical check for the italics trap. Run it first, every time:

   ```bash
   python3 ../../docx_pdf.py lint "<name>.js"
   ```

   Exit 4 prints the matching line numbers. Remove the italics and continue. Don't skip this.

4. **Convert to PDF.** LibreOffice headless with an automatic font QA, retrying up to 6 times:

   ```bash
   python3 ../../docx_pdf.py convert "<name>.docx"
   ```

   Paste the output as is. Exit codes:
   - 0 success
   - 2 soffice failed or timed out
   - 3 input file missing or wrong extension
   - 4 hard gate failed: a lint hit, a failed PDF check, or font QA still failing after the retries. If it fails here, first check step 1 for stray italics or a missing `columnWidths`
   - 5 missing dependency (soffice or pdffonts). Relay the install command it prints

5. **Check the PDF.** The `.docx` intermediate file stays in `workspace/` by default (pass `--remove-docx` to delete it after a successful conversion, or when the user wants a clean folder). Render a page to an image with `pdftoppm -jpeg -r 90 -f <page> -l <page> <pdf> <name>` only when the page count or word count looks wrong. Don't do it every time, because screenshots are expensive. `pdftotext <pdf> -` is usually enough to see whether the CJK text came out garbled.

## Requirements

Check these when something fails:
- Node.js and the `docx` package (`npm install` in `docx-gen-tools/`)
- LibreOffice: `brew install --cask libreoffice`
- Poppler (`pdffonts`, `pdftotext`, `pdftoppm`): `brew install poppler`
- PingFang TC ships with macOS. On other systems set `CJK_FONT` in your script to a CJK font you have installed. The font check only rejects known handwriting and decorative fonts

Exit codes for the scripts: 0 success, 2 external command or network failure, 3 file not found, 4 hard gate failed, 5 missing dependency.
