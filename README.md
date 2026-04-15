# DoubtGPT

DoubtGPT is a confidence-aware chatbot that does not immediately answer every prompt. Instead, it decides whether it should:

- answer
- clarify
- abstain

The project is now a working FastAPI app with:

- a browser-based chat UI
- SQLite-backed persistence
- multi-sample confidence scoring
- semantic agreement scoring
- fast-path latency optimization
- provider-based model support
- a tiny evaluation suite

## What It Does

For each user message, DoubtGPT can:

- answer directly when the prompt is clear and confidence is high
- ask a follow-up question when the prompt is ambiguous
- abstain when the system is not confident enough to answer safely

The current backend combines:

- multiple candidate model outputs
- model-reported self-confidence
- response agreement across samples
- semantic similarity scoring
- final backend decision logic

## Current Architecture

```text
User Message
   ↓
Session History Load
   ↓
Context Resolution
   ↓
Fast Path (optional cheap clarify rules)
   ↓
Provider Responder (Ollama / Gemini / fallback)
   ↓
Multiple Candidate Judgments
   ↓
Agreement + Confidence Aggregation
   ↓
Final Decision: Answer / Clarify / Abstain
   ↓
Stored in SQLite + Returned to UI
```

## Key Features

### 1. Browser Chat UI

The app serves a built-in web UI from the FastAPI server.

Current UI features:

- chat interface
- decision badge
- confidence badge
- debug toggle
- saved session list
- new chat button
- rename chat
- delete chat

### 2. Confidence-Aware Backend

The backend does not rely on a single model output.

For model-backed paths it:

- samples multiple candidate judgments
- asks each candidate for:
  - `decision`
  - `self_confidence`
  - `response`
  - `reason`
- computes agreement
- computes final confidence
- chooses the final action in backend code

### 3. Semantic Agreement

The backend uses semantic similarity scoring for candidate response agreement.

Supported modes:

- local sentence-transformers scorer
- Ollama embedding scorer
- lexical fallback if semantic scoring is unavailable

### 4. Fast Path Optimization

To reduce latency and cost, DoubtGPT has a fast-path layer for prompts that are obviously underspecified.

Examples:

- very short prompts
- ambiguous prompts with no context

These can skip the expensive multi-sample model path.

### 5. Context Resolution

The backend can resolve some follow-up references using recent history.

Example:

- `What is the capital of India?`
- `Tell me the national bird of this country`

This helps the system rewrite `this country` to `India` before calling the model.

### 6. Persistent Storage

The project now uses SQLite for persistence.

Stored data includes:

- session id
- role
- message content
- assistant decision
- assistant confidence
- reason
- debug metadata
- timestamps

This means:

- conversations survive server restarts
- the UI can reload previous sessions
- sessions can be renamed or deleted

### 7. Provider Switching

The project supports multiple responders through a provider abstraction.

Current providers:

- `ollama`
- `gemini`
- `rule_based` fallback

## Current Tech Stack

- Backend: FastAPI
- Frontend: static HTML/CSS/JS served by FastAPI
- Persistence: SQLite
- Primary local model option: Ollama
- Optional hosted model option: Gemini
- Semantic agreement: sentence-transformers and/or Ollama embeddings

## Project Structure

```text
app/
  main.py                  # API routes and overall request flow
  config.py                # env-based configuration
  models.py                # request/response/storage schemas
  memory.py                # SQLite session/message storage
  fast_path.py             # cheap clarify rules
  context_resolution.py    # follow-up reference grounding
  responder_factory.py     # provider selection
  uncertainty.py           # agreement + confidence + final decision
  semantic_similarity.py   # semantic similarity scorers
  decision_engine.py       # fallback rule-based logic
  responders/
    ollama.py              # Ollama responder
    gemini.py              # Gemini responder
    rule_based.py          # fallback responder
  static/
    index.html             # browser UI
    app.js                 # frontend behavior
    styles.css             # frontend styling

evals/
  eval_cases.json          # tiny behavior test set
  run_eval.py              # eval runner
```

## How Confidence Works

Each model sample produces:

- `decision`
- `self_confidence`
- `response`
- `reason`

The backend then aggregates the samples using:

- decision consensus
- response agreement
- average self-confidence

The current confidence score is used to estimate:

**how confident the system is that its final action is the correct action**

That means:

- a high-confidence `answer` means the system is confident it should answer
- a high-confidence `clarify` means the system is confident it should ask a follow-up
- a high-confidence `abstain` means the system is confident it should avoid answering

## Running the Project

### Option A: Run With Ollama

This is the recommended local setup if you want to avoid hosted API limits.

Pull models:

```bash
ollama pull qwen3:4b
ollama pull nomic-embed-text
```

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Set it roughly like this:

```env
LLM_PROVIDER=ollama
DATABASE_PATH=data/doubtgpt.sqlite3
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen3:4b
OLLAMA_EMBED_MODEL=nomic-embed-text
OLLAMA_SAMPLE_COUNT=2
SEMANTIC_AGREEMENT_ENABLED=true
FAST_PATH_ENABLED=true
```

Start Ollama:

```bash
ollama serve
```

Then start the app:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/
```

### Option B: Run With Gemini

If you want to use Gemini instead:

```env
LLM_PROVIDER=gemini
DATABASE_PATH=data/doubtgpt.sqlite3
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash
GEMINI_SAMPLE_COUNT=2
SEMANTIC_AGREEMENT_ENABLED=true
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
FAST_PATH_ENABLED=true
```

Then run:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Useful Endpoints

- `GET /`
  - browser chat UI
- `GET /health`
  - system/provider status
- `POST /chat`
  - send a chat message
- `GET /sessions`
  - list stored chats
- `GET /sessions/{session_id}/messages`
  - fetch one session transcript
- `PATCH /sessions/{session_id}`
  - rename a session
- `DELETE /sessions/{session_id}`
  - delete a session

## Example Chat Request

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"demo","message":"Explain this subject","include_debug":true}'
```

## Evaluation

Run the tiny eval suite with:

```bash
.venv/bin/python evals/run_eval.py
```

This checks a small set of expected behaviors and helps catch regressions when the backend changes.

## Current Status

What is already implemented:

- browser UI
- SQLite persistence
- chat list / rename / delete
- fast-path optimization
- context resolution for some follow-ups
- Ollama integration
- Gemini integration
- semantic agreement
- multi-sample uncertainty scoring
- tiny eval suite

What still remains for future work:

- richer eval dataset
- threshold tuning
- better local-model latency optimization
- RAG / document grounding
- export / share chat history
- production deployment

## Core Idea

The main idea of DoubtGPT is still:

> A good chatbot should not only generate responses. It should also know when to answer, when to ask for more context, and when not to answer at all.
