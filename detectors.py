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
    
    # 1. arithmetic_error
    for inv_no, inv in invoices.items():
        calc_sub = sum(i["amount"] for i in inv["items"])
        if abs(calc_sub - inv["subtotal"]) > 1.0:
            add_finding("arithmetic_error", [inv["page"]], [inv_no], "Subtotal mismatch", inv["subtotal"], calc_sub)
        
        for idx, item in enumerate(inv["items"]):
            if abs(item["qty"] * item["rate"] - item["amount"]) > 1.0:
                add_finding("arithmetic_error", [inv["page"]], [inv_no], f"Line item {idx+1} mismatch", item["amount"], round(item["qty"] * item["rate"], 2))

        calc_gt = inv["subtotal"] + inv.get("cgst", 0) + inv.get("sgst", 0)
        if abs(calc_gt - inv["grand_total"]) > 1.0:
            add_finding("arithmetic_error", [inv["page"]], [inv_no], "Grand total mismatch", inv["grand_total"], calc_gt)

    # 2. billing_typo
