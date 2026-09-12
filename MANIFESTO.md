# Every comment is guilty until proven necessary

A comment creates a second source of truth. Code changes while the comment keeps asserting what used to be true, and readers trust the lie because it sits beside the code.

## Every comment has one of three outcomes

A comment is any text in comment syntax in a supported language. Documentation comments also count, including Python docstrings.

### Replace it

When the content is needed but can live in a form that expresses, enforces or preserves it, replace the comment. The replacements include, but are not limited to:

* replace explanations of code meaning with names, types and structure;
* replace explanations of complicated logic by splitting the code into small, named operations;
* replace statements of required behaviour with tests that enforce it;
* replace a comment used as the only record of a swallowed failure with a runtime log of the actual occurrence;
* move unfinished work to an issue;
* move product knowledge and working rules to project or team documentation;
* leave accounts of what the code used to do to Git history.

### Delete it

Delete a comment that adds no content the reader needs. This includes a comment that:

* paraphrases the code beneath it;
* describes an earlier implementation preserved in Git;
* holds old code in comment syntax;
* repeats the name of a function, type or parameter.

A comment with unique content the reader needs belongs under Replace it or Keep it, not here.

A documentation comment in a project that publishes no reference cannot qualify under Keep it. Replace or delete it according to its content.

### Keep it

A licence header, section marker, shebang or tool directive recognised by the scanner passes without a declaration.

So does a documentation comment, in a project that says where its reference is published:

```yaml
documentation: https://pkg.go.dev/example.com/thing
```

The exemption reaches only what the language's own generator publishes: a docstring of a public name, a Go doc comment on an exported declaration. A comment anywhere else is a comment. The address is not taken on trust either: the page is read, and it MUST name something the exempted comments document, so an address that leads nowhere or to someone else's page fails the run.

Every other comment MUST be declared in `.commentcensor.yaml` and MUST meet one of these exceptions:

* a constraint imposed by a named external system that code cannot express or verify;
* a deliberate compromise whose rejected alternative and accepted cost are named.

A declaration does not make a comment valid. It records the alternatives that were tried and what each of them could not express, enforce or preserve. A shorter comment is still a comment.
