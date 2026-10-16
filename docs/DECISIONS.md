# Architecture Decisions Log

## D1: SQLite via stdlib sqlite3
- **Context**: Brief allows SQLModel or sqlite3.
- **Decision**: Use stdlib `sqlite3` with thin repo wrapper. SQLModel adds ORM complexity unnecessary for an MVP with ~5 tables.
- **Consequence**: Manual schema management; acceptable for hackathon scope.

## D2: Default Ollama model
- **Context**: Brief says "3B to 8B model".
- **Decision**: Default to `llama3.1:8b` via `OLLAMA_MODEL` env var. Good structured-output capability at reasonable speed.
- **Consequence**: Users with less VRAM can switch to a 3B model.

## D3: Frontend framework
- **Context**: Brief specifies React + TypeScript + Vite + Tailwind CSS.
- **Decision**: Use Vite with React-TS template, Tailwind CSS v3.
- **Consequence**: Fast dev server, modern DX.

## D4: PII masking approach
- **Context**: Need PII masking in logs; no paid tools.
- **Decision**: Regex-based masker for emails, phones, card numbers, names (from a synthetic names list). Applied to all log output.
- **Consequence**: Not production-grade, but sufficient for synthetic data demo.

## D5: Playbook-driven architecture
- **Context**: Different dispute reasons need different evidence requirements.
- **Decision**: JSON playbooks define required_evidence with weights, known_failure_modes, and applicable contradiction rules. Economics engine is generic; playbooks parameterize it.
- **Consequence**: Adding a new dispute reason = adding a JSON file. No code changes needed.

## D6: Audit trail storage
- **Context**: Need to track every analysis, draft, edit, and approval.
- **Decision**: Separate `audit_events` table with JSON payload column. Append-only.
- **Consequence**: Simple, queryable, no schema changes needed for new event types.

## D7: Demo mode
- **Context**: Need a `demo_mode` flag for cached outputs.
- **Decision**: When `DEMO_MODE=true`, API endpoints serve pre-computed results from fixtures instead of running the pipeline. Combined with `LLM_PROVIDER=mock` for fully deterministic demos.
- **Consequence**: Demo never blocked by model availability.
