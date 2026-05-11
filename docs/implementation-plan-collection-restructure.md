# Implementation Plan — Collection restructure

Tracking issue: [#4](https://github.com/tomboo/obsidian-tools/issues/4)
PRD: [prd-collection-restructure.md](./prd-collection-restructure.md)
Status: Phase 0/1 package scaffold complete; Phase 3 CI tracked in [#9](https://github.com/tomboo/obsidian-tools/issues/9)

The plan is sequenced so the repo stays usable at the end of every phase. Each phase is a single PR.

---

## Phase 0 — Repo scaffolding (no behaviour change)

**Goal:** add the workspace skeleton without moving any existing files yet.

**Changes:**

- New `pyproject.toml` at repo root:
  ```toml
  [tool.uv.workspace]
  members = ["tools/*"]
  ```
  No `[project]` block — the root is a workspace marker, not an installable package.
- New empty `tools/` directory with a `.gitkeep`.
- New `docs/` already exists (this PR adds the PRD + this plan).

**Validation:**
- `uv sync` at the repo root runs without error (will be a no-op until phase 1).
- `print_md/` continues to work exactly as today.

**Rollback:** delete `pyproject.toml` and `tools/`.

---

## Phase 1 — Migrate `print_md` into the workspace

**Goal:** `print_md` is installable via `uv tool install` from Git and continues to behave identically when invoked as `print_md ...`.

**Changes:**

- Move `print_md/print_md.py` → `tools/print_md/src/print_md/cli.py`. Add `__init__.py`. `main()` already exists at line 282; no refactor needed, just relocation.
- Move `print_md/tests/fixtures/` → `tools/print_md/tests/fixtures/`.
- Move `print_md/tests/test_cli.py` → `tools/print_md/tests/test_cli.py` and update its script import to target `print_md.cli` after the source move.
- Move `print_md/README.md` → `tools/print_md/README.md` (rewritten in phase 2).
- Delete `print_md/install.sh` and `print_md/requirements.txt` (replaced by `pyproject.toml`).
- Delete stale `tmp/*` and `!tmp/.gitkeep` lines from `.gitignore` — there is no `tmp/` directory in the tree and the default output already lives at `~/Downloads`.
- New `tools/print_md/pyproject.toml`:
  ```toml
  [project]
  name = "print-md"
  version = "0.2.0"
  requires-python = ">=3.11"
  dependencies = [
      "python-frontmatter>=1.1.0",
      "markdown>=3.5.0",
      "weasyprint>=62.0",
  ]

  [project.scripts]
  print_md = "print_md.cli:main"

  [build-system]
  requires = ["hatchling"]
  build-backend = "hatchling.build"
  ```
- Remove the now-empty `print_md/` directory at the repo root.

**Validation:**
- `uv sync` from the repo root resolves and installs `print_md` editable.
- `uv run --package print-md print_md tools/print_md/tests/fixtures/minimal.md --no-open --output-dir /tmp/print_md_smoke` produces a PDF without error.
- `uv run --package print-md print_md --help` exits 0.
- From a scratch directory: `uv tool install 'git+file:///Users/tom/Projects/obsidian-tools#subdirectory=tools/print_md'` succeeds and `print_md --help` works (when `~/.local/bin` is on `PATH` — `uv tool install` prints a `uv tool update-shell` hint if it isn't).
- _Note:_ pytest validation already exists in the loose-folder layout; Phase 1 keeps it passing through the move.

**Rollback:** revert the PR. No data is destroyed; the old layout is in Git history.

---

## Phase 1.5 — Baseline test suite

**Goal:** preserve and extend the current loose-folder pytest baseline so CI in Phase 3 has something meaningful to run, and future refactors have a regression net.

**Why a separate phase:** keeps the file-move PR (Phase 1) reviewable on its own, and keeps test expansion separate from layout churn.

**Changes:**

- `tools/print_md/tests/test_cli.py` covers, at minimum:
  - `test_help_exits_zero` — invoke `cli.main()` with `['--help']`, assert `SystemExit.code == 0`.
  - `test_missing_file_reports_and_exits_nonzero` — pass a bogus path with `--no-open`, assert exit code reflects failure and stderr mentions "not found".
  - `test_convert_minimal_md_to_temp_dir` — use `fixtures/minimal.md`, pass `--output-dir <tmp> --no-open`, assert the expected `.pdf` is created and non-empty.
  - `test_frontmatter_flag_renders_metadata_block` — use `fixtures/frontmatter_full.md` with `--frontmatter --no-open`, assert PDF is produced (binary content check; we're not parsing the PDF, just confirming no crash on that code path).
  - `test_no_open_flag_suppresses_subprocess` — monkeypatch `subprocess.run`, assert it isn't called when `--no-open` is passed.
- Add `pytest` to the `[dependency-groups] dev` table in `tools/print_md/pyproject.toml` (see Phase 3 for the group decision). This replaces the temporary loose-folder `print_md/requirements-dev.txt`.
- Add a `tools/print_md/conftest.py` only if a fixture path helper turns out to be needed; otherwise skip.

**Validation:**
- `uv run --package print-md pytest tools/print_md/tests` runs all five tests green on a clean dev machine.
- Tests do not require network access or write outside the pytest tmp dir.

**Rollback:** revert the PR. Removing tests does not affect the runtime.

**Out of scope:** PDF-output golden-file diffing (timestamps embedded in the PDF defeat byte comparison; structural assertions are enough for v1).

---

## Phase 2 — Documentation cutover

**Goal:** both READMEs reflect the new install + usage flow. Anyone landing on the repo can install `print_md` in one command without prior context.

**Changes:**

- Rewrite root `README.md`:
  - One-paragraph intro: what this repo is.
  - One-time `uv` install instructions (link to upstream).
  - "Available tools" table (one row per tool, currently only `print_md`).
  - Brief note on the install pattern; details live in each tool's README.
- Rewrite `tools/print_md/README.md`:
  - What it does (current intro stays).
  - Install: single `uv tool install 'git+...#subdirectory=tools/print_md'` block. `pipx` shown as the alternative one-liner.
  - CLI usage: simplify all examples to `print_md ...` (no `python3 path/to/print_md.py`).
  - **Obsidian Shell Commands setup** — must cover both PATH options explicitly, because `~/.local/bin` is not on Obsidian's GUI-launched `PATH` by default:
    - **Option A (recommended):** snippet is `print_md {{file_path:absolute}}`. Requires one-time edit of Shell Commands plugin → Settings → Environments → add `~/.local/bin` to `PATH`.
    - **Option B (zero-config fallback):** snippet is `$HOME/.local/bin/print_md {{file_path:absolute}}`. Works with no plugin configuration.
    - Show both options. Pick A as the primary example; B as a callout for users who don't want to touch plugin settings.
  - Drop the absolute-path-to-venv-python guidance entirely.
  - Add a "Migrating from the pre-1.0 install" callout: tell users with existing entries to remove the old `print_md/.venv/`, delete their old Shell Commands entries, and re-add using the new snippet. Otherwise their old entries will silently break the day they remove the cloned repo.
  - Keep the frontmatter, output-location, and troubleshooting sections — they're still accurate.
- Move `docs/prd-collection-restructure.md` and this plan into `docs/` (already done in phase 0).

**Validation:**
- A first-time reader following only the root README ends up with a working `print_md` and a working Shell Commands entry (either option A or option B).
- No README references `install.sh`, `requirements.txt`, or `.venv/bin/python`.
- Migration callout is present in `tools/print_md/README.md` and is reachable from the root README's "Available tools" row.

**Rollback:** revert the docs PR; code from phase 1 continues to work.

---

## Phase 3 — CI

**Goal:** every PR runs lint + tests for the tool(s) it touches.

**Changes:**

- New `.github/workflows/ci.yml`:
  - Trigger on PRs.
  - Use [`dorny/paths-filter`](https://github.com/dorny/paths-filter) as the first job to compute per-tool change flags (`print_md: 'tools/print_md/**'`). Downstream per-tool jobs gate themselves with `if: needs.changes.outputs.print_md == 'true'`. This is finer-grained than workflow-level `on.pull_request.paths:`, which is all-or-nothing.
  - Per-tool jobs install `uv` via `astral-sh/setup-uv@v3`, run `uv sync --package <tool> --group dev`, then `uv run ruff check` and `uv run pytest`.
  - WeasyPrint native deps on Ubuntu runners: add `apt-get install -y libpango-1.0-0 libpangoft2-1.0-0` before `uv sync` in the `print_md` job. (Heads-up: this is the most likely place CI breaks first.)
- New `[tool.ruff]` table in root `pyproject.toml` with line length 100 and the default rule set. Root-level so all tools share config.
- Add `pytest` and `ruff` to a PEP 735 `[dependency-groups] dev = [...]` table in each tool's `pyproject.toml`. (Decision: PEP 735, not `[project.optional-dependencies]`. uv treats dependency-groups as first-class for `--group dev` selection, and they don't pollute the installable distribution.)

**Validation:**
- CI runs green on a no-op PR.
- A PR that touches only `docs/` does not run tool test jobs.
- A PR that breaks a `print_md` test fails CI.

**Rollback:** remove the workflow file. No runtime impact.

---

## Phase 4 — Tool skeleton for new tools

**Goal:** adding tool number two takes <10 minutes of boilerplate.

**Location decision:** put the skeleton at `templates/tool-skeleton/`, **outside** `tools/`. Earlier draft suggested `tools/_template/` with an `exclude` glob, but keeping the skeleton inside the workspace directory means every future contributor (and `uv sync`) has to remember the exclude rule. Moving it outside `tools/` makes the workspace glob simple (`members = ["tools/*"]`) and removes a class of "I copied the template and got weird errors" bugs.

**Changes:**

- New `templates/tool-skeleton/` containing:
  - `pyproject.toml` with TODO placeholders (`name`, `description`, entry point) and the same `hatchling` build backend + PEP 735 dev group as `print_md`.
  - `src/<package_name>/__init__.py` and `src/<package_name>/cli.py` with a stub `main()` and `argparse` skeleton (one `--help`-only command).
  - `tests/test_cli.py` with one passing smoke test (`--help` exits 0).
  - `README.md` skeleton mirroring `print_md`'s post-Phase-2 structure: what it does, install one-liner, CLI usage, Obsidian Shell Commands snippet with both PATH options (A and B from Phase 2).
- Root README "Adding a new tool" section: ~5 numbered steps — copy `templates/tool-skeleton/` into `tools/<new_name>/`, search-replace placeholders, `uv sync`, run the smoke test, commit.

**Validation:**
- `cp -r templates/tool-skeleton tools/hello_world`, search-replace placeholders, `uv sync`, `uv tool install 'git+file:///...#subdirectory=tools/hello_world'` → working `hello_world --help` command on `PATH`.
- `uv sync` at the root does **not** attempt to install `templates/tool-skeleton/` (because it's outside the workspace glob).

**Rollback:** delete `templates/` and the README section.

---

## Cross-cutting

- **Branching:** one branch per phase, merged in order. Don't stack phase 2 on phase 1 in a single PR — separate reviews keep blast radius small.
- **Issue hygiene:** close issue #4 after phase 4 lands; open follow-up issues for PyPI publishing and shared-helpers as they become real.
- **What can break:** the only externally-visible breakage is the install instructions changing. Anyone with an existing `print_md/.venv` keeps working until they remove it; the new install creates a parallel `uv` tool install.

## Out of scope for this plan

- PyPI publishing (deferred; see PRD §9).
- Renaming the executable (`print_md` stays `print_md`).
- Migrating any tool other than `print_md`.
- Adding shared helper packages between tools.
