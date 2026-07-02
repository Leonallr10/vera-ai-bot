# leonal Vera Bot Submission

## Approach
This bot leverages **FastAPI** for the serving infrastructure and the `google-genai` Python SDK to communicate with **Gemini 2.5 Flash** for message composition. The prompt engineering focuses on deterministic output generation matching the five scoring criteria:
- **Specificity** – always anchor to numeric facts and real references.
- **Category & Merchant Fit** – use the provided context structs.
- **Trigger Relevance** – inject the trigger logic.
- **Engagement Compulsion** – end with a binary or short open‑ended question.

## Model Choice
**Model:** `gemini-2.5-flash`
We chose this model because it handles large structured JSON contexts exceptionally well, follows strict JSON schemas for the response format, and produces responses quickly (vital for the 30‑second timeout).

## Tradeoffs
- Zero‑shot prompting only – no external RAG because each trigger contains ≤ 4 payloads, comfortably fitting the model window.
- In‑memory dictionaries for state management – sufficient for the single‑instance test harness but would need a datastore (e.g., Redis) for horizontal scaling.
- LLM‑driven multi‑turn logic – flexible but less predictable than a strict state machine; mitigated by strict prompt constraints.

## Public URL (ngrok)
The bot is publicly reachable via the following ngrok tunnel (keep the tunnel running while the judge evaluates):

```
https://unprovided-patternless-ignacio.ngrok-free.dev
```

### Example Requests & Responses
You can interact with the bot directly using `curl` (or any HTTP client). All responses are **JSON** and conform to the judge’s schema.

#### 1️⃣ Health Check
```bash
curl https://unprovided-patternless-ignacio.ngrok-free.dev/v1/healthz
```
**Response**
```json
{"status":"ok"}
```

#### 2️⃣ Metadata
```bash
curl https://unprovided-patternless-ignacio.ngrok-free.dev/v1/metadata
```
**Response**
```json
{
  "team":"Antigravity",
  "model":"gemini-2.5-flash",
  "description":"Vera AI bot for Magicpin challenge"
}
```

#### 3️⃣ Push Context (example – a single category)
```bash
curl -X POST https://unprovided-patternless-ignacio.ngrok-free.dev/v1/context \
  -H "Content-Type: application/json" \
  -d '{"type":"category","id":"dentists","payload":{...}}'
```
**Response**
```json
{"status":"accepted"}
```
*(The actual payload follows the schema described in the challenge brief.)*

#### 4️⃣ Get a Reply (merchant initiates conversation)
```bash
curl -X POST https://unprovided-patternless-ignacio.ngrok-free.dev/v1/reply \
  -H "Content-Type: application/json" \
  -d '{"merchant_id":"001","turn_number":1,"messages":[{"role":"merchant","content":"Hi, I want to try Vera!"}]}'
```
**Response** (example)
```json
{
  "action":"send",
  "body":"Great! To get started, I'll need a few details from you."
}
```

### Full End‑to‑End Test Procedure
1. **Start the bot** (keep this terminal open):
   ```powershell
   .\.venv\Scripts\activate
   uvicorn bot:app --host 0.0.0.0 --port 8080
   ```
2. **Open a second terminal** and launch the ngrok tunnel:
   ```powershell
   ngrok http --region ap 8080
   ```
   Copy the **Forwarding** URL that appears (e.g., the one above).
3. **Verify the tunnel**:
   ```powershell
   Invoke-WebRequest -Uri 'https://unprovided-patternless-ignacio.ngrok-free.dev/v1/healthz' -UseBasicParsing
   ```
   You should see a JSON `{"status":"ok"}` and a `200` status code.
4. **Run the official judge locally** (optional, you already did this):
   ```powershell
   $env:BOT_URL="https://unprovided-patternless-ignacio.ngrok-free.dev"
   python judge_simulator.py
   ```
   All scenarios (`warmup`, `auto_reply`, `intent`, `hostile`) should pass.
5. **Submit** the **base ngrok URL** (no trailing path) on the Magicpin submission page together with this README.

> **IMPORTANT:** Keep *both* terminals (FastAPI server and ngrok) running for the entire duration of the judge’s evaluation. If either process stops, the URL goes offline and the judge will fail.

## Running Locally (without ngrok)
If you only want to test on your machine:
```bash
# Activate env
source .venv/bin/activate   # Linux/macOS
#.\.venv\Scripts\activate   # Windows PowerShell

# Install deps
pip install -r requirements.txt
uvicorn bot:app --port 8080
```
