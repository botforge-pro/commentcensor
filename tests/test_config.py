from pathlib import Path

import pytest

from commentcensor.cli import CLEAN, FOUND, UNUSABLE, main

SPOKEN = "// the provider answers out of order\nvar x = 1\n"
ALLOWED = (
    "allow:\n"
    "  - file: sample.go\n"
    '    text: "// the provider answers out of order"\n'
    '    why: "Their own docs say otherwise."\n'
)


def a_file(directory: Path, source: str = SPOKEN, name: str = "sample.go") -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    written = directory / name
    written.write_text(f"package main\n\n{source}" if name.endswith(".go") else source)
    return written


def configured(directory: Path, yaml: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / ".commentcensor.yaml").write_text(yaml)
    return directory


def test_a_config_above_the_scanned_directory_still_applies(tmp_path):
    a_file(tmp_path / "src" / "deep")
    configured(tmp_path, ALLOWED.replace("file: sample.go", "file: src/deep/sample.go"))

    assert main([str(tmp_path / "src" / "deep")]) == CLEAN
    assert main([str(tmp_path / "src")]) == CLEAN
    assert main([str(tmp_path)]) == CLEAN


def test_the_same_file_answers_the_same_however_it_is_reached(tmp_path):
    file = a_file(tmp_path / "src")
    configured(tmp_path, ALLOWED.replace("file: sample.go", "file: src/sample.go"))

    assert main([str(file)]) == CLEAN
    assert main([str(tmp_path / "src")]) == CLEAN


@pytest.mark.parametrize("why", ["", "~", "0", "false", '""'])
def test_an_allowance_with_no_reason_is_refused(tmp_path, why):
    a_file(tmp_path)
    configured(
        tmp_path,
        "allow:\n"
        "  - file: sample.go\n"
        '    text: "// the provider answers out of order"\n'
        f"    why: {why}\n",
    )

    assert main([str(tmp_path)]) == UNUSABLE


def test_a_setting_nobody_declared_is_refused(tmp_path):
    a_file(tmp_path)
    configured(tmp_path, "skips:\n  - somewhere/\n")

    assert main([str(tmp_path)]) == UNUSABLE


def test_a_file_named_twice_is_counted_once(tmp_path, capsys):
    a_file(tmp_path)

    assert main([str(tmp_path), str(tmp_path)]) == FOUND
    assert capsys.readouterr().out.count("sample.go") == 1


def test_a_file_that_cannot_be_read_is_refused(tmp_path):
    file = a_file(tmp_path)
    file.chmod(0o000)
    try:
        assert main([str(tmp_path)]) == UNUSABLE
    finally:
        file.chmod(0o644)


def test_the_whole_comment_is_printed_so_it_can_be_declared(tmp_path, capsys):
    a_file(tmp_path, "// the provider answers\n// out of order\nvar x = 1\n")

    assert main([str(tmp_path)]) == FOUND
    printed = capsys.readouterr().out
    assert "// the provider answers" in printed
    assert "// out of order" in printed


def test_a_comment_block_is_declared_by_its_whole_text(tmp_path):
    a_file(tmp_path, "// the provider answers\n// out of order\nvar x = 1\n")
    configured(
        tmp_path,
        "allow:\n"
        "  - file: sample.go\n"
        "    text: |-\n"
        "      // the provider answers\n"
        "      // out of order\n"
        '    why: "Their own docs say otherwise."\n',
    )

    assert main([str(tmp_path)]) == CLEAN


def test_a_skipped_path_covers_what_is_under_it(tmp_path):
    a_file(tmp_path / "vendored")
    configured(tmp_path, "skip:\n  - vendored/\n")

    assert main([str(tmp_path)]) == CLEAN


def test_a_skip_pattern_reaches_a_nested_directory(tmp_path):
    a_file(tmp_path / "pkg" / "Generated")
    configured(tmp_path, "skip:\n  - '*/Generated'\n")

    assert main([str(tmp_path)]) == CLEAN


def test_what_to_do_is_said_once_after_the_findings(tmp_path, capsys):
    a_file(tmp_path, "// first thing\nvar x = 1\n\n// second thing\nvar y = 2\n")

    assert main([str(tmp_path)]) == FOUND
    printed = capsys.readouterr().out
    assert printed.count("# The comment is not the source") == 1
    assert printed.index("// second thing") < printed.index("# The comment is not the source")


def test_a_clean_run_says_nothing(tmp_path, capsys):
    a_file(tmp_path, "var x = 1\n")

    assert main([str(tmp_path)]) == CLEAN
    assert capsys.readouterr().out == ""
