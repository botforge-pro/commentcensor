from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from tree_sitter import Node
from tree_sitter_language_pack import get_parser

from .languages import (
    Language,
    instructs_a_tool,
    language_of,
    names_a_section,
    runs_the_file,
    states_a_licence,
)

DOCSTRING_HOLDERS = ("module", "function_definition", "class_definition")
STRING_TYPES = ("string", "concatenated_string")


class Unopenable(Exception):
    pass


@dataclass(frozen=True)
class Comment:
    file: Path
    line: int
    text: str
    column: int

    @property
    def last_line(self) -> int:
        return self.line + self.text.count("\n")

    def continues(self, earlier: "Comment") -> bool:
        return (
            "\n" not in self.text
            and self.column == earlier.column
            and self.line == earlier.last_line + 1
        )

    def joined(self, later: "Comment") -> "Comment":
        return Comment(self.file, self.line, f"{self.text}\n{later.text}", self.column)


def comments_in(path: Path) -> list[Comment]:
    language = language_of(path.suffix)
    if language is None:
        return []
    try:
        source = path.read_bytes()
    except OSError as failure:
        raise Unopenable(f"{path}: {failure.strerror or failure}") from failure
    tree = get_parser(language.grammar).parse(source)
    found = [
        comment_at(path, node)
        for node in speaking_nodes(tree.root_node, language)
        if not passes(node, language)
    ]
    return blocks(sorted(found, key=lambda comment: comment.line))


def blocks(comments: list[Comment]) -> list[Comment]:
    gathered: list[Comment] = []
    for comment in comments:
        if gathered and comment.continues(gathered[-1]):
            gathered[-1] = gathered[-1].joined(comment)
        else:
            gathered.append(comment)
    return gathered


def comment_at(path: Path, node: Node) -> Comment:
    return Comment(path, node.start_point[0] + 1, text_of(node), node.start_point[1])


def text_of(node: Node) -> str:
    return (node.text or b"").decode("utf-8", "replace").strip()


def passes(node: Node, language: Language) -> bool:
    text = text_of(node)
    if not text:
        return True
    line = node.start_point[0] + 1
    return (
        runs_the_file(text, line)
        or instructs_a_tool(text, language)
        or states_a_licence(text, line)
        or names_a_section(text)
    )


def speaking_nodes(root: Node, language: Language) -> Iterator[Node]:
    yield from comment_nodes(root)
    if language.docstrings:
        yield from docstring_nodes(root)


def comment_nodes(node: Node) -> Iterator[Node]:
    if "comment" in node.type:
        yield node
        return
    for child in node.children:
        yield from comment_nodes(child)


def docstring_nodes(node: Node) -> Iterator[Node]:
    if node.type in DOCSTRING_HOLDERS:
        docstring = docstring_of(node)
        if docstring is not None:
            yield docstring
    for child in node.children:
        yield from docstring_nodes(child)


def docstring_of(holder: Node) -> Node | None:
    body = holder if holder.type == "module" else holder.child_by_field_name("body")
    if body is None or not body.named_children:
        return None
    first = body.named_children[0]
    if first.type in STRING_TYPES:
        return first
    if first.type == "expression_statement" and len(first.named_children) == 1:
        inner = first.named_children[0]
        return inner if inner.type in STRING_TYPES else None
    return None
