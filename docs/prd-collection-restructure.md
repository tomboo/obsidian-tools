# PRD — Restructure `obsidian-tools` as a packaged collection

Tracking issue: [#4](https://github.com/tomboo/obsidian-tools/issues/4)
Status: Draft
Last updated: 2026-05-10

## 1. Problem

Before this restructure, the repo held a single tool (`print_md/`) as a loose folder with its own `install.sh`, `requirements.txt`, and a README that walked users through copying absolute paths into Obsidian's Shell Commands plugin. This worked for one script, but it did not generalise:

- Adding a second tool means duplicating the install-script / venv / README pattern.
- Each tool would need its own `.venv` in-repo, with users juggling absolute Python paths per tool.
- There's no way for a user to install only the tool they want without cloning the whole repo and running shell scripts.
- Obsidian Shell Commands entries break whenever the repo or venv moves on disk.

We want to grow this repo into a collection of small, independent Obsidian-augmenting Python utilities without re-inventing packaging for each one.

## 2. Goals

- **G1 — One-line install per tool.** A user can install any single tool with one command, without cloning the repo.
- **G2 — Commands land on `PATH`.** Installed tools expose a console entry point (e.g. `print_md`) so Obsidian Shell Commands entries don't need absolute interpreter paths.
- **G3 — Dependency isolation per tool.** A heavy or pinned dependency in one tool (e.g. WeasyPrint) cannot affect another tool's install or runtime.
- **G4 — Low-friction "add a new tool" workflow.** Creating a second/third tool follows a copy-the-template pattern; no bespoke install scripts.
- **G5 — Single repo, single source of truth.** All tools, issues, and docs stay in one place.

## 3. Non-goals

- **NG1** — Publishing to PyPI in v1. Git-install is sufficient; PyPI is a follow-up if/when there's demand.
- **NG2** — Cross-platform binary distribution (Homebrew, .pkg, .exe). Out of scope.
- **NG3** — A plugin/SDK API for tools to share helpers. Premature; revisit only if duplication emerges.
- **NG4** — Migrating tools that don't exist yet. The cutover only covers `print_md`.
- **NG5** — Replacing the Obsidian Shell Commands integration with a native Obsidian plugin.

## 4. Users

- **Primary:** the repo owner, using these tools daily inside personal Obsidian vaults on macOS.
- **Secondary:** other Obsidian users who find the repo and want to install one of its tools without reading a setup guide.

Both audiences are comfortable running a single shell command; neither wants to manage Python virtual environments or edit absolute paths.

## 5. Requirements

### 5.1 Functional

- **F1** — Each tool is installable in isolation with one command of the form:
  ```
  uv tool install 'git+https://github.com/tomboo/obsidian-tools.git#subdirectory=tools/<name>'
  ```
- **F2** — Each tool exposes a console script entry point (e.g. `print_md`) that lands on the user's `PATH` via `uv tool` / `pipx` shims.
- **F3** — `print_md`'s entire CLI surface (`--frontmatter`/`-f`, `--double-space`/`-d`, `--output-dir`/`-o`, `--no-open`, default output `~/Downloads`) is preserved through the migration; no flag rename, no behaviour change.
- **F4** — Each tool ships a `README.md` covering: what it does, one-line install, CLI usage, and the Obsidian Shell Commands snippet using the bare command name.
- **F5** — The root `README.md` is an index: one row per tool with a one-line description and a link to the tool's README. The global install pattern is documented once at the top.
- **F6** — A `tools/_template/` skeleton exists so adding a new tool is "copy this folder, rename, edit `pyproject.toml`".

### 5.2 Non-functional

- **NF1 — Build backend:** `hatchling` per tool. Lightweight, PEP 621 native, no setuptools cruft.
- **NF2 — Layout:** each tool uses `src/<package>/` layout so `pip install -e .` and `uv tool install` resolve the same imports.
- **NF3 — Python floor:** Python 3.11+. Matches macOS Homebrew default and unlocks modern typing.
- **NF4 — Dev workflow:** root `pyproject.toml` declares a `uv` workspace listing each tool under `tools/*`. `uv sync` from the root sets up a unified dev environment. Dev-only deps (pytest, ruff) live in a PEP 735 `[dependency-groups]` table per tool, not in `[project.optional-dependencies]`.
- **NF5 — Versioning:** independent SemVer per tool. Tags as `<tool>/v<MAJOR>.<MINOR>.<PATCH>` (e.g. `print_md/v0.2.0`). No global repo version.
- **NF6 — Distribution:** Git-install only for v1. PyPI is a deferred follow-up.
- **NF7 — CI:** GitHub Actions runs ruff + pytest per tool, scoped by path filter so a change in one tool doesn't run unrelated tests.

## 6. Success criteria

- **S1** — A clean macOS machine with `uv` installed can run the one-line install command from `tools/print_md/README.md` and end up with a working `print_md` command on `PATH`. No clone, no venv setup, no path editing.
- **S2** — The Obsidian Shell Commands entry for printing the current file does not reference a venv-specific Python interpreter path. The recommended snippet is `print_md {{file_path:absolute}}` (requires `~/.local/bin` on the Shell Commands plugin's `PATH`; see R4); the supported fallback is `$HOME/.local/bin/print_md {{file_path:absolute}}` with no PATH configuration needed.
- **S3** — Adding a hypothetical second tool requires only: copy `tools/_template/`, rename, edit `pyproject.toml`, write code. No edits to root config, no install-script authoring.
- **S4** — `uv sync` at the repo root produces a single dev environment in which every tool's tests run via `pytest`.

## 7. Decisions (resolves issue #4 open questions)

| Question | Decision | Reasoning |
|---|---|---|
| Recommended installer | `uv tool install` primary; `pipx install` mentioned as alternative | Faster, single-binary, becoming the new default. Both work; pick one to keep docs short. |
| Build backend | `hatchling` | PEP 621 native, minimal config, no setuptools history to inherit. |
| Versioning | Independent SemVer per tool, tags `<tool>/vX.Y.Z` | Tools evolve at different paces; coupling them forces noise releases. |
| Distribution | Git-install only for v1 | No PyPI account / naming / release tooling needed to ship. Add later if useful. |
| Python floor | 3.11+ | Modern enough for typing improvements; available everywhere relevant. |
| CI | GitHub Actions, per-tool path filters, ruff + pytest | Standard, free, isolates blast radius of one tool's breakage. |
| `print_md/install.sh` | Removed as part of cutover; not preserved | One-line `uv tool install` supersedes it. Keeping both is a maintenance trap. |

## 8. Risks

- **R1 — `uv` not installed on user machines.** Mitigation: tool READMEs include the one-line `uv` install command and a `pipx` fallback.
- **R2 — WeasyPrint native deps still bite under `uv tool`.** Mitigation: the existing macOS `brew install pango` troubleshooting note stays in `print_md`'s README; nothing about that changes.
- **R3 — Users with existing Shell Commands entries break on upgrade.** Mitigation: tool README adds a "Migrating from the pre-1.0 install" callout explaining the new snippet, and old absolute-path entries keep working until the user removes the old venv.
- **R4 — Obsidian's GUI `PATH` does not include `~/.local/bin`.** When Obsidian is launched from Finder on macOS, the inherited `PATH` is the GUI default (`/usr/bin:/bin:/usr/sbin:/sbin`), so a bare `print_md` command in Shell Commands resolves to "command not found." Mitigation: tool README documents two supported snippets — (a) bare command name plus a one-time edit of the Shell Commands plugin's `PATH` env var to include `~/.local/bin`, and (b) `$HOME/.local/bin/print_md` as a zero-config fallback. Same caveat applies to `pipx` installs.

## 9. Deferred / out of scope (revisit later)

Each item has a concrete revisit trigger so the deferral stays bounded:

- **PyPI publishing and namespaced names** (`vaults-print-md`). Revisit when: an external user files an issue asking for a PyPI install, or a tool needs binary wheels.
- **Shared helper library** for tools that need common Obsidian-parsing logic. Revisit when: the same parsing code is duplicated across ≥2 tools.
- **Pre-built native installers** (Homebrew formula, `.pkg`). Revisit when: install friction is the top complaint in issues.
- **Windows / Linux verification.** Best-effort, not blocking. Revisit when: a non-macOS user files a bug.
