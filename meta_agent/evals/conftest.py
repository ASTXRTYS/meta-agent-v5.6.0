"""Shared fixtures for the eval suite.

Provides common test fixtures for eval execution.
"""

from __future__ import annotations

import os
import tempfile
from typing import Generator

import pytest

from meta_agent.project import init_project


@pytest.fixture
def temp_workspace() -> Generator[str, None, None]:
    """Create a temporary workspace directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def test_project(temp_workspace: str) -> dict:
    """Create a test project with full directory structure."""
    result = init_project(
        base_dir=temp_workspace,
        project_name="Test Project",
        description="A test project for eval suite",
    )
    return result


@pytest.fixture
def test_project_dir(test_project: dict) -> str:
    """Return just the project directory path."""
    return test_project["project_dir"]


@pytest.fixture
def test_project_with_prd(test_project_dir: str) -> str:
    """Create a test project with a sample PRD."""
    prd_path = os.path.join(test_project_dir, "artifacts", "intake", "prd.md")
    prd_content = """---
artifact: prd
project_id: test-project
title: Test Project PRD
version: "1.0.0"
status: draft
stage: INTAKE
authors:
  - orchestrator
lineage: []
---

# Test Project PRD

## Product Summary

A test project for validating the meta-agent eval suite.

## Goals

- Validate eval infrastructure works correctly
- Ensure all required sections are present

## Non-Goals

- Production deployment
- Performance optimization

## Constraints

- Must complete within test timeout

## Target User

Developers testing the meta-agent system.

## Core User Workflows

1. Run evals → See results → Fix failures

## Functional Requirements

- FR-001: Eval runner executes all registered evals
- FR-002: Results are reported with pass/fail status

## Acceptance Criteria

- All Phase 0 evals pass
- Results are printed to stdout

## Risks

- External dependencies may not be available in test environment

## Unresolved Questions

- None for Phase 0
"""
    with open(prd_path, "w") as f:
        f.write(prd_content)
    return test_project_dir
