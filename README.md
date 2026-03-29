# 🤖 DoubtGPT: A Confidence-Aware Conversational Agent

## 📌 Overview

Traditional AI chatbots often generate responses even when they are **uncertain, ambiguous, or incorrect**, leading to overconfident hallucinations.

**DoubtGPT** is a novel **LLM-powered conversational chatbot** that introduces a **confidence-aware decision-making layer**, enabling it to:

* ✅ Answer when confident
* ❓ Ask clarification questions when input is ambiguous
* 🚫 Abstain when uncertainty is high

Unlike conventional chatbots, DoubtGPT does not immediately respond — it first evaluates whether it *should* respond.

---

## 🎯 Motivation

Modern Large Language Models (LLMs) are powerful but lack **self-awareness of uncertainty**, which leads to:

* Hallucinated answers
* Misleading confidence
* Poor handling of ambiguous queries

This project transforms a standard chatbot into a **self-regulating conversational system** that prioritizes reliability over blind responsiveness.

---

## 💬 Conversational Chatbot Interface

DoubtGPT is implemented as a **real-time interactive chatbot**, allowing users to communicate naturally through a chat interface.

### 🔹 Features

* **Interactive Chat Interface**

  * Natural language input/output
  * Seamless conversational experience

* **Context Handling (Basic)**

  * Supports follow-up questions
  * Maintains short-term conversation context

* **Decision-Aware Conversations**

  * Responses are not immediate
  * Each query passes through a decision pipeline

* **Dynamic Response Behavior**
  Depending on confidence, the chatbot:

  * Responds directly
  * Asks clarifying questions
  * Requests more context

---

### 🧠 Chat Flow

```text id="flow1"
User Message
   ↓
Chatbot Backend
   ↓
Decision Pipeline (LLM + Uncertainty + Decision)
   ↓
Final Response
   ↓
Displayed in Chat UI
```

---

## 🧠 Core Idea

```text id="arch_main"
User Query
   ↓
Multiple LLM Responses
   ↓
Uncertainty Estimation Layer
   ↓
Decision Engine
   ↓
[Answer] / [Clarify] / [Abstain]
```

The chatbot evaluates its own confidence before deciding how to respond.

---

## 🚀 Key Features

### 🔹 Multi-Response Generation

Generates multiple responses for a single query to analyze consistency.

### 🔹 Uncertainty Estimation Layer

Computes confidence using:

* Semantic agreement (embeddings)
* Self-reported confidence
* Hedging/uncertainty detection
* Response quality signals

### 🔹 Decision Engine

Selects one of:

* **Answer**
* **Clarification Question**
* **Abstain**

### 🔹 Clarification Generation

Produces intelligent follow-up questions for ambiguous queries.

### 🔹 Transparency (Optional UI)

Displays:

* Confidence score
* Decision taken
* Reason for uncertainty

---

## ⚙️ Tech Stack

* **Backend:** Python (FastAPI / Flask)
* **LLM API:** OpenAI / Gemini
* **Embeddings:** Sentence Transformers / OpenAI Embeddings
* **Frontend:** React.js (Chat Interface)

**Libraries:**

* `scikit-learn`
* `numpy`, `pandas`
* `transformers` (optional)

---

## 🛠️ Installation & Setup

### 1. Clone Repository

```bash id="s1"
git clone https://github.com/your-repo/doubtgpt.git
cd doubtgpt
```

### 2. Create Virtual Environment

```bash id="s2"
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash id="s3"
pip install -r requirements.txt
```

### 4. Set API Key

```bash id="s4"
export OPENAI_API_KEY=your_api_key
# or
export GEMINI_API_KEY=your_api_key
```

### 5. Run Backend

```bash id="s5"
python app.py
```

### 6. Run Frontend

```bash id="s6"
cd frontend
npm install
npm start
```

---

## 🧪 How It Works

### Step 1: Generate Multiple Responses

The system queries the LLM multiple times using controlled randomness.

### Step 2: Compute Uncertainty Signals

* **Agreement Score:** Semantic similarity between responses
* **Self-Confidence:** Extracted from model output
* **Hedging Score:** Detects uncertainty phrases

### Step 3: Confidence Calculation

```text id="conf_eq"
confidence = w1 * agreement + w2 * self_confidence - w3 * hedging
```

### Step 4: Decision Engine

* **High Confidence → Answer**
* **Medium Confidence → Clarify**
* **Low Confidence → Abstain**

---

## 💬 Example Interactions

### Example 1 (Ambiguous Query)

**User:**

> Explain this algorithm

**DoubtGPT:**

> Could you clarify which algorithm you are referring to (e.g., Dijkstra’s, Prim’s, etc.)?

---

### Example 2 (High Confidence)

**User:**

> What is the capital of Australia?

**DoubtGPT:**

> Canberra

---

### Example 3 (Low Confidence)

**User:**

> Explain the theory from that paper we discussed earlier

**DoubtGPT:**

> I’m not confident I have enough context to answer accurately. Could you provide more details?

---

## 📊 Evaluation Metrics

* **Accuracy (Correct Responses)**
* **Hallucination Reduction Rate**
* **Clarification Quality**
* **User Trust & Reliability (Qualitative)**

---

## 👥 Team Contributions

| Member   | Responsibility                       |
| -------- | ------------------------------------ |
| Member 1 | LLM Integration & Prompt Engineering |
| Member 2 | Uncertainty Estimation Module        |
| Member 3 | Decision Engine Logic                |
| Member 4 | Frontend & Visualization             |

---

## 🔮 Future Enhancements

* Reinforcement learning for decision optimization
* Domain-specific knowledge integration (RAG)
* Conversation memory & personalization
* Fine-tuned uncertainty estimation models

---

## 💡 Key Insight

> “A good AI doesn’t just give answers —
> it knows when **not** to.”

---

## 🏁 Conclusion

DoubtGPT transforms a traditional chatbot into a **self-aware conversational system** by integrating uncertainty estimation and decision-making. This significantly improves reliability, making LLM interactions safer, more transparent, and more trustworthy.

---
