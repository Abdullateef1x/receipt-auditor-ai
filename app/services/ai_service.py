import json
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

def get_client():
    return Groq(api_key=os.getenv("GROQ_API_KEY"))

def ai_extraction(text: str) -> dict:
    client = get_client()
    completion = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": """You are an expert at extracting structured invoice data.
Always respond with valid JSON matching this exact structure:
{
    "vendor_name": null,
    "invoice_number": null,
    "date": null,
    "total_amount": null,
    "currency": null,
    "tax": null,
    "tax_included": null,
    "payment_method": null,
    "expense_category": null,
    "business_purpose": null,
    "attendees": [],
    "approval_reference": null,
    "line_items": [
        {
            "description": "",
            "quantity": 0,
            "unit_price": 0,
            "total": 0
        }
    ]
}

For expense_category, identify the most appropriate category
based on the receipt. Examples include meals, travel,
transportation, office_supplies, accommodation,
client_entertainment, software, equipment, other, and unknown.

- Determine whether tax is already included in the line-item
  totals only when the receipt explicitly provides enough
  information.
- Return true if tax is included.
- Return false if tax is separate and excluded.
- Return null if this cannot be determined.
- Never guess.

If the expense category cannot be determined from the
available information, return "unknown".

Extract business_purpose and attendees only when explicitly
provided in the receipt.

If no approval reference or approval statement appears on the
receipt, return null. Do not interpret null as proof that
approval was never granted.

If information is absent, return null for scalar fields
and [] for attendees or line_items.

Never return placeholder line items. If no line items
are found, return an empty array.

Never invent missing information.

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
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": """You are a financial compliance auditor.

You will receive extracted invoice data and relevant company
expense policies.

Your task is to evaluate the expense against ALL applicable
policy requirements.

Follow these rules:

1. POLICY COMPLIANCE
- Identify every applicable policy rule.
- Compare the extracted expense data against those rules.
- Do not invent policy requirements that are not present
  in the supplied policy context.
- Do not ignore relevant approval thresholds.

2. APPROVAL VERIFICATION
- Check whether the expense requires prior approval.
- Check whether approval evidence is present in the
  extracted invoice data.
- A null approval_reference means no approval evidence
  was found on the receipt.
- It does NOT prove that approval was never obtained.
- Never automatically classify missing approval evidence
  as a confirmed policy violation.
- If approval cannot be verified, flag it as requiring
  verification.
- Do not flag an expense solely because approval_reference is null.
- First establish that an applicable policy rule requires
approval for that specific expense.
- If approval is not explicitly required by the available
policy context, do not create an approval anomaly.


3. MISSING INFORMATION
- Distinguish missing documentation from confirmed
  policy violations.
- Do not assume missing information means non-compliance.
- Request clarification when necessary.

4. EXPENSE CLASSIFICATION
- Consider both the expense category and business context.
- A meal involving external clients may also qualify as
  client entertainment.
- Apply all relevant policy requirements.

5. AUDIT STATUS
- approved: All applicable requirements are satisfied
  based on the available evidence.
- flagged: Information is missing, approval needs
  verification, or a potential policy issue requires review.
- rejected: There is sufficient evidence of a clear,
  material policy violation that warrants rejection
  under the supplied policy.

6. CONFIDENCE
- Return a confidence score between 0.0 and 1.0.
- Reduce confidence when important information is missing.
- Do not express certainty beyond the available evidence.

Return valid JSON using exactly this structure:
{
  "status": "approved",
  "anomalies": [
    {
      "field": "string",
      "issue": "string",
      "severity": "low"
    }
  ],
  "recommendation": "string",
  "confidence": 0.0
}

If no anomalies are found, return an empty anomalies array.

Return only the JSON object. No explanation or markdown."""
            },
            {
    "role": "user",
    "content": f"""Company expense policy:
{policy_text}

Extracted invoice data:
{json.dumps(extracted_data, indent=2)}

Analyze this invoice against the supplied policy.
Return your findings using the required JSON structure."""
}
        ],
        response_format={"type": "json_object"},
        temperature=0.0
    )

    raw = completion.choices[0].message.content

    if not raw:
        raise ValueError("Groq returned an empty response")

    return json.loads(raw)