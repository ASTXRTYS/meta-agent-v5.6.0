"""Legacy ratchet — fail if legacy test count increases above the frozen baseline."""
import pytest
import subprocess
import sys
from pathlib import Path

LEGACY_CEILING = 410  # Frozen after Phase 4 cleanup. Must only decrease.

@pytest.mark.drift
class TestLegacyRatchet:
    def test_legacy_count_does_not_increase(self):
        """Legacy test count must not exceed the frozen ceiling."""
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/unit/", "--co", "-q", "--no-header"],
            capture_output=True, text=True,
            cwd=str(Path(__file__).parent.parent.parent)
        )
        # Last non-empty line should be "N tests collected" or "no tests ran"
        lines = [l.strip() for l in result.stdout.strip().splitlines() if l.strip()]
        count_line = lines[-1] if lines else ""
        
        import re
        match = re.search(r"([0-9]+) test", count_line)
        count = int(match.group(1)) if match else 0
        
        assert count <= LEGACY_CEILING, (
            f"Legacy test count ({count}) exceeds ceiling ({LEGACY_CEILING}). "
            f"Legacy tests must not increase. Delete legacy tests or raise the ceiling with justification."
        )
    
    def test_legacy_count_reported(self):
        """Report current legacy count for tracking."""
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/unit/", "--co", "-q", "--no-header"],
            capture_output=True, text=True,
            cwd=str(Path(__file__).parent.parent.parent)
        )
        lines = [l.strip() for l in result.stdout.strip().splitlines() if l.strip()]
        count_line = lines[-1] if lines else "0"
        # Just report — this test always passes
        print(f"Current legacy count: {count_line}")
