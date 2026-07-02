# Antigravity Vera Bot Submission

## Approach
This bot leverages FastAPI for the serving infrastructure and the `google-genai` Python SDK to communicate with Gemini 2.5 Flash for message composition.
The prompt engineering focuses on deterministic output generation matching the 5 criteria:
- **Specificity**: Instructing the model to always anchor to numeric facts and real references.
- **Category & Merchant Fit**: Utilizing the provided context structs in a clear zero-shot instruction prompt.
- **Trigger Relevance**: Explicit injection of the trigger logic.
- **Engagement Compulsion**: Pushing the LLM to end with a binary or short open-ended question.

## Model Choice
**Model**: `gemini-2.5-flash`
We chose this model because it handles large structured JSON contexts exceptionally well, follows strict JSON schemas for the response format, and produces responses quickly (vital for the 30s timeout).

## Tradeoffs
- We are using zero-shot prompt instructions without complex RAG or retrieval tools because the context sizes (4 payloads per trigger) fit comfortably within the Gemini context window.
- In-memory dictionaries are used for state management. This won't scale across multiple instances without a centralized datastore (like Redis), but is sufficient and performant for the single-instance test harness constraints.
- We rely on LLM logic for multi-turn conversation parsing. While flexible, this could be less predictable than a strict state machine, but it allows for robust recovery from edge cases (like the auto-reply loop).

## Running Locally
Ensure you have set `GEMINI_API_KEY` in your `.env` or environment variables before running the FastAPI server.
```bash
python -m venv .venv
source .venv/bin/activate  # or .\.venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn bot:app --port 8080
```
