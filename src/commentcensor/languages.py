from dataclasses import dataclass
from functools import cache
from importlib.resources import files

import yaml

PACKAGE = "commentcensor"
DATA = "languages.yaml"
REQUIRED = ("grammar", "extensions", "directives")
DEFAULT_MARKERS = "/-#*<!"


class Undefined(Exception):
    pass


@dataclass(frozen=True)
class Language:
    name: str
    grammar: str
    directives: tuple[str, ...]
    docstrings: bool


@cache
def written() -> dict:
    loaded = yaml.safe_load(files(PACKAGE).joinpath(DATA).read_text())
    if not isinstance(loaded, dict):
        raise Undefined(f"{DATA}: expected a mapping")
    return loaded


@cache
def defined() -> dict[str, Language]:
    by_extension: dict[str, Language] = {}
    for name, entry in (written().get("languages") or {}).items():
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
def phrases(key: str) -> tuple[str, ...]:
    return tuple(str(phrase) for phrase in written().get(key) or ())


@cache
def marker_characters() -> str:
    return str(written().get("marker_characters") or DEFAULT_MARKERS)


def language_of(suffix: str) -> Language | None:
    return defined().get(suffix.lower())


def opens_with(text: str, phrases: tuple[str, ...]) -> bool:
    stripped = text.lstrip(marker_characters()).lstrip()
    return any(opens_exactly_with(stripped, phrase) for phrase in phrases)


def opens_exactly_with(stripped: str, phrase: str) -> bool:
    if not stripped.startswith(phrase):
        return False
    if not phrase[-1].isalnum():
        return True
    rest = stripped[len(phrase) :]
    return not rest or not rest[0].isalnum()


def instructs_a_tool(text: str, language: Language) -> bool:
    return opens_with(text, language.directives)


def names_a_section(text: str) -> bool:
    return opens_with(text, phrases("section_markers"))


def states_a_licence(text: str, line: int) -> bool:
    return line <= 5 and any(marker in text for marker in phrases("licence_markers"))


def runs_the_file(text: str, line: int) -> bool:
    return line == 1 and text.startswith("#!")
