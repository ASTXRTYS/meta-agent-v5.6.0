"""Shared test fixtures for the meta-agent test suite."""

from __future__ import annotations

import os
import sys
import tempfile
from typing import Generator

import pytest

# Ensure meta_agent package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from meta_agent.project import init_project


@pytest.fixture
def temp_dir() -> Generator[str, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def test_project(temp_dir: str) -> dict:
    """Create a fully initialized test project."""
    return init_project(
        base_dir=temp_dir,
        project_name="Test Project",
        description="A test project",
    )


@pytest.fixture
def test_project_dir(test_project: dict) -> str:
    """Return the project directory from a test project."""
    return test_project["project_dir"]


@pytest.fixture
def sample_prd_content() -> str:
    """Return sample PRD content with valid frontmatter and all sections."""
    return '''---
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

A test product for validating the meta-agent system.

## Goals

- Goal 1: Validate infrastructure
- Goal 2: Ensure correctness

## Non-Goals

- Production deployment

## Constraints

- Must run locally

## Target User

Developers testing the meta-agent.

## Core User Workflows

1. Initialize project
2. Run evals

## Functional Requirements

- FR-001: Project init creates all directories

## Acceptance Criteria

- All Phase 0 evals pass

## Risks

- External dependencies may be unavailable

## Unresolved Questions

- None for Phase 0
'''


@pytest.fixture
def test_project_with_prd(test_project_dir: str, sample_prd_content: str) -> str:
    """Create a test project with a sample PRD file."""
    prd_path = os.path.join(test_project_dir, "artifacts", "intake", "prd.md")
    with open(prd_path, "w") as f:
        f.write(sample_prd_content)
    return test_project_dir
