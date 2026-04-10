#!/usr/bin/env python3
"""SDK Alignment Hook - Loads prompt from co-located Markdown file.

Droid UserPromptSubmit hook that injects SDK alignment instructions as context.
Prompt content lives in sdk_alignment_prompt.md (YAML frontmatter + markdown body).

Session-aware: reads transcript_path to detect if alignment context was already
injected earlier in this session. If so, skips re-injection to avoid redundant
noise in the context window.

For UserPromptSubmit: JSON output with hookSpecificOutput.additionalContext is
injected directly into Droid's context.
"""

import json
import sys
from pathlib import Path

import yaml

# Sentinel string written into context on first injection.
# Used to detect whether this session already received alignment instructions.
INJECTION_SENTINEL = "[SDK_ALIGNMENT_INJECTED]"


def load_prompt_file() -> tuple[str, str, str]:
    """Load hook metadata and prompt from co-located Markdown file.

    Returns:
        Tuple of (name, description, prompt)
    """
    prompt_path = Path(__file__).with_name("sdk_alignment_prompt.md")
    content = prompt_path.read_text()

    if content.startswith("---"):
        _, frontmatter, body = content.split("---", 2)
        metadata = yaml.safe_load(frontmatter.strip())
        prompt = body.strip()
    else:
        raise ValueError("Prompt file missing YAML frontmatter")

    return metadata["name"], metadata["description"], prompt


def already_injected(transcript_path: str) -> bool:
    """Return True if the alignment sentinel appears in the session transcript.

    Scans the JSONL transcript for any message whose content contains the
    sentinel string, which is written by this hook on first injection.
    """
    path = Path(transcript_path)
    if not path.exists():
        return False

    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Droid JSONL entries vary by type; search all string values
            raw = json.dumps(entry)
            if INJECTION_SENTINEL in raw:
                return True
    except Exception:
        # If we can't read the transcript, fail open (inject anyway)
        return False

    return False


def main() -> None:
    raw_input = sys.stdin.read()

    try:
        data = json.loads(raw_input)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}", file=sys.stderr)
        sys.exit(1)

    transcript_path = data.get("transcript_path", "")

    # Skip injection if alignment instructions already in this session's context
    if already_injected(transcript_path):
        # Empty additionalContext — no noise added, no re-injection
        result = {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": "",
            },
            "suppressOutput": True,
        }
        print(json.dumps(result))
        sys.exit(0)

    try:
        name, description, prompt = load_prompt_file()
    except Exception as e:
        print(f"Hook error loading prompt file: {e}", file=sys.stderr)
        sys.exit(1)

    # Sentinel is embedded in the injected text so future hook calls can detect it
    context = (
        f"{INJECTION_SENTINEL}\n\n"
        f"Hook Name: {name}\n\n"
        f"Description: {description}\n\n"
        f"Instructions:\n{prompt}"
    )

    result = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": context,
        },
        "suppressOutput": True,
    }
    print(json.dumps(result))
    sys.exit(0)


if __name__ == "__main__":
    main()
