---
description:  Transform localized code-debt signals (bugs, TODOs, FIXMEs) into high-integrity architectural opportunities. This workflow guides assistants and developers in "trajecting" an issue from a naive patch to a global, SDK-aligned standard.
---

# Workflow: The Team Pitch (Strategic Architectural Evolution)

---

## Phase 1: Signal Identification (Architectural Drift)

When you encounter a bug, a communication comment (`TODO`, `FIXME`, `ISSUE`), or a pattern that feels "off," stop. Do not just patch the line. Evaluate if this is a symptom of **Architectural Drift**.

**The Signal**: Any code that deviates from the "Big Vision" or the SDK's core philosophy (e.g., duplicated logic, heuristic-based hacks where deterministic systems are needed, or manually managed state).

---

## Phase 2: The Trajectory (Systemic Patterns)

Investigate the root case. If this bug/TODO exists here, does it exist elsewhere? 
- **The Scope**: Grep the codebase for similar patterns.
- **The Rationale**: Move from a **"Local Patch"** mindset to a **"Global Standard"** mindset. 
- **The Question**: "How do I solve this once for the entire platform?"

---

## Phase 3: Solution Geometry (Entropy Reduction)

Design the transformational shape of the fix. 
- **Alignment**: How does this align us further with the SDK (e.g., `deepagents`, `langchain`)?
- **Simplification**: How much custom logic can we delete by centralizing this?
- **Standardization**: Draft a solution that reduces system entropy through centralization, generalization, or better abstraction.

---

## Phase 4: The Failure to Act (The Hidden Cost)

Explicitly document the **Hidden Cost of Inaction**. 
- What happens if we just patch this code?
- What is the cumulative cost in developer debugging time, brittle runtime behavior, or maintenance debt?
- **The Narrative**: Why is ignoring this "minor" issue a strategic error?

---

## Phase 5: Reality-Based ROI (User Stories)

Frame the fix through the lens of human value. Brainstorm 2-3 user stories that show actual real-world ROI.
- **Velocity**: How does this make adding/modifying features faster?
- **Safety**: How does this prevent production crashes or "silent failures"?
- **Extensibility**: How does this lower the floor for other developers/assistants to contribute?

---

## 🏛️ The Pitch Abstract (The Formula)

When presenting the opportunity to the team, use this high-signal formula:

1.  **Title**: A bold, strategic name for the initiative.
2.  **Concept**: The high-level architectural shift.
3.  **Status**: The current state of the debt (Citations required).
4.  **Goal & Benefit**: The specific "What" and "Why."
5.  **The Vision**: The broader impact on the system's longevity.
6.  **Business Value (ROI)**: 2-3 concrete User Stories.
