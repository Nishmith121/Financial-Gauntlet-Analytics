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
