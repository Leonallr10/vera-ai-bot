import os
import time
from datetime import datetime
from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import Any, Optional, List
from prompts import generate_message, generate_reply

app = FastAPI()
START = time.time()

# In-memory stores (use Redis/SQLite for production-grade)
contexts: dict = {}    # (scope, context_id) -> {version, payload}
conversations: dict = {}           # conversation_id -> [turns]


@app.get("/v1/healthz")
async def healthz():
    counts = {"category": 0, "merchant": 0, "customer": 0, "trigger": 0}
    for (scope, _), _ in contexts.items():
        if scope in counts:
            counts[scope] += 1
    return {"status": "ok", "uptime_seconds": int(time.time() - START), "contexts_loaded": counts}


@app.get("/v1/metadata")
async def metadata():
    return {
        "team_name": "Antigravity", 
        "team_members": ["Antigravity AI"], 
        "model": "gemini-2.5-flash",
        "approach": "FastAPI with Gemini 2.5 Flash for proactive context-aware generation and reactive conversation handling.", 
        "contact_email": "hello@example.com",
        "version": "1.0.0", 
        "submitted_at": datetime.utcnow().isoformat() + "Z"
    }


class CtxBody(BaseModel):
    scope: str
    context_id: str
    version: int
    payload: dict[str, Any]
    delivered_at: str

@app.post("/v1/context")
async def push_context(body: CtxBody):
    key = (body.scope, body.context_id)
    cur = contexts.get(key)
    if cur and cur["version"] >= body.version:
        return {"accepted": False, "reason": "stale_version", "current_version": cur["version"]}
    contexts[key] = {"version": body.version, "payload": body.payload}
    return {"accepted": True, "ack_id": f"ack_{body.context_id}_v{body.version}",
            "stored_at": datetime.utcnow().isoformat() + "Z"}


class TickBody(BaseModel):
    now: str
    available_triggers: List[str] = []

@app.post("/v1/tick")
async def tick(body: TickBody):
    actions = []
    for trg_id in body.available_triggers:
        trg = contexts.get(("trigger", trg_id), {}).get("payload")
        if not trg: continue
        
        merchant_id = trg.get("merchant_id")
        merchant = contexts.get(("merchant", merchant_id), {}).get("payload")
        if not merchant: continue
            
        category = contexts.get(("category", merchant.get("category_slug")), {}).get("payload")
        
        customer = None
        customer_id = trg.get("customer_id")
        if customer_id:
            customer = contexts.get(("customer", customer_id), {}).get("payload")
            
        if not (merchant and category): continue
        
        # Call the composer from prompts.py
        llm_response = generate_message(category, merchant, trg, customer)
        
        actions.append({
            "conversation_id": f"conv_{merchant_id}_{trg_id}",
            "merchant_id": merchant_id, 
            "customer_id": customer_id,
            "send_as": llm_response.get("send_as", "vera"), 
            "trigger_id": trg_id,
            "template_name": "vera_generic_v1",
            "template_params": [merchant.get('identity', {}).get('name', 'Merchant')],
            "body": llm_response.get("body", ""), 
            "cta": llm_response.get("cta", "open_ended"),
            "suppression_key": llm_response.get("suppression_key", trg.get("suppression_key", "")),
            "rationale": llm_response.get("rationale", "Composed from context")
        })
    return {"actions": actions}


class ReplyBody(BaseModel):
    conversation_id: str
    merchant_id: Optional[str] = None
    customer_id: Optional[str] = None
    from_role: str
    message: str
    received_at: str
    turn_number: int

@app.post("/v1/reply")
async def reply(body: ReplyBody):
    # Retrieve conversation history
    conv_history = conversations.setdefault(body.conversation_id, [])
    conv_history.append({"from": body.from_role, "msg": body.message})
    
    # Generate reply using LLM
    llm_reply = generate_reply(conv_history, body.message)
    
    # If the action is send, record our reply
    if llm_reply.get("action") == "send":
        conv_history.append({"from": "vera", "msg": llm_reply.get("body", "")})
    
    return {
        "action": llm_reply.get("action", "wait"), 
        "body": llm_reply.get("body", ""), 
        "cta": llm_reply.get("cta", "none"),
        "rationale": llm_reply.get("rationale", "")
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
