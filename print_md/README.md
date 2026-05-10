# print_md — Setup & Usage Guide

Convert Obsidian markdown scenes to clean, print-ready PDFs with running
headers, footers, frontmatter, and optional double-spacing.

---

## What You Get

Every PDF includes:
- **Header** — filename (left) · scene title from frontmatter (right)
- **Footer** — print date (left) · page "1 / 10" numbering (right)
- **Rendered markdown** — headings, italics, bold, blockquotes, lists, tables
- **`--frontmatter` / `-f` flag** — render YAML frontmatter as a metadata card (off by default)
- **`--double-space` / `-d` flag** — for proofreading printouts

---

## One-Time Setup

### 1 — Install Python dependencies

Open Terminal and run:

```bash
pip3 install python-frontmatter markdown weasyprint
```

> WeasyPrint may take a minute to install — it pulls in several rendering libraries.

Or, for a self-contained install, create a local virtual environment:

```bash
git clone https://github.com/tomboo/vaults-scripts.git
cd /path/to/vaults-scripts/print_md
./install.sh
```

The installer creates `print_md/.venv/`, installs the requirements, verifies
the imports, and prints the exact Obsidian Shell Commands entries for your
machine.

### 2 — Save the script

Put the `print_md/` folder somewhere permanent. Location doesn't matter as long as it won't accidentally get deleted. Good options:

| Location | Good if… |
|---|---|
| `~/scripts/print_md/` | You already have a general scripts folder |
| `~/Documents/print_md/` | You prefer keeping things in Documents |
| Inside the Obsidian vault | You want everything in one place |

Wherever you put it, update the path in the Shell Commands settings to match.

---

## Terminal Usage

```bash
# Single file
python3 ~/scripts/print_md/print_md.py chapter_01.md

# Single file, double-spaced (proofreading)
python3 ~/scripts/print_md/print_md.py chapter_01.md --double-space

# Single file, with frontmatter card
python3 ~/scripts/print_md/print_md.py chapter_01.md --frontmatter

# Multiple files — PDF lands next to each .md file
python3 ~/scripts/print_md/print_md.py scenes/*.md

# Send all PDFs to a specific folder
python3 ~/scripts/print_md/print_md.py scenes/*.md --output-dir prints/
```

The PDF is written to `scripts/tmp/` by default, keeping your vault folders clean.

---

## Obsidian Integration (Shell Commands Plugin)

This lets you print the current Markdown file with a hotkey or from the
Command Palette. The reliable path is to call `print_md.py` directly with
`{{file_path:absolute}}`; no workspace-inspection wrapper is needed.

### Install the plugin

1. Obsidian → **Settings → Community plugins → Browse**
2. Search **Shell commands** (by Teemu Vainio)
3. Install → Enable

### Add the commands

Go to **Settings → Shell commands → + New shell command**.

Use absolute paths for both Python and the script. If you use a virtual
environment, point to its `bin/python`. If not, use the full path printed by
`command -v python3` after installing the requirements.

**Command 1 — Print Scene**
```bash
/ABSOLUTE/PATH/TO/python3 /ABSOLUTE/PATH/TO/print_md.py {{file_path:absolute}}
```
- Alias: `Print Scene to PDF`
- Assign hotkey: `Cmd+Shift+P` (or whatever feels right)

**Command 2 — Print Scene (Double-spaced)**
```bash
/ABSOLUTE/PATH/TO/python3 /ABSOLUTE/PATH/TO/print_md.py {{file_path:absolute}} --double-space
```
- Alias: `Print Scene to PDF (Double-spaced)`
- Assign hotkey: `Cmd+Shift+D`

**Command 3 — Print Scene (with frontmatter)**
```bash
/ABSOLUTE/PATH/TO/python3 /ABSOLUTE/PATH/TO/print_md.py {{file_path:absolute}} --frontmatter
```
- Alias: `Print Scene to PDF (with Frontmatter)`

### Shell Commands variables used
| Variable | Expands to |
|---|---|
| `{{file_path:absolute}}` | Shell-escaped absolute path to the currently open file |

Do not wrap `{{file_path:absolute}}` in quotes. Shell Commands already escapes path characters for the shell; quoting it would make the backslashes literal.

### After setup
Open any `.md` scene file → `Cmd+P` → type "Print" → hit Enter.
By default, PDFs are written to `scripts/tmp/`, keeping your vault folders
clean. Pass `--output-dir` if you want a different location.

---

## Frontmatter Support

YAML frontmatter is parsed but hidden by default. Pass `--frontmatter` (or `-f`) to render it as a metadata card at the top of the PDF. The `title` field is always used in the running header regardless. Example:

```yaml
---
title: The Glass Garden
project: Echoes of the Hollow Crown
chapter: 3
scene: 2
pov: Mirela
status: draft
tags: [tension, magic, betrayal]
---
```

If there is no `title` field, the filename is used in its place.

---

## Output Location

| Scenario | PDF location |
|---|---|
| Default | `scripts/tmp/` |
| `--output-dir prints/` | Inside `prints/` relative to where you run the command |
| Obsidian Shell Commands | `scripts/tmp/` |

---

## Troubleshooting

**`weasyprint` install fails**
Try: `pip3 install weasyprint --pre`
On macOS you may need: `brew install pango`

**PDF is blank or has no content**
Check that the `.md` file is valid UTF-8 and has a proper YAML frontmatter block
(or none at all — missing frontmatter is fine).

**Shell Commands can't find Python / missing packages**
Use an absolute interpreter path in the command. For a local virtual environment:
```bash
cd /ABSOLUTE/PATH/TO/print_md
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```
Then start each Shell Commands entry with `/ABSOLUTE/PATH/TO/print_md/.venv/bin/python`.
