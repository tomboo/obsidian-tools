#!/usr/bin/env python3
"""
print_md.py — Convert Obsidian markdown files to print-ready PDFs.

Usage:
    python print_md.py <file.md>
    python print_md.py <file.md> --double-space
    python print_md.py <file.md> --frontmatter
    python print_md.py scenes/*.md --output-dir prints/
"""

import argparse
import subprocess
import sys
from datetime import date
from pathlib import Path

DEFAULT_OUTPUT_DIR = Path.home() / "Downloads"

try:
    import frontmatter
except ImportError:
    sys.exit("Missing: pip install python-frontmatter")

try:
    import markdown
except ImportError:
    sys.exit("Missing: pip install markdown")

try:
    from weasyprint import HTML
    from weasyprint.text.fonts import FontConfiguration
except ImportError:
    sys.exit("Missing: pip install weasyprint")


# ── Helpers ──────────────────────────────────────────────────────────────────

def parse_file(path: Path):
    """Return (metadata dict, body string) from a markdown file."""
    with open(path, "r", encoding="utf-8") as f:
        post = frontmatter.load(f)
    return post.metadata, post.content


def render_frontmatter(meta: dict) -> str:
    """Render frontmatter as a styled metadata block."""
    if not meta:
        return ""
    rows = ""
    for key, value in meta.items():
        if isinstance(value, list):
            value = ", ".join(str(v) for v in value)
        label = str(key).replace("_", " ").title()
        rows += f"    <tr><th>{label}</th><td>{value}</td></tr>\n"
    return f'<div class="frontmatter"><table>\n{rows}</table></div>\n'


def render_body(content: str) -> str:
    """Render markdown to HTML."""
    md = markdown.Markdown(extensions=["extra", "nl2br", "sane_lists"])
    return md.convert(content)


# ── HTML / CSS template ───────────────────────────────────────────────────────

def build_html(meta: dict, body_html: str, filename: str, double_space: bool, show_frontmatter: bool = False) -> str:
    title      = str(meta.get("title", Path(filename).stem))
    print_date = date.today().strftime("%B %d, %Y")
    line_height = "2.2" if double_space else "1.65"
    fm_html    = render_frontmatter(meta) if show_frontmatter else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>

/* ── Page geometry ─────────────────────────────────────── */
@page {{
  size: letter;
  margin: 0.85in 1in 0.85in 1in;

  @top-left {{
    content: string(hdr-filename);
    font-family: Georgia, serif;
    font-size: 8pt;
    color: #999;
    padding-bottom: 6pt;
    border-bottom: 0.5pt solid #ddd;
  }}
  @top-right {{
    content: string(hdr-title);
    font-family: Georgia, serif;
    font-size: 8pt;
    color: #999;
    padding-bottom: 6pt;
    border-bottom: 0.5pt solid #ddd;
  }}
  @bottom-left {{
    content: "{print_date}";
    font-family: Georgia, serif;
    font-size: 8pt;
    color: #aaa;
    padding-top: 4pt;
  }}
  @bottom-right {{
    content: counter(page) " / " counter(pages);
    font-family: Georgia, serif;
    font-size: 8pt;
    color: #aaa;
    padding-top: 4pt;
  }}
}}

/* ── Named strings (feed the @page header slots) ───────── */
#hdr-filename {{ string-set: hdr-filename content(); }}
#hdr-title    {{ string-set: hdr-title    content(); }}
.hdr-source   {{
  position: absolute;
  width: 1px; height: 1px;
  overflow: hidden;
  clip: rect(0,0,0,0);
}}

/* ── Base typography ────────────────────────────────────── */
body {{
  font-family: Georgia, "Times New Roman", serif;
  font-size: 11pt;
  line-height: {line_height};
  color: #1a1a1a;
  margin: 0; padding: 0;
  background: white;
}}

/* ── Frontmatter block ──────────────────────────────────── */
.frontmatter {{
  border: 1pt solid #ddd;
  border-radius: 3pt;
  background: #f9f9f9;
  padding: 7pt 10pt;
  margin-bottom: 20pt;
  font-size: 8.5pt;
  page-break-inside: avoid;
}}
.frontmatter table {{
  border-collapse: collapse;
  width: 100%;
}}
.frontmatter th {{
  font-family: Georgia, serif;
  font-weight: bold;
  font-style: normal;
  color: #666;
  text-align: left;
  padding: 1.5pt 14pt 1.5pt 0;
  white-space: nowrap;
  vertical-align: top;
  width: 1%;
}}
.frontmatter td {{
  color: #333;
  padding: 1.5pt 0;
}}

/* ── Headings ───────────────────────────────────────────── */
h1 {{ font-size: 17pt; margin: 0 0 10pt; page-break-after: avoid; }}
h2 {{ font-size: 13pt; margin: 14pt 0 6pt; page-break-after: avoid; }}
h3 {{ font-size: 11.5pt; margin: 12pt 0 4pt; page-break-after: avoid; }}
h4, h5, h6 {{ font-size: 11pt; margin: 10pt 0 3pt; page-break-after: avoid; }}

