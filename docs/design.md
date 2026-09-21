# SmartBank AI Assistant — Design Document

## Overview

A multi-agent banking chatbot that uses a **SuperAgent** to route customer queries to specialized agents. Each agent has domain-specific tools that interact with the bank database through Supabase.

## Architecture

### Agent System

```
Customer Message
       │
       ▼
 ┌───────────────┐
 │  SuperAgent    │  ← Analyzes intent, routes to specialist
 │  (Router)      │
 └───────┬───────┘
         │
    ┌────┼────┬────────────┐
    ▼    ▼    ▼            ▼
┌──────┐┌──────┐┌──────┐┌──────────┐
│ Loan ││Acct  ││ Card ││Complaint │
│Agent ││Agent ││Agent ││  Agent   │
└──┬───┘└──┬───┘└──┬───┘└────┬─────┘
   │       │       │         │
   ▼       ▼       ▼         ▼
┌──────────────────────────────────┐
│      Tool Dispatch Layer         │
│  (type coercion, idempotency)    │
└──────────────┬───────────────────┘
               │
               ▼
┌──────────────────────────────────┐
│     Supabase (PostgreSQL)        │
│  bank tables  │  agent tables    │
└──────────────────────────────────┘
```

### Routing Decision

The SuperAgent uses a zero-temperature LLM call with structured JSON output to classify the user's intent:

- **loan_agent**: Loan eligibility, EMI, applications, status
- **account_agent**: Balance, transactions, statements, profile
- **card_agent**: Card details, block/unblock, credit card bills
- **complaint_agent**: File/track/escalate complaints
- **self**: General greetings or ambiguous queries

### Tool System

Each agent has a tool class (e.g., `LoanTools`) with Python methods. The `dispatch.py` module:

1. Introspects method signatures to generate OpenAI function-calling schemas
2. Dispatches tool calls from the model to the right Python method
3. Coerces argument types (handles model sending `12.0` instead of `12`)

Tool docstrings serve as the prompt — they tell the model when/how to use each tool.

### Execution Flow

1. User sends message via API or CLI
2. Message saved to `message` table, run created in `run` table
3. SuperAgent classifies intent → routes to specialist agent
4. Specialist agent enters tool-calling loop:
   - Generate model response
   - If model requests tool calls → execute tools → feed results back
   - If model produces text → loop ends
5. Every step recorded in `run_step` table (for crash recovery)
6. Final reply saved to `message` table, run marked succeeded

### Idempotency

Side-effect tools (loan application, card blocking, complaint filing) are wrapped in an exactly-once guard:

```
key = SHA256(run_id + step_seq + tool_name + canonical_json(args))
result = once(key, lambda: actual_effect())
```

If the same tool call is attempted again (after a crash/retry), the stored result is returned without re-executing.

### Worker System

For async processing (optional):

- **Enqueue**: Save message + create `queued` run
- **Claim**: Worker atomically claims run via `lease_owner` + `lease_until`
- **Heartbeat**: Worker extends lease during long runs
- **Reap**: Expired leases get requeued or dead-lettered
- **Retry**: Exponential backoff (5s, 10s, 20s), max 3 attempts

### Database Design

**Two logical groups in one Supabase project:**

| Group | Tables | Purpose |
|-------|--------|---------|
| Bank | customer, account, transaction, loan, card, complaint | Business/domain data |
| Agent | thread, message, run, run_step, agent_log, idempotency | Conversation + execution tracking |

Key patterns:
- Messages are append-only (immutable history)
- Runs track status machine: queued → running → succeeded/failed
- Agent logs provide full observability into routing and tool calls
- Idempotency keys prevent duplicate side effects

### Memory

- Each conversation is a `thread` tied to a `customer_id`
- Messages have sequential `seq` numbers per thread
- History is loaded and converted to OpenAI chat format
- The `Memory` class handles all read/write operations

### Provider Abstraction

The `providers.py` module abstracts the LLM so tests can run without API calls:

- `OpenAIProvider`: Production — calls OpenAI API
- `ScriptedProvider`: Returns pre-defined turns in order
- `EchoProvider`: Echoes back the user's message

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/auth/signup | Register new user |
| POST | /api/auth/login | Login, returns JWT |
| POST | /api/chat/send | Send message, get agent response |
| POST | /api/chat/threads | Create new thread |
| GET | /api/chat/threads/:id | List threads for customer |
| GET | /api/chat/messages/:id | Get messages for thread |
| GET | /api/agents/logs/:id | Agent activity for thread |
| GET | /api/agents/runs/:id | Run history for thread |
| GET | /api/agents/stats | Global agent usage stats |

## Frontend

- **Sidebar**: Thread list + new chat button
- **Chat area**: Messages with agent badges showing which specialist replied
- **Agent panel**: Real-time activity log + usage statistics
- **Auth**: Login/signup with Supabase Auth
