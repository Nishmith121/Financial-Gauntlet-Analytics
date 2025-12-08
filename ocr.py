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

