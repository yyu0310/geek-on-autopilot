Convert a Markdown file to PDF using the PingFang TC font template.

⚙️ One-time setup before use: replace the placeholder below with your actual value, save, and you're ready.

```
REFDIR = /your/local/path/to/geek-on-autopilot
```

`reference_pingfang.docx` is bundled in this repo. After cloning, just set REFDIR to the repo root.

Usage:
- `/md-to-pdf` — convert the .md currently open in the IDE
- `/md-to-pdf /path/to/file.md` — convert the .md at the given path

Steps:

1. Confirm the target MD path:
   - User gave a path → use it.
   - None → take the path of the file open in the IDE.

2. Check for formatting traps (a numbered list needs a blank line before it):
   Scan the MD content for numbered lists that don't start at 1 (`4.`, `5.`, etc.) and check whether there's a blank line before them. If there's a formatting problem, list the line numbers and let the user decide whether to fix it before converting.

3. Run the conversion (two steps):

```bash
FILE="<target MD path>"
DIR=$(dirname "$FILE")
BASENAME=$(basename "$FILE" .md)
REFDIR="<geek-on-autopilot repo path>"

# Step 1: MD → DOCX
pandoc "$FILE" --reference-doc="$REFDIR/reference_pingfang.docx" -o "$DIR/$BASENAME.docx"

# Step 2: DOCX → PDF
/Applications/LibreOffice.app/Contents/MacOS/soffice --headless --convert-to pdf "$DIR/$BASENAME.docx" --outdir "$DIR"
```

4. Confirm the PDF was created (`ls "$DIR/$BASENAME.pdf"`):
   - Success → delete the intermediate file `rm "$DIR/$BASENAME.docx"` and report the PDF output path.
   - Failure → output the error and diagnose the cause (pandoc not installed? wrong LibreOffice path? font template not found?); keep the .docx for debugging.

Requirements (check these on failure):
- pandoc: `brew install pandoc`
- LibreOffice: `brew install --cask libreoffice`
- Font template: `reference_pingfang.docx` at REFDIR (bundled in this repo)
