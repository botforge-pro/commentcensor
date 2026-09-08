# Changelog

commentcensor treats every comment in your code as an error until you write
down why it cannot be avoided, on the grounds that a comment is a second
source of truth: the code changes, the sentence beside it goes on asserting
what used to be true, and readers believe it.

Changes are documented here in the format of
[Keep a Changelog](https://keepachangelog.com/).

## [0.2.0] - 2026-09-08

### Fixed

- In SQL, `-- name:` passes as a directive only when a single token follows
  it, which is what a query name is. Anything else after it is prose that was
  hiding behind the directive and going unreported: `-- name: get-wiki, the
  one the settings page reads` was read as an instruction to a tool.

  A repository that passed on 0.1.0 may report comments now. Each of them was
  always there; the check was looking past them.

## [0.1.0] - 2026-09-08

First public release. Requires Python 3.11 or newer:

```
python -m pip install git+https://github.com/botforge-pro/commentcensor.git
```

### Added

- `commentcensor <path>` reports every comment in the code under that path
  that is not declared in `.commentcensor.yaml`. It exits 1 both when a
  comment has no declaration and when a declaration names a comment that is
  no longer there, so a deleted comment takes its declaration with it.
- Python, Go, SQL, Swift, Kotlin, TypeScript and JavaScript, parsed with
  tree-sitter, so a `#` inside a string or a `//` inside a URL is not taken
  for a comment. Python docstrings count as comments.
- `.commentcensor.yaml` takes two keys and no more. `skip` lists paths left
  out of the check. `allow` declares a comment that stays: the file it is
  in, its text exactly as printed, and a free-text field naming which
  replacements were attempted first — a name, an extracted function, a log
  line, a test — and what each of them could not carry. A declaration is
  matched by the comment's own text rather than by its line, so moving the
  code keeps the exception and rewording the comment loses it.
- Passed without a declaration: a licence header in the first five lines, a
  shebang, a section marker (`// MARK:`, `# region`), and a directive
  addressed to a tool rather than a reader (`# noqa`, `# type: ignore`,
  `//go:embed`, `// swiftlint:disable`, `@ts-expect-error`).
- The reasoning behind all of it is `MANIFESTO.md`, installed with the
  package and printed after the findings of a failing run.

[0.2.0]: https://github.com/botforge-pro/commentcensor/releases/tag/v0.2.0
[0.1.0]: https://github.com/botforge-pro/commentcensor/releases/tag/v0.1.0
