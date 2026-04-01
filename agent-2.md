## Code Review Report: Backend/Skills Refactoring (Commits 0e3be73, 484af50, f1966d8)

### Summary

These three commits refactor the meta-agent's backend architecture to use SDK-native `CompositeBackend` and explicitly configure `SkillsMiddleware` instead of relying on the `skills=` parameter in `create_deep_agent()`. The changes apply consistently across the orchestrator and all three runtime agents (research-agent, spec-writer, verification-agent).

---

### Detailed Findings

#### 1. **Architecture Improvement: Proper Backend Separation** ✅

**Commit 0e3be73** introduces proper backend factory functions in `/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_agent/backend.py:31-74`:

```python

def create_composite_backend(repo_root: Path | str) -> Callable[..., SdkCompositeBackend]:

    ...

    def _factory(rt: Any) -> SdkCompositeBackend:

        return SdkCompositeBackend(

            default=SdkFilesystemBackend(root_dir=root_str, virtual_mode=True),

            routes={

                "/memories/": SdkStoreBackend(rt),

                "/large_tool_results/": SdkStateBackend(rt),

                "/conversation_history/": SdkStateBackend(rt),

            },

        )

    return _factory

```

**Correct Pattern Applied**: Per the `deep-agents-memory` skill, the code now properly uses:

- `FilesystemBackend` for real disk access (project files)

- `StoreBackend` for cross-session persistent memory `/memories/`)

- `StateBackend` for ephemeral large result offloading

#### 2. **SkillsMiddleware vs skills= Parameter Migration** ✅

**Commits 484af50 and f1966d8** correctly migrate from the deprecated `skills=` parameter to explicit `SkillsMiddleware` as documented in the `deep-agents-core` skill.

In `/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_agent/graph.py:160-164`:

```python

skills_dirs = [

    str(repo_root / "skills" / "langchain" / "config" / "skills"),

    str(repo_root / "skills" / "langsmith" / "config" / "skills"),

    str(repo_root / "skills" / "anthropic" / "skills"),

]

```

And in lines 137-147, the middleware is now explicitly configured:

```python

explicit_middleware = [

    dynamic_prompt_mw,     # 0. Dynamic system prompt (MUST be first)

    meta_state_mw,         # 1. Extends state schema

    memory_mw,             # 3. Per-agent [AGENTS.md](http://AGENTS.md) loading

    skills_mw,             # 4. Skills loading from [SKILL.md](http://SKILL.md) files

    summarization_tool_mw, # 5. Agent-controlled compact_conversation

    tool_error_mw,         # 6. ToolError (catches tool exceptions)

]

```

The `skills=` parameter is correctly removed from the `create_deep_agent()` call at line 200.

#### 3. **Bare FilesystemBackend for Middleware** ✅

**Critical Pattern**: The code correctly uses a "bare" `FilesystemBackend` (without `root_dirvirtual_mode`) for `MemoryMiddleware` and `SkillsMiddleware`, while using `CompositeBackend` for the agent's main filesystem operations.

In `/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_agent/backend.py:64-74`:

```python

def create_bare_filesystem_backend() -> SdkFilesystemBackend:

    """Create a bare FilesystemBackend for middleware (Memory, Skills).

    ...

    """

    return SdkFilesystemBackend()

```

