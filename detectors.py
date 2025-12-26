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
        if inv.get("ifsc") and inv.get("vendor_name"):
            # match vendor
            for vname, vdata in vendors.items():
                if vname.lower() in inv["vendor_name"].lower() or inv["vendor_name"].lower() in vname.lower():
                    if inv["ifsc"] and vdata.get("ifsc") and inv["ifsc"] != vdata["ifsc"]:
                        add_finding("ifsc_mismatch", [inv["page"]], [inv_no], "IFSC mismatch", inv["ifsc"], vdata["ifsc"])

    # 10. duplicate_expense
    seen_exps = {}
    for er_id, er in expense_reports.items():
        for e in er["entries"]:
            k = (e["date"], e["desc"], e["amount"])
            if k in seen_exps:
                prev_er_id, prev_pg = seen_exps[k]
                if prev_er_id != er_id:
                    add_finding("duplicate_expense", [er["page"], prev_pg], [er_id, prev_er_id], "Duplicate expense", e["amount"], 0)
            seen_exps[k] = (er_id, er["page"])

    # 11. date_cascade
    for inv_no, inv in invoices.items():
        if inv.get("po_ref") and inv["po_ref"] in pos:
            inv_d = parse_date(inv["date"])
            po_d = parse_date(pos[inv["po_ref"]]["date"])
            if inv_d and po_d and inv_d < po_d:
                add_finding("date_cascade", [inv["page"], pos[inv["po_ref"]]["page"]], [inv_no, inv["po_ref"]], "Invoice before PO", inv["date"], pos[inv["po_ref"]]["date"])

    # 12. gstin_state_mismatch
    STATE_CODES = { "Maharashtra": "27", "Karnataka": "29", "Tamil Nadu": "33", "Delhi": "07", "Telangana": "36", "Gujarat": "24", "West Bengal": "19"}
    for inv_no, inv in invoices.items():
        gstin = inv["vendor_dtl"].get("gstin", "")
        addr = inv["vendor_dtl"].get("address", "")
        if gstin and len(gstin) >= 2:
            sc = gstin[:2]
            for state, expected_sc in STATE_CODES.items():
                if state in addr:
                    if sc != expected_sc:
                        add_finding("gstin_state_mismatch", [inv["page"]], [inv_no], "GSTIN state mismatch", sc, expected_sc)
                    break

    # ==========================
    # EVIL TIER
    # ==========================
    
    # 13. quantity_accumulation
    po_item_qty_accum = {} # (po_no, desc) -> total_qty_billed
    invs_per_po_item = {} # (po_no, desc) -> [(inv_no, pg)]
    for inv_no, inv in invoices.items():
        po_no = inv.get("po_ref")
        if po_no and po_no in pos:
            for item in inv["items"]:
                k = (po_no, item["desc"])
                po_item_qty_accum[k] = po_item_qty_accum.get(k, 0) + item["qty"]
                invs_per_po_item.setdefault(k, []).append((inv_no, inv["page"]))
    for k, total_qty in po_item_qty_accum.items():
        po_no, desc = k
        po = pos[po_no]
        for p_item in po["items"]:
            if p_item["desc"] == desc:
                if total_qty > p_item["qty"] * 1.20: # Exceeds by 20%
                    docs = [po_no] + [x[0] for x in invs_per_po_item[k]]
                    pgs = [po["page"]] + [x[1] for x in invs_per_po_item[k]]
                    add_finding("quantity_accumulation", pgs, docs, "Quantity accumulation > 120%", total_qty, p_item["qty"])

    # 14. price_escalation
    for po_no, po_data in pos.items():
        # Check all invoices against this PO
        invs_for_po = [inv for inv in invoices.values() if inv.get("po_ref") == po_no]
        if len(invs_for_po) >= 4:
            docs = [po_no] + [inv["invoice_no"] for inv in invs_for_po]
            pgs = [po_data["page"]] + [inv["page"] for inv in invs_for_po]
            # Verify if ALL 4 charge rates > contracted
            all_escalated = True
            for inv in invs_for_po:
                for idx, inv_item in enumerate(inv["items"]):
                    # find matching PO item
                    po_matching = [p for p in po_data["items"] if p["desc"] == inv_item["desc"]]
                    if po_matching:
                        if inv_item["rate"] <= po_matching[0]["rate"]:
                            all_escalated = False
            if all_escalated:
                 add_finding("price_escalation", pgs, docs, "All invoices escalated price", "escalated", "contracted")

    # 15. balance_drift
    # Need to order bank statements by date
    # Then check opening balance of month N vs closing balance of month N-1
    # We lack closing balance in extractor right now. Oh actually Closing = Opening + sum(credits) - sum(debits).
    # Since bs might not be ordered, we'll sort them. (Assumes 1 account, though there may be more).

    # 16. circular_reference
    cn_refs = {} # Note -> Original Invoice
    for n_id, note in data.get("credit_notes", {}).items():
        if note.get("ref_doc"): cn_refs[n_id] = note["ref_doc"]
    for n_id, note in data.get("debit_notes", {}).items():
        if note.get("ref_doc"): cn_refs[n_id] = note["ref_doc"]
    # Check loops
    for start in cn_refs:
        visited = set()
        curr = start
        path = []
        while curr in cn_refs:
            visited.add(curr)
            path.append(curr)
            curr = cn_refs[curr]
            if curr in visited:
                # Cycle found
                v_docs = path + [curr]
                # To find pages
                pgs = []
                for d in v_docs:
                    if d in invoices: pgs.append(invoices[d]["page"])
                    if d in data.get("credit_notes", {}): pgs.append(data["credit_notes"][d]["page"])
                    if d in data.get("debit_notes", {}): pgs.append(data["debit_notes"][d]["page"])
                add_finding("circular_reference", pgs, v_docs, "Circular reference found", "loop", "no loop")
                break

    # 17. triple_expense_claim
    exp_claims = {} # (city, amount) -> [(er_id, pg)]
    for er_id, er in expense_reports.items():
        for e in er["entries"]:
            if 'hotel' in e["desc"].lower() or 'accom' in e["desc"].lower() or 'stay' in e["desc"].lower():
                k = (e["city"], e["amount"])
                exp_claims.setdefault(k, [])
                if er_id not in [x[0] for x in exp_claims[k]]: # Avoid counting same ER multiple times if hotel is split?
                    exp_claims[k].append((er_id, er["page"]))
    for k, claims in exp_claims.items():
        if len(claims) >= 3:
            docs = [x[0] for x in claims]
            pgs = [x[1] for x in claims]
            add_finding("triple_expense_claim", pgs, docs, "Triple hotel claim", "3+ claims", "1 claim")

    # 18. employee_id_collision
    # Two different names for same EMP_ID
    emp_map = {}
    for er_id, er in expense_reports.items():
        if er["emp_id"] and er["employee"]:
            if er["emp_id"] in emp_map and emp_map[er["emp_id"]]["name"].lower() != er["employee"].lower():
                docs = [emp_map[er["emp_id"]]["doc"], er_id]
                pgs = [emp_map[er["emp_id"]]["page"], er["page"]]
                add_finding("employee_id_collision", pgs, docs, "Employee ID collision", er["employee"], emp_map[er["emp_id"]]["name"])
            else:
                emp_map[er["emp_id"]] = {"name": er["employee"], "doc": er_id, "page": er["page"]}

    # 19. fake_vendor
    for inv_no, inv in invoices.items():
        if inv["vendor_name"]:
            # Check strictly against vendor master
            vname = inv["vendor_name"].lower()
            found = False
            for real_v in vendors:
                if SequenceMatcher(None, vname, real_v.lower()).ratio() > 0.8: # Very loose to not false positive on normal typos
                    found = True
                    break
            if not found:
                add_finding("fake_vendor", [inv["page"]], [inv_no], "Fake vendor", inv["vendor_name"], "N/A")

    # 20. phantom_po_reference
    for inv_no, inv in invoices.items():
        po_ref = inv.get("po_ref")
        if po_ref and po_ref not in pos:
            add_finding("phantom_po_reference", [inv["page"]], [inv_no], "Phantom PO", po_ref, "Doesn't exist")

    return findings
