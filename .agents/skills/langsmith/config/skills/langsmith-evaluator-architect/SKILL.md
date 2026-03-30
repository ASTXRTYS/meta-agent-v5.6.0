---
name: langsmith-evaluator-architect
description: "INVOKE THIS SKILL whenever the user wants LangSmith evaluators designed from natural-language requirements, especially copy-paste-ready UI evaluator profiles, evaluator prompts with `{{input}}`/`{{output}}`/`{{reference}}`, Feedback Configuration JSON, rubric design, judge-model recommendations, sampling-rate guidance, or Python SDK equivalents. Use it for requests like 'I need 5 evaluators,' 'turn this app into evaluators,' 'write a LangSmith judge prompt,' or 'create these evaluators programmatically.'"
---

<oneliner>
Turn evaluation requirements into complete LangSmith evaluator profiles for the UI, then translate the same evaluators into Python SDK code on demand.
</oneliner>

<scope>
Use this skill when the main task is evaluator design. Pair it with `langsmith-evaluator` when you need to inspect traces, implement custom code evaluators, or wire evaluators into an actual evaluation run.
</scope>

<workflow>
## Working Style

1. Read the current conversation first. Do not ask for context the user already provided.
2. If core inputs are still missing, ask only the minimum questions needed:
   - What does the LLM application do?
   - What does good output look like?
   - What does bad output look like?
   - Do reference answers exist, or is this reference-free?
   - How many evaluators are needed, and which criteria matter most?
3. If the user only describes the app, proactively recommend a sensible evaluator set before drafting.
4. Default to UI-ready evaluator profiles.
5. If the user mentions code, SDK, CLI, or programmatic setup, include Python SDK equivalents. If they say "now do it in code," do not re-ask previously answered questions.
6. If the user changes criteria, reuse stable context and regenerate immediately.

## Common Evaluator Suggestions

- RAG apps: faithfulness, answer relevance, context utilization, completeness, hallucination detection
- Customer support: accuracy, policy compliance, tone, resolution completeness, escalation correctness
- Extraction or classification: schema validity, field completeness, normalization correctness, label accuracy
- Tool-using agents: task success, tool selection, argument correctness, trajectory efficiency, safety
- Writing copilots: instruction following, factuality, tone consistency, coverage, structure
</workflow>

<output_contract>
## Output Contract

When producing evaluators, output each one as a complete, independently copy-pasteable profile.

If the user asked for multiple evaluators, deliver all of them in one response and number them.

Always use this exact structure for each evaluator:

### Evaluator Profile: `<Evaluator Name>`

**Recommended Model:** `<specific judge model>`

**Prompt** (paste this entire block into the LangSmith prompt editor):

```text
<full evaluator prompt>
```

**Feedback Configuration JSON** (paste into the Feedback Configuration section):

```json
<full JSON schema>
```

**Recommended Sampling Rate:** `<percentage>` — `<brief justification>`

Never leave placeholder tokens like `<Criterion Name>` or `<type>` in the final output. Fill everything in.
</output_contract>

<prompt_rules>
## Prompt Rules

The prompt block must be complete. Do not output partial instructions or only a rubric fragment.

Always include the full LangSmith UI template block exactly once:

```xml
Please grade the following example according to the above instructions:

<example>
<input>
{{input}}
</input>

<output>
{{output}}
</output>

<reference_outputs>
{{reference}}
</reference_outputs>
</example>
```

Prompt-writing requirements:

- Start with a short system role and a precise description of the single criterion being judged.
- Define an explicit scoring rubric for the chosen response type.
- Give concrete examples at each score band. Vague rubrics produce inconsistent evaluators.
- Tell the judge to analyze carefully, be strict, and stay consistent.
- Ask for reasoning first and the score second.
- Keep the `{{reference}}` block even for reference-free evaluators. If references may be empty, explicitly tell the judge to ignore `{{reference}}` when it is blank or irrelevant.
- Prefer one primary metric per evaluator profile. If the user truly wants a multi-field extractor, say so explicitly and design the JSON schema to match.

Use the rubric pattern that matches the criterion type:

- `boolean`: define clear pass/fail conditions with concrete pass and fail examples
- `number`: define explicit bands, usually `0.0-1.0`
- `integer`: define each score on the scale, usually `1-5`
- `string`: define categorical labels and examples for each label
</prompt_rules>

