# The comment is not the source

A comment is usually a second record of a fact that already has a place of
its own: a name or the structure of the code, a log entry, a test, the
project documentation, or the history of the change. Two records drift
apart unnoticed. One is updated while the other keeps asserting what used
to be true, and the record nearest the code is the one readers trust.

Put each fact where a change can prove it wrong:

- names, types and structure say what the code is;
- the log says what a run actually did;
- a test enforces behaviour that must survive a change;
- project documentation owns product knowledge and working rules;
- version history records what the code used to be.

Do not copy a rule into the code and do not point at it from the code. The
copy, paraphrase, address or title can go stale while still carrying the
authority of the source. Identifiers, error messages and test names may state
the rule when it is part of the program's behaviour.

A comment earns its place only when the fact cannot live in any of those
places and the reader needs it beside the code:

- an external constraint of a library, platform, network or licence;
- the price of a deliberate compromise;
- a dead end that was tried and is recorded nowhere else;
- a contract at the boundary of a module.

Shortening a comment does not move the fact into its proper place. A short
comment is examined exactly like a long one. When a comment remains, keep it
brief and declare why this fact cannot be carried anywhere better.
