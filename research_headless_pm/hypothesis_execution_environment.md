# Hypothesis: Project Execution Environment As The Agent's Computer

| Field | Value |
|---|---|
| Status | Proposed for team review |
| Date | 2026-04-20 |
| Scope | Meta Harness sandbox, VM/devbox, local-first execution, repository contribution, PR publishing |
| Related AD Sections | `meta_harness/AD.md` constraints, Q8 sandbox topology, mounted graph execution, web app sandbox browsing |
| Primary Runtime Assumption | Deep Agents backends expose filesystem/shell capabilities; LangGraph threads/runs provide durable execution identity |

## 1. Answer

Meta Harness must standardize an **Execution Environment** abstraction. This is the concrete "computer" a coding/evaluation agent uses to clone repositories, install dependencies, run commands, modify files, commit, push, and open pull requests.

The important distinction:

- A **project memory/artifact filesystem** is where Deep Agents store one project's plans, artifacts, summaries, eval outputs, and handoff packages. This must remain project-scoped.
- **Global memory** is limited to durable cross-project knowledge such as procedural lessons, reusable skills, org-level preferences, and a minimal project registry/index. It should not contain raw project artifacts.
- An **execution environment** is a shell-capable workspace. It has an operating system boundary, a working directory, git, package managers, network policy, resource limits, and credentials mediated by the harness.

For autonomous coding work, the agent does need its own computer. A plain virtual file system is not enough. It cannot responsibly contribute to a client repository unless it can operate in a real execution environment where it can clone the repo, run the project, test changes, and publish a PR.

## 2. Is A Sandbox Different From A VM / Daytona-Style Computer?

The words are currently overloaded. The clean model is layered:

| Layer | Meaning | Examples |
|---|---|---|
| Deep Agents backend | Interface the agent uses for files and, when available, shell execution | `FilesystemBackend`, `StoreBackend`, sandbox backend |
| Execution environment | The actual computer where commands run | LangSmith sandbox, Daytona sandbox/devbox, Runloop devbox, Modal sandbox, local machine |
| Sandbox policy | Security boundary and lifecycle rules around that computer | isolated VM/microVM/container, provider limits, auth proxy, cleanup policy |
| Repository workspace | The cloned git checkout inside the execution environment | `/workspace/<repo>` |

So: **a sandbox is not fundamentally opposed to "giving the agent its own computer."** For Meta Harness, a sandbox should mean "a provider-backed computer behind the Deep Agents backend interface." Daytona is one possible provider for that computer. LangSmith, Runloop, and Modal are other possible providers.

What is different is **local-first mode**. A local shell backend gives the agent the user's computer. That can be useful for trusted solo/local development, but it is not the same security posture as a provider sandbox. Local mode must be opt-in and guarded; managed sandbox mode should be the default for headless, client, and multi-tenant work.

## 3. Standardized Execution Modes

Meta Harness should support three execution modes behind one contract. The distinction is not the vendor name; it is who owns and operates the environment boundary.

| Mode | Purpose | Default posture |
|---|---|---|
| `managed_sandbox` | Meta Harness provisions and manages the remote sandbox/devbox lifecycle for the user or org. The underlying provider could be LangSmith, Daytona, Runloop, Modal, or another configured default. | Default for production, headless/autonomous work, web app, client repos, and any untrusted code |
| `external_devbox` | The customer or enterprise brings the devbox/sandbox provider, image, network policy, secrets policy, and lifecycle constraints. Meta Harness connects to it through the same backend contract. | Same security intent as `managed_sandbox`, but provider and governance are owned by the customer/org |
| `local_workspace` | The agent operates on the user's local machine, usually from the TUI/CLI. This can mean local disk only or local shell execution, depending on configuration. | Explicit opt-in; shell access requires HITL/allow-list because commands run with the user's host permissions |

`local_workspace` is the mode where a regular individual using the TUI decides not to use a remote sandbox and instead allows Meta Harness to operate on a configured local root directory. If shell is enabled, the agent is using the user's computer. This is useful for trusted solo development, but it is not an isolation boundary.

All modes must present the same product-level capabilities:

- clone or create a repository,
- create/select a branch,
- run implementation and verification commands,
- stage and commit changes,
- push a branch,
- open or update a draft PR,
- expose files/diffs/logs to the UI/TUI,
- persist enough environment identity for follow-up runs.

## 4. Recommended Scoping: Project-Scoped Execution Environment

Open SWE uses one persistent sandbox per LangGraph thread. Meta Harness should map that pattern onto the canonical project execution thread:

```txt
project_thread_id -> execution_environment_id -> provider sandbox/devbox/local root
```

