import pytest

from commentcensor.scan import comments_in

SPEAKING = {
    "sample.py": "# the provider answers out of order\nx = 1\n",
    "sample.go": "package main\n\n// the provider answers out of order\nvar x = 1\n",
    "sample.sql": "-- the provider answers out of order\nselect 1;\n",
    "sample.swift": "// the provider answers out of order\nlet x = 1\n",
    "sample.kt": "// the provider answers out of order\nval x = 1\n",
    "sample.ts": "// the provider answers out of order\nexport const x = 1;\n",
    "sample.tsx": "// the provider answers out of order\nexport const x = 1;\n",
    "sample.js": "// the provider answers out of order\nexport const x = 1;\n",
}

INSTRUCTING = {
    "sample.py": "import os  # noqa: F401\n",
    "sample.go": "//go:embed all:assets\nvar assets string\n",
    "sample.sql": "-- name: get-wiki\nselect 1;\n",
    "sample.swift": "// swiftlint:disable force_cast\nlet x = 1\n",
    "sample.kt": "// noinspection SpellCheckingInspection\nval x = 1\n",
    "sample.ts": "// @ts-expect-error the upstream types are wrong\nexport const x = 1;\n",
    "sample.js": "// eslint-disable-next-line no-undef\nexport const x = 1;\n",
}

QUOTED = {
    "sample.py": 'url = "# not a comment"\n',
    "sample.go": 'package main\n\nvar url = "https://example.com//not-a-comment"\n',
    "sample.sql": "select '-- not a comment';\n",
    "sample.swift": 'let url = "// not a comment"\n',
    "sample.kt": 'val url = "// not a comment"\n',
    "sample.ts": 'export const url = "https://example.com // not a comment";\n',
}


def written(tmp_path, name, source):
    file = tmp_path / name
    file.write_text(source)
    return file


@pytest.mark.parametrize("name,source", SPEAKING.items())
def test_a_comment_addressed_to_a_reader_is_found(tmp_path, name, source):
    found = comments_in(written(tmp_path, name, source))
    spoken = next(line for line in source.splitlines() if "answers out of order" in line)
    assert [comment.text for comment in found] == [spoken.strip()]


@pytest.mark.parametrize("name,source", INSTRUCTING.items())
def test_a_comment_addressed_to_a_tool_passes(tmp_path, name, source):
    assert comments_in(written(tmp_path, name, source)) == []


@pytest.mark.parametrize("name,source", QUOTED.items())
def test_a_marker_inside_a_string_is_not_a_comment(tmp_path, name, source):
    assert comments_in(written(tmp_path, name, source)) == []


def test_a_shebang_is_not_a_comment(tmp_path):
    assert comments_in(written(tmp_path, "run.py", "#!/usr/bin/env python3\nx = 1\n")) == []


def test_a_licence_header_is_not_a_comment(tmp_path):
    source = "// SPDX-License-Identifier: MIT\nlet x = 1\n"
    assert comments_in(written(tmp_path, "sample.swift", source)) == []


def test_a_licence_further_down_the_file_is_a_comment(tmp_path):
    source = "let a = 1\nlet b = 2\nlet c = 3\nlet d = 4\nlet e = 5\n// Copyright somebody\n"
    assert len(comments_in(written(tmp_path, "sample.swift", source))) == 1


def test_a_python_docstring_is_a_comment(tmp_path):
    source = 'def retry():\n    """Retries the call."""\n    return 1\n'
    found = comments_in(written(tmp_path, "sample.py", source))
    assert [comment.line for comment in found] == [2]


def test_a_module_docstring_is_a_comment(tmp_path):
    found = comments_in(written(tmp_path, "sample.py", '"""What this module is."""\nx = 1\n'))
    assert [comment.line for comment in found] == [1]


def test_a_string_that_is_not_the_first_statement_is_not_a_docstring(tmp_path):
    source = "def retry():\n    x = 1\n    return 'plain string'\n"
    assert comments_in(written(tmp_path, "sample.py", source)) == []


def test_a_file_in_a_language_it_does_not_know_is_left_alone(tmp_path):
    assert comments_in(written(tmp_path, "notes.md", "<!-- a comment -->\n")) == []


def test_the_line_is_the_one_the_comment_starts_on(tmp_path):
    source = "package main\n\nvar x = 1\n\n// what the reader is told\nvar y = 2\n"
    found = comments_in(written(tmp_path, "sample.go", source))
    assert [comment.line for comment in found] == [5]


def test_lines_of_one_comment_block_are_one_comment(tmp_path):
    source = "// the provider answers\n// out of order\nlet x = 1\n"
    found = comments_in(written(tmp_path, "sample.swift", source))
    assert [comment.text for comment in found] == ["// the provider answers\n// out of order"]


def test_two_blocks_apart_stay_two_comments(tmp_path):
    source = "// first thing\nlet x = 1\n// second thing\nlet y = 2\n"
    assert len(comments_in(written(tmp_path, "sample.swift", source))) == 2


def test_a_block_indented_differently_is_a_second_comment(tmp_path):
    source = "// at the margin\n    // indented under something\nlet x = 1\n"
    assert len(comments_in(written(tmp_path, "sample.swift", source))) == 2


def test_a_section_marker_is_not_a_comment(tmp_path):
    assert comments_in(written(tmp_path, "sample.swift", "// MARK: - Reading\nlet x = 1\n")) == []


def test_a_region_marker_is_not_a_comment(tmp_path):
    assert comments_in(written(tmp_path, "sample.kt", "// region reading\nval x = 1\n")) == []
