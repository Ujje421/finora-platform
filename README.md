# Financial Intelligence Platform

> *"Never optimize for an impressive answer. Optimize for a verifiable answer."*

A production-grade financial intelligence system that provides **evidence-backed, verifiable** answers about markets, companies, and financial events. Every claim is cited, every source is tracked, every answer is auditable.

## What Makes This Different

| What Most AI Finance Tools Do | What This System Does |
|---|---|
| LLM answers from training data | Evidence-backed answers from primary sources |
| No source attribution | Every claim linked to specific filing paragraph |
| No verification | Deterministic numerical verification before delivery |
| Says confident wrong things | Says "I don't know" when evidence is insufficient |
| One model, their cost | BYOM: user picks their preferred AI model |

## Architecture

```
YOUR INFRASTRUCTURE                     USER'S AI (BYOM)
──────────────────                     ─────────────────
SEC EDGAR → Extraction → Events →      Gemini / GPT / Claude
Entity Resolution → Evidence Pack →    → Reasoning
Verification (deterministic)           
```

**BYOM (Bring Your Own Model)**: Users connect their own AI provider (Gemini, OpenAI, Claude, Groq, or local Ollama). You pay for data + infra. Users pay for their own AI reasoning.

## Tech Stack

- **Backend**: Python 3.12 + FastAPI
- **Database**: PostgreSQL 16 + pgvector
- **Cache**: Redis
- **Frontend**: Next.js 14 + TypeScript
- **AI (extraction)**: Gemma 2 / Llama via Groq free tier
- **AI (reasoning)**: User's own model (BYOM)
- **Embeddings**: nomic-embed-text-v1.5 (self-hosted)

## Quick Start

### Prerequisites
- Python 3.12+
- Node.js 20 LTS
- Docker & Docker Compose

### 1. Start infrastructure
```bash
docker compose up -d
```

### 2. Backend setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac
pip install -r requirements.txt
cp ../.env.example .env      # Edit with your values
```

### 3. Run database migrations
```bash
alembic upgrade head
```

### 4. Start the API
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Verify
```bash
curl http://localhost:8000/health
```

## Project Structure

```
financial-terminal/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── config.py            # Environment configuration
│   │   ├── database.py          # Async SQLAlchemy + pgvector
│   │   ├── models/              # ORM models
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── api/                 # API routers
│   │   ├── services/            # Business logic
│   │   │   ├── ingestion/       # Data pipeline workers
│   │   │   ├── extraction/      # AI extraction + entity resolution
│   │   │   ├── agent/           # Research agent + verification
│   │   │   └── ai/              # BYOM model routing
│   │   ├── tools/               # Agent tools (API the AI calls)
│   │   └── utils/               # Logging, tracing, crypto
│   ├── alembic/                 # Database migrations
│   └── tests/
├── frontend/                    # Next.js terminal UI
├── docker-compose.yml           # PostgreSQL + Redis
└── docs/                        # Architecture documentation
```

## Design Principles

1. **Facts ≠ AI**: Financial facts come from deterministic sources. AI interprets, never invents.
2. **Provenance**: Every data point has a source, tier, and timestamp. Always.
3. **Verification**: Every numerical claim is checked against the fact store before delivery.
4. **"I Don't Know"**: When evidence is insufficient, the system says so explicitly.
5. **Audit Trail**: Every tool call, query, and model invocation is logged with trace_id.

## License

Private — Not open source.
