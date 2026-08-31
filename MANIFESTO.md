# Every comment is guilty until proven necessary

A comment creates a second source of truth. Code changes while the comment
keeps asserting what used to be true, and readers trust the lie because it
sits beside the code.

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

- an external constraint of a library, platform, network or licence;
- the price of a deliberate compromise;
- a dead end that was tried and is recorded nowhere else;
- a contract at the boundary of a module.

If the fact can live elsewhere, the comment is an error. Making it shorter
does not fix it. If it must remain, keep it brief and declare why no better
owner can carry the fact.
