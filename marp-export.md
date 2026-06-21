QA-check a Marp deck before delivery, then export it to PDF.

Usage:
- `/marp-export` — export the Marp .md currently open in the IDE
- `/marp-export /path/to/file.md` — export the given file

Steps:

1. Confirm the target .md path:
   - User gave one → use it.
   - None → take the file currently open in the IDE.

2. QA check (export only if everything passes):

   **2-A Draft-marker scan**
   ```bash
   grep -n "【" {target file}
   ```
   If there's output → list the line numbers and content, ⏸ ask the user to confirm whether to clear them before continuing.

   **2-B Image-path check**
   Scan every `![` reference; confirm the `assets/` folder exists and each image file is actually present. If any image is missing → list them and ⏸ wait for the user.

3. Export the PDF:
   ```bash
   cd "{target file's folder}"
   npx --yes @marp-team/marp-cli@latest "{filename}.md" --pdf --allow-local-files -o "{filename}.pdf"
   ```

4. Confirm the PDF was created (`ls "{filename}.pdf"`):
   - Success → report the PDF path and file size.
   - Failure → output the error (npx issue? node version?).
