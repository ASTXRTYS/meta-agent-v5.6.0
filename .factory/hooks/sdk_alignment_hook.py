#!/usr/bin/env python3
"""SDK Alignment Hook - Loads prompt from co-located Markdown file.

Droid UserPromptSubmit hook that injects SDK alignment instructions.
Prompt content lives in sdk_alignment_prompt.md (YAML frontmatter + markdown body).

For UserPromptSubmit: exit code 0 stdout is injected directly into Droid's context.
"""

import json
import re
import sys
from pathlib import Path


def load_prompt_file() -> tuple[str, str, str]:
    """Load hook metadata and prompt from co-located Markdown file.

    Returns:
        Tuple of (name, description, prompt)
    """
    prompt_path = Path(__file__).with_name("sdk_alignment_prompt.md")
    content = prompt_path.read_text()

    if not content.startswith("---"):
        raise ValueError("Prompt file missing YAML frontmatter")

    _, frontmatter, body = content.split("---", 2)

    # Parse simple YAML frontmatter without external dependency
    metadata = {}
    for line in frontmatter.strip().splitlines():
        match = re.match(r'^(\w+)\s*:\s*"?(.+?)"?\s*$', line)
        if match:
            metadata[match.group(1)] = match.group(2)

    return metadata.get("name", ""), metadata.get("description", ""), body.strip()


def main() -> None:
    # Consume stdin to avoid broken pipe (Factory sends JSON on stdin)
    sys.stdin.read()

    name, description, prompt = load_prompt_file()

    # stdout with exit code 0 is injected as context for UserPromptSubmit
    print(f"Hook Name: {name}\n\nDescription: {description}\n\nInstructions:\n{prompt}")


if __name__ == "__main__":
    main()
