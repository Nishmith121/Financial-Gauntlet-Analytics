import re
from datetime import datetime

def parse_date(date_str):
    try:
        if date_str:
            return datetime.strptime(date_str, "%d/%m/%Y")
    except:
        pass
    return None

def is_valid_date(date_str):
    if not date_str: return True
    try:
        datetime.strptime(date_str, "%d/%m/%Y")
        return True
    except:
        return False

def run_detectors(data):
    findings = []
    f_num = 1
    def add_finding(cat, pages, docs, desc, rep_val, corr_val):
        nonlocal f_num
        findings.append({
            "finding_id": f"F-{f_num:03d}",
            "category": cat,
            "pages": pages,
            "document_refs": docs,
            "description": desc,
            "reported_value": str(rep_val),
            "correct_value": str(corr_val)
        })
        f_num += 1

    vendors = data.get("vendors", {})
    invoices = data.get("invoices", {})
    pos = data.get("pos", {})
    bank_statements = data.get("bank_statements", {})
    expense_reports = data.get("expense_reports", {})

    # ==========================
    # EASY TIER
    # ==========================
    
# Finding ID format: F-XXX with zero padding
