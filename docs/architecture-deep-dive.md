# Why AI Alone Isn't Enough: Combining Deterministic Validation with LLM-Based Expense Auditing

AI can extract information from receipts, interpret expense policies, and identify potential anomalies. But should an application rely on an AI model to perform every part of a financial audit?

I don't think it should.

Some auditing tasks require interpretation. Others involve rules that can be expressed precisely in code. Treating both as AI problems introduces unnecessary uncertainty into a system that needs predictable behaviour.

While building **Receipt Auditor AI**, I explored an approach that combines large language models (LLMs) with deterministic validation. The application uses AI to extract receipt information and interpret policy requirements, while Python handles arithmetic checks that can be verified programmatically.

This article examines that architecture, why I chose it, and some limitations I encountered.

## 1. The problem with relying entirely on AI

Receipts are unstructured documents. Their layouts differ, field names are inconsistent, and important information may appear in unexpected places.

An LLM can help extract fields such as:

- Vendor name
- Transaction date
- Line items
- Tax amount
- Reported total

It can also interpret expense policies written in natural language.

However, there is a distinction between interpreting information and verifying a mathematical relationship.

Consider a receipt containing:

| Description | Amount |
|---|---:|
| Accommodation | $120 |
| Transportation | $30 |
| Meals | $50 |
| Tax | $10 |
| **Reported total** | **$210** |

The line items and tax add up to $210.

If the reported total were $220 instead, the application wouldn't need an LLM to decide whether the arithmetic is consistent. It could calculate the expected amount and compare it with the reported total.

This is an important architectural distinction:

- **Interpretation:** Understanding what a receipt says or what an expense policy means.
- **Verification:** Checking whether values satisfy a known rule.

The first can benefit from AI. The second is often better handled by deterministic code.

## 2. Using deterministic validation for financial checks

In Receipt Auditor AI, I implemented a Python validation function called `validate_amounts()`.

Its responsibility is to check relationships between extracted receipt amounts.

The function considers:

1. The sum of the line-item amounts.
2. Whether tax is included in the reported total.
3. Whether a tax amount is available when tax is not included.
4. Whether the calculated amount matches the reported total.

For example, if tax is not included in the line-item amounts, the expected total is:

\[
\text{Expected Total} = \sum \text{Line Items} + \text{Tax}
\]

The application compares this calculated value with the reported total.

When tax is already included in the line-item amounts, the application compares their sum directly with the reported total instead of adding tax again. This distinction prevents the validation logic from counting tax twice.

A difference greater than $0.01 between the calculated amount and the reported total produces a validation anomaly, provided the information required for the comparison is available.

The implementation also accounts for uncertainty around tax inclusion. If the extracted information says tax inclusion is unknown, the function records an anomaly rather than assuming that tax should be added.

This matters because the application should not silently make assumptions about information it hasn't established.

### Why this matters

Deterministic validation has a useful property: given the same valid inputs, the same rules produce the same result.

An LLM can produce different interpretations of similar inputs. A Python arithmetic check does not need to interpret the receipt again to determine whether two amounts match.

There are, however, limitations in my implementation.

If the receipt has no line items or no reported total, the arithmetic check is skipped. The validation function also does not establish that the extracted values themselves are correct. It operates on the information provided to it.

That distinction is important: **a correct calculation using incorrectly extracted values can still produce an incorrect audit result.**

## 3. Using an LLM for receipt extraction

Before deterministic validation can happen, the application needs structured information from the receipt.

Receipt Auditor AI uses a language model accessed through Groq to extract relevant fields from uploaded PDF receipts.

The model is instructed to return structured JSON containing receipt information.

This is useful because receipts do not follow one universal format. A vendor might label a field `Amount Due`, while another uses `Total`, `Grand Total`, or something similar.

Rather than writing separate extraction rules for every possible layout, the application uses an LLM to interpret the document and identify the relevant information.

The extracted data is then passed to the validation stage.

This creates a separation of responsibilities:

- The model interprets the document.
- Python checks the extracted financial relationships.

There is still a reliability concern here. The application parses the model's JSON response, but it does not yet perform comprehensive schema validation on every extracted field.

A model returning valid JSON does not necessarily mean that every field has the expected type, format, or meaning.

A stronger implementation would validate the extracted response against a defined schema before allowing it into the financial validation stage.

For example, it could reject malformed monetary values, normalize dates, and distinguish missing fields from invalid values.

## 4. Retrieving relevant expense policies with ChromaDB

Financial arithmetic is only one part of an expense audit. An expense can be mathematically correct and still violate an organization's policy.

For example, a receipt might contain a valid accommodation charge, but the organization's policy could restrict the amount an employee may claim.

