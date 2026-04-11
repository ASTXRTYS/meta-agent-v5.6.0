# Agent API Schemas (`meta_agent/schemas/`)

This directory contains pure-Python `TypedDict` and `Pydantic` definitions that formalize the communication contract between the LangGraph server and frontend UI applications.

## Interrupt Communication Convention

When pausing an agent workflow via LangGraph's `interrupt()`, the emitted payload **MUST NOT** be a raw primitive dictionary. 

Instead, a strictly-typed schema must be defined in this directory and instantiated by the emitting tool. This guarantees that UI clients traversing the backend API can import and rely on static object shapes (e.g. `AskUserRequest`, `ExecuteCommandRequest`, `ApprovalRequest`) to render interactive components like modals, radio buttons, or code blocks natively without pulling in execution modules or `langchain` overhead.

By treating these schemas as the static API surface layer, frontend and integration teams can quickly map UX schemas independently of agent flow logic.
