from dataclasses import dataclass, field
from pathlib import Path

import yaml

CONFIG_NAME = ".commentcensor.yaml"


class Unreadable(Exception):
    pass


@dataclass(frozen=True)
class Allowance:
    file: Path
    text: str
    why: str


@dataclass
class Rules:
    skipped: list[Path] = field(default_factory=list)
    allowed: list[Allowance] = field(default_factory=list)

    def skips(self, path: Path) -> bool:
        return any(path.is_relative_to(skipped) for skipped in self.skipped)

    def reason_for(self, file: Path, text: str) -> str | None:
        for allowance in self.allowed:
            if allowance.file == file and allowance.text == text.strip():
                return allowance.why
        return None

    def joined(self, addition: "Rules") -> "Rules":
        return Rules(self.skipped + addition.skipped, self.allowed + addition.allowed)


class RuleBook:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.remembered: dict[Path, Rules] = {}

    def for_file(self, file: Path) -> Rules:
        return self.for_directory(file.resolve().parent)

    def for_directory(self, directory: Path) -> Rules:
        if directory in self.remembered:
            return self.remembered[directory]
        above = directory.parent
        inherited = (
            Rules()
            if directory == above or not directory.is_relative_to(self.root)
            else self.for_directory(above)
        )
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

    here = config.parent
    rules = Rules()
    for entry in written.get("skip") or []:
        rules.skipped.append((here / str(entry)).resolve())
    for entry in written.get("allow") or []:
        rules.allowed.append(allowance(entry, here, config))
    return rules


def allowance(entry: object, here: Path, config: Path) -> Allowance:
    if not isinstance(entry, dict):
        raise Unreadable(f"{config}: every allow entry is a mapping of file, text and why")
    missing = [key for key in ("file", "text", "why") if not str(entry.get(key, "")).strip()]
    if missing:
        raise Unreadable(f"{config}: an allow entry has no {', '.join(missing)}")
    return Allowance(
        file=(here / str(entry["file"])).resolve(),
        text=str(entry["text"]).strip(),
        why=str(entry["why"]).strip(),
    )
