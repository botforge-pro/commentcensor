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
