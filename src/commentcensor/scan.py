from dataclasses import dataclass
from pathlib import Path

from tree_sitter import Node
from tree_sitter_language_pack import get_parser

from .languages import (
    Language,
    instructs_a_tool,
    language_of,
    runs_the_file,
    states_a_licence,
)

DOCSTRING_HOLDERS = ("module", "function_definition", "class_definition")
STRING_TYPES = ("string", "concatenated_string")


@dataclass(frozen=True)
class Comment:
    file: Path
    line: int
    text: str


def comments_in(path: Path) -> list[Comment]:
    language = language_of(path.suffix)
    if language is None:
        return []
    tree = get_parser(language.grammar).parse(path.read_bytes())
    found = [
        comment_at(path, node)
        for node in speaking_nodes(tree.root_node, language)
        if not passes(node, language)
    ]
    return sorted(found, key=lambda comment: comment.line)


def comment_at(path: Path, node: Node) -> Comment:
    return Comment(path, node.start_point[0] + 1, text_of(node))


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
    )


def speaking_nodes(root: Node, language: Language):
    yield from comment_nodes(root)
    if language.docstrings:
        yield from docstring_nodes(root)


def comment_nodes(node: Node):
    if "comment" in node.type:
        yield node
        return
    for child in node.children:
        yield from comment_nodes(child)


def docstring_nodes(node: Node):
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
