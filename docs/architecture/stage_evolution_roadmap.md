# Stage Evolution Roadmap: Beyond Syntactic Alignment

This document preserves architectural opportunities identified during the Phase 3 "Cleanup Pass" (v5.6.0). These insights are recorded here to prevent "fog of war" loss as development progresses.

## 1. Formalized Stage Interface (FSI) — ✅ IMPLEMENTED (v5.6.0)
**Concept:** Move from independent, duck-typed classes to a `BaseStage` managed architecture.

- **Status:** Integrated into core `meta_agent/stages/`.
- **Goal:** Centralize boilerplate (path resolution, common logic) and enforce a shared telemetry standard using LangChain/LangSmith conventions.
- **Benefit:** Dramatically reduces the friction of adding new workflow stages and provides a unified "hook" for system-wide performance auditing.

## 2. State Encapsulation (Localizing the Namespace) — ✅ IMPLEMENTED (v5.6.0)
**Concept:** Stop polluting the top-level `MetaAgentState` with stage-specific counters and flags.

- **Status:** Integrated via `stage_metadata` dictionary with localized `StageContext` and `operator.or_` LangGraph shallow-merge reducers.

- **Opportunity:** Introduce a `stage_metadata: dict[str, StageContext]` field.
- **Implementation:** Each stage manages its own key in this dictionary (e.g., `stage_metadata["SPEC_GENERATION"].revision_count`). 
- **Benefit:** Prevents the `TypedDict` from growing indefinitely and makes the state schema easier to reason about.

## 3. Artifact Provenance (Thread-Based Verification) — ✅ IMPLEMENTED (v5.6.0)
**Concept:** Trust the graph history, not just the filesystem.

- **Status:** Integrated via `BaseStage._artifact_is_proven` helper.
- **Opportunity:** Update `check_exit_conditions` to verify that an artifact exists **AND** was recorded in `artifacts_written` **AND** has a passing `ApprovalEntry` in the current thread history.
- **Implementation:** Query the reductive state lists (`approval_history`, `artifacts_written`) rather than just calling `os.path.isfile()`.
- **Benefit:** Protects the agent from "ghost artifacts" left behind by previous failed runs or external file moves.

## 4. Protocol-Driven Validation — ✅ IMPLEMENTED (v5.6.0)
**Concept:** Standardize artifact schema checking.

- **Status:** Integrated via `ArtifactProtocolMiddleware` utilizing `ArtifactProtocol` schema models.
- **Opportunity:** Implement an `ArtifactProtocol` validation engine.
- **Implementation:** A centralized utility in `meta_agent/utils/artifact_validator.py` that verifies Markdown and JSON files against definitions in `.agents/protocols/artifacts.yaml`.
- **Benefit:** Moves the system from "Check that the file exists" to "Check that the work is high quality," safely sandboxed with zero-trust provenance.

## 5. Telemetry: The "Shadow Gate" Pattern — ✅ IMPLEMENTED (v5.6.0)
**Concept:** Automatic LangSmith observability for every stage transition.

- **Status:** Consolidated into `BaseStage._emit_span` template method.
- **Implementation:** Integrates with Item #1 (BaseStage) using `@traceable`.
- **Benefit:** Provides a "heat map" of where agents get stuck most often (e.g., "Agents fail PRD exit conditions 30% more on Windows").

## 6. Canonical JSON Extraction (Hardening the Handshake) — ✅ IMPLEMENTED (v5.6.0)
**Concept:** Move from brittle, heuristic regex to a deterministic, stack-based brace-counting algorithm.

- **Status:** Integrated via `meta_agent/utils/parsing.py`.
- **Implementation:** Replaces four identical, private regex helpers with a single, high-integrity parser verified by Hypothesis property-based testing.
- **Benefit:** Eliminates silent runtime failures for complex nested JSON (Kubernetes manifests, IAM policies) and provides precise character-offset diagnostics for MTTR improvement.
