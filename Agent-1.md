## Code Review Summary

### Commits Reviewed

- **f1966d8**: fix(subagents): apply CompositeBackend + explicit SkillsMiddleware to all 3 runtime agents
- **484af50**: fix(graph): replace skills= param with explicit SkillsMiddleware, fix summarization backend
- **0e3be73**: refactor(backend): replace custom dead-code backends with SDK-native CompositeBackend

## Findings

### 1. **Bug: Missing _resolve_skills_dirs Helper** (f1966d8) — **HIGH**

**Location**: meta_agent/subagents/research_[agent.py](http://agent.py), `spec_writer_agent.py`, `verification_agent_runtime.py`

All three subagent files call _resolve_skills_dirs(skills_dirs) but this helper function is **never defined** in any of them. The function exists in [graph.py](http://graph.py) but is not imported or defined in the subagent modules.

**Impact**: Runtime `NameError` when creating any subagent graph.

```python

# Lines 569-570 in research_[agent.py](http://agent.py) (post-commit)

resolved_skills = *resolve*skills_dirs(skills_dirs)  # NameError!

skills_mw = SkillsMiddleware(backend=bare_fs, sources=resolved_skills)

```

**Fix**: Either add the helper to each file or import from [graph.py](http://graph.py):

```python

def *resolve*skills_dirs(skills_dirs: list[str] | None) -> list[str]:

    """Resolve skill directory paths, filtering to existing directories only."""

    if not skills_dirs:

        return []

    return [d for d in skills_dirs if os.path.isdir(d)]

```

### 2. **Bug: Incorrect Import in research_**[**agent.py**](http://agent.py) (f1966d8) — **HIGH**

**Location**: `meta_agent/subagents/research_agent.py:23`

The import was changed to:

```python

from meta_agent.backend import (

    create_bare_filesystem_backend,

    create_checkpointer,

    create_composite_backend,

    create_store,

)

```

But create_composite_backend and create_bare_filesystem_backend are **not used** in the final code — the file still uses `SdkFilesystemBackend` directly. This creates a dead import warning and indicates the refactoring was incomplete.

**Fix**: Either use the imported functions or remove them from the import.

### 3. **Bug: SummarizationMiddleware Backend Inconsistency** (f1966d8) — **MEDIUM**

**Location**: `meta_agent/subagents/research_agent.py:549`

```python

summarization_mw = SummarizationMiddleware(model=cfg["model_string"], backend=backend)

```

The `backend` here is still the old `SdkFilesystemBackend`, not `bare_fs`. Per the deep-agents-memory skill, SummarizationMiddleware should use the same bare filesystem backend as MemoryMiddleware for consistency.

**Fix**: Change to `backend=bare_fs` for consistency with other middleware.

### 4. **Pattern Violation: Backend Factory Lambda Not Called** (0e3be73, 484af50) — **MEDIUM**

**Location**: `meta_agent/graph.py:97`, `meta_agent/subagents/*.py`

The create_composite_backend() returns a **factory lambda** that expects a runtime parameter:

```python

def create_composite_backend(repo_root) -> Callable[..., SdkCompositeBackend]:

    def _factory(rt: Any) -> SdkCompositeBackend:

        ...

    return _factory

```

But it's passed directly to `create_deep_agent(backend=composite_backend)` without being called. The SDK expects either a backend instance or a callable that produces one. Looking at [backend.py](http://backend.py), the factory needs a runtime context that `create_deep_agent()` provides internally.

**Verification**: The deep-agents-core skill shows `backend` can be a callable, but this pattern needs confirmation against actual SDK behavior.

### 5. **Architecture Issue: Comment Drift** (484af50) — **LOW**

**Location**: `meta_agent/graph.py:141-147`

The middleware order comments are now inconsistent:

```python

explicit_middleware = [

    dynamic_prompt_mw,     # 0. Dynamic system prompt (MUST be first)

    meta_state_mw,         # 1. Extends state schema

    memory_mw,             # 3. Per-agent [AGENTS.md](http://AGENTS.md) loading    <- Was 9

    skills_mw,             # 4. Skills loading                 <- NEW

    summarization_tool_mw, # 5. Agent-controlled...            <- Was 8

    tool_error_mw,         # 6. ToolError...                   <- Was 10

]

```

The header docstring at line 8-21 still lists positions up to 12 but the actual indices are now wrong.

**Fix**: Update header comment to reflect actual middleware order.

### 6. **Missing Test Coverage for New Backend Functions** (0e3be73) — **MEDIUM**

**Location**: `tests/unit/test_backend.py`

The new create_composite_backend and create_bare_filesystem_backend functions have minimal tests:

- Only 2 test cases for create_composite_backend
- Only 1 test case for create_bare_filesystem_backend
- **No integration test** verifying the CompositeBackend routes actually work
- **No test** for the route behaviors `/memories/`, `/large_tool_results/`)

### 7. **Pre-existing Issue: Unused Import** (research_[agent.py](http://agent.py)) — **LOW**

**Location**: `meta_agent/subagents/research_agent.py:16`

```python

from deepagents.backends import FilesystemBackend as SdkFilesystemBackend

```

This is imported but should be removed since we're now using the backend from `meta_agent.backend` imports (though as noted in #2, those aren't being used either).

## Positive Changes

1. **Correct Pattern**: Using `SkillsMiddleware` explicitly instead of `skills=` parameter aligns with deep-agents-core skill guidance that middleware provides better control.
2. **Proper Backend Separation**: Using `bare_fs` for middleware that needs unrestricted file access (MemoryMiddleware, SkillsMiddleware) while using `composite_backend` for the main filesystem operations is correct per the skills.
3. **Clean Removal**: The old custom backend classes were properly removed in favor of SDK-native backends.

## Recommendations

| Priority | Action |

|----------|--------|

| **P0** | Add _resolve_skills_dirs helper to all 3 subagent files |

| **P0** | Fix imports in research_[agent.py](http://agent.py) (remove dead imports or use them) |

| **P1** | Fix summarization backend consistency |

| **P1** | Add integration tests for CompositeBackend routing |

| **P2** | Update middleware order comments |

| **P2** | Remove unused imports |

**Overall Assessment**: The architectural direction is correct (explicit middleware over parameter-based skills, SDK-native backends), but commit **f1966d8 has runtime-breaking bugs** that need immediate fixes before the code can execute.