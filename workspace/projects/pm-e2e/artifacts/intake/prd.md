---
title: "EnvGuard — Encrypted .env File Sync CLI"
version: "0.1.0"
status: draft
author: PM Agent
project_id: pm-e2e
created: 2025-01-01
last_updated: 2025-01-01
---

# EnvGuard — Product Requirements Document

## 1. Overview

EnvGuard is a CLI tool that lets development teams securely share `.env` files through their existing Git repository. It encrypts environment files with a project-level passphrase before committing them, so secrets never appear in plaintext in version control. Team members use `push`, `pull`, and `diff` commands to synchronize environment variables across machines.

### 1.1 Problem Statement

Development teams routinely share `.env` files through insecure channels — Slack DMs, email, shared drives — because committing them to Git in plaintext is a security risk. This leads to:

- **Stale secrets:** Team members run different versions of environment variables.
- **Onboarding friction:** New developers must manually collect secrets from teammates.
- **No history:** When a secret changes, there's no record of what it was before.

### 1.2 Proposed Solution

A lightweight CLI that encrypts `.env` files and stores the ciphertext in the Git repo (e.g., `.env.development.enc`). The passphrase is shared out-of-band. The CLI provides `push` (encrypt + commit), `pull` (fetch + decrypt), and `diff` (compare local vs remote) commands.

### 1.3 Target Users

- Small-to-medium development teams (2–20 developers) using Git-based workflows.
- Developers who currently share `.env` files manually or via insecure channels.

---

## 2. Functional Requirements

### FR-1: Project Initialization (`envguard init`)

**Description:** Initialize EnvGuard in a project directory.

**Behavior:**
- Prompts the user for a passphrase (with confirmation).
- Creates `.envguard.yaml` in the project root with default configuration.
- Adds `.env*` patterns (excluding `*.enc`) to `.gitignore` if not already present.
- Default config includes the three standard environments: `development`, `staging`, `production`.

**Inputs:** Passphrase (interactive prompt, masked).

**Outputs:** `.envguard.yaml` config file created; `.gitignore` updated.

**Error cases:**
- `.envguard.yaml` already exists → exit with error: "Project already initialized. Use --force to re-initialize."
- No `.git` directory found → exit with error: "Not a Git repository."

---

### FR-2: Push Encrypted Env File (`envguard push <environment>`)

**Description:** Encrypt a local `.env.<environment>` file and save the ciphertext as `.env.<environment>.enc` in the repo.

**Behavior:**
- Reads `.env.<environment>` from the project root.
- Prompts for passphrase (or reads from `ENVGUARD_PASSPHRASE` env var).
- Encrypts the file contents using the passphrase.
- Writes `.env.<environment>.enc` to the project root.
- Prints confirmation: "Encrypted .env.<environment> → .env.<environment>.enc"

**Inputs:** Environment name (positional arg); passphrase (prompt or env var).

**Outputs:** `.env.<environment>.enc` file written to disk.

**Error cases:**
- `.env.<environment>` does not exist → exit with error: "File .env.<environment> not found."
- `.envguard.yaml` not found → exit with error: "Not an EnvGuard project. Run `envguard init` first."
- Invalid/empty passphrase → exit with error: "Passphrase cannot be empty."

---

### FR-3: Pull and Decrypt Env File (`envguard pull <environment>`)

**Description:** Decrypt `.env.<environment>.enc` to produce the plaintext `.env.<environment>` file.

**Behavior:**
- Reads `.env.<environment>.enc` from the project root.
- Prompts for passphrase (or reads from `ENVGUARD_PASSPHRASE` env var).
- Decrypts the file contents.
- If a local `.env.<environment>` already exists and differs from the decrypted content, display a warning: "Local .env.<environment> differs from remote. Overwriting with remote version."
- Writes decrypted content to `.env.<environment>`.
- Prints confirmation: "Decrypted .env.<environment>.enc → .env.<environment>"

**Inputs:** Environment name (positional arg); passphrase (prompt or env var).

**Outputs:** `.env.<environment>` file written to disk.

**Error cases:**
- `.env.<environment>.enc` does not exist → exit with error: "No encrypted file found for environment '<environment>'."
- Wrong passphrase → exit with error: "Decryption failed. Check your passphrase."
- `.envguard.yaml` not found → exit with error: "Not an EnvGuard project. Run `envguard init` first."

---

### FR-4: Diff Local vs Remote (`envguard diff <environment>`)

**Description:** Show differences between the local `.env.<environment>` and the decrypted contents of `.env.<environment>.enc`.

**Behavior:**
- Reads and decrypts `.env.<environment>.enc` (prompts for passphrase or reads env var).
- Reads local `.env.<environment>`.
- Computes a unified diff between the two.
- Prints the diff to stdout. If no differences, prints: "No differences found."
- Values are masked by default in diff output (shows keys only + `****` for values). Use `--show-values` flag to reveal actual values.

**Inputs:** Environment name (positional arg); passphrase (prompt or env var); optional `--show-values` flag.

**Outputs:** Diff printed to stdout.

