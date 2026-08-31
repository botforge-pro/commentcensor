from dataclasses import dataclass
from functools import cache
from importlib.resources import files

import yaml

DATA = "languages.yaml"
REQUIRED = ("grammar", "extensions", "directives")


class Undefined(Exception):
    pass


@dataclass(frozen=True)
class Language:
    name: str
    grammar: str
    directives: tuple[str, ...]
    docstrings: bool


@cache
def defined() -> dict[str, Language]:
    written = yaml.safe_load(files("commentcensor").joinpath(DATA).read_text())
    by_extension: dict[str, Language] = {}
    for name, entry in (written.get("languages") or {}).items():
        missing = [key for key in REQUIRED if not entry.get(key)]
        if missing:
            raise Undefined(f"{DATA}: {name} has no {', '.join(missing)}")
        language = Language(
            name=name,
            grammar=str(entry["grammar"]),
            directives=tuple(str(directive) for directive in entry["directives"]),
            docstrings=bool(entry.get("docstrings", False)),
        )
        for extension in entry["extensions"]:
            claimed = by_extension.get(str(extension))
            if claimed is not None:
                raise Undefined(f"{DATA}: {extension} is claimed by {claimed.name} and {name}")
            by_extension[str(extension)] = language
    if not by_extension:
        raise Undefined(f"{DATA}: no languages defined")
    return by_extension


@cache
def licence_markers() -> tuple[str, ...]:
    written = yaml.safe_load(files("commentcensor").joinpath(DATA).read_text())
    return tuple(str(marker) for marker in written.get("licence_markers") or ())


@cache
def marker_characters() -> str:
    written = yaml.safe_load(files("commentcensor").joinpath(DATA).read_text())
    return str(written.get("marker_characters") or "/-#*<!")


def language_of(suffix: str) -> Language | None:
    return defined().get(suffix.lower())


def instructs_a_tool(text: str, language: Language) -> bool:
    stripped = text.lstrip(marker_characters()).lstrip()
    return any(stripped.startswith(directive) for directive in language.directives)


def states_a_licence(text: str, line: int) -> bool:
    return line <= 5 and any(marker in text for marker in licence_markers())


def runs_the_file(text: str, line: int) -> bool:
    return line == 1 and text.startswith("#!")
