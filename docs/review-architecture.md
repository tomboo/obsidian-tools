# Review — Repository architecture

Reviewed: repo at `tomboo/obsidian-tools` (root, `tools/print_md`, CI, `docs/`)
Reviewer: external high-level architectural review
Date: 2026-05-10

A high-level architectural review of the repo as it stands after the collection restructure. Focus is on structure, packaging, and design decisions — not line-level code review. Companion to [`review-collection-restructure.md`](./review-collection-restructure.md), which reviews the restructure spec itself rather than the resulting repo.

---

## 1. What it is

A small Python monorepo that treats itself as a *collection of independent CLI tools* for Obsidian users, rather than as a single application. Today it holds exactly one tool — `print_md`, a markdown-to-PDF converter built on WeasyPrint — but the scaffolding is set up for more. The architectural bet is: each tool stands alone, installs alone, versions alone, and the repo just hosts them.

## 2. The shape of the design

The repo is structured as a **uv workspace** with three layers of separation:

- The **root** (`pyproject.toml`) is a workspace marker only — no `[project]` block, just `[tool.uv.workspace] members = ["tools/*"]` plus a shared `ruff` config. This is the right call: it gives a single dev environment via `uv sync` without coupling tools to a parent package.
- Each tool lives under `tools/<name>/` with its own `pyproject.toml`, `src/<pkg>/` layout, `hatchling` build backend, and PEP 621 metadata. Dev deps use PEP 735 `[dependency-groups]` instead of optional-extras.
- **Distribution** uses git-subdirectory installs: `uv tool install 'git+…#subdirectory=tools/print_md'`. No PyPI, no install scripts, no venv juggling for end users. The shim lands on `~/.local/bin` and the console-script entry point (`print_md = "print_md.cli:main"`) becomes the integration surface for Obsidian's Shell Commands plugin.

CI mirrors the same isolation: GitHub Actions uses `dorny/paths-filter` so that touching one tool only runs that tool's lint + tests. There's a single Ubuntu runner installing Pango natively for WeasyPrint.

## 3. What's done well

The packaging model is the strongest part. The choices — `uv tool install` as primary, `hatchling` build backend, src-layout, per-tool SemVer with `<tool>/vX.Y.Z` tags, git-install before PyPI — are all the modern, low-friction defaults. There's no setuptools cruft, no editable-install footguns, no requirements.txt drift.

The **documentation discipline is unusual for a project this size**: `docs/` contains a real PRD, a phased implementation plan, and a self-review that names blockers (B1, B2) and inaccuracies (I1–I4) against the plan. That review surfaces real issues — most notably the macOS GUI-`PATH` trap where Obsidian launched from Finder doesn't see `~/.local/bin`, breaking the "just type `print_md`" promise. The README's "Option B: absolute shim" fallback is the right mitigation.

CI scoping by path filter is also well-chosen: the blast radius of one tool's breakage stays inside that tool.

## 4. Architectural tensions worth flagging

### T1 — The "collection" abstraction is forward-looking

With N=1, all the workspace machinery is overhead that pays off only when the second tool lands. The PRD's **F6** calls for a `tools/_template/` skeleton, but it doesn't exist in the tree yet — adding tool #2 would be the moment to define the template by extracting it. Until then, "copy `print_md`, rename, delete the WeasyPrint stuff" is the de facto template.

### T2 — `print_md/cli.py` is a single ~450-line file

It holds argparse setup, frontmatter parsing, markdown→HTML rendering, a large inline HTML/CSS template, PDF generation, and PDF combining. That's fine at this size, but as soon as a second markdown-rendering tool appears (or `print_md` grows themes/templates), the natural split is `cli.py` / `renderer.py` / `templates/` / `combine.py`. The defensive `try: import …; except ImportError: sys.exit(...)` blocks at the top of `cli.py` are essentially dead in the installed-tool path since `pyproject.toml` declares those as hard deps; they were useful in the pre-package era and could go.

### T3 — macOS is a first-class platform; everything else is best-effort

This is explicit and acknowledged (PRD R4, deferred Windows/Linux verification), but it shows up in code: `_add_macos_homebrew_library_paths()`, `subprocess.run(["open", str(out)])` for auto-opening PDFs, `~/Downloads` as the default output. None are wrong given the stated user base, but they constrain what "add another tool" means — any new tool will likely inherit the same macOS assumptions unless someone draws a portability line.

### T4 — No shared helper package, by design (PRD NG3)

Correct now — premature abstraction would hurt more than duplication. The PRD even names the revisit trigger ("same parsing code duplicated across ≥2 tools"). Just worth remembering that the first markdown-parsing-adjacent tool that lands will tempt the wrong refactor.

### T5 — Workspace lock vs. independent versioning

`uv.lock` at the root couples dev-time dependency resolution across tools even though tools version independently. Practical consequence: a major WeasyPrint bump in `print_md` may force lockfile churn that touches dev setup for other tools. Minor friction, probably worth the unified dev environment.

## 5. Summary

For a one-tool repo, this is over-engineered in the deliberate sense — the architecture is sized for the *next* five tools, not for the one that exists. The packaging, CI, and documentation choices are sound and modern; the main risks (GUI PATH trap, macOS-only assumptions, eventual `cli.py` bloat) are either already documented or naturally deferred to "when tool #2 arrives." The PRD's discipline of naming non-goals and revisit triggers is what makes the over-engineering feel intentional rather than speculative.

## 6. Suggested follow-ups (non-blocking)

- When adding tool #2, extract `tools/_template/` from the diff rather than designing it up front. Closes PRD **F6**.
- Consider splitting `tools/print_md/src/print_md/cli.py` into `cli.py` / `renderer.py` / `template.py` the next time the HTML/CSS template needs a non-trivial change. Closes **T2**.
- Drop the `try/except ImportError` import guards in `cli.py`; `pyproject.toml` is now the source of truth for dependencies. Small cleanup under **T2**.
- Decide explicitly whether new tools target macOS-only or aim for cross-platform; document the position in the root README so it shapes future PRs. Addresses **T3**.
