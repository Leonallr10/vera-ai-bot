import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# We will initialize the client here
API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY) if API_KEY else None

SYSTEM_INSTRUCTION = """You are Vera, an AI merchant assistant for magicpin. Your job is to compose a WhatsApp message to a merchant.
You will be provided with four layers of context:
1. Category Context: Defines the business category, voice, allowed terms, and current trends.
2. Merchant Context: Specific details about the merchant, their performance, active offers, and history.
3. Trigger Context: The event that prompted this message.
4. Customer Context (Optional): The customer being targeted, if this is on behalf of the merchant.

Your task is to write a single composed message that scores a 10/10 on the following criteria:
- Specificity: Anchor on concrete, verifiable facts from the contexts (numbers, dates, headlines). NO generic "10% off" if service+price exists. NO hallucinated numbers.
- Category Fit: Match the voice/tone from the Category Context (e.g. clinical for dentists, NOT promotional).
- Merchant Fit: Personalize to this specific merchant's stats, offers, and language preference (e.g. Hindi-English mix if requested).
- Trigger Relevance: Explicitly communicate the trigger (the "why now").
- Engagement Compulsion: Use one of: curiosity, social proof, loss aversion, effort externalization, single-binary CTA (YES/STOP) or a simple open-ended question.

Output your response strictly as JSON with the following schema:
{
  "body": "The actual text of the WhatsApp message you compose",
  "cta": "The call to action type: 'open_ended', 'binary', or 'none'",
  "send_as": "'vera' if talking to merchant, or 'merchant_on_behalf' if customer context is provided",
  "rationale": "A short 1-2 sentence explanation of why this message fits the 5 evaluation criteria."
}

CRITICAL RULES:
- If the trigger is external (news/research), cite the source.
- If the merchant has a specific offer, use that specific offer (e.g. "Dental Cleaning @ 299").
- Never make up data, numbers, or facts.
- Your output must be parseable JSON. Do not include markdown codeblocks (e.g., ```json) around your output, output only the JSON object.
"""

def generate_message(category, merchant, trigger, customer=None):
    if not client:
        # Fallback if no API key is provided
        return {
            "body": f"Hi {merchant['identity']['name']}, this is a mock message. Setup GEMINI_API_KEY.",
            "cta": "open_ended",
            "send_as": "vera",
            "rationale": "Fallback message."
        }
    
    prompt = {
        "category_context": category,
        "merchant_context": merchant,
        "trigger_context": trigger,
        "customer_context": customer
    }
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=json.dumps(prompt, indent=2),
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.0,
                response_mime_type="application/json",
            ),
        )
        result = json.loads(response.text)
        # Add suppression key manually
        result["suppression_key"] = trigger.get("suppression_key", "")
        return result
    except Exception as e:
        print(f"Error generating message: {e}")
        return {
            "body": "Sorry, an error occurred while generating the message.",
            "cta": "none",
            "send_as": "vera",
            "suppression_key": trigger.get("suppression_key", ""),
            "rationale": str(e)
        }

def generate_reply(conversation_history, merchant_message):
    if not client:
        return {
            "action": "send",
            "body": "Mock reply. Setup GEMINI_API_KEY.",
            "cta": "open_ended",
            "rationale": "Fallback reply."
        }
    
    # We will build a multi-turn prompt
    prompt = {
        "instruction": "You are Vera, responding to a merchant's message. Analyze the conversation history and the latest merchant message.",
        "conversation_history": conversation_history,
        "latest_merchant_message": merchant_message,
        "rules": [
            "If the merchant's message is an auto-reply (e.g. automated assistant, thank you for contacting us) and repeated, return action 'end'.",
            "If the merchant shows explicit intent to proceed (e.g. 'Yes', 'ok let's do it'), return action 'send' and advance to the next step, don't ask more qualifying questions.",
            "If the merchant asks for time, return action 'wait'.",
            "Output JSON only with keys: action ('send', 'wait', 'end'), body (string), cta (string), rationale (string)."
        ]
    }
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=json.dumps(prompt, indent=2),
            config=types.GenerateContentConfig(
                temperature=0.0,
                response_mime_type="application/json",
            ),
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"Error generating reply: {e}")
        return {
            "action": "end",
            "body": "",
            "cta": "none",
            "rationale": str(e)
        }
