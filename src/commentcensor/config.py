from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import Path

import yaml

CONFIG_NAME = ".commentcensor.yaml"
KEYS = ("skip", "allow", "documentation")
ADDRESSES = ("https://", "http://")
REASON = "what_was_tried_and_why_none_of_it_worked"
ENTRY_KEYS = ("file", "text", REASON)


class Unreadable(Exception):
    pass


@dataclass(frozen=True)
class Allowance:
    file: Path
    text: str
    reason: str
    declared_in: Path
    ordinal: int


@dataclass
class Skip:
    under: Path
    pattern: str

    def covers(self, path: Path) -> bool:
        if not path.is_relative_to(self.under):
            return False
        inside = path.relative_to(self.under).as_posix()
        named = self.pattern.rstrip("/")
        return fnmatch(inside, named) or fnmatch(inside, f"{named}/*")


@dataclass
class Rules:
    skipped: list[Skip] = field(default_factory=list)
    allowed: list[Allowance] = field(default_factory=list)
    documentation: str = ""

    def skips(self, path: Path) -> bool:
        return any(skipped.covers(path) for skipped in self.skipped)

    def allowances_for(self, file: Path, text: str) -> list[Allowance]:
        return [
            allowance
            for allowance in self.allowed
            if allowance.file == file and allowance.text == text.strip()
        ]

    def joined(self, addition: "Rules") -> "Rules":
        return Rules(
            self.skipped + addition.skipped,
            self.allowed + addition.allowed,
            addition.documentation or self.documentation,
        )


class RuleBook:
    def __init__(self) -> None:
        self.remembered: dict[Path, Rules] = {}

    def for_file(self, file: Path) -> Rules:
        return self.for_directory(file.resolve().parent)

    def for_directory(self, directory: Path) -> Rules:
        if directory in self.remembered:
            return self.remembered[directory]
        above = directory.parent
        inherited = Rules() if directory == above else self.for_directory(above)
        config = directory / CONFIG_NAME
        rules = inherited.joined(read(config)) if config.is_file() else inherited
        self.remembered[directory] = rules
        return rules


def read(config: Path) -> Rules:
    try:
        written = yaml.safe_load(config.read_text()) or {}
    except (OSError, yaml.YAMLError) as failure:
        raise Unreadable(f"{config}: {failure}") from failure
    if not isinstance(written, dict):
        raise Unreadable(f"{config}: expected a mapping of skip and allow")
    unknown = sorted(set(written) - set(KEYS))
    if unknown:
        raise Unreadable(f"{config}: {', '.join(unknown)} is not a setting; there are {KEYS}")

    here = config.parent
    rules = Rules()
    for entry in entries(written, "skip", config):
        if not isinstance(entry, str):
            raise Unreadable(f"{config}: every skip entry is a string")
        rules.skipped.append(Skip(under=here.resolve(), pattern=entry))
    for ordinal, entry in enumerate(entries(written, "allow", config)):
        rules.allowed.append(allowance(entry, here, config, ordinal))
    rules.documentation = address(written.get("documentation"), config)
    return rules


def address(written: object, config: Path) -> str:
    if written is None:
        return ""
    if not isinstance(written, str) or not written.startswith(ADDRESSES):
        raise Unreadable(
            f"{config}: documentation is the address the reference is published at, "
            f"beginning with {' or '.join(ADDRESSES)}"
        )
    return written


def entries(written: dict, setting: str, config: Path) -> list:
    value = written.get(setting)
    if value is None:
        return []
    if not isinstance(value, list):
        raise Unreadable(f"{config}: {setting} must be a list")
    return value


def allowance(entry: object, here: Path, config: Path, ordinal: int) -> Allowance:
    if not isinstance(entry, dict):
        raise Unreadable(f"{config}: every allow entry is a mapping of {', '.join(ENTRY_KEYS)}")
    unknown = sorted(set(entry) - set(ENTRY_KEYS))
    if unknown:
        raise Unreadable(f"{config}: an allow entry has no {unknown[0]}; the keys are {ENTRY_KEYS}")
    said = {key: spoken(entry.get(key)) for key in ENTRY_KEYS}
    missing = [key for key, value in said.items() if not value]
    if missing:
        raise Unreadable(f"{config}: an allow entry has no {', '.join(missing)}")
    return Allowance(
        file=(here / said["file"]).resolve(),
        text=said["text"],
        reason=said[REASON],
        declared_in=config.resolve(),
        ordinal=ordinal,
    )


def spoken(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""
