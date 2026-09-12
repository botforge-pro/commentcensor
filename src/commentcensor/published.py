import hashlib
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

CACHE_VARIABLE = "XDG_CACHE_HOME"
CACHE_NAME = "commentcensor"
FRESH_FOR = 7 * 24 * 60 * 60
WAIT = 10


class Unpublished(Exception):
    pass


def names_one_of(url: str, names: set[str]) -> bool:
    page = reference(url)
    return any(name in page for name in names)


def reference(url: str) -> str:
    kept = kept_for(url)
    if fresh(kept):
        return kept.read_text(encoding="utf-8")
    try:
        with urllib.request.urlopen(url, timeout=WAIT) as answer:
            page = answer.read().decode("utf-8", "replace")
    except (urllib.error.URLError, OSError, ValueError) as failure:
        if kept.is_file():
            return kept.read_text(encoding="utf-8")
        raise Unpublished(
            f"{url}: the reference cannot be read, so the documentation it claims to "
            f"publish cannot be shown to exist ({failure})"
        ) from failure
    kept.parent.mkdir(parents=True, exist_ok=True)
    kept.write_text(page, encoding="utf-8")
    return page


def kept_for(url: str) -> Path:
    return cache() / f"{hashlib.sha256(url.encode()).hexdigest()}.page"


def cache() -> Path:
    named = os.environ.get(CACHE_VARIABLE)
    return (Path(named) if named else Path.home() / ".cache") / CACHE_NAME


def fresh(kept: Path) -> bool:
    return kept.is_file() and time.time() - kept.stat().st_mtime < FRESH_FOR
