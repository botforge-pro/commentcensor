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
GO_MEMBER_LISTS = {
    "field_declaration_list": ("field_declaration",),
    "interface_type": ("method_elem", "type_elem"),
}
GO_TYPE_SPECS = ("type_spec", "type_alias")
GO_TEST_SUFFIX = "_test"
GO_TYPE_WRAPPERS = ("pointer_type", "slice_type", "array_type", "map_type", "channel_type")


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
    published = not (language.name == "go" and module.endswith(GO_TEST_SUFFIX))
    for node in comment_nodes(root):
        yield node, documented_export(node, language) if published else ""
    if language.docstrings:
        for holder, docstring in docstring_nodes(root):
            yield docstring, documented_holder(holder, language, module)


def documented_export(node: Node, language: Language) -> str:
    if not language.publishes_documentation:
        return ""
    if language.name in ("swift", "kotlin"):
        return documented_native_export(node, language)
    if language.name != "go":
        return ""
    parent = node.parent
    declared = go_doc_target(node)
    if parent is None or declared is None:
        return ""
    if parent.type == GO_ROOT:
        if declared.type not in GO_DECLARATIONS:
            return ""
        if declared.type == "package_clause":
            return next((text_of(child) for child in declared.named_children), "")
        return exported(declared_names(declared))
    if parent.type == "type_declaration" and at_go_root(parent):
        named = declared.child_by_field_name("name") if declared.type in GO_TYPE_SPECS else None
        return exported([text_of(named)] if named is not None else [])
    if parent.type in GO_MEMBER_LISTS and published_members(parent):
        if declared.type not in GO_MEMBER_LISTS[parent.type]:
            return ""
        return exported(member_names(declared))
    return ""


def go_doc_target(node: Node) -> Node | None:
    before = node.prev_sibling
    if before is not None and before.end_point[0] == node.start_point[0]:
        return None
    last = node
    following = node.next_named_sibling
    while following is not None and following.type == "comment":
        if following.start_point[0] != last.end_point[0] + 1:
            return None
        last = following
        following = following.next_named_sibling
    if following is None or following.start_point[0] != last.end_point[0] + 1:
        return None
    return following


def member_names(member: Node) -> list[str]:
    names = [text_of(child) for child in member.children_by_field_name("name")]
    if names:
        return names
    embedded = member.child_by_field_name("type")
    if embedded is None and member.type == "type_elem":
        embedded = next(iter(member.named_children), None)
    if embedded is None:
        return []
    return [text_of(embedded).lstrip("*").split("[")[0].rsplit(".", 1)[-1]]


def exported(names: list[str]) -> str:
    return next((name for name in names if name[:1].isupper()), "")


def at_go_root(declaration: Node) -> bool:
    return declaration.parent is not None and declaration.parent.type == GO_ROOT


def published_members(members: Node) -> bool:
    holder = members.parent if members.type == "field_declaration_list" else members
    owner = holder.parent if holder is not None else None
    while owner is not None and owner.type in GO_TYPE_WRAPPERS:
        owner = owner.parent
    if owner is None:
        return False
    if owner.type == "field_declaration":
        within = owner.parent
        return (
            bool(exported(member_names(owner)))
            and within is not None
            and within.type == "field_declaration_list"
            and published_members(within)
        )
    if owner.type not in GO_TYPE_SPECS:
        return False
    declaration = owner.parent
    if declaration is None or not at_go_root(declaration):
        return False
    named = owner.child_by_field_name("name")
    return named is not None and text_of(named)[:1].isupper()


def documented_native_export(node: Node, language: Language) -> str:
    written = text_of(node)
    if not written.startswith(("///", "/**")):
        return ""
    declared = node.next_named_sibling
    if declared is None:
        return ""
    visibility = declaration_visibility(declared)
    if language.name == "swift" and declared.type == "enum_entry":
        visibility = enclosing_swift_type_visibility(declared)
    if language.name == "swift" and visibility not in ("public", "open"):
        return ""
    if language.name == "kotlin" and visibility in ("private", "internal", "protected"):
        return ""
    named = declared.child_by_field_name("name")
    if named is None and language.name == "kotlin":
        named = kotlin_declaration_name(declared)
    return text_of(named) if named is not None else ""


def enclosing_swift_type_visibility(declared: Node) -> str:
    holder = declared.parent
    while holder is not None and holder.type != "class_declaration":
        holder = holder.parent
    return declaration_visibility(holder) if holder is not None else ""


def kotlin_declaration_name(declared: Node) -> Node | None:
    named = next(
        (
            child
            for child in declared.named_children
            if child.type in ("simple_identifier", "type_identifier")
        ),
        None,
    )
    if named is not None:
        return named
    variable = next(
        (child for child in declared.named_children if child.type == "variable_declaration"),
        None,
    )
    if variable is None:
        return None
    return variable.child_by_field_name("name") or next(
        (child for child in variable.named_children if child.type == "simple_identifier"),
        None,
    )


def declaration_visibility(declared: Node) -> str:
    modifiers = next(
        (child for child in declared.named_children if child.type == "modifiers"), None
    )
    if modifiers is None:
        return ""
    visibility = first_descendant(modifiers, "visibility_modifier")
    return text_of(visibility) if visibility is not None else ""


def first_descendant(node: Node, kind: str) -> Node | None:
    for child in node.named_children:
        if child.type == kind:
            return child
        if found := first_descendant(child, kind):
            return found
    return None


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