This matters because Meta Harness has multiple role agents. The Developer, Evaluator, and Harness Engineer may all need to inspect or run against the same candidate repository state. They should not each clone unrelated copies unless the harness intentionally creates evaluation snapshots.

Recommended v1 rule:

- `pm_session` threads do not get an execution environment by default.
- `project` threads get one execution environment when the project requires code execution.
- PM, Researcher, Architect, and Planner usually operate on memory/artifacts, not shell access.
- Developer is the primary writer to the repository workspace.
- Evaluator and Harness Engineer can read and execute checks/evals against the candidate workspace during blocked review phases.
- Handoff gates serialize write/evaluation moments so roles do not concurrently mutate the same repo.

If later we need stronger isolation between Developer and Evaluator/HE, the provider can create copy-on-write snapshots per phase. That is a refinement of the execution environment lifecycle, not a change to the agent topology.

### 4.1 PM Session Access To Project Threads And Sandboxes

A LangGraph thread does **not** live inside the sandbox. The thread is checkpointed state in the LangGraph runtime:

| Deployment mode | Where thread/checkpoint state lives |
|---|---|
| Local dev / local TUI | Local checkpointer such as SQLite on the user's machine |
| LangGraph Platform cloud | LangGraph/LangSmith managed infrastructure |
| Hybrid or self-hosted LangGraph Platform | The customer's configured infrastructure |

The sandbox/devbox is separate runtime infrastructure. The project thread stores metadata such as `execution_environment_id` or `sandbox_id`; that ID lets the harness reconnect to the VM/devbox when a project run needs shell or filesystem access.

Therefore a PM session can access project information, but not by freely reading another thread's VM. The intended path is explicit and permissioned:

1. Resolve the project through the project registry/global index.
2. Read project-scoped memory: summary, current status, artifact index, handoff packages, eval status, and PR/repo bindings.
3. If live files are needed, call a harness tool/API that is authorized to read selected project artifacts or sandbox paths for that project.
4. If the project graph needs to do work, schedule or resume a run on the project thread instead of mutating the PM session into that project.

This preserves the boundary: PM sessions can answer cross-project questions and pull appropriate project context, while raw project artifacts remain in project-scoped storage and raw sandbox access remains gated by auth, project membership, and tool policy.

## 5. Core Data Contracts

### `ExecutionEnvironmentBinding`

The harness should persist one binding per project execution thread:

```json
{
  "project_id": "support_qa_agent",
  "project_thread_id": "project_support_qa_agent",
  "environment_id": "sandbox_abc123",
  "mode": "managed_sandbox | local_workspace | external_devbox",
  "provider": "langsmith | daytona | runloop | modal | local | internal",
  "status": "creating | ready | unavailable | archived",
  "work_dir": "/workspace",
  "credential_mode": "auth_proxy | github_app_token | user_oauth | local_git",
  "created_at": "2026-04-20T00:00:00Z",
  "updated_at": "2026-04-20T00:00:00Z"
}
```

Store this in LangGraph thread metadata and/or the project's Store namespace. Thread metadata is the runtime lookup path; project Store memory is the durable project/audit path. Do not store project artifacts in global memory. Global memory may store only registry entries, aliases, summaries, and locators needed to find the right project.

### `RepositoryBinding`

Each project can have zero, one, or many repositories:

```json
{
  "project_id": "support_qa_agent",
  "repo_owner": "acme",
  "repo_name": "support-qa-agent",
  "repo_url": "https://github.com/acme/support-qa-agent",
  "workspace_path": "/workspace/support-qa-agent",
  "base_branch": "main",
  "working_branch": "meta-harness/support-qa-agent",
  "pr_url": null,
  "repo_kind": "existing_client_repo | greenfield_repo",
  "persistence_mode": "vm_only | meta_harness_staging_repo | client_repo | archive_artifact",
  "write_policy": "none | draft_pr_only | direct_push_allowed"
}
```

### `ContributionPolicy`

The policy should be explicit because client repo safety is a product boundary:

```json
{
  "allowed_orgs": ["acme"],
  "allowed_repos": ["acme/support-qa-agent"],
  "branch_prefix": "meta-harness/",
  "default_pr_state": "draft",
  "require_user_approval_before_repo_create": true,
  "require_user_approval_before_first_push": false,
  "require_checks_before_pr": true,
  "commit_identity": "meta-harness[bot]"
}
```

## 6. Existing Client Repository Flow

