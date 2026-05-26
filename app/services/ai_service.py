import json
import os
from groq import Groq

def get_client():
    return Groq(api_key=os.getenv("GROQ_API_KEY"))

def ai_extraction(text: str) -> dict:
    client = get_client()
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": """You are an expert at extracting structured invoice data.
Always respond with valid JSON matching this exact structure:
{
  "vendor_name": string or null,
  "invoice_number": string or null,
  "date": string (YYYY-MM-DD) or null,
  "total_amount": number or null,
  "currency": string (e.g. "USD") or null,
  "tax": number or null,
  "payment_method": string or null,
  "line_items": [{"description": string, "quantity": number, "unit_price": number, "total": number}] or []
}
Return only the JSON object. No explanation, no markdown, no extra text."""
            },
            {
                "role": "user",
                "content": f"Extract the required fields from this text:\n\n{text}"
            }
        ],
        response_format={"type": "json_object"},
        temperature=0.0
    )

    raw_response = completion.choices[0].message.content

    if not raw_response:                                       # ← guard here, before the try
        raise ValueError("Groq returned an empty response")

    try:
        parsed = json.loads(raw_response)                      # ✅ Pylance now knows it's str
        if not isinstance(parsed, dict):
            raise ValueError(f"Expected dict, got {type(parsed)}")
        return parsed
    except Exception as e:
        raise ValueError(f"LLM returned invalid structure: {e}\nRaw: {raw_response}")
    
def analyze_anomalies(extracted_data: dict, policy_context: list[str]) -> dict:
    client = get_client()
    policy_text = "\n\n".join(policy_context) if policy_context else "No policy context available."
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": """You are a financial compliance auditor. 
You will be given an extracted invoice and relevant company expense policies.
Analyze the invoice for policy violations or anomalies and respond with JSON in this exact structure:
{
  "status": "approved" | "flagged" | "rejected",
  "anomalies": [{"field": string, "issue": string, "severity": "low" | "medium" | "high"}],
  "recommendation": string,
  "confidence": number (0.0 to 1.0)
}
If no anomalies are found, return an empty list for anomalies and status "approved"."""
            },
            {
                "role": "user",
                "content": f"""Company expense policy:
{policy_text}

Extracted invoice data:
{json.dumps(extracted_data, indent=2)}

Analyze this invoice against the policy and return your findings."""
            }
        ],
        response_format={"type": "json_object"},
        temperature=0.0
    )

    raw = completion.choices[0].message.content

    if not raw:
        raise ValueError("Groq returned an empty response")

    return json.loads(raw)