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
GO_DECLARATIONS = (
    "package_clause",
    "function_declaration",
    "method_declaration",
    "type_declaration",
    "var_declaration",
    "const_declaration",
)
GO_ROOT = "source_file"


class Unopenable(Exception):
    pass


@dataclass(frozen=True)
class Comment:
    file: Path
    line: int
    text: str
    column: int
    documents: str = ""

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
        return Comment(
            self.file,
            self.line,
            f"{self.text}\n{later.text}",
            self.column,
            self.documents or later.documents,
        )


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
        comment_at(path, node, documents)
        for node, documents in speaking_nodes(tree.root_node, language, path.stem)
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


def comment_at(path: Path, node: Node, documents: str) -> Comment:
    return Comment(path, node.start_point[0] + 1, text_of(node), node.start_point[1], documents)


def text_of(node: Node) -> str:
    return (node.text or b"").decode("utf-8", "replace").strip()


def passes(node: Node, language: Language) -> bool:
    text = text_of(node)
    if not text:
        return True
    line = node.start_point[0] + 1
    return (
        runs_the_file(text, line)
        or ("comment" in node.type and language.declares_encoding(text, line))
        or instructs_a_tool(text, language)
        or states_a_licence(text, line)
        or names_a_section(text)
    )


def speaking_nodes(root: Node, language: Language, module: str) -> Iterator[tuple[Node, str]]:
    for node in comment_nodes(root):
        yield node, documented_export(node, language)
    if language.docstrings:
        for holder, docstring in docstring_nodes(root):
            yield docstring, documented_holder(holder, language, module)


def documented_export(node: Node, language: Language) -> str:
    if not language.publishes_documentation or language.name != "go":
        return ""
    parent = node.parent
    if parent is None or parent.type != GO_ROOT:
        return ""
    declared = node.next_named_sibling
    while declared is not None and declared.type == "comment":
        declared = declared.next_named_sibling
    if declared is None or declared.type not in GO_DECLARATIONS:
        return ""
    if declared.type == "package_clause":
        return next((text_of(child) for child in declared.named_children), "")
    return next((name for name in declared_names(declared) if name[:1].isupper()), "")


def declared_names(declared: Node) -> list[str]:
    named = declared.child_by_field_name("name")
    if named is not None:
        return [text_of(named)]
    return [
        text_of(name)
        for spec in declared.named_children
        if (name := spec.child_by_field_name("name")) is not None
    ]


def documented_holder(holder: Node, language: Language, module: str) -> str:
    if not language.publishes_documentation:
        return ""
    if holder.type == "module":
        return "" if module.startswith("_") else module
    named = holder.child_by_field_name("name")
    if named is None:
        return ""
    name = text_of(named)
    return "" if name.startswith("_") else name


def comment_nodes(node: Node) -> Iterator[Node]:
    if "comment" in node.type:
        yield node
        return
    for child in node.children:
        yield from comment_nodes(child)


def docstring_nodes(node: Node) -> Iterator[tuple[Node, Node]]:
    if node.type in DOCSTRING_HOLDERS:
        docstring = docstring_of(node)
        if docstring is not None:
            yield node, docstring
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
