# commentcensor

Every comment in your code is an error until you write down why it cannot
be avoided.

[Read the manifesto.](MANIFESTO.md)

```
$ commentcensor src/
src/store.py:41: comment
    # retry three times before giving up
src/parser.go:87: comment
    // the server sends the fields out of order

2 comments not declared in .commentcensor.yaml
```

## What it does

Parses the file, finds every comment the grammar reports, and fails on
each one that is not declared in `.commentcensor.yaml` with a reason.
Exit code is 1 when the code and the declarations disagree either way, so
it belongs in CI beside the formatter.

These are not comments in that sense and pass without being declared:
instructions to a tool (`# noqa`, `# type: ignore`, `//go:embed`,
`// swiftlint:disable`, `@ts-expect-error`), a shebang, a licence header,
and a section marker (`// MARK:`, `# region`).

## Languages

Python, Go, SQL, Swift, Kotlin, TypeScript, JavaScript. Parsed with
tree-sitter, so a `#` inside a string or a `//` inside a URL is not
mistaken for a comment.

Python docstrings count. A docstring that repeats the name of the
function under it is the thing this tool exists to remove.

## Configuration

Two knobs, and there will not be a third.

```yaml
# .commentcensor.yaml
skip:
  - Generated/
  - vendor/

allow:
  - file: src/store.py
    text: "# retry three times before giving up"
    why: "The provider drops the first request of a cold connection."
```

`skip` takes whole paths out of the check: generated code, vendored
code, a directory you have not got to yet.

`allow` names one comment and the reason it stays. The reason is
required and is what the next reader is owed. An entry is matched by the
comment's own text, not by its line, so moving the code keeps the
exception and editing the comment loses it — an argument that was made
for one sentence does not carry over to another.

An entry that matches nothing is a finding of its own: it claims a
comment is in a file, and the claim is false once the comment is edited,
moved to another file or deleted. Only entries naming files inside the
run are checked this way, so checking one directory says nothing about
the entries for another.

The nearest `.commentcensor.yaml` above a file is the one that applies,
and its `skip` and `allow` add to those of the configs above it.

There is no mode that takes an existing repository as it stands. A
codebase adopts this by fixing its comments or by listing its paths in
`skip` until it does.

## Installing

```
pip install commentcensor
```
