QA-check a Marp deck before delivery, then export it to PDF. The mechanical work lives in `marp_export.py`, which sits in the repo root next to this file.

Usage:
- `/marp-export` exports the Marp .md currently open in the IDE.
- `/marp-export path/to/deck.md` exports the given file.

Prerequisites:
- Python 3 and Node.js with `npx`. Marp CLI runs through `npx`, so there's nothing else to install. The first export downloads the package.
- If `npx` isn't found on PATH, the script checks Homebrew and nvm locations before giving up with exit 5. When you run `npx` yourself, add those directories to PATH first.

Steps:

1. Confirm the target .md path. Use the one the user gave, or the file currently open in the IDE.

2. Run the QA check from the repo root, or use the full path to `marp_export.py`. Export only if it passes.

   ```bash
   python3 marp_export.py qa deck.md
   ```

   It scans for two things:
   - Draft markers: `TODO`, `FIXME`, `TBD`, `XXX`, and the full-width `【` bracket. Each hit is printed with its line number.
   - Local image references (`![alt](path)`, including `![bg fit](path)`) whose file doesn't exist. Remote images aren't checked, and each one gets a WARN line. Tell the user about every remote image, since it can break offline.

   On exit 4, paste the output and ⏸ wait for the user. Clearing markers, adding images or removing references is the user's call.

3. Export the PDF, then verify it.

   ```bash
   python3 marp_export.py export deck.md
   python3 marp_export.py verify deck.md
   ```

   `export` runs `npx --yes @marp-team/marp-cli@latest deck.md --pdf --allow-local-files --no-stdin -o deck.pdf` from the deck's folder. It accepts `--timeout SECONDS` and defaults to 300. `verify` checks that the sibling .pdf exists, is larger than 0 bytes and isn't older than the .md. Paste both outputs and report the PDF path and size.

   On failure, show the error output and check npx, the Node version and network access.

Subcommands:

| Command | What it does |
| --- | --- |
| `qa <file.md>` | Draft-marker scan and local image existence check |
| `export <file.md>` | PDF export through Marp CLI |
| `verify <file.md>` | Existence, size and freshness check on the PDF |

Run `python3 marp_export.py --selftest` to test the script itself in a temp folder.

Exit codes:

| Code | Meaning |
| --- | --- |
| 0 | Success |
| 2 | External command (npx) failed or timed out |
| 3 | File doesn't exist or isn't a .md |
| 4 | Hard gate FAIL: QA found problems, or verify failed |
| 5 | Environment missing: npx not found |

Gotchas:
- marp-cli often hangs because stdin stays open. If you run it by hand, add `--no-stdin` and redirect input with `< /dev/null`. The script already does both.
- Image paths resolve relative to the .md file's folder, so paths with spaces are fine.
