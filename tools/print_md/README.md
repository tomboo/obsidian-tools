# print_md

Convert Obsidian Markdown files to clean, print-ready PDFs with running
headers, footers, optional frontmatter, and optional double-spacing.

## Install

On macOS, install WeasyPrint's native rendering libraries first:

```bash
brew install pango
```

Recommended:

```bash
uv tool install 'git+https://github.com/tomboo/obsidian-tools.git#subdirectory=tools/print_md'
```

Alternative with `pipx`:

```bash
pipx install 'git+https://github.com/tomboo/obsidian-tools.git#subdirectory=tools/print_md'
```

`print_md` automatically checks standard Homebrew library folders
(`/opt/homebrew/lib` and `/usr/local/lib`) when WeasyPrint starts.

## CLI Usage

```bash
print_md chapter_01.md
print_md chapter_01.md --double-space
print_md chapter_01.md --frontmatter
print_md scenes/*.md --output-dir prints/
```

By default, PDFs are written to `~/Downloads`.

## Obsidian Shell Commands

Shell Commands escapes `{{file_path:absolute}}` for the shell, so do not wrap it
in quotes.

### Option A: Configure PATH

Add `~/.local/bin` to the Shell Commands plugin's PATH environment setting, then
use:

```bash
print_md {{file_path:absolute}}
```

Double-spaced:

```bash
print_md {{file_path:absolute}} --double-space
```

With frontmatter:

```bash
print_md {{file_path:absolute}} --frontmatter
```

### Option B: Zero-config Absolute Shim

If you do not want to change the plugin PATH, use the full shim path:

```bash
$HOME/.local/bin/print_md {{file_path:absolute}}
```

## Frontmatter

YAML frontmatter is parsed but hidden by default. Pass `--frontmatter` or `-f`
to render it as a metadata card at the top of the PDF. The `title` field is
always used in the running header when present.

Example:

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

If there is no `title` field, the filename is used.

## Migrating From The Pre-0.2 Install

Old Shell Commands entries may point at a cloned repo path or a local
`.venv/bin/python`. Those entries will keep working only while that clone and
venv stay in place.

Recommended migration:

1. Install with `uv tool install`.
2. Replace old Shell Commands entries with one of the snippets above.
3. Remove the old clone or `.venv` only after the new command works.

## Development

From the repo root:

```bash
uv sync
uv run --package print-md pytest tools/print_md/tests
uv run --package print-md print_md --help
uv run --package print-md print_md tools/print_md/tests/fixtures/minimal.md --output-dir /tmp/print_md_smoke --no-open
```
