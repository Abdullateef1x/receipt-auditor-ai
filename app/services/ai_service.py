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
