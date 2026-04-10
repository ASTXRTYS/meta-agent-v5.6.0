#!/usr/bin/env python3
"""SDK Alignment Hook - Loads prompt from co-located Markdown file.

Windsurf Cascade pre_user_prompt hook that logs and validates SDK alignment.
Prompt content lives in sdk_alignment_prompt.md (YAML frontmatter + markdown body).
"""

import json
import sys
from pathlib import Path

import yaml


def load_prompt_file() -> tuple[str, str, str]:
    """Load hook metadata and prompt from co-located Markdown file.

    Returns:
        Tuple of (name, description, prompt)
    """
    prompt_path = Path(__file__).with_name("sdk_alignment_prompt.md")
    content = prompt_path.read_text()

    # Parse YAML frontmatter
    if content.startswith("---"):
        _, frontmatter, body = content.split("---", 2)
        metadata = yaml.safe_load(frontmatter.strip())
        prompt = body.strip()
    else:
        raise ValueError("Prompt file missing YAML frontmatter")

    return metadata["name"], metadata["description"], prompt


def main() -> None:
    # Read the JSON data from stdin (provided by Windsurf Cascade)
    input_data = sys.stdin.read()

    # Setup file logging for debugging (since pre_user_prompt doesn't show output in UI)
    log_path = Path(__file__).with_name("hook.log")

    def log(msg: str) -> None:
        """Log to both stderr and file for visibility."""
        print(msg, file=sys.stderr)
        with open(log_path, "a") as f:
            f.write(msg + "\n")

    try:
        data = json.loads(input_data)

        if data.get("agent_action_name") == "pre_user_prompt":
            tool_info = data.get("tool_info", {})
            user_prompt = tool_info.get("user_prompt", "")

            # Load the prompt file
            name, description, prompt = load_prompt_file()

            # Log hook execution
            log(f"[SDK Alignment Hook] TRIGGERED")
            log(f"[SDK Alignment Hook] Name: {name}")
            log(f"[SDK Alignment Hook] User prompt: {user_prompt[:100]}...")

    except json.JSONDecodeError as e:
        log(f"Error parsing JSON: {e}")
        sys.exit(1)
    except Exception as e:
        log(f"Hook error: {e}")
        sys.exit(1)

    # Hook succeeds (exit 0) - this hook is for logging/auditing
    # To block a prompt, exit with code 2
    sys.exit(0)


if __name__ == "__main__":
    main()
