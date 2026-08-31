import argparse
import sys
from pathlib import Path

from .config import RuleBook, Unreadable
from .languages import language_of
from .scan import Comment, comments_in

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
        undeclared = [comment for path in paths for comment in undeclared_in(path)]
    except Unreadable as failure:
        print(failure, file=sys.stderr)
        return UNUSABLE

    for comment in undeclared:
        print(f"{comment.file}:{comment.line}: comment — {first_line(comment.text)}")
    if not undeclared:
        return CLEAN
    print(f"\n{count(len(undeclared))} not declared in .commentcensor.yaml")
    return FOUND


def parser() -> argparse.ArgumentParser:
    built = argparse.ArgumentParser(
        prog="commentcensor",
        description="Every comment is an error until you write down why it cannot be avoided",
    )
    built.add_argument("paths", nargs="*", default=["."], help="files or directories to check")
    return built


def undeclared_in(path: Path) -> list[Comment]:
    book = RuleBook(path if path.is_dir() else path.parent)
    return [
        comment
        for file in files_under(path)
        if not book.for_file(file).skips(file.resolve())
        for comment in comments_in(file)
        if book.for_file(file).reason_for(file.resolve(), comment.text) is None
    ]


def files_under(path: Path) -> list[Path]:
    if path.is_file():
        return [path] if language_of(path.suffix) else []
    return sorted(
        file
        for file in path.rglob("*")
        if file.is_file() and language_of(file.suffix) and not hidden(file, path)
    )


def hidden(file: Path, root: Path) -> bool:
    return any(part.startswith(".") for part in file.relative_to(root).parts)


def first_line(text: str) -> str:
    lines = text.splitlines()
    head = lines[0].strip() if lines else ""
    return f"{head} …" if len(lines) > 1 else head


def count(found: int) -> str:
    return "1 comment" if found == 1 else f"{found} comments"


if __name__ == "__main__":
    sys.exit(main())