```txt
1. Resolve target repo from project context, explicit user input, GitHub App installation, or PM confirmation.
2. Resolve or create the project execution environment.
3. Configure credentials through an auth proxy or short-lived token broker. Do not write long-lived secrets into the sandbox.
4. Clone the repository into /workspace/<repo>.
5. Read the target repo's AGENTS.md before implementation.
6. Create or checkout the project working branch.
7. Developer implements the phase, runs checks, and records evidence.
8. Evaluator and/or HE review against the same workspace or a phase snapshot.
9. On acceptance, stage, commit, push, and open or update a draft PR.
10. Attach the PR URL, commit SHA, checks, and summary to project memory and the PM handoff.
11. Notify the originating channel: web, TUI, Slack, email, GitHub, or Linear.
```

The contribution path is independent of headless mode. Headless only changes where the user messages came from and where status is posted.

## 7. Greenfield Project Flow

Greenfield projects still need a computer, but they do not always need an immediate remote GitHub repo. Flexibility is the right default. The project can live in the execution environment first, then be promoted to a remote repo only when the user, PM, or delivery policy decides that is useful.

Recommended greenfield persistence modes:

| Mode | Meaning | When to use |
|---|---|---|
| `vm_only` | Keep the working project inside the provisioned execution environment and expose it through artifacts, previews, screenshots, and exports. | Early prototypes, experiments, disposable demos |
| `meta_harness_staging_repo` | Push to a Meta Harness-owned GitHub org/repo for storage, review, or handoff. | Internal staging, client previews before client repo access exists |
| `client_repo` | Create or push to the client's GitHub org/repo. | Client is ready to own the codebase or review a PR |
| `archive_artifact` | Export a zip/tarball or generated bundle without remote git publication. | Deliverables that do not need GitHub yet |

Flow:

```txt
1. PM scopes the project and captures whether the deliverable needs a remote repo now, later, or not at all.
2. Architect/Planner decide repository shape and initial package/runtime choices.
3. Developer creates the project in the execution environment under /workspace/<project>.
4. Developer runs local checks in the execution environment.
5. If `vm_only`, keep the project in the VM/devbox and surface previews, diffs, logs, and exported artifacts.
6. If `meta_harness_staging_repo`, push to our configured org/repo for storage or review.
7. If `client_repo`, ask for approval before creating or pushing to the client's GitHub repo unless project policy already grants that permission.
8. If `archive_artifact`, export the bundle and record it in project artifacts.
9. PM returns the appropriate output: environment preview, artifact bundle, staging repo link, client repo link, or PR link.
```

Do not treat "greenfield" as "must create a GitHub repo immediately." It is a code lifecycle. The remote repo is one possible persistence/publishing target, not the only one.

## 8. Interactive Use Outside Headless Mode

The execution environment must be available from all user surfaces, not only headless triggers.

| Surface | How it uses the same execution environment |
|---|---|
| Web app | Connects to the project thread; file browser/diff/log endpoints resolve the same `execution_environment_id` |
| TUI | Shows active environment, repo binding, branch, changed files, check status, and PR URL |
| Local CLI/TUI | Can use `local_workspace` or a remote sandbox provider |
| Slack/email/Discord | Thin adapters create/select threads and post status/PR links; no special execution model |
| API | Creates runs against the same project thread and environment binding |

The UI should not fake artifact visibility from agent messages. It should read files/diffs/logs from the execution environment or project artifact store through authenticated routes.

## 9. Required Tools / Middleware

v1 should not rely on model steering alone for repo publication. Some steps need deterministic tools or middleware:

| Component | Responsibility |
|---|---|
| `resolve_execution_environment` | Resolve/create/reconnect the project environment and return work dir/provider status |
| `resolve_repository` | Map project context to repo owner/name/base branch and validate allowed org/repo when a remote repo is selected |
| `clone_or_refresh_repository` | Clone repo if missing; fetch and checkout branch if an existing repo is selected |
| `create_or_checkout_work_branch` | Ensure branch naming and branch provenance are consistent |
| `publish_artifact_or_pull_request` | Publish according to `persistence_mode`: VM artifact/export, Meta Harness staging repo, client repo branch, or draft PR |
| `open_pr_if_needed` middleware | Safety net only when the project policy says a PR is required |
| `sandbox_health_check` middleware | Reconnect/recreate unavailable environments before tool execution |
| `execution_policy` middleware | Enforce local/sandbox shell permissions, repo allowlist, and approval policy |

Tool naming can change during implementation, but the capabilities should not disappear.

## 10. Open SWE Pattern To Adopt And Where To Diverge

Open SWE gives us a strong implementation pattern, but it is narrower than Meta Harness:

