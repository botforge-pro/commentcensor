import argparse
import sys
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path

from .config import Allowance, RuleBook, Unreadable
from .languages import language_of
from .scan import Comment, Unopenable, comments_in

CLEAN = 0
FOUND = 1
UNUSABLE = 2


@dataclass(frozen=True)
class Findings:
    undeclared: list[Comment]
    stale: list[Allowance]

    def any(self) -> bool:
        return bool(self.undeclared or self.stale)


def main(argv: list[str] | None = None) -> int:
    arguments = parser().parse_args(argv)
    paths = [Path(name) for name in arguments.paths]
    missing = [path for path in paths if not path.exists()]
    if missing:
        for path in missing:
            print(f"{path}: no such file or directory", file=sys.stderr)
        return UNUSABLE

    try:
        findings = findings_in(paths)
    except (Unreadable, Unopenable) as failure:
        print(failure, file=sys.stderr)
        return UNUSABLE

    if not findings.any():
        return CLEAN
    report(findings)
    return FOUND


def report(findings: Findings) -> None:
    for comment in findings.undeclared:
        print(f"{comment.file}:{comment.line}: comment")
        for line in comment.text.splitlines():
            print(f"    {line}")
    for allowance in findings.stale:
        print(f"{named(allowance.declared_in)}: nothing to allow in {named(allowance.file)}")
        for line in allowance.text.splitlines():
            print(f"    {line}")

    print()
    if findings.undeclared:
        print(f"{counted(len(findings.undeclared), 'comment')} not declared in .commentcensor.yaml")
    if findings.stale:
        print(f"{counted(len(findings.stale), 'declaration')} matching nothing")
    print(f"\n{manifesto()}")
    if findings.undeclared:
        print(
            "Declare a comment that remains:\n\n"
            "  allow:\n"
            "    - file: path/to/file\n"
            '      text: "the comment, exactly as printed above"\n'
            '      why: "why the fact cannot be carried anywhere better"\n'
        )
    if findings.stale:
        print(
            "\nA declaration claims the comment beneath it is still in the file. This one\n"
            "is not there any more, so delete the entry."
        )


def manifesto() -> str:
    packaged = files("commentcensor").joinpath("MANIFESTO.md")
    source = Path(__file__).parents[2] / "MANIFESTO.md"
    return (packaged if packaged.is_file() else source).read_text(encoding="utf-8").strip()


def parser() -> argparse.ArgumentParser:
    built = argparse.ArgumentParser(
        prog="commentcensor",
        description="Every comment is an error until you write down why it cannot be avoided",
    )
    built.add_argument("paths", nargs="*", default=["."], help="files or directories to check")
    return built


def findings_in(paths: list[Path]) -> Findings:
    book = RuleBook()
    undeclared: list[Comment] = []
    used: set[Allowance] = set()
    for file in files_under(paths):
        rules = book.for_file(file)
        if rules.skips(file.resolve()):
            continue
        for comment in comments_in(file):
            allowed = rules.allowances_for(file.resolve(), comment.text)
            used.update(allowed)
            if not allowed:
                undeclared.append(comment)
    for path in paths:
        book.for_directory(path.resolve() if path.is_dir() else path.resolve().parent)
    return Findings(undeclared, stale(book, used, paths))


def stale(book: RuleBook, used: set[Allowance], paths: list[Path]) -> list[Allowance]:
    declared = {allowance for rules in book.remembered.values() for allowance in rules.allowed}
    left = [allowance for allowance in declared - used if within(allowance.file, paths)]
    return sorted(
        left, key=lambda allowance: (allowance.declared_in, allowance.file, allowance.text)
    )


def within(file: Path, paths: list[Path]) -> bool:
    return any(file.is_relative_to(path.resolve()) for path in paths)


def named(path: Path) -> str:
    here = Path.cwd()
    return str(path.relative_to(here)) if path.is_relative_to(here) else str(path)


def files_under(paths: list[Path]) -> list[Path]:
    found: dict[Path, Path] = {}
    for path in paths:
        for file in walked(path):
            found.setdefault(file.resolve(), file)
    return [found[key] for key in sorted(found)]


def walked(path: Path) -> list[Path]:
    if path.is_file():
        return [path] if language_of(path.suffix) else []
    return [
        file
        for file in path.rglob("*")
        if file.is_file() and language_of(file.suffix) and not hidden(file, path)
    ]


def hidden(file: Path, root: Path) -> bool:
    return any(part.startswith(".") for part in file.relative_to(root).parts)


def counted(found: int, thing: str) -> str:
    return f"1 {thing}" if found == 1 else f"{found} {thing}s"


if __name__ == "__main__":
    sys.exit(main())