<feedback_config>
## Feedback Configuration JSON Rules

Use a JSON schema that matches the LangSmith UI format:

```json
{
  "title": "extract",
  "description": "<what this evaluator measures>",
  "type": "object",
  "properties": {
    "<criterion_key>": {
      "type": "<boolean | number | integer | string>",
      "description": "<what this criterion measures>"
    },
    "comment": {
      "type": "string",
      "description": "Reasoning for the score"
    }
  },
  "required": ["<criterion_key>", "comment"],
  "strict": true
}
```

Rules:

- Use concise lowercase `snake_case` for criterion keys.
- Always include the `comment` field.
- Keep `"title": "extract"` and `"strict": true`.
- For categorical strings, include an `enum` array.
- For continuous numeric scores, state the expected range in the prompt and description.
- If the user wants several criteria, prefer several evaluator profiles over a single overloaded schema unless they explicitly ask for one combined evaluator.
</feedback_config>

<model_and_sampling>
## Judge Model And Sampling Guidance

Recommend a concrete model that fits the task and the user's stack.

Model guidance:

- Simple binary or format checks: use a fast, low-cost mini judge model
- Nuanced quality, policy, or safety judgments: use a stronger judge model
- If the user names a provider or model family, stay within it
- If no preference is given, pick a widely available, reliable judge model rather than an obscure one

Sampling guidance:

- Safety, compliance, or blocking release gates: `100%`
- Mission-critical correctness: `50-100%`
- General quality monitoring: `25-50%`
- High-volume, cost-sensitive monitoring: `5-15%`

Always include a short explanation for the sampling choice.
</model_and_sampling>

<sdk_mode>
## SDK Mode

If the user asks for code, produce Python SDK equivalents for the same evaluators without re-gathering requirements.

Online evaluator template:

```python
from langsmith import Client

client = Client()

client.create_run_rule(
    display_name="<Evaluator Name>",
    session_name="<LangSmith project name>",
    sampling_rate=<0.0_to_1.0>,
    evaluator_type="llm",
    model_config={
        "model": "<Recommended Model>",
        "temperature": 0,
    },
    prompt_template="""<full UI prompt from the evaluator profile>""",
    feedback_config={
        "<criterion_key>": {
            "type": "<boolean|continuous|categorical|int>",
            "description": "<criterion description>",
        }
    },
)
```

Offline evaluator template:

```python
from langsmith import evaluate

def my_evaluator(run, example):
    score = ...
    return {
        "key": "<criterion_key>",
        "score": score,
        "comment": "reasoning here",
    }

results = evaluate(
    my_llm_app,
    data="<dataset_name>",
    evaluators=[my_evaluator],
    experiment_prefix="<experiment_name>",
)
```

Type mapping from UI schema to SDK:

- `boolean` -> `boolean`
- `number` -> `continuous` with `min` and `max`
- `integer` -> `int` with `min` and `max`
- `string` with `enum` -> `categorical` with `categories`

When the user asks for code after already getting UI profiles:

- Keep the same evaluator names, criterion keys, models, rubrics, and sampling rates
- Add only the missing runtime fields such as `session_name` or `dataset_name`
- If those runtime names are unknown, use clear placeholders instead of re-deriving the evaluator logic
</sdk_mode>

<quality_bar>
## Quality Bar

- Sharpen vague asks. Replace soft labels like "goodness" with observable behaviors.
- Separate overlapping criteria. Do not mash "accuracy" and "tone" into one evaluator unless the user explicitly wants that tradeoff.
- Make every rubric operational. Each level should be distinguishable by behavior, not vibes.
- Keep outputs immediately usable. The user should be able to paste the prompt and JSON without further editing.
- When a request is underspecified, make a reasonable assumption, state it briefly, and move forward.
</quality_bar>

<example_pattern>
## Example Interaction Pattern

If the user says, "I have a customer support chatbot. I need evaluators for tone, accuracy, and completeness," produce three full evaluator profiles, each with:

- a full prompt containing `{{input}}`, `{{output}}`, and `{{reference}}`
- a valid Feedback Configuration JSON schema
- a recommended judge model
- a recommended sampling rate

If the user then says, "now do it in code," convert those same three evaluators into Python SDK code immediately.
</example_pattern>