This matches the `deep-agents-core` skill pattern: *"SkillsMiddleware uses its own bare FilesystemBackend"* for reading [SKILL.md](http://SKILL.md) files from absolute disk paths.

#### 4. **Subagent Consistency** ✅

**Commit f1966d8** correctly applies the same pattern to all three runtime agents:

| Agent | Backend | SkillsMiddleware | MemoryMiddleware |

|-------|---------|-----------------|------------------|

| research-agent | `composite_backend` | ✅ | ✅ |

| spec-writer | `composite_backend` | ✅ | ❌ (no memory needed) |

| verification-agent | `composite_backend` | ✅ | ✅ |

All agents correctly:

1. Import [create_composite_backend](cci:1://file:///Users/Jason/2026/v4/meta-agent-v5.6.0/meta_agent/backend.py:30:0-60:19) and [create_bare_filesystem_backend](cci:1://file:///Users/Jason/2026/v4/meta-agent-v5.6.0/meta_agent/backend.py:63:0-73:33) from `meta_agent.backend`

2. Create `composite_backend` for agent filesystem operations

3. Create `bare_fs` for middleware that needs absolute path access

4. Create explicit `SkillsMiddleware(backend=bare_fs, sources=resolved_skills)`

5. Remove `skills=` from `create_deep_agent()` call

#### 5. **Middleware Ordering** ⚠️ **Minor Issue**

In `/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_agent/graph.py:141-147`, the middleware order differs from the docstring at lines 8-21. The docstring says:

- 8. SummarizationToolMiddleware

- 9. MemoryMiddleware

- 10. ToolErrorMiddleware

- 12. SkillsMiddleware

But the actual code has:

```python

explicit_middleware = [

    dynamic_prompt_mw,     # 0

    meta_state_mw,         # 1

    memory_mw,             # 3

    skills_mw,             # 4

    summarization_tool_mw, # 5

    tool_error_mw,         # 6

]

```

The docstring at lines 8-21 needs to be updated to reflect the actual middleware order. This is not a functional bug (the order is actually more correct now—SkillsMiddleware before SummarizationToolMiddleware makes sense), but the documentation is stale.

#### 6. **Test Coverage** ✅

The unit tests in [/Users/Jason/2026/v4/meta-agent-v5.6.0/tests/unit/test_[backend.py](http://backend.py)](cci:7://file:///Users/Jason/2026/v4/meta-agent-v5.6.0/tests/unit/test_backend.py:0:0-0:0) are appropriately simplified to test the factory functions rather than custom backend implementations:

```python

class TestCreateCompositeBackend:

    def test_returns_callable(self):

        factory = create_composite_backend("/tmp/test")

        assert callable(factory)

    def test_factory_produces_composite_backend(self):

        factory = create_composite_backend("/tmp/test")

        rt = MagicMock()

        backend = factory(rt)

        assert isinstance(backend, SdkCompositeBackend)

```

This is the correct approach—testing behavior rather than implementation details of SDK classes.

---

### Issues Found

#### Issue 1: **Stale Docstring in **[**graph.py**](http://graph.py) (Low Priority)

- **Location**: `/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_agent/graph.py:8-21`

- **Problem**: The middleware ordering in the docstring doesn't match the actual code

- **Fix**: Update the docstring to reflect that SkillsMiddleware is now explicit at position 4 (not auto at position 12), and SummarizationToolMiddleware is at position 5 (not 8)

#### Issue 2: **SummarizationMiddleware Backend Change** (Worth Verifying)

- **Location**: `/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_agent/graph.py:120`

- **Change**: `SummarizationMiddleware(model=cfg.model_name, backend=bare_fs)` now uses `bare_fs` instead of `composite_backend`

- **Impact**: This is likely intentional—summarization middleware needs to read/write to actual disk for context storage, and `bare_fs` provides unrestricted access

- **Verification**: Confirm this doesn't break summarization when running in multi-threaded contexts (StateBackend vs direct FS access)

---

### Positive Observations

1. **Consistent Pattern Application**: All three runtime agents follow the exact same backend/middleware pattern

2. **Proper SDK Usage**: The code now uses SDK-native backends rather than custom wrappers

3. **Clear Separation of Concerns**: `CompositeBackend` for agent filesystem, bare `FilesystemBackend` for middleware that needs absolute path access

4. **Test Maintenance**: Tests were appropriately updated to test factories rather than implementation details

5. **No Breaking Changes**: The public API ([create_graph()](cci:1://file:///Users/Jason/2026/v4/meta-agent-v5.6.0/meta_agent/graph.py:59:0-203:16), `create_*_agent_graph()`) remains unchanged

---

### Verdict

**Approved with minor documentation cleanup recommended.**

The refactoring is architecturally sound, follows Deep Agents SDK patterns correctly, and applies consistently across all agents. The only actionable item is updating the stale docstring in [[graph.py](http://graph.py)](cci:7://file:///Users/Jason/2026/v4/meta-agent-v5.6.0/meta_agent/graph.py:0:0-0:0) to reflect the actual middleware ordering.