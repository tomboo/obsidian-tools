#!/usr/bin/env python3
"""
print_md.py — Convert Obsidian markdown files to print-ready PDFs.

Usage:
    print_md <file.md>
    print_md <file.md> --double-space
    print_md <file.md> --frontmatter
    print_md <file.md> <file.md> --combine
    print_md scenes/*.md --output-dir prints/
"""

import argparse
import os
import subprocess
import sys
from datetime import date
from io import BytesIO
from pathlib import Path

DEFAULT_OUTPUT_DIR = Path.home() / "Downloads"


def _add_macos_homebrew_library_paths() -> None:
    """Help WeasyPrint find Homebrew's native Pango/GLib libraries."""
    if sys.platform != "darwin":
        return

    existing = os.environ.get("DYLD_FALLBACK_LIBRARY_PATH", "")
    library_paths = [
        str(path)
        for path in (Path("/opt/homebrew/lib"), Path("/usr/local/lib"))
        if path.is_dir()
    ]

    for path in existing.split(":"):
        if path and path not in library_paths:
            library_paths.append(path)

    if library_paths:
        os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = ":".join(library_paths)


_add_macos_homebrew_library_paths()

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

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    sys.exit("Missing: pip install pypdf")


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

def render_pdf_bytes(input_path: Path, double_space: bool, show_frontmatter: bool = False) -> bytes:
    filename  = input_path.name
    meta, body = parse_file(input_path)
    body_html = render_body(body)
    html      = build_html(meta, body_html, filename, double_space, show_frontmatter)

    font_config = FontConfiguration()
    return HTML(string=html, base_url=str(input_path.parent)).write_pdf(font_config=font_config)


def convert_file(input_path: Path, output_dir: Path, double_space: bool, show_frontmatter: bool = False) -> Path:
    output_path = output_dir / (input_path.stem + ".pdf")
    output_path.write_bytes(render_pdf_bytes(input_path, double_space, show_frontmatter))
    return output_path


def combine_files(
    input_paths: list[Path],
    output_dir: Path,
    double_space: bool,
    show_frontmatter: bool = False,
) -> Path:
    output_path = output_dir / "combined.pdf"
    writer = PdfWriter()
    # Keep source streams alive until PdfWriter finishes writing the combined file.
    streams = []

    for input_path in input_paths:
        stream = BytesIO(render_pdf_bytes(input_path, double_space, show_frontmatter))
        streams.append(stream)
        reader = PdfReader(stream)
        for page in reader.pages:
            writer.add_page(page)

    with output_path.open("wb") as output_file:
        writer.write(output_file)

    return output_path


def validate_input_paths(file_args: list[str]) -> tuple[list[Path], int]:
    valid_paths = []
    fail = 0

    for file_arg in file_args:
        path = Path(file_arg)
        if not path.exists():
            print(f"  ✗  not found: {file_arg}", file=sys.stderr)
            fail += 1
            continue
        if path.suffix.lower() != ".md":
            print(f"  ✗  skipping (not .md): {file_arg}", file=sys.stderr)
            fail += 1
            continue
        valid_paths.append(path)

    return valid_paths, fail


# ── CLI ───────────────────────────────────────────────────────────────────────

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Convert Obsidian markdown files to print-ready PDFs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  print_md chapter_01.md
  print_md chapter_01.md --double-space
  print_md chapter_01.md chapter_02.md --combine
  print_md scenes/*.md --output-dir prints/
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
        "--combine",
        action="store_true",
        help="Combine all input files into one PDF named combined.pdf",
    )
    parser.add_argument(
        "--no-open",
        dest="open_after",
        action="store_false",
        help="Don't open PDFs in Preview after conversion",
    )
    parser.set_defaults(open_after=True)
    args = parser.parse_args(argv)

    modes = []
    if args.combine:
        modes.append("combined")
    modes.append("double-spaced" if args.double_space else "standard")
    mode = ", ".join(modes)
    print(f"\nprint_md  [{mode} mode]")
    print("─" * 42)

    out_dir = Path(args.output_dir) if args.output_dir else DEFAULT_OUTPUT_DIR
    valid_paths, fail = validate_input_paths(args.files)

    ok = 0
    if args.combine:
        if not fail:
            out_dir.mkdir(parents=True, exist_ok=True)
            try:
                out = combine_files(valid_paths, out_dir, args.double_space, args.frontmatter)
                ok = len(valid_paths)
                print(f"  ✓  {len(valid_paths)} file(s)  →  {out}")
                if args.open_after:
                    subprocess.run(["open", str(out)], check=False)
            except Exception as exc:
                print(f"  ✗  combined.pdf  —  {exc}", file=sys.stderr)
                fail += 1
    else:
        if valid_paths:
            out_dir.mkdir(parents=True, exist_ok=True)
        for path in valid_paths:
            try:
                out = convert_file(path, out_dir, args.double_space, args.frontmatter)
                print(f"  ✓  {path.name}  →  {out}")
                ok += 1
                if args.open_after:
                    subprocess.run(["open", str(out)], check=False)
            except Exception as exc:
                print(f"  ✗  {path.name}  —  {exc}", file=sys.stderr)
                fail += 1

    if args.combine and fail and valid_paths:
        for path in valid_paths:
            print(f"  -  not combined: {path.name}", file=sys.stderr)

    print("─" * 42)
    print(f"  Done — {ok} converted, {fail} failed.\n")
    if fail:
        print(f"print_md: {fail} file(s) failed — check the file path and format.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
