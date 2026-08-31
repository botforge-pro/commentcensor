# commentcensor

Every comment in your code is an error until you write down why it cannot
be avoided.

```
$ commentcensor src/
src/store.py:41: comment — "# retry three times before giving up"
src/parser.go:87: comment — "// the server sends the fields out of order"

2 comments not declared in .commentcensor.yaml
```

## Why

A comment is the one part of a file that nothing checks. It is not
compiled, not run, not typed and not covered by a test, so it drifts
away from the code beside it — and then misleads with the authority of
something written down. The more comments a file carries, the less each
one is worth reading, and the ones that do carry something are lost among
the ones that repeat the line below them.

So the default is none, and each exception is argued in writing.

## What carries it instead

A comment is usually a repair for something the code should have said
itself:

- **a name.** `if wiki.origin == .added` with a paragraph above it becomes
  `if wiki.canBeTakenOff`. The paragraph moves onto the property, once,
  instead of onto every use of it.
- **a test.** "a node that moved changes the page it belongs to" is a
  requirement. Written as a comment nothing holds it; written as a test
  name it fails when it stops being true.
- **a different shape.** A comment explaining how three flags stay in step
  is a description of the wrong structure. One state instead of three
  flags, and there is nothing left to explain.
- **nothing at all.** Most of what gets written was already legible in the
  code.

What is left after that is worth keeping: a fact from outside the file
that the reader cannot get from the code — an API that behaves against
its own documentation, a workaround for a bug in a dependency, a measured
number, a rule of the domain. Those are the ones you declare.

## What it does

Parses the file, finds every comment the grammar reports, and fails on
each one that is not declared in `.commentcensor.yaml` with a reason.
Exit code is 1 when anything is undeclared, so it belongs in CI beside
the formatter.

Comments that instruct a tool rather than a reader — `# noqa`,
`# type: ignore`, `//go:embed`, `// swiftlint:disable`, `@ts-expect-error`,
a shebang, a license header — are not comments in this sense and pass
without being declared.

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

The nearest `.commentcensor.yaml` above a file is the one that applies,
and its `skip` and `allow` add to those of the configs above it.

There is no mode that takes an existing repository as it stands. A
codebase adopts this by fixing its comments or by listing its paths in
`skip` until it does.

## Installing

```
pip install commentcensor
```
