import os
import mimetypes
import json
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from enum import Enum

class DocType(str, Enum):
    INVOICE = "invoice"
    TAX_1040 = "tax_1040"
    INSURANCE_CLAIM = "insurance_claim"
    BANK_STATEMENT = "bank_statement"
    UNKNOWN = "unknown"

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

class LineItem(BaseModel):
    extraction_reasoning: str = Field(description="Step-by-step logic detailing how this record was extracted.")
    description: str | None = None
    qty: float | None = None
    price: float | None = None
    discount: float | None = None
    total: float | None = None
    wages: float | None = None
    interest: float | None = None
    dividends: float | None = None
    total_income: float | None = None
    claim_amount: float | None = None
    deductible: float | None = None
    covered_amount: float | None = None

class FinancialDocument(BaseModel):
    extraction_reasoning: str = Field(description="Overall reasoning for document classification and data location.")
    vendor_or_entity_name: str | None = Field(description="The name of the vendor, business, or person on the document. Return 'N/A' if missing.")
    grand_total: float | None = Field(description="The final total amount of the document.")
    document_type: DocType = Field(description="Must be one of the explicitly defined document types.", default=DocType.UNKNOWN)
    raw_text: str = Field(description="The full extracted text of the document")
    records: list[LineItem] = Field(description="Structured records extracted from the document.")

def extract_financial_data(file):
    filename = file.name.lower()
    mime_type, _ = mimetypes.guess_type(filename)
    if not mime_type:
        mime_type = "application/pdf" if filename.endswith(".pdf") else "text/plain"
        
    file_bytes = file.read()
    part = types.Part.from_bytes(data=file_bytes, mime_type=mime_type)
    
    system_instruction = (
        "You are an expert Document Intelligence API. "
        "Extract all structured financial data linearly from the document. "
        "Before extracting the final numerical values, use the 'extraction_reasoning' field to explain your step-by-step logic. "
        "Locate the item, identify the raw string, explain any discounts applied, and state the final calculation. "
        "Classify the document exactly as 'invoice', 'tax_1040', 'insurance_claim', or 'logs'. "
        "Extract the raw text. "
        "For 'records', construct a list of JSON objects representing table rows or logical line items. "
        "For invoices, include description, qty, price, discount, and total. "
        "For tax_1040, include wages, interest, dividends, and total_income. "
        "For insurance_claim, include claim_amount, deductible, and covered_amount."
    )
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[part],
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=FinancialDocument,
                temperature=0.1,
            ),
        )
        
        parsed = json.loads(response.text)
        
        doc_type_val = parsed.get("document_type", "unknown")
        # Ensure it falls back safely if the model hallucinated something outside the Enum
        if doc_type_val not in [e.value for e in DocType]:
            doc_type_val = DocType.UNKNOWN.value

        result = {
            "type": doc_type_val,
            "vendor_or_entity_name": parsed.get("vendor_or_entity_name", "N/A"),
            "grand_total": parsed.get("grand_total", 0.0),
            "text": parsed.get("raw_text", ""),
            "data": parsed.get("records", []),
            "extraction_reasoning": parsed.get("extraction_reasoning", "")
        }
        
        # High-risk warning tag mapping for the UI
        if doc_type_val == DocType.UNKNOWN.value:
             result["high_risk_warning"] = "CRITICAL: AI failed to classify this document. Manual Review required. Pipeline will skip math validation."

        return result
    except Exception as e:
        return {
            "type": "error",
            "text": str(e),
            "data": []
        }