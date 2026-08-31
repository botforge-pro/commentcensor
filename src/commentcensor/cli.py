import argparse
import sys
from importlib.resources import files
from pathlib import Path

from .config import RuleBook, Unreadable
from .languages import language_of
from .scan import Comment, Unopenable, comments_in

CLEAN = 0
FOUND = 1
UNUSABLE = 2


def main(argv: list[str] | None = None) -> int:
    arguments = parser().parse_args(argv)
    paths = [Path(name) for name in arguments.paths]
    missing = [path for path in paths if not path.exists()]
    if missing:
        for path in missing:
            print(f"{path}: no such file or directory", file=sys.stderr)
        return UNUSABLE

    try:
        undeclared = undeclared_in(paths)
    except (Unreadable, Unopenable) as failure:
        print(failure, file=sys.stderr)
        return UNUSABLE

    for comment in undeclared:
        print(f"{comment.file}:{comment.line}: comment")
        for line in comment.text.splitlines():
            print(f"    {line}")
    if not undeclared:
        return CLEAN
    print(f"\n{count(len(undeclared))} not declared in .commentcensor.yaml")
    print(f"\n{manifesto()}")
    print(
        "Declare a comment that remains:\n\n"
        "  allow:\n"
        "    - file: path/to/file\n"
        '      text: "the comment, exactly as printed above"\n'
        '      why: "why the fact cannot be carried anywhere better"'
    )
    return FOUND


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


def undeclared_in(paths: list[Path]) -> list[Comment]:
    book = RuleBook()
    found = []
    for file in files_under(paths):
        rules = book.for_file(file)
        if rules.skips(file.resolve()):
            continue
        found += [
            comment
            for comment in comments_in(file)
            if rules.reason_for(file.resolve(), comment.text) is None
        ]
    return found


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


def count(found: int) -> str:
    return "1 comment" if found == 1 else f"{found} comments"


if __name__ == "__main__":
    sys.exit(main())
