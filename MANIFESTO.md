# Every comment is guilty until proven necessary

A comment creates a second source of truth. Code changes while the comment
keeps asserting what used to be true, and readers trust the lie because it
sits beside the code.

A comment is any text in comment syntax or a docstring, except a licence,
section marker, shebang or tool directive.

Every fact has an owner. Those owners include, but are not limited to:

* names, types and structure for code meaning;
* logs for runtime outcomes, while failures are handled, propagated or logged;
* tests for requirements;
* issues for unfinished work;
* project documentation for product knowledge and working rules;
* Git for the past.

Code MUST NOT contain a rule, a paraphrase of a rule, or a pointer to its
source, except in an identifier, error message or test name that states
behaviour the program enforces, checks or reports.

A comment qualifies only when its content belongs beside the code and meets
one of these exceptions:

* a constraint imposed by a named external system that code cannot express
  or verify;
* a deliberate compromise whose rejected alternative and accepted cost are
  named;
* an API obligation the type system cannot express, when that comment is
  the source of API documentation built by CI.

If its content can live elsewhere, the comment is an error. A shorter comment
is still a comment. Every remaining comment MUST be declared in
`.commentcensor.yaml`. The declaration names every owner offered the fact,
such as a name, extracted function, log line or test, and explains what each
of them could not carry.
