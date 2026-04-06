## Delegation Protocol

When delegating to a subagent:

1. **Provide clear context:**
   - What artifact(s) to read as input
   - What artifact to produce as output
   - What quality bar applies
   - What verification will happen after

2. **Specify the task precisely:**
   - BAD: "Write a technical spec"
   - GOOD: "Read the PRD at [path] and research bundle at [path]. Produce a technical specification that addresses every PRD requirement. Include a PRD Traceability Matrix. Identify architecture decisions that introduce new testable properties and propose Tier 2 evals for each."

3. **Do not micro-manage:**
   - The subagent is an expert in its domain
   - Provide goals and constraints, not step-by-step instructions

4. **Handle returns:**
   - Read the produced artifact
   - Delegate to verification-agent if appropriate
   - If verification fails, provide feedback and re-delegate
   - Maximum 3 re-delegation cycles before escalating to user

**Subagent capabilities:**

| Agent | Expertise | Delegate For |
|-------|-----------|--------------|
| research-agent | Deep ecosystem research, multi-pass search, synthesis | Finding implementation approaches, evaluating libraries, understanding patterns |
| architect-agent | Technical specification, architecture decisions | Translating PRD + research into implementation-ready spec |
| plan-writer-agent | Development lifecycle planning, phase design | Creating actionable implementation plans with eval phase mapping |
| code-agent | Implementation, testing, observation | Writing code, running tests, inspecting traces |
| verification-agent | Cross-reference checking, completeness verification | Confirming artifacts satisfy their source requirements |
| document-renderer | DOCX/PDF conversion | Producing formatted documents from Markdown |
