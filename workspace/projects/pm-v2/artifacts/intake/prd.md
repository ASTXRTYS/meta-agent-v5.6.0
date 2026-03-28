---
artifact: prd
project_id: pm-v2
title: "Bookmark Manager CLI — Product Requirements Document"
version: "1.0.0"
status: draft
stage: intake
authors:
  - orchestrator
lineage: []
---

# Bookmark Manager CLI — PRD

## Product Summary

A command-line bookmark manager for individual developers who want to save, tag, search, and export their personal bookmarks. Built in Python (3.10+) using only the standard library — `argparse` for CLI, `sqlite3` for storage. Zero external dependencies.

## Goals

1. Let users add bookmarks with a URL, title, and comma-separated tags.
2. Let users search bookmarks by tag name or title substring.
3. Let users list all bookmarks.
4. Let users delete bookmarks.
5. Let users export all bookmarks to a self-contained HTML page.
6. Persist all data in a local SQLite database file.

## Non-Goals

- **No edit/update command** — out of scope for v1.
- **No import** — no ingestion from browser bookmark files or other formats.
- **No auto-fetch** — the tool does not fetch page titles or metadata from URLs.
- **No GUI or TUI** — strictly a CLI tool.
- **No external dependencies** — no pip-installable packages.
- **No multi-user support** — single-user, single-database.

## Constraints

| Constraint | Detail |
|---|---|
| Python version | 3.10+ |
| CLI framework | `argparse` (stdlib) |
| Database | `sqlite3` (stdlib) |
| External deps | None — stdlib only |
| Platform | Any OS with Python 3.10+ |

## Target User

An individual developer managing personal bookmarks from the terminal. Comfortable with CLI tools. Wants something lightweight that just works, with no setup beyond having Python installed.

## Core User Workflows

### Workflow 1: Add a Bookmark
```
$ bookmarks add --url https://example.com --title "Example Site" --tags python,tutorial
Bookmark added: "Example Site"
```

### Workflow 2: Search Bookmarks
```
$ bookmarks search --tag python
[1] Example Site — https://example.com [python, tutorial]

$ bookmarks search --title "example"
[1] Example Site — https://example.com [python, tutorial]
```

### Workflow 3: List All Bookmarks
```
$ bookmarks list
[1] Example Site — https://example.com [python, tutorial]
[2] Another Page — https://another.com [reference]
```

### Workflow 4: Delete a Bookmark
```
$ bookmarks delete --id 1
Deleted bookmark: "Example Site"
```

### Workflow 5: Export to HTML
```
$ bookmarks export --output bookmarks.html
Exported 2 bookmarks to bookmarks.html
```

## Functional Requirements

### FR-1: Add Bookmark
- Command: `add --url <url> --title <title> --tags <comma-separated>`
- `--url` is required. `--title` is required. `--tags` is optional (defaults to no tags).
- URL must have a UNIQUE constraint. Adding a duplicate URL prints an error and exits with a non-zero code.
- Tags are stored as comma-separated strings, split on commas, stripped of whitespace, and stored individually associated with the bookmark.
- On success, prints a confirmation message and exits with code 0.

### FR-2: Search Bookmarks
- Command: `search --tag <tag>` or `search --title <query>`
- At least one of `--tag` or `--title` must be provided. Both can be provided (AND logic: results must match both).
- `--title` search is case-insensitive substring match.
- `--tag` search matches the exact tag name (case-insensitive).
- Results are printed one per line with ID, title, URL, and tags.
- If no results found, prints "No bookmarks found." and exits with code 0.

### FR-3: List All Bookmarks
- Command: `list`
- Prints all bookmarks, one per line, with ID, title, URL, and tags.
- If database is empty, prints "No bookmarks." and exits with code 0.

### FR-4: Delete Bookmark
- Command: `delete --id <id>`
- Deletes the bookmark with the given ID.
- If the ID does not exist, prints an error and exits with a non-zero code.
- On success, prints a confirmation message and exits with code 0.

### FR-5: Export to HTML
- Command: `export --output <filepath>`
- Generates a self-contained HTML file with all bookmarks.
- HTML structure: valid HTML5 document with a `<title>`, an `<h1>` heading, and an unordered list (`<ul>`) where each `<li>` contains an `<a>` link with the bookmark title as link text and tags displayed alongside.
- If no bookmarks exist, the HTML file is still generated with an empty list or a "No bookmarks" message.
- On success, prints a confirmation with the count and filepath, exits with code 0.

### FR-6: Database Initialization
- On first run of any command, the SQLite database is created automatically if it does not exist.
- The database file defaults to `~/.bookmarks.db` (or a configurable path via `--db` global flag).
- Schema is created automatically (bookmarks table, tags table or column).

### FR-7: Error Handling
- Invalid commands print usage help and exit with code 2.
- Missing required arguments print a clear error and exit with non-zero code.
- Database errors (e.g., corruption) print a user-friendly message, not a raw traceback.

## Acceptance Criteria

| ID | Criterion |
|---|---|
| AC-1 | `add` creates a bookmark retrievable by `list` |
| AC-2 | `add` with a duplicate URL fails with non-zero exit code |
| AC-3 | `search --tag` returns only bookmarks with that tag |
| AC-4 | `search --title` returns bookmarks whose title contains the query (case-insensitive) |
| AC-5 | `list` returns all bookmarks with correct ID, title, URL, tags |
| AC-6 | `delete --id` removes the bookmark; subsequent `list` does not show it |
| AC-7 | `delete --id` with nonexistent ID fails with non-zero exit code |
| AC-8 | `export` produces valid HTML5 containing all bookmark URLs as `<a>` links |
| AC-9 | Database is auto-created on first command |
| AC-10 | All commands exit 0 on success, non-zero on error |
| AC-11 | No external dependencies — only stdlib imports |

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Schema migration needed later | Medium | Medium | Keep schema simple; document it for future migration scripts |
| Large bookmark counts slow `list`/`export` | Low | Low | SQLite handles thousands easily; pagination is a v2 concern |
| HTML export doesn't match user expectations | Medium | Low | Keep format simple and well-specified; user can customize later |

## Unresolved Questions

1. **Database path default**: Is `~/.bookmarks.db` acceptable, or would the user prefer `~/.local/share/bookmarks/bookmarks.db` (XDG-compliant)?
2. **Tag deletion**: When a bookmark is deleted, its tags are removed. But should there be a separate `tags` command to list all known tags? (Deferred to v2.)
