#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
venv_dir="$script_dir/.venv"
python_cmd="${PYTHON:-python3}"

quote() {
  printf '%q' "$1"
}

if ! command -v "$python_cmd" >/dev/null 2>&1; then
  echo "print_md install: could not find Python command: $python_cmd" >&2
  echo "Install Python 3, or run with PYTHON=/absolute/path/to/python3 $0" >&2
  exit 1
fi

echo "Creating virtual environment:"
echo "  $venv_dir"
"$python_cmd" -m venv "$venv_dir"

echo
echo "Installing Python dependencies..."
"$venv_dir/bin/python" -m pip install --upgrade pip
"$venv_dir/bin/python" -m pip install -r "$script_dir/requirements.txt"

echo
echo "Verifying install..."
if ! "$venv_dir/bin/python" - <<'PY'
import frontmatter
import markdown
import weasyprint

print("  dependencies ok")
PY
then
  cat >&2 <<'EOF'

print_md install: dependency verification failed.

On macOS, WeasyPrint may also need Homebrew rendering libraries:
  brew install pango

Then rerun:
  ./install.sh

EOF
  exit 1
fi

python_path="$(quote "$venv_dir/bin/python")"
script_path="$(quote "$script_dir/print_md.py")"

cat <<EOF

Install complete.

Paste these into Obsidian's Shell Commands plugin:

Print Scene to PDF:
$python_path $script_path {{file_path:absolute}}

Print Scene to PDF (Double-spaced):
$python_path $script_path {{file_path:absolute}} --double-space

Print Scene to PDF (with Frontmatter):
$python_path $script_path {{file_path:absolute}} --frontmatter

Important: do not wrap {{file_path:absolute}} in quotes. Shell Commands already
escapes that value for the shell.

EOF