This introduces a different problem: the application needs to compare receipt information against policy documents written in natural language.

I used ChromaDB to store and retrieve policy information.

When a policy PDF is uploaded, the application:

1. Processes the document.
2. Splits its extracted text into smaller chunks.
3. Stores those chunks in ChromaDB.
4. Retrieves relevant chunks when an expense is audited.

The current chunking implementation uses a chunk size of 500 characters with an overlap of 50 characters.

During an audit, the application constructs a query using the vendor name:

`expense policy for {vendor_name}`

It then retrieves up to three relevant chunks to provide policy context for the next stage.

This is a relatively simple retrieval pipeline. It gives the model selected portions of the policy instead of requiring it to interpret the entire document for every receipt.

However, the retrieval strategy has limitations.

The query relies primarily on the vendor name. It does not explicitly incorporate other useful details such as expense category, amount, or transaction context.

Consequently, the retrieved chunks may not always contain the most relevant policy requirements.

A possible improvement would be to construct richer queries using extracted receipt information and evaluate retrieval quality against a collection of representative expense scenarios.

## 5. Combining deterministic results with AI-based anomaly analysis

Once receipt extraction, arithmetic validation, and policy retrieval are complete, the application sends the relevant information to the LLM for anomaly analysis.

The model receives receipt information alongside the retrieved policy context.

Its instructions include distinguishing missing information from confirmed policy violations. It is also instructed not to treat the absence of approval evidence as automatic proof of a violation.

The model is expected to return a structured result containing:

- An audit status.
- A confidence value.
- Anomalies identified.
- A recommendation.

The application then combines the AI-generated findings with the deterministic validation results.

This is an important part of the architecture.

If deterministic validation identifies an anomaly, the application changes the overall status to `flagged`. It can also adjust the recommendation when the validation concerns the reported total, tax, or tax inclusion.

In other words, the model does not get the final say over every aspect of the audit.

The application retains responsibility for enforcing the checks that it can verify directly.

The resulting workflow looks like this:

**Receipt PDF → AI extraction → Deterministic validation → Policy retrieval → AI anomaly analysis → Result merging → PDF report**

The separation makes the responsibilities of each stage easier to reason about.

It also creates a clearer path for debugging. If a financial discrepancy is missed, I can investigate the extracted values and arithmetic validation separately from the model's policy interpretation.

## 6. Where the current implementation can improve

Combining deterministic logic with AI does not automatically make an application reliable. The boundaries between the components need to be designed carefully.

There are several areas I would improve in Receipt Auditor AI.

### Validate model output against explicit schemas

The application parses JSON returned by the model, but parsing alone does not guarantee that the response follows the expected data structure.

I would introduce explicit schema validation for both extraction and anomaly-analysis results.

This would make it easier to reject malformed responses and handle missing or incorrectly typed fields.

### Improve policy retrieval

The current retrieval query is based on the vendor name.

A richer query could incorporate the expense category, amount, and other relevant receipt details.

I would also evaluate retrieval quality to determine whether the returned chunks actually contain the policy rules needed for a given audit.

### Make uncertain outcomes more explicit

A model's confidence value should not be treated as proof that an audit result is correct.

The application should distinguish between confirmed arithmetic discrepancies, possible policy violations, and cases where insufficient information prevents a reliable conclusion.

### Reconsider synchronous processing

The current receipt-processing pipeline runs within the request rather than being delegated to a background worker.

For larger documents or slower model responses, this could lead to long-running requests.

A background-processing architecture could allow the API to return a processing status immediately while the audit continues separately.

These improvements would make the system more robust, but they also reinforce the original design principle: every stage should have a clearly defined responsibility.

## 7. Lessons from building the application

One of the most useful lessons from building Receipt Auditor AI was that adding an LLM does not remove the need for conventional software engineering.

The application still needs input validation, error handling, data storage, predictable business rules, and clear boundaries between components.

More importantly, not every problem should be solved with AI.

If a rule can be expressed as a mathematical relationship or a well-defined condition, deterministic code is often easier to test and reason about.

If a task requires interpreting unstructured documents or comparing natural-language information, an LLM may provide useful capabilities.

The engineering challenge is deciding where each approach belongs.

For Receipt Auditor AI, that meant using AI to interpret receipts and expense policies while keeping arithmetic validation in Python.

The result is not a fully autonomous or infallible auditing system. It is an application that combines two different approaches, each responsible for the tasks it is better suited to handle.

And that, ultimately, is the principle I would carry into other AI-powered applications: **don't use AI to replace deterministic logic when deterministic logic is the better tool for the job.**