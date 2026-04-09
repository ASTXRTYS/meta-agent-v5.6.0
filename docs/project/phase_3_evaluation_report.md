# Phase 3 Experimental Findings and Known Issues

*This document contains historical observations from live execution of the Phase 3 implementation. It serves as a deeper-dive retrospective outside the core PM operating instructions.*

## Experiment Context

- **Trace ID**: 019d404a-8275-7cb3-81a7-4bc166c13cb1 (LangSmith)
- **Date**: 2026-03-30
- **PRD**: .agents/pm/projects/meta-agent/artifacts/intake/research-agent-prd.md
- **Status**: Experiment cut off before research phase began

## Issues Discovered

### Skills Usage Behavior

The research-agent demonstrated incorrect skills consultation:

- **Expected**: Use SkillsMiddleware to internalize pre-loaded skills before web research
- **Actual**: Brute-force directory traversal through `/skills/` with 78 read_file calls
- **Problem**: Measurement stack was rewarding filesystem access rather than middleware-driven skill usage

### Research Approach

- **Expected**: Web research using web_search and web_fetch tools
- **Actual**: 0 web_search calls, 0 web_fetch calls
- **Problem**: Agent stuck in filesystem exploration mode instead of conducting research

### Delegation Patterns

- **Expected**: Intentional sub-agent topology with parallel research
- **Actual**: Only 2 task calls, minimal delegation
- **Problem**: Poor reasoning about delegation topology and workload distribution

### Middleware Integration

- **Expected**: DynamicSystemPromptMiddleware firing correctly
- **Actual**: Middleware not operating as intended
- **Problem**: Stage-aware prompts and system message handling broken

### PRD Decomposition

- **Expected**: Structured decomposition into research domains
- **Actual**: Failed to properly decompose PRD requirements
- **Problem**: Agent couldn't translate PRD into actionable research agenda

## Current Frozen State

Development is frozen until API funding is available. The architectural foundation exists (all three Phase 3 agents implemented as Deep Agents), but behavioral fixes are required before the research-agent can perform as designed.

## Detailed Analysis Reference

See DEVIATION_RECORD.md Section 21 for comprehensive analysis of:

- Why the measurement stack rewarded incorrect behaviors
- Skills-first research posture implementation gaps
- Middleware evidence vs filesystem access patterns
- Evaluation contract misalignment

This section contains high-signal feedback about the root causes of these issues.
