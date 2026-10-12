from pathlib import Path

from commentcensor.cli import CLEAN, FOUND, UNUSABLE, main
from commentcensor.published import CACHE_VARIABLE, kept_for

REFERENCE = "https://pkg.go.dev/example.test/thing"
DOCUMENTED = (
    "// Package thing does something.\n"
    "package thing\n"
    "\n"
    "// Dialect is what the source says.\n"
    "type Dialect struct{}\n"
)
UNDOCUMENTED = "package thing\n\n// helper is not exported.\nfunc helper() {}\n"


def a_project(directory: Path, source: str, declared: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "thing.go").write_text(source)
    (directory / ".commentcensor.yaml").write_text(declared)
    return directory


def a_cache(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv(CACHE_VARIABLE, str(tmp_path / "cache"))


def a_reference(monkeypatch, tmp_path: Path, page: str) -> None:
    a_cache(monkeypatch, tmp_path)
    kept = kept_for(REFERENCE)
    kept.parent.mkdir(parents=True, exist_ok=True)
    kept.write_text(page, encoding="utf-8")


def test_a_published_doc_comment_needs_no_declaration(tmp_path, monkeypatch):
    a_reference(monkeypatch, tmp_path, "<html>type Dialect struct</html>")
    project = a_project(tmp_path / "src", DOCUMENTED, f"documentation: {REFERENCE}\n")

    assert main([str(project)]) == CLEAN


def test_a_comment_the_reference_does_not_publish_still_needs_one(tmp_path, monkeypatch):
    a_reference(monkeypatch, tmp_path, "<html>type Dialect struct</html>")
    project = a_project(tmp_path / "src", UNDOCUMENTED, f"documentation: {REFERENCE}\n")

    assert main([str(project)]) == FOUND


def test_without_the_address_a_doc_comment_is_a_comment(tmp_path, monkeypatch):
    a_cache(monkeypatch, tmp_path)
    project = a_project(tmp_path / "src", DOCUMENTED, "skip: []\n")

    assert main([str(project)]) == FOUND


def test_an_address_naming_none_of_them_is_refused(tmp_path, monkeypatch):
    a_reference(monkeypatch, tmp_path, "<html>Example Domain</html>")
    project = a_project(tmp_path / "src", DOCUMENTED, f"documentation: {REFERENCE}\n")

    assert main([str(project)]) == UNUSABLE


def test_an_address_that_answers_nothing_is_refused(tmp_path, monkeypatch):
    a_cache(monkeypatch, tmp_path)
    project = a_project(tmp_path / "src", DOCUMENTED, "documentation: http://127.0.0.1:1/none\n")

    assert main([str(project)]) == UNUSABLE


def test_an_address_that_is_not_one_is_refused(tmp_path, monkeypatch):
    a_cache(monkeypatch, tmp_path)
    project = a_project(tmp_path / "src", DOCUMENTED, "documentation: pkg.go.dev/thing\n")

    assert main([str(project)]) == UNUSABLE


PUBLISHED_PAGE = "<html>type Dialect struct type Reader interface Name Read</html>"


def test_a_doc_comment_in_a_test_file_still_needs_a_declaration(tmp_path, monkeypatch):
    a_reference(monkeypatch, tmp_path, "<html>type Dialect struct TestDialect</html>")
    project = a_project(tmp_path / "src", DOCUMENTED, f"documentation: {REFERENCE}\n")
    (project / "thing_test.go").write_text(
        "package thing\n\n// TestDialect checks what a dialect says.\nfunc TestDialect(t *testing.T) {}\n"
    )

    assert main([str(project)]) == FOUND, (
        "go doc and pkg.go.dev publish nothing from a _test.go file"
    )


def a_go_project(tmp_path: Path, case: str, declarations: str) -> Path:
    return a_project(
        tmp_path / case.replace(" ", "-"),
        "package thing\n\n" + declarations,
        f"documentation: {REFERENCE}\n",
    )


def test_a_doc_comment_go_doc_publishes_needs_no_declaration(tmp_path, monkeypatch):
    published = {
        "exported field": "type Dialect struct {\n\t// Name is its name.\n\tName string\n}\n",
        "two lines over an exported field": (
            "type Dialect struct {\n\t// Name is its name,\n\t// in full.\n\tName string\n}\n"
        ),
        "exported interface method": (
            "type Reader interface {\n\t// Read fills p.\n\tRead(p []byte) (int, error)\n}\n"
        ),
        "embedded exported type": "type Dialect struct {\n\t// Reader reads.\n\tio.Reader\n}\n",
        "field of a generic type": "type Dialect[T any] struct {\n\t// Name is T.\n\tName T\n}\n",
        "type in a group": "type (\n\t// Dialect is grouped.\n\tDialect struct{}\n)\n",
        "field of a type in a group": (
            "type (\n\tDialect struct {\n\t\t// Name is its name.\n\t\tName string\n\t}\n)\n"
        ),
        "field of an alias of a struct": (
            "type Dialect = struct {\n\t// Name is its name.\n\tName string\n}\n"
        ),
        "method of an alias of an interface": (
            "type Reader = interface {\n\t// Read fills p.\n\tRead(p []byte) (int, error)\n}\n"
        ),
        "type embedded in an exported interface": (
            "type Reader interface {\n\t// Reader reads.\n\tio.Reader\n}\n"
        ),
        "field of a struct inside an exported field": (
            "type Dialect struct {\n\tName struct {\n\t\t// Read is deep.\n\t\tRead int\n\t}\n}\n"
        ),
        "field of a struct behind a pointer in an exported field": (
            "type Dialect struct {\n\tName *struct {\n\t\t// Read is deep.\n\t\tRead int\n\t}\n}\n"
        ),
    }
    a_reference(monkeypatch, tmp_path, PUBLISHED_PAGE)
    for case, declarations in published.items():
        assert main([str(a_go_project(tmp_path, case, declarations))]) == CLEAN, case


def test_a_comment_go_doc_does_not_publish_still_needs_one(tmp_path, monkeypatch):
    unpublished = {
        "unexported field": "type Dialect struct {\n\t// name is private.\n\tname string\n}\n",
        "field of an unexported type": "type dialect struct {\n\t// Name is private.\n\tName string\n}\n",
        "field of a struct inside an unexported field": (
            "type Dialect struct {\n\tinner struct {\n\t\t// Deep is private.\n\t\tDeep int\n\t}\n}\n"
        ),
        "type embedded in an unexported interface": (
            "type reader interface {\n\t// Reader reads.\n\tio.Reader\n}\n"
        ),
        "field of a struct declared in a function": (
            "func make() {\n\ttype Local struct {\n\t\t// Name is private.\n\t\tName string\n\t}\n}\n"
        ),
        "comment at the end of the line before an exported field": (
            "type Dialect struct {\n\tTitle string // the title\n\tName string\n}\n"
        ),
        "comment parted from an exported field by a blank line": (
            "type Dialect struct {\n\t// Parted from Name.\n\n\tName string\n}\n"
        ),
        "comment parted from an exported type by a blank line": (
            "// Parted from Dialect.\n\ntype Dialect struct{}\n"
        ),
        "comment at the end of the line before an exported type": (
            "var x = 1 // the x\ntype Dialect struct{}\n"
        ),
        "embedded unexported type": "type Dialect struct {\n\t// reader reads.\n\treader\n}\n",
    }
    a_reference(monkeypatch, tmp_path, PUBLISHED_PAGE)
    for case, declarations in unpublished.items():
        assert main([str(a_go_project(tmp_path, case, declarations))]) == FOUND, case
