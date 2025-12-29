import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

MAX_BOUND = Decimal('999999999.99')

def clean_dec(val) -> Decimal:
    """Robustly converts any value to a Decimal for financial-grade math."""
    try:
        cleaned = re.sub(r'[^\d.-]', '', str(val))
        return Decimal(cleaned) if cleaned and cleaned not in ('.', '-') else Decimal('0')
    except InvalidOperation:
        return Decimal('0')

def validate_line_items(extracted_data: dict) -> dict:
    doc_type = extracted_data.get("type", "unknown")
    records: list = extracted_data.get("data", [])
    vendor_or_entity_name = str(extracted_data.get("vendor_or_entity_name", "N/A"))
    grand_total = clean_dec(extracted_data.get("grand_total", 0.0))

    valid_records = []
    anomalies = []

    if grand_total > MAX_BOUND:
        anomalies.append({
             "description": "Document Total",
             "errors": [f"Boundary Exceeded / OCR Parsing Error: grand_total {grand_total} exceeds 999,999,999.99 limit."]
        })
        grand_total = Decimal('0')

    if not records:
        return {"doc_type": doc_type, "status": "FAIL", "valid_records": [], "anomalies": anomalies, "accuracy_score": 0.0}

    # 1. SMART ANOMALY: Missing Context Rule
    if not vendor_or_entity_name or vendor_or_entity_name.lower() in ["n/a", "none", "null", "missing"]:
        anomalies.append({
             "description": "Document Context",
             "errors": ["Missing Context Anomaly: vendor_or_entity_name is 'N/A' or missing. Anonymous financial documents represent a critical compliance risk."]
        })

    # 2. SMART ANOMALY: Duplicate Detection Rule
