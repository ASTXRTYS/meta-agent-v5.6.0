## Scoring Strategy Selection (V1)

Use two scoring strategies:

### Binary Pass/Fail
**Use when:** The expected behavior is deterministic. Same input → same expected output. No judgment required.

**Examples:**
- "Command exits with code 0" — Binary
- "File contains expected JSON structure" — Binary
- "API returns 200 status" — Binary
- "Output contains the string 'success'" — Binary

**Threshold:** Always 1.0 (must pass)

**Output format:** `{pass: true}` or `{pass: false, reason: "..."}`

### Likert 1-5 with Anchored Definitions
**Use when:** The expected behavior requires judgment. Quality is on a spectrum. Different evaluators might reasonably disagree.

**Examples:**
- "Error messages are helpful" — Likert (what is "helpful"?)
- "Documentation is clear" — Likert (what is "clear"?)
- "Response time is acceptable" — Likert (unless you have a specific ms threshold)
- "The UI is user-friendly" — Likert

**Threshold:** Mean >= 3.5 (above "adequate")

**CRITICAL:** Every Likert eval MUST have anchored definitions for all 5 levels. Never propose a bare "rate 1-5."

**Anchor template:**
| Score | Anchor |
|-------|--------|
| 1 | [Worst case — complete failure] |
| 2 | [Poor — significant problems] |
| 3 | [Adequate — works but has issues] |
| 4 | [Good — minor issues only] |
| 5 | [Excellent — no issues, exceeds expectations] |

**Example anchors for "error message helpfulness":**
| Score | Anchor |
|-------|--------|
| 1 | Error message is a raw exception or stack trace with no user-facing text |
| 2 | Error message exists but is cryptic or technical ("Error code 0x8004") |
| 3 | Error message explains what went wrong but not how to fix it |
| 4 | Error message explains the problem and suggests a fix, minor clarity issues |
| 5 | Error message clearly explains the problem, suggests specific fix, consistent tone |

**When in doubt:** Ask yourself "could two reasonable people disagree on whether this passes?" If yes → Likert. If no → Binary.
