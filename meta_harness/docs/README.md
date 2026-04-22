# Meta Harness Documentation

This directory is the Meta Harness product documentation tree. Governance for
this directory — creation rules, provenance requirements, co-modification
rules, deprecation flow, and folder-growth approval — lives in
[`../AGENTS.md`](../AGENTS.md) under **Documentation Hierarchy**. Read that
section before creating or moving any document here.

## Layout

Subfolders are created only when concrete content exists. Empty scaffolds are
not permitted.

- `specs/` — implementation contracts derived from `AD.md` decisions.
- `archive/` — superseded source material kept for historical context only.

Reserved subfolders (created on first real need, not pre-scaffolded):

- `operations/` — operational runbooks (deploy, debug, eval execution).
- `integrations/` — third-party surface contracts (sandbox providers,
  LangSmith, Supabase, GitHub).
- `reference/` — standalone reference material (glossary, enum tables,
  shared diagrams).

New top-level subfolders under `docs/` require approval before creation, same
gate as renaming a module.

## Quick rules

1. Every doc under `docs/specs/` has a provenance header pointing to the AD
   section(s) it derives from, and is registered in `AD.md §9 Decision Index`
   under **Derived Specs**.
2. Decisions originate in `AD.md` and flow *into* specs. Specs never
   introduce new architectural decisions — if spec writing surfaces a
   decision, land the AD change first, then update the spec.
3. PRs modifying an AD section with a downstream spec update that spec in the
   same PR and bump `last_synced`.
4. Specs are deprecated, not deleted. Stub pointers to successors remain.

See [`../AGENTS.md`](../AGENTS.md) **Documentation Hierarchy** for the full
normative rules.
