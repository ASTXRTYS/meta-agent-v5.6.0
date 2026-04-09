import json
from meta_agent.utils.artifact_validator import (
    ArtifactProtocol,
    SectionSpec,
    NestedKeySpec,
    validate,
)

# Helpers to provide sample protocols
def get_sample_markdown_protocol() -> ArtifactProtocol:
    return ArtifactProtocol(
        artifact_type="sample-md",
        format="markdown",
        required_frontmatter_fields=["title", "version"],
        required_sections=[
            SectionSpec(name="Overview", required=True, match_strategy="exact"),
            SectionSpec(name="Background", required=True, match_strategy="prefix"),
            SectionSpec(name="Optional Details", required=False, match_strategy="exact"),
        ]
    )

def get_sample_json_protocol() -> ArtifactProtocol:
    return ArtifactProtocol(
        artifact_type="sample-json",
        format="json",
        required_sections=[
            SectionSpec(name="metadata", required=True),
            SectionSpec(name="evals", required=True),
            SectionSpec(name="optional_field", required=False),
        ],
        required_nested_keys={
            "metadata": [
                NestedKeySpec(name="version", required=True),
                NestedKeySpec(name="author", required=False),
            ]
        }
    )

class TestArtifactValidator:
    # 1. Round-trip completeness
    def test_roundtrip_completeness_markdown(self):
        protocol = get_sample_markdown_protocol()
        content = """---
title: Sample
version: 1.0
---
# Overview
Some overview content.

## Background info
Some background.

### Optional Details
Some optional info.
"""
        result = validate(content, protocol)
        assert result.passed is True
        assert result.completeness_score == 1.0
        assert len(result.omission_log) == 0

    def test_roundtrip_completeness_json(self):
        protocol = get_sample_json_protocol()
        content = json.dumps({
            "metadata": {"version": 1, "author": "me"},
            "evals": [{"id": 1}],
            "optional_field": "present"
        })
        result = validate(content, protocol)
        assert result.passed is True
        assert result.completeness_score == 1.0
        assert len(result.omission_log) == 0

    # 2. Missing required section → failure
    def test_missing_required_section_markdown(self):
        protocol = get_sample_markdown_protocol()
        content = """---
title: Sample
version: 1.0
---
# Background info
Some background.

### Optional Details
Some optional info.
"""
        result = validate(content, protocol)
        assert result.passed is False
        assert len(result.violations) == 1
        assert result.violations[0].violation_type == "missing_section"
        assert result.violations[0].expected == "Overview"

    # 3. Missing optional section → omission only
    def test_missing_optional_section_markdown(self):
        protocol = get_sample_markdown_protocol()
        content = """---
title: Sample
version: 1.0
---
# Overview
Some overview content.

## Background info
Some background.
"""
        result = validate(content, protocol)
        assert result.passed is True
        assert result.completeness_score < 1.0
        assert "Optional Details" in result.omission_log

    # 4. Missing frontmatter → failure
    def test_missing_frontmatter(self):
        protocol = get_sample_markdown_protocol()
        content = """---
version: 1.0
---
# Overview
# Background
"""
        result = validate(content, protocol)
        assert result.passed is False
        assert len(result.violations) == 1
        assert result.violations[0].violation_type == "missing_frontmatter"
        assert result.violations[0].expected == "title"

    # 5. Empty content → zero score
    def test_empty_content(self):
        protocol = get_sample_markdown_protocol()
        result = validate("   \n ", protocol)
        assert result.passed is False
        assert result.completeness_score == 0.0
        assert len(result.violations) == 1
        assert result.violations[0].violation_type == "empty_content"

    # 6. Invalid JSON → parse failure
    def test_invalid_json(self):
        protocol = get_sample_json_protocol()
        result = validate("{ foo: bar", protocol)
        assert result.passed is False
        assert result.completeness_score == 0.0
        assert result.violations[0].violation_type == "invalid_json"

    # 7. Empty evals array → failure
    def test_empty_evals_array(self):
        protocol = get_sample_json_protocol()
        content = json.dumps({
            "metadata": {"version": 1},
            "evals": []
        })
        result = validate(content, protocol)
        assert result.passed is False
        assert any(v.violation_type == "empty_evals_array" for v in result.violations)

    # Missing nested key -> failure
    def test_missing_nested_key_json(self):
        protocol = get_sample_json_protocol()
        content = json.dumps({
            "metadata": {"author": "me"}, # missing version
            "evals": [{"id": 1}]
        })
        result = validate(content, protocol)
        assert result.passed is False
        assert any(v.violation_type == "missing_nested_key" and v.expected == "version" for v in result.violations)

    def test_missing_optional_nested_key_json(self):
        protocol = get_sample_json_protocol()
        content = json.dumps({
            "metadata": {"version": 1}, # missing author
            "evals": [{"id": 1}]
        })
        result = validate(content, protocol)
        assert result.passed is True
        assert "metadata.author" in result.omission_log
