import json
import pytest
from unittest.mock import MagicMock

from langchain.tools import ToolRuntime
from langgraph.runtime import Runtime
from langchain_core.runnables import RunnableConfig

class MockReadResult:
    def __init__(self, error=None, file_data=None):
        self.error = error
        self.file_data = file_data

from meta_agent.middleware.artifact_protocol import ArtifactProtocolMiddleware, ArtifactProtocolState

class MockFilesystemBackend:
    def __init__(self, downloaded_files=None, read_result=None):
        self.downloaded_files = downloaded_files or []
        self.read_result = read_result

    def download_files(self, paths):
        return self.downloaded_files
    
    def read(self, path):
        return self.read_result


class MockRuntime(Runtime):
     def __init__(self, **kwargs):
         self.__dict__.update(kwargs)

def test_skip_if_present():
    backend = MockFilesystemBackend()
    mw = ArtifactProtocolMiddleware(backend=backend)
    state = ArtifactProtocolState(artifact_protocols={"prd": "fake_protocol"})
    
    config = RunnableConfig()
    # Missing explicit 'stream_writer', 'store' on our MockRuntime, let's use a very basic mock
    runtime_mock = MagicMock(spec=Runtime)
    
    result = mw.before_agent(state, runtime_mock, config)
    assert result is None

def test_file_not_found():
    backend = MockFilesystemBackend(
        downloaded_files=[MagicMock(error="file_not_found")]
    )
    mw = ArtifactProtocolMiddleware(backend=backend)
    state = ArtifactProtocolState()
    
    with pytest.raises(FileNotFoundError):
        mw.before_agent(state, MagicMock(), RunnableConfig())

def test_successful_load():
    yaml_content = b"""
protocols:
  prd:
    artifact_type: prd
    format: markdown
    required_frontmatter_fields: ["title"]
    required_sections:
      - name: "Summary"
        required: true
        match_strategy: exact
"""
    backend = MockFilesystemBackend(
        downloaded_files=[MagicMock(error=None, content=yaml_content)]
    )
    mw = ArtifactProtocolMiddleware(backend=backend)
    
    result = mw.before_agent(ArtifactProtocolState(), MagicMock(), RunnableConfig())
    assert result is not None
    assert "artifact_protocols" in result
    assert "prd" in result["artifact_protocols"]
    assert result["artifact_protocols"]["prd"].artifact_type == "prd"

def test_tool_unknown_protocol():
    mw = ArtifactProtocolMiddleware(backend=MagicMock())
    tool = mw.tools[0]
    
    runtime = ToolRuntime(
        state=ArtifactProtocolState(artifact_protocols={}),
        context={},
        stream_writer=None,
        store=None,
        config=RunnableConfig(),
        tool_call_id="call_id"
    )
    
    res = tool.func(artifact_path="/path", artifact_type="unknown", runtime=runtime)
    assert "✗ Validation failed" in res
    assert "[unknown_protocol]" in res

def test_tool_file_not_found():
    backend = MockFilesystemBackend(
        read_result=MockReadResult(error="file_not_found")
    )
    mw = ArtifactProtocolMiddleware(backend=backend)
    tool = mw.tools[0]
    
    # We must patch the state with a valid protocol to pass the protocol check
    from meta_agent.utils.artifact_validator import ArtifactProtocol, SectionSpec
    protocol = ArtifactProtocol(
        artifact_type="prd",
        format="markdown",
        required_sections=[SectionSpec(name="Summary")]
    )
    
    runtime = ToolRuntime(
        state=ArtifactProtocolState(artifact_protocols={"prd": protocol}),
        context={},
        stream_writer=None,
        store=None,
        config=RunnableConfig(),
        tool_call_id="call_id"
    )
    
    res = tool.func(artifact_path="/fake", artifact_type="prd", runtime=runtime)
    assert "✗ Validation failed" in res
    assert "[file_not_found]" in res

def test_tool_valid_artifact():
    backend = MockFilesystemBackend(
        read_result=MockReadResult(error=None, file_data={"content": "---\ntitle: a\n---\n# Summary"})
    )
    mw = ArtifactProtocolMiddleware(backend=backend)
    tool = mw.tools[0]
    
    from meta_agent.utils.artifact_validator import ArtifactProtocol, SectionSpec
    protocol = ArtifactProtocol(
        artifact_type="prd",
        format="markdown",
        required_frontmatter_fields=["title"],
        required_sections=[SectionSpec(name="Summary")]
    )
    
    runtime = ToolRuntime(
        state=ArtifactProtocolState(artifact_protocols={"prd": protocol}),
        context={},
        stream_writer=None,
        store=None,
        config=RunnableConfig(),
        tool_call_id="call_id"
    )
    
    res = tool.func(artifact_path="/fake", artifact_type="prd", runtime=runtime)
    assert "✓ Validation passed" in res
    assert "completeness 100%" in res
