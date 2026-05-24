import json
from groq import Groq
client = Groq()

def ai_extraction(text: str):
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
        response_format={
            "type": "json_object",
        },
        temperature=0.0
    )
    
    raw_response = completion.choices[0].message.content

    try:
         parsed = completion.choices[0].message.content
         return parsed.model_dump()
    except Exception as e:
        return ValueError(F"LLM returned invalid structure: {e}\nRaw: {raw_response}")


def analyze_anomalies(extracted_data: dict, policy_context: list[str]) -> dict:
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
    return json.loads(raw)