| Open SWE behavior | Adopt for Meta Harness? | Notes |
|---|---|---|
| Per-thread persistent sandbox, reused across follow-up messages | Yes | Map to project execution threads, not PM session threads |
| Pluggable sandbox providers selected by configuration | Yes | Keep provider boundary, but distinguish Meta-managed vs customer-managed/BYO |
| Repo selection from explicit syntax, channel/team mapping, thread metadata, or default repo | Yes | Useful for existing client repos and headless channel adapters |
| Repo is cloned into the sandbox before work starts | Yes, for existing repo work | Not required for greenfield `vm_only` or archive-only work |
| `commit_and_open_pr` tool and `open_pr_if_needed` middleware | Partially | Use the deterministic PR safety net only when policy requires GitHub publication |
| Automatic PR creation as final step | No, not universally | Meta Harness needs greenfield flexibility: VM-only, staging repo, client repo, archive, or PR |
| Existing-repo orientation | No, not universally | Meta Harness also builds net-new apps/harnesses where no remote repo exists yet |

## 11. Relationship To Existing AD Decisions

This hypothesis does not reopen the selected topology:

- Core roles remain peer stateful Deep Agents under the Project Coordination Graph.
- Sandbox support remains backend/runtime configuration, not a reason to split roles into separate top-level assistants.
- Headless channel adapters remain thin and route to LangGraph threads/runs.

It does refine the sandbox language:

```txt
Sandbox support means a project-scoped execution environment with filesystem,
shell, git, network policy, credentials, lifecycle, and UI/TUI inspection.
It is more than memory storage.
```

## 12. Team Review Questions

The solution is solid enough to review. The team should explicitly decide:

1. Default provider for managed sandbox in v1: LangSmith, Daytona, or provider-neutral with one configured default.
2. Whether project-scoped shared environment is acceptable for Developer/Evaluator/HE in v1, with serialized handoff gates preventing concurrent mutation.
3. Whether first push/PR should be autonomous after the user grants repo access, or require an approval gate per client/project.
4. Which greenfield persistence modes are v1: `vm_only`, `meta_harness_staging_repo`, `client_repo`, `archive_artifact`.
5. The exact local-first safety posture: local filesystem only, local shell with approval, or local shell unrestricted for trusted solo use.
6. Whether PR publication should be a Developer tool only, middleware safety net only, or both.
7. Which PM-session tools are allowed to read live project sandbox files versus only project memory/artifact indexes.

## 13. Source Support

- Deep Agents docs define sandbox backends as the shell-capable environment layer that provides filesystem tools plus `execute`: https://docs.langchain.com/oss/python/deepagents/sandboxes
- Deep Agents backend docs distinguish local filesystem, local shell, Store, Composite, and sandbox backends: https://docs.langchain.com/oss/python/deepagents/backends
- Deep Agents frontend sandbox docs recommend thread-scoped sandbox resolution and exposing authenticated file browsing routes through `langgraph.json` `http.app`: https://docs.langchain.com/oss/python/deepagents/frontend/sandbox
- LangChain's Open SWE README describes task-scoped isolated cloud sandboxes, provider pluggability, repository cloning, full permissions inside the boundary, and automatic PR creation: https://github.com/langchain-ai/open-swe
- Open SWE local source confirms the implementation pattern: thread metadata stores `sandbox_id`, thread metadata stores repo config, the agent is created with `backend=sandbox_backend`, tools include `list_repos`, `get_branch_name`, and `commit_and_open_pr`, and middleware includes `open_pr_if_needed` (`.reference/open-swe/agent/server.py`, `.reference/open-swe/agent/webapp.py`, `.reference/open-swe/agent/prompt.py`, `.reference/open-swe/agent/middleware/open_pr.py`).
- Open SWE local source also confirms local mode is not isolated: its `local` provider wraps `LocalShellBackend` and warns that commands run directly on the host machine (`.reference/open-swe/agent/integrations/local.py`).
- LangSmith Sandboxes are positioned as isolated execution environments for agents that need to clone repos, run tests, and open PRs: https://www.langchain.com/blog/introducing-langsmith-sandboxes-secure-code-execution-for-agents

## 14. Current Recommendation

Adopt **project-scoped execution environments** as the Meta Harness answer to "the agent needs its own computer."

Use a managed sandbox/devbox provider by default for headless, web, client, and multi-tenant work. Keep local-first execution as a first-class mode, but make local shell access explicit and guarded.

Expose the same repo contribution workflow across all surfaces. Headless mode should not own special powers that the web app, TUI, or local builder mode cannot use.

Promote this into the AD after team review resolves the six questions above.
