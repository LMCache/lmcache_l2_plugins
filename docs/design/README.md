# LMCache L2 Plugins Design Docs

This directory holds design documents for plugin modules, following the
[LMCache convention](https://github.com/LMCache/LMCache/blob/dev/docs/design/README.md).

## Layout convention

**`docs/design/` mirrors the `lmcache_l2_plugins/` package tree.**

For source at `lmcache_l2_plugins/<path>/`, look for its design documents under
`docs/design/<path>/`.

| Source module | Design doc location |
| --- | --- |
| `lmcache_l2_plugins/autumn/` | `docs/design/autumn/` |
| `lmcache_l2_plugins/<name>/adapter.py` | `docs/design/<name>/` |

Not every module needs a design document. Create a directory when there is a
design to explain; a missing directory means no standalone design doc exists yet.

## Adding a design doc

- Place the document at the path matching the module it describes. A document
  spanning sibling modules belongs at their common parent.
- Use a descriptive topic name, such as `buffer-lifetime.md`.
- Explain the problem, constraints, chosen design, alternatives, and relevant
  failure or concurrency behavior. Separate proposed behavior from implemented
  behavior and state how the design can be validated.
- Use relative links between documents in this tree.
- Keep installation and operational instructions in the user-facing guides under
  `docs/source/` or in the plugin README; link to them rather than duplicating them.

## Shared infrastructure

- [Real-server L2 e2e](e2e.md): package reuse, call chain and backend boundaries.
