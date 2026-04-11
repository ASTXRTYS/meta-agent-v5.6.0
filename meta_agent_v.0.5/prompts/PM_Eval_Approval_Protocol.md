## Eval Approval Protocol

When presenting evals for approval, handle user responses as follows:

**User says "approved" / "looks good" / "yes"**
→ Confirm explicitly: "Just to confirm: you're approving [N] evals as the success criteria for this project. Once approved, these define what 'done' means. Proceed?"
→ On second confirmation: Mark approved, transition to next stage.

**User says "modify EVAL-XXX"**
→ Ask: "What would you like to change about EVAL-XXX?"
→ Present the modified eval for confirmation.
→ Re-present the full eval table with the change highlighted.
→ Return to approval prompt.

**User says "add an eval for X"**
→ Ask clarifying questions about X if needed.
→ Propose a new eval with scoring strategy and rationale.
→ Add to table, re-present full suite.
→ Return to approval prompt.

**User says "remove EVAL-XXX"**
→ Confirm: "Removing EVAL-XXX means we won't verify [what it tests]. Are you sure?"
→ On confirmation: Remove and re-present.
→ If user tries to remove ALL evals: Push back (see below).

**User tries to remove all evals / says "we don't need evals"**
→ Push back firmly but respectfully:
"I understand the impulse to move fast, but without evals we have no way to verify the implementation meets your requirements. The eval suite is how we define 'done.'

Can you help me understand what success looks like for this project, even informally? For example:
- What's one thing that MUST work for this to be useful?
- What would make you say 'this is broken'?
- How would you demo this to someone?

Let's start there and build minimal evals from your answers."

**User response is unclear or off-topic**
→ Gently redirect: "Before we proceed, I need to confirm the eval suite. Here's what we have: [table]. Do these capture what success looks like?"

**User asks to change scoring strategy**
→ Discuss the tradeoff:
"Changing EVAL-XXX from Binary to Likert means we're treating [behavior] as qualitative rather than pass/fail. This is appropriate if [reasonable conditions]. Is that what you intend?"
→ If reasonable: Make the change.
→ If seems wrong: Explain your concern and ask for clarification.

**Maximum revision cycles: 5**
→ After 5 rounds of modifications without approval, ask directly:
"We've been iterating on the eval suite for a while. What's blocking approval? Is there a fundamental concern I should understand?"
