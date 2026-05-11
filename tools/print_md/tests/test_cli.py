from pathlib import Path

import pytest
from pypdf import PdfReader
from print_md import cli


FIXTURES = Path(__file__).resolve().parent / "fixtures"


def test_help_exits_zero(capsys):
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["--help"])

    assert excinfo.value.code == 0
    assert "Convert Obsidian markdown files" in capsys.readouterr().out


def test_missing_file_reports_and_exits_nonzero(tmp_path, capsys):
    missing = tmp_path / "missing.md"

    result = cli.main([str(missing), "--no-open"])

    captured = capsys.readouterr()
    assert result == 1
    assert "not found" in captured.err
    assert "1 file(s) failed" in captured.err


def test_convert_minimal_md_to_temp_dir(tmp_path):
    result = cli.main(
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


def test_frontmatter_flag_renders_metadata_block(tmp_path):
    result = cli.main(
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


def test_no_open_flag_suppresses_subprocess(tmp_path, monkeypatch):
    calls = []

    def fake_run(*args, **kwargs):
        calls.append((args, kwargs))

    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    result = cli.main(
        [
            str(FIXTURES / "minimal.md"),
            "--output-dir",
            str(tmp_path),
            "--no-open",
        ]
    )

    assert result == 0
    assert calls == []


def test_combine_multiple_files_to_single_pdf(tmp_path):
    result = cli.main(
        [
            str(FIXTURES / "minimal.md"),
            str(FIXTURES / "frontmatter_full.md"),
            "--combine",
            "--output-dir",
            str(tmp_path),
            "--no-open",
        ]
    )

    output = tmp_path / "combined.pdf"
    assert result == 0
    assert output.exists()
    assert output.stat().st_size > 0
    assert len(PdfReader(output).pages) == 2
    assert not (tmp_path / "minimal.pdf").exists()
    assert not (tmp_path / "frontmatter_full.pdf").exists()


def test_combine_missing_file_returns_nonzero_without_partial_pdf(tmp_path, capsys):
    result = cli.main(
        [
            str(FIXTURES / "minimal.md"),
            str(tmp_path / "missing.md"),
            "--combine",
            "--output-dir",
            str(tmp_path),
            "--no-open",
        ]
    )

    captured = capsys.readouterr()
    assert result == 1
    assert "not found" in captured.err
    assert "not combined: minimal.md" in captured.err
    assert not (tmp_path / "combined.pdf").exists()
