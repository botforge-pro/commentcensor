# Every comment is guilty until proven necessary

A comment creates a second source of truth. Code changes while the comment
keeps asserting what used to be true, and readers trust the lie because it
sits beside the code.

A comment is any text in comment syntax or a docstring, except a licence,
section marker, shebang or tool directive.

Every fact has an owner:

- names, types and structure say what the code is;
- the log says what a run actually did;
- a test enforces behaviour that must survive a change;
- project documentation owns product knowledge and working rules;
- version history records what the code used to be.

Code MUST NOT contain a rule, a paraphrase of a rule, or a pointer to its
source, except in an identifier, error message or test name that states
behaviour the program enforces, checks or reports.

A comment earns its place only when the fact cannot live in any of those
places and the reader needs it beside the code:

- a constraint imposed by a named external system that code cannot express
  or verify;
- a deliberate compromise whose rejected alternative and accepted cost are
  named;
- an API obligation the type system cannot express, when that comment is
  the source of API documentation built by CI.

If the fact can live elsewhere, the comment is an error. A shorter comment is
still a comment. Every remaining comment MUST be declared in
`.commentcensor.yaml` with the concrete reason it meets one of these exceptions.
