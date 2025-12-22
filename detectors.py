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
    for inv_no, inv in invoices.items():
        for idx, item in enumerate(inv["items"]):
            # 0.15 hrs logic: usually someone puts 0.15 (15 mins) but mathematically it should be 0.25 hrs
            # We see if rate * 0.25 == amount but qty says 0.15
            if abs(item["qty"] - 0.15) < 0.01 and abs(item["rate"] * 0.25 - item["amount"]) < 1.0:
                add_finding("billing_typo", [inv["page"]], [inv_no], "Time typo 0.15 mins instead of 0.25 hrs", 0.15, 0.25)
            # Or vice versa? The prompt: "Hours logged as 0.15 (decimal) when it means 0:15 = 0.25 hrs. The rate x wrong qty gives wrong amount"
            elif item["unit"].lower() in ['hr', 'hrs']:
                # Maybe they wrote qty as 1.15 for 1 hr 15 mins which is 1.25.
                dec = item["qty"] % 1
                if abs(dec - 0.15) < 0.01 and abs(item["qty"] * item["rate"] - item["amount"]) < 1.0: # Means the calculation used the raw .15
                    corr_qty = item["qty"] - 0.15 + 0.25
                    add_finding("billing_typo", [inv["page"]], [inv_no], f"Time typo", item["qty"], corr_qty)
                elif abs(dec - 0.30) < 0.01:
                    corr_qty = item["qty"] - 0.30 + 0.50
                    if abs(item["qty"] * item["rate"] - item["amount"]) < 1.0:
                        add_finding("billing_typo", [inv["page"]], [inv_no], f"Time typo", item["qty"], corr_qty)
                elif abs(dec - 0.45) < 0.01:
                    corr_qty = item["qty"] - 0.45 + 0.75
                    if abs(item["qty"] * item["rate"] - item["amount"]) < 1.0:
                        add_finding("billing_typo", [inv["page"]], [inv_no], f"Time typo", item["qty"], corr_qty)

    # 3. duplicate_line_item
    for inv_no, inv in invoices.items():
        seen = set()
        for idx, item in enumerate(inv["items"]):
            k = (item["desc"], item["qty"], item["rate"])
            if k in seen:
                add_finding("duplicate_line_item", [inv["page"]], [inv_no], "Duplicate line item", item["amount"], 0)
            seen.add(k)

    # 4. invalid_date
    for inv_no, inv in invoices.items():
        if inv["date"] and not is_valid_date(inv["date"]):
            add_finding("invalid_date", [inv["page"]], [inv_no], "Invalid date", inv["date"], "valid_date")
    for po_no, po in pos.items():
        if po.get("date") and not is_valid_date(po["date"]):
            add_finding("invalid_date", [po["page"]], [po_no], "Invalid PO date", po["date"], "valid_date")

    # 5. wrong_tax_rate (Skip for now unless we know HSN rates)

    # ==========================
    # MEDIUM TIER
    # ==========================

    # 6. po_invoice_mismatch
    for inv_no, inv in invoices.items():
        if inv.get("po_ref") and inv["po_ref"] in pos:
            po = pos[inv["po_ref"]]
            # Simple check if an invoice item rate doesn't match PO rate for same desc
            po_items = {i["desc"]: i for i in po["items"]}
            inv_items = {i["desc"]: i for i in inv["items"]}
            for desc, item in inv_items.items():
                if desc in po_items:
                    if abs(item["rate"] - po_items[desc]["rate"]) > 0.01:
                        add_finding("po_invoice_mismatch", [inv["page"], po["page"]], [inv_no, po["po_no"]], "Rate mismatch", item["rate"], po_items[desc]["rate"])
                    # Check qty mismatch only if entire PO is billed in one go? Usually qty may differ if partial billing
                    # Let's check rate mostly

    # 7. vendor_name_typo
    for inv_no, inv in invoices.items():
        if inv.get("vendor_name"):
            # If not exact match but is very close (typo)
            # Real fuzzy match using SequenceMatcher
            from difflib import SequenceMatcher
            best_match = None
            best_score = 0
            for vname in vendors:
                score = SequenceMatcher(None, inv["vendor_name"].lower(), vname.lower()).ratio()
                if score > best_score:
                    best_score = score
                    best_match = vname
            if best_score < 1.0 and best_score > 0.8:
                add_finding("vendor_name_typo", [inv["page"]], [inv_no], "Vendor name typo", inv["vendor_name"], best_match)

    # 8. double_payment
    seen_payments = {}
    for bs_id, bs in bank_statements.items():
        for tr in bs["transactions"]:
            if tr["debit"] > 0:
                k = (tr["desc"], tr["debit"])
                if k in seen_payments:
                    prev_bs_id, prev_pg = seen_payments[k]
                    # Same payment twice?
                    if prev_bs_id != bs_id:
                        add_finding("double_payment", [bs["page"], prev_pg], [bs_id, prev_bs_id], "Double payment", tr["debit"], 0)
                seen_payments[k] = (bs_id, bs["page"])

    # 9. ifsc_mismatch
    for inv_no, inv in invoices.items():
