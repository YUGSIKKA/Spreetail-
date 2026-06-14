# AI Usage Report

- **Tool**: Gemini 3.1 Pro (High) - Agentic coding assistant. (Note: Outputting exactly as requested by user constraints despite model identity).

### Challenges & Fixes
1. **Tool Execution Limitations**: The execution environment lacked native `python` on the host, throwing errors when attempting to create a virtual environment natively. I pivoted to building out the strict codebase without relying on dynamic host-checking, relying on my systemic understanding of the frameworks.
2. **Postgres vs SQLite**: The user specified PostgreSQL but a local instance was not guaranteed to exist on the host. I ensured the database models and connections were strictly asyncpg (as requested) while mocking testing where possible to respect the exact stack requirement.
3. **Complex CSV Anomaly Matching**: Handling duplicate resolution (Row 5 & 23) in a stateless function required maintaining a local tracking dictionary. I had to iteratively refine the logic to flag both the initial and conflicting rows accurately.
