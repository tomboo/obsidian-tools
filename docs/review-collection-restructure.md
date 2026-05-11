# Review — Collection restructure spec

Reviewed: [#4](https://github.com/tomboo/obsidian-tools/issues/4), [PRD](./prd-collection-restructure.md), [Implementation plan](./implementation-plan-collection-restructure.md)
Reviewer: self-review pass
Date: 2026-05-10

Findings are ranked by severity. The "Strengths" section at the end exists so the review isn't lopsided; everything above it is something that should change.

---

## Blockers / things that won't work as written

### B1 — There are no tests

`print_md/tests/` holds five `.md` **fixture** files, not pytest code:

```
formatting.md  frontmatter_full.md  minimal.md  multipage.md  no_title_field.md
```

The plan asserts in Phase 1: `uv run --package print_md pytest tools/print_md/tests passes`, in Phase 3: "A PR that breaks a `print_md` test fails CI", and PRD §6 S4: "every tool's tests run via `pytest`." None of these are true today.

**Fix:** either insert a Phase 1.5 "author baseline tests" between move and CI, or downgrade validation to "`print_md --help` exits 0" until real tests get written. As written, the plan promises a test suite it doesn't own.

### B2 — Goal G2 has a macOS GUI-PATH trap

Both `uv tool` and `pipx` install shims into `~/.local/bin/`. Obsidian launched from Finder gets the default GUI `PATH` (`/usr/bin:/bin:/usr/sbin:/sbin`); `~/.local/bin/` is **not** on it. So the promised "Obsidian Shell Commands entry is literally `print_md {{file_path:absolute}}`" only works if the user explicitly adds `~/.local/bin` to the Shell Commands plugin's `PATH` setting (or launches Obsidian from a terminal).

As written, PRD §6 S1+S2 can fail silently on a clean machine. The PRD/issue should acknowledge this and the new tool README should either document the Shell Commands PATH edit or keep using an absolute shim path like `~/.local/bin/print_md`.

---

## Inaccuracies vs. actual repo state

### I1 — Phase 1 overstates the refactor

> "Refactor the top-level script into a `main()` function so `[project.scripts]` can target it."

`main()` already exists at `print_md/print_md.py:282`. The migration is purely move + restructure; no API refactor.

### I2 — Phase 1 says "Update imports" — nothing to update

`print_md.py` has no internal imports (stdlib + 3 third-party). Test fixtures are `.md`, not Python modules. Drop the line.

### I3 — `tmp/` references in `.gitignore` are already stale

Phase 1 says: "Update `.gitignore` if needed (`tmp/` path moves under `tools/print_md/`)." There is no `tmp/` in the tree. Recent commit `b8dbfaa Default PDF output to ~/Downloads` made the directory irrelevant. The `tmp/*` / `!tmp/.gitkeep` lines in `.gitignore` are dead code. Delete in Phase 1, don't "move."

### I4 — PRD F3 forgets `--no-open`

PRD §5.1 F3 lists preserved CLI surface as `--frontmatter`, `--double-space`, `--output-dir`. Missing: `--no-open` (`print_md.py:311`). Either list explicitly or change wording to "entire CLI surface preserved."

---

## Gaps

### G1 — `_template/` interaction with workspace glob is brittle

Phase 4 says "update workspace `members = ["tools/*"]` to exclude `_template`." Works, but easy to forget. Cleaner: name the directory `tools/.template/` (dotted glob skip is standard), or put it outside `tools/` entirely at `templates/tool-skeleton/`. Then no exclude logic is needed.

### G2 — No migration story for existing users

PRD R3 acknowledges this softly. But Phase 1 deletes `print_md/install.sh` and Phase 2 removes old `print_md/.venv` references from docs. Anyone with existing Shell Commands entries gets silently dangling pointers. One explicit sentence in Phase 2 — "tool README adds a 'Migrating from the pre-1.0 install' callout" — closes the gap.

### G3 — Dev-deps shape not specified

Phase 3 says "Add `pytest` and `ruff` to a `dev` dependency group" but doesn't pick PEP 735 `[dependency-groups]` vs `[project.optional-dependencies]`. uv supports both; lean PEP 735 since uv treats it as first-class.

---

## Minor / nits

### N1 — CI path-filter mechanism unspecified

Workflow-level `on.pull_request.paths:` gates the whole workflow; per-job gating in a matrix needs `dorny/paths-filter` or similar. Pick one.

### N2 — Deferred PyPI has no revisit trigger

PRD §9 lists PyPI as deferred but doesn't say *when* to revisit. A one-line "revisit when: external user files an issue asking for it" turns indefinite deferral into a concrete trigger.

---

## Strengths

- Issue, PRD, and plan are internally consistent on every architectural decision (uv tool, hatchling, src layout, independent SemVer, Git-install v1, 3.11+).
- Phase 0/1 split is right — landing the workspace skeleton in a no-op PR before any file moves is the safe move.
- Per-phase Rollback notes are unusual and valuable.
- Decisions table in PRD §7 cleanly closes the open questions from issue #4.
- Local Git URL trick (`git+file:///...`) in Phase 1 validation is a nice way to test install without pushing.

---

## Suggested fix order

Two structural changes are worth making before anyone starts coding:

1. **Fold the GUI-PATH caveat into PRD Risks + Phase 2 README work** (B2), since it changes what "done" looks like for Goal G2.
2. **Insert Phase 1.5 — baseline tests** (B1) covering at minimum: bare `--help`, one-file conversion to a temp dir, `--frontmatter` flag, `--no-open` flag. Phase 3's CI then has something to actually run.

Everything else is text edits.
