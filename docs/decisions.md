# Architecture Decisions

## Why Celery + Redis for Task Processing?

**Decision:** Async task queue instead of sync HTTP response.

**Rationale:**
- LLM generation can take 30+ seconds; blocking HTTP request would timeout in production
- Client can receive response instantly with `message_id`, poll or stream updates independently
- Worker can retry failed generation without user intervention
- Multiple workers scale horizontally

**Trade-offs:**
- Added complexity: message polling, SSE subscription, error recovery
- Eventual consistency: UI may briefly show stale state before refresh
- **Chosen because:** Aligns with MVP scalability goal and user expectation of async feedback

---

## Why Redis for Caching Context History?

**Decision:** Cache last N messages with TTL instead of querying DB every time.

**Rationale:**
- Each LLM request needs conversation history → expensive DB round-trip
- TTL 60s balances freshness with cache hit rate (typical user sends 1-2 msgs/min)
- On miss, fetch and recompute; on hit, use cached JSON directly
- Logs show CACHE HIT/MISS for observability

**Trade-offs:**
- Stale history if user switches clients mid-conversation (TTL mismatch)
- Cache invalidation on admin message deletion requires manual intervention
- **Chosen because:** Simple, effective for MVP; misses are rare

---

## Why Message-Level Retry Instead of Task Retry?

**Decision:** `POST /messages/{id}/retry` creates a new message instead of updating the old one.

**Rationale:**
- Preserves failed message for audit trail and user context
- New message gets fresh `message_id`, new task enqueueing, new latency timing
- UI shows both failed and retried attempts in history
- Avoids race conditions from overlapping retries

**Alternative considered:** Update in-place retry with message.status cycling (failed → queued → done)
- Simpler for backend, but loses history
- User cannot see what failed vs. what succeeded

**Chosen because:** Transparency and auditability align with corporate chatbot use-case

---

## Why Ollama Instead of API Keys + Commercial LLM?

**Decision:** Local, self-hosted Ollama model.

**Rationale:**
- No external API calls → no rate limits, no billing, no vendor lock-in
- Chat data stays on-premises
- Model runs on Docker container → portable deployment

**Trade-offs:**
- Limited model quality vs. GPT-4/Claude
- Inference latency depends on hardware
- No auto-scaling across regions

**Chosen because:** ТЗ requirement: "no paid LLM API"

---

## Why RAG-lite (Simple Keyword Search) Over Full Vector Embeddings?

**Decision:** ILIKE SQL search on FAQ title/content, not vector similarity.

**Rationale:**
- No external embedding service required
- Fast for small FAQ corpus (<1000 items)
- User query parsed into keywords (3+ char words)
- System FAQs (tagged 'system', 'global') always injected

**Trade-offs:**
- Keyword mismatch misses relevant FAQ (typos, synonyms)
- Scales poorly beyond 10K items
- No semantic ranking

**Chosen because:** MVP goal: "knowledge from FAQ available to bot", not perfection

---

## Why SSE Streaming Instead of Polling?

**Decision:** Server-Sent Events (GET /messages/{id}/stream).

**Rationale:**
- Real-time feedback to user as tokens arrive
- Reduced latency perception
- Single HTTP connection (vs. poll spam)
- Standard web API (vs. WebSocket complexity)

**Trade-offs:**
- Unidirectional (server → client only)
- Connection drops require reconnect logic on frontend
- Limited to text; no binary data

**Chosen because:** Simpler than WebSocket, sufficient for text streaming

---

## Why Zustand + React Query on Frontend?

**Decision:** Zustand for auth/chat state, React Query for server data fetching.

**Rationale:**
- **Zustand:** Lightweight, sync store for session + UI state (tokens, conversation list)
- **React Query:** Built-in cache, refetch, retry, loading states for API responses
- Separation of concerns: state ≠ server data

**Trade-offs:**
- Two state systems to learn
- No built-in time-travel debugging (vs. Redux)

**Chosen because:** Minimal boilerplate, good for small teams

---

## Why JSON Structured Logging?

**Decision:** JSONFormatter for all logs (chat_service_logger, worker_logger).

**Rationale:**
- Machine-parseable: fields (request_id, user_id, latency_ms) extractable by log aggregator
- Structured context aids debugging: full request trace by `request_id`
- Standard in production (e.g., ELK Stack, Datadog ingest)

**Trade-offs:**
- Less human-readable in console (use log aggregator UI instead)
- Requires custom formatter

**Chosen because:** Observability requirement: "track latency and status across request lifecycle"

---

## Why JWT Tokens + Optional Refresh?

**Decision:** Access token (30 min) + Refresh token (7 days).

**Rationale:**
- Short-lived access token limits exposure if leaked
- Refresh token allows user to stay logged in without re-entering password
- Refresh endpoint (`POST /auth/refresh`) handles token rotation

**Trade-offs:**
- Added complexity for token rotation
- No token revocation (logout doesn't invalidate on server)
- Stateless JWT means backend doesn't know if user deleted account elsewhere

**Chosen because:** Standard OAuth2 pattern, balances security + UX

---

## Why SQLite for Tests, PostgreSQL for Prod?

**Decision:** Different databases for test vs. production.

**Rationale:**
- SQLite in-memory: fast, zero setup, isolated per test
- PostgreSQL in prod: ACID guarantees, scaling, replication
- Same SQLAlchemy ORM masks differences during development

**Trade-offs:**
- SQL quirks may not surface in tests (e.g., DISTINCT behavior)
- Alembic migrations must work on both

**Chosen because:** Pragmatic: reduce test feedback loop

---

## Why AdminAPI for FAQ, Not User-Facing?

**Decision:** FAQ management restricted to admins only.

**Rationale:**
- Prevents spam/vandalism of knowledge base
- Clear ownership and update workflow
- ТЗ states: "Админ API для FAQ"

**Trade-offs:**
- Users cannot contribute knowledge
- Requires admin user creation (manual DB insert or separate admin panel)

**Chosen because:** Simple, safe for MVP

---

## Summary Table

| Decision | Why | Trade-off |
|----------|-----|-----------|
| Celery async | Scale, no timeout | UI polling complexity |
| Redis cache | Fast context fetch | Stale data risk (TTL) |
| Message retry | Auditability | New ID (instead of update) |
| Ollama local | No API keys, on-premise | Limited model quality |
| Keyword FAQ search | Simple, fast | Synonym misses |
| SSE streams | Real-time, standard | Reconnect logic needed |
| Zustand + RQ | Lightweight | Two state systems |
| JSON logs | Machine-readable | Less human-readable |
| JWT + refresh | Secure + UX | No server revocation |
| SQLite + PG | Test speed + prod safety | SQL dialect differences |
| Admin FAQ only | Safe, clear ownership | No user contribution |

