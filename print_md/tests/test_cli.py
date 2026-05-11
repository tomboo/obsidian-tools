import importlib.util
from pathlib import Path

import pytest


PRINT_MD_DIR = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture()
def print_md_module():
    spec = importlib.util.spec_from_file_location("print_md_cli", PRINT_MD_DIR / "print_md.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_help_exits_zero(print_md_module, capsys):
    with pytest.raises(SystemExit) as excinfo:
        print_md_module.main(["--help"])

    assert excinfo.value.code == 0
    assert "Convert Obsidian markdown files" in capsys.readouterr().out


def test_missing_file_reports_and_exits_nonzero(print_md_module, tmp_path, capsys):
    missing = tmp_path / "missing.md"

    result = print_md_module.main([str(missing), "--no-open"])

    captured = capsys.readouterr()
    assert result == 1
    assert "not found" in captured.err
    assert "1 file(s) failed" in captured.err


def test_convert_minimal_md_to_temp_dir(print_md_module, tmp_path):
    result = print_md_module.main(
        [
            str(FIXTURES / "minimal.md"),
            "--output-dir",
            str(tmp_path),
            "--no-open",
        ]
    )

    output = tmp_path / "minimal.pdf"
    assert result == 0
    assert output.exists()
    assert output.stat().st_size > 0


def test_frontmatter_flag_renders_metadata_block(print_md_module, tmp_path):
    result = print_md_module.main(
        [
            str(FIXTURES / "frontmatter_full.md"),
            "--frontmatter",
            "--output-dir",
            str(tmp_path),
            "--no-open",
        ]
    )

    output = tmp_path / "frontmatter_full.pdf"
    assert result == 0
    assert output.exists()
    assert output.stat().st_size > 0


def test_no_open_flag_suppresses_subprocess(print_md_module, tmp_path, monkeypatch):
    calls = []

    def fake_run(*args, **kwargs):
        calls.append((args, kwargs))

    monkeypatch.setattr(print_md_module.subprocess, "run", fake_run)

    result = print_md_module.main(
        [
            str(FIXTURES / "minimal.md"),
            "--output-dir",
            str(tmp_path),
            "--no-open",
        ]
    )

    assert result == 0
    assert calls == []