**Error cases:**
- Either file missing → exit with error indicating which file is missing.
- Wrong passphrase → exit with error: "Decryption failed. Check your passphrase."

---

### FR-5: Configuration File (`.envguard.yaml`)

**Description:** Project-level configuration stored in `.envguard.yaml`.

**Schema:**
```yaml
version: 1
environments:
  - development
  - staging
  - production
```

**Behavior:**
- Created by `envguard init` with default values.
- Read by all commands to validate the environment argument.
- If a user passes an environment not listed in config → exit with error: "Unknown environment '<name>'. Available: development, staging, production."

---

### FR-6: Multiple Environment Support

**Description:** All commands accept an `<environment>` argument that maps to `.env.<environment>` / `.env.<environment>.enc` file pairs.

**Behavior:**
- Three default environments: `development`, `staging`, `production`.
- The environment list is defined in `.envguard.yaml` and can be edited manually.
- All commands (push, pull, diff) operate on a single environment at a time.

---

### FR-7: Passphrase Handling

**Description:** The passphrase can be provided interactively or via the `ENVGUARD_PASSPHRASE` environment variable.

**Behavior:**
- If `ENVGUARD_PASSPHRASE` env var is set, use it (enables CI/CD usage).
- Otherwise, prompt interactively with masked input.
- During `init`, prompt twice for confirmation.
- The passphrase is never written to disk or logged.

**Security constraint:** The passphrase is the single project-level secret. All team members use the same passphrase. It is shared out-of-band (not managed by EnvGuard).

---

### FR-8: Gitignore Management

**Description:** `envguard init` ensures plaintext `.env` files are gitignored.

**Behavior:**
- Adds the following patterns to `.gitignore` if not already present:
  ```
  .env
  .env.*
  !.env.*.enc
  ```
- Does NOT remove existing `.gitignore` entries.
- If `.gitignore` does not exist, creates it.

---

## 3. Non-Functional Requirements

### NFR-1: Encryption Standard

- Use AES-256-GCM (or equivalent authenticated encryption).
- Key derivation from passphrase via Argon2 or PBKDF2 with a random salt.
- Salt stored as a header in the `.enc` file.

### NFR-2: CLI Response Time

- All commands should complete in under 2 seconds for `.env` files up to 100KB.

### NFR-3: Cross-Platform Compatibility

- Must work on macOS, Linux, and Windows.
- No OS-specific dependencies beyond the language runtime.

### NFR-4: Zero External Services

- No cloud services, no accounts, no network calls. Everything is local + Git.

---

## 4. Out of Scope (v1)

- **Audit trail / change history** — not needed for v1.
- **Per-user encryption keys** — single project passphrase only.
- **Automatic Git commit/push** — `envguard push` writes the `.enc` file; the user runs `git add/commit/push` themselves.
- **Merge conflict resolution** — last-write-wins; no three-way merge.
- **GUI or TUI** — CLI only.
- **Secret rotation** — no automatic passphrase rotation.
- **Key management** — passphrase is shared out-of-band.

---

## 5. User Flows

### 5.1 First-Time Setup (Team Lead)

```
$ cd my-project
$ envguard init
Enter passphrase: ********
Confirm passphrase: ********
✓ Created .envguard.yaml
✓ Updated .gitignore
Share the passphrase with your team via a secure channel.

$ envguard push development
Enter passphrase: ********
✓ Encrypted .env.development → .env.development.enc

$ git add .envguard.yaml .env.development.enc .gitignore
$ git commit -m "Add encrypted env files"
$ git push
```

### 5.2 Joining Developer (New Team Member)

```
$ git clone <repo>
$ cd my-project
$ envguard pull development
Enter passphrase: ********
✓ Decrypted .env.development.enc → .env.development
```

### 5.3 Checking for Changes

```
$ git pull
$ envguard diff development
Enter passphrase: ********
--- local .env.development
+++ remote .env.development.enc (decrypted)
  DATABASE_URL=****
+ NEW_API_KEY=****
- OLD_SECRET=****
```

### 5.4 Updating Secrets

```
$ vim .env.development
$ envguard push development
Enter passphrase: ********
✓ Encrypted .env.development → .env.development.enc
$ git add .env.development.enc
$ git commit -m "Update development secrets"
$ git push
```

---

## 6. Assumptions

| # | Assumption | Status |
|---|-----------|--------|
| A1 | Single project-level passphrase, shared out-of-band | Confirmed |
| A2 | Last-write-wins conflict resolution with warning on pull | Confirmed |
| A3 | Diff compares local plaintext vs decrypted remote | Confirmed |
| A4 | No audit trail in v1 | Confirmed |

---

## 7. Open Questions

None — all questions resolved during intake.

---

## 8. Success Criteria

This project is successful when:

1. A developer can initialize EnvGuard, push an encrypted `.env` file, and another developer can pull and decrypt it using the shared passphrase.
2. The diff command accurately shows differences between local and remote environment files.
3. Plaintext secrets never appear in Git history.
4. All error cases produce clear, actionable error messages.
5. The tool works on macOS, Linux, and Windows without OS-specific dependencies.
