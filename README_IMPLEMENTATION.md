# DoubtGPT Implementation Notes

## MVP Step 1

This first implementation slice adds a runnable FastAPI backend with:

- a `/health` route
- a `/chat` route
- in-memory session storage
- a simple rule-based decision engine that returns `answer`, `clarify`, or `abstain`
- a pluggable responder layer so the provider can be swapped later
- a browser-based chat UI served from `/`

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000/
```

## Configure Gemini

Copy `.env.example` to `.env` and set your Gemini key:

```bash
cp .env.example .env
```

The app reads:

- `LLM_PROVIDER`
- `DATABASE_PATH`
- `GEMINI_API_KEY`
- `GEMINI_MODEL`
- `GEMINI_SAMPLE_COUNT`
- `OLLAMA_BASE_URL`
- `OLLAMA_MODEL`
- `OLLAMA_EMBED_MODEL`
- `OLLAMA_SAMPLE_COUNT`
- `SEMANTIC_AGREEMENT_ENABLED`
- `EMBEDDING_MODEL_NAME`
- `FAST_PATH_ENABLED`

If `LLM_PROVIDER=gemini` but the key is missing, the API falls back to the rule-based responder.

If `LLM_PROVIDER=ollama`, the app uses your local Ollama server for generation and embeddings instead of a hosted API.

## Current Confidence-Aware Flow

When Gemini is enabled, the backend now:

- generates multiple structured candidate judgments
- scores how much the candidates agree
- combines agreement with self-reported confidence
- chooses the final `answer`, `clarify`, or `abstain` in backend code

Semantic agreement now prefers sentence-embedding similarity when available and falls back to lexical overlap otherwise.

To reduce latency and cost, the backend now includes a fast-path layer for obviously ambiguous or underspecified prompts, so those cases can skip the full multi-sample Gemini pipeline.

Conversation history is now stored in SQLite, so sessions persist across server restarts. The browser UI reuses a saved session id from local storage and loads prior messages automatically.

## Tiny Eval Set

Run the lightweight evaluation suite with:

```bash
python evals/run_eval.py
```

This checks a small set of prompts against expected decisions and prints pass/fail results.

To inspect the intermediate scoring, send `include_debug: true` in the `/chat` request body.

## Example Requests

```bash
curl http://127.0.0.1:8000/health
```

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"demo","message":"What is the capital of Australia?"}'
```