/* ── Body text ──────────────────────────────────────────── */
p {{
  margin: 0 0 8pt;
  orphans: 3;
  widows: 3;
}}

/* ── Blockquotes ────────────────────────────────────────── */
blockquote {{
  margin: 10pt 0 10pt 18pt;
  padding-left: 12pt;
  border-left: 2.5pt solid #ccc;
  color: #444;
  font-style: italic;
}}

/* ── Emphasis / strong ──────────────────────────────────── */
em    {{ font-style: italic; }}
strong {{ font-weight: bold; }}

/* ── Code ───────────────────────────────────────────────── */
code {{
  font-family: "Courier New", Courier, monospace;
  font-size: 9pt;
  background: #f2f2f2;
  padding: 1pt 3pt;
  border-radius: 2pt;
}}
pre {{
  background: #f2f2f2;
  padding: 8pt 10pt;
  font-size: 9pt;
  page-break-inside: avoid;
  white-space: pre-wrap;
}}
pre code {{ background: none; padding: 0; }}

/* ── Horizontal rules ───────────────────────────────────── */
hr {{
  border: none;
  border-top: 0.75pt solid #ccc;
  margin: 14pt 0;
}}

/* ── Lists ──────────────────────────────────────────────── */
ul, ol {{ padding-left: 20pt; margin: 0 0 8pt; }}
li {{ margin-bottom: 3pt; }}

/* ── Tables ─────────────────────────────────────────────── */
table {{
  border-collapse: collapse;
  width: 100%;
  margin-bottom: 10pt;
  font-size: 10pt;
  page-break-inside: avoid;
}}
th {{
  background: #efefef;
  border: 0.75pt solid #ccc;
  padding: 4pt 7pt;
  text-align: left;
  font-weight: bold;
}}
td {{
  border: 0.75pt solid #ccc;
  padding: 4pt 7pt;
}}

/* ── Images ─────────────────────────────────────────────── */
img {{ max-width: 100%; height: auto; }}

/* ── Links (print-friendly) ─────────────────────────────── */
a {{ color: #1a1a1a; text-decoration: underline; }}

</style>
</head>
<body>

<!-- Named-string sources: invisible, feed the running header slots -->
<span class="hdr-source" id="hdr-filename">{filename}</span>
<span class="hdr-source" id="hdr-title">{title}</span>

{fm_html}
<div class="content">
{body_html}
</div>

</body>
</html>"""


# ── Core conversion ───────────────────────────────────────────────────────────

def convert_file(input_path: Path, output_dir: Path, double_space: bool, show_frontmatter: bool = False) -> Path:
    filename  = input_path.name
    meta, body = parse_file(input_path)
    body_html = render_body(body)
    html      = build_html(meta, body_html, filename, double_space, show_frontmatter)

    output_path = output_dir / (input_path.stem + ".pdf")
    font_config = FontConfiguration()
    HTML(string=html, base_url=str(input_path.parent)).write_pdf(
        str(output_path), font_config=font_config
    )
    return output_path


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Convert Obsidian markdown files to print-ready PDFs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python print_md.py chapter_01.md
  python print_md.py chapter_01.md --double-space
  python print_md.py scenes/*.md --output-dir prints/
        """,
    )
    parser.add_argument("files", nargs="+", help="Markdown file(s) to convert")
    parser.add_argument(
        "--double-space", "-d",
        action="store_true",
        help="Double-space body text (proofreading mode)",
    )
    parser.add_argument(
        "--frontmatter", "-f",
        action="store_true",
        help="Render YAML frontmatter as a metadata card at the top of the PDF",
    )
    parser.add_argument(
        "--output-dir", "-o",
        default=None,
        metavar="DIR",
        help=f"Output directory for PDFs (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--no-open",
        dest="open_after",
        action="store_false",
        help="Don't open PDFs in Preview after conversion",
    )
    parser.set_defaults(open_after=True)
    args = parser.parse_args()

    mode = "double-spaced" if args.double_space else "standard"
    print(f"\nprint_md  [{mode} mode]")
    print("─" * 42)

    ok = fail = 0
    for file_arg in args.files:
        path = Path(file_arg)
        if not path.exists():
            print(f"  ✗  not found: {file_arg}", file=sys.stderr)
            fail += 1
            continue
        if path.suffix.lower() != ".md":
            print(f"  ✗  skipping (not .md): {file_arg}", file=sys.stderr)
            fail += 1
            continue

        out_dir = Path(args.output_dir) if args.output_dir else DEFAULT_OUTPUT_DIR
        out_dir.mkdir(parents=True, exist_ok=True)

        try:
            out = convert_file(path, out_dir, args.double_space, args.frontmatter)
            print(f"  ✓  {path.name}  →  {out}")
            ok += 1
            if args.open_after:
                subprocess.run(["open", str(out)], check=False)
        except Exception as exc:
            print(f"  ✗  {path.name}  —  {exc}", file=sys.stderr)
            fail += 1

    print("─" * 42)
    print(f"  Done — {ok} converted, {fail} failed.\n")
    if fail:
        print(f"print_md: {fail} file(s) failed — check the file path and format.", file=sys.stderr)


if __name__ == "__main__":
    main()
