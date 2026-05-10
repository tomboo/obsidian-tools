# scene_print — Setup & Usage Guide

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

### 2 — Save the script

Put `scene_print.py` somewhere permanent. A dedicated folder works well:

```
~/scripts/scene_print/scene_print.py
```

---

## Terminal Usage

```bash
# Single file
python3 ~/scripts/scene_print/scene_print.py chapter_01.md

# Single file, double-spaced (proofreading)
python3 ~/scripts/scene_print/scene_print.py chapter_01.md --double-space

# Single file, with frontmatter card
python3 ~/scripts/scene_print/scene_print.py chapter_01.md --frontmatter

# Multiple files — PDF lands next to each .md file
python3 ~/scripts/scene_print/scene_print.py scenes/*.md

# Send all PDFs to a specific folder
python3 ~/scripts/scene_print/scene_print.py scenes/*.md --output-dir prints/
```

The PDF is written to `/tmp/scene_print/` by default, keeping your vault folders clean.

---

## Obsidian Integration (Shell Commands Plugin)

This lets you print the current scene with a hotkey or from the Command
Palette — no Terminal required.

### Install the plugin

1. Obsidian → **Settings → Community plugins → Browse**
2. Search **Shell commands** (by Teemu Vainio)
3. Install → Enable

### Add the two commands

Go to **Settings → Shell commands → + New shell command**

**Command 1 — Print Scene**
```
python3 /Users/YOURNAME/scripts/scene_print/scene_print.py "{{file_path}}"
```
- Alias: `Print Scene to PDF`
- Assign hotkey: `Cmd+Shift+P` (or whatever feels right)

**Command 2 — Print Scene (Double-spaced)**
```
python3 /Users/YOURNAME/scripts/scene_print/scene_print.py "{{file_path}}" --double-space
```
- Alias: `Print Scene to PDF (Double-spaced)`
- Assign hotkey: `Cmd+Shift+D`

**Command 3 — Print Scene (with frontmatter)**
```
python3 /Users/YOURNAME/scripts/scene_print/scene_print.py "{{file_path}}" --frontmatter
```
- Alias: `Print Scene to PDF (with Frontmatter)`

> Replace `/Users/YOURNAME/scripts/` with the actual path to your script.
> On Windows use `python` instead of `python3`.

### Shell Commands variables used
| Variable | Expands to |
|---|---|
| `{{file_path}}` | Full path to the currently open file |

### After setup
Open any `.md` scene file → `Cmd+P` → type "Print" → hit Enter.
The PDF appears in the same folder as the scene, ready to open or send to a printer.

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
| Default | `/tmp/scene_print/` |
| `--output-dir prints/` | Inside `prints/` relative to where you run the command |
| Obsidian Shell Commands | `/tmp/scene_print/` |

---

## Troubleshooting

**`weasyprint` install fails**
Try: `pip3 install weasyprint --pre`
On macOS you may need: `brew install pango`

**PDF is blank or has no content**
Check that the `.md` file is valid UTF-8 and has a proper YAML frontmatter block
(or none at all — missing frontmatter is fine).

**Shell Commands can't find Python**
Use the full path to Python in the shell command:
```bash
/usr/local/bin/python3 /path/to/scene_print.py "{{file_path}}"
```
Find your Python path with: `which python3`
