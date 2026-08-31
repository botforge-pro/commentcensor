from commentcensor.cli import CLEAN, FOUND, UNUSABLE, main

SPOKEN = "// the provider answers out of order\nvar x = 1\n"


def a_wiki(tmp_path, source=SPOKEN, name="sample.go"):
    (tmp_path / name).write_text(f"package main\n\n{source}" if name.endswith(".go") else source)
    return tmp_path


def configured(tmp_path, yaml):
    (tmp_path / ".commentcensor.yaml").write_text(yaml)
    return tmp_path


def test_a_file_with_no_comment_passes(tmp_path):
    assert main([str(a_wiki(tmp_path, "var x = 1\n"))]) == CLEAN


def test_an_undeclared_comment_fails(tmp_path):
    assert main([str(a_wiki(tmp_path))]) == FOUND


def test_a_declared_comment_passes(tmp_path):
    configured(
        a_wiki(tmp_path),
        'allow:\n'
        '  - file: sample.go\n'
        '    text: "// the provider answers out of order"\n'
        '    why: "Their own docs say otherwise."\n',
    )
    assert main([str(tmp_path)]) == CLEAN


def test_editing_the_comment_loses_the_argument_made_for_it(tmp_path):
    configured(
        a_wiki(tmp_path, "// the provider answers in another order entirely\nvar x = 1\n"),
        'allow:\n'
        '  - file: sample.go\n'
        '    text: "// the provider answers out of order"\n'
        '    why: "Their own docs say otherwise."\n',
    )
    assert main([str(tmp_path)]) == FOUND


def test_an_allowance_without_a_reason_is_refused(tmp_path):
    configured(
        a_wiki(tmp_path),
        'allow:\n'
        '  - file: sample.go\n'
        '    text: "// the provider answers out of order"\n'
        '    why: ""\n',
    )
    assert main([str(tmp_path)]) == UNUSABLE


def test_a_skipped_directory_is_not_read(tmp_path):
    vendored = tmp_path / "vendored"
    vendored.mkdir()
    a_wiki(vendored)
    configured(tmp_path, "skip:\n  - vendored/\n")
    assert main([str(tmp_path)]) == CLEAN


def test_a_config_further_down_adds_to_the_one_above(tmp_path):
    inner = tmp_path / "inner"
    inner.mkdir()
    a_wiki(inner)
    configured(tmp_path, "skip:\n  - nothing/\n")
    configured(
        inner,
        'allow:\n'
        '  - file: sample.go\n'
        '    text: "// the provider answers out of order"\n'
        '    why: "Their own docs say otherwise."\n',
    )
    assert main([str(tmp_path)]) == CLEAN


def test_a_path_that_is_not_there_is_refused(tmp_path):
    assert main([str(tmp_path / "nowhere")]) == UNUSABLE


def test_a_broken_config_is_refused(tmp_path):
    configured(a_wiki(tmp_path), "allow: [oops\n")
    assert main([str(tmp_path)]) == UNUSABLE


def test_a_single_file_is_checked_on_its_own(tmp_path):
    a_wiki(tmp_path)
    assert main([str(tmp_path / "sample.go")]) == FOUND
