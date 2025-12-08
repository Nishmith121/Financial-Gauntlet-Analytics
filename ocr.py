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

