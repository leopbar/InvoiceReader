EXTRACTION_PROMPT = """
You are an expert invoice data extraction AI. Analyze the following invoice content and extract ALL relevant data.

Review the following invoice content carefully. Extract supplier details, invoice metadata (number, dates, currency), billing/shipping addresses, all line items with their quantities and prices, and final totals.

If any field is not found in the invoice, leave it null.
For dates, always convert to YYYY-MM-DD format.
For monetary values, use numbers without currency symbols.
"""

TARGETED_RETRY_TEMPLATE = """
The previous extraction was mostly correct but the following fields were missing or invalid:
{failed_fields_list}

Review the relevant section of the document below and return ONLY a JSON object
containing corrections for those specific fields. Do not repeat fields that were
already extracted correctly.

Document excerpt (most relevant section):
{document_excerpt}
"""

def build_targeted_retry_prompt(failed_fields: list, document_excerpt: str) -> str:
    failed_fields_list = "\n".join([f"- {field}" for field in failed_fields])
    return TARGETED_RETRY_TEMPLATE.format(
        failed_fields_list=failed_fields_list,
        document_excerpt=document_excerpt
    )
