import pdfplumber
import re
import json
import os

def clean_amount(val):
    if not val or not isinstance(val, str): return 0.0
    cleaned = re.sub(r'[^\d.-]', '', val)
    try:
        return float(cleaned)
    except:
        return 0.0

def _parse_vendor_master(pdf):
    vendors = {}
    for pg_num in [2, 3]: # Pages 3 and 4 (0-indexed)
        page = pdf.pages[pg_num]
        tables = page.extract_tables()
        if not tables: continue
        
        for table in tables:
            headers = None
            for row in table:
                if not row or row[0] == '#' or row[1] == 'Vendor Name':
                    headers = row
                    continue
                if not row[1] or row[1].strip() == '':
                    continue
                
                try:
                    name = row[1].strip()
                    gstin = row[2].strip() if len(row) > 2 and row[2] else ""
                    state = row[3].strip() if len(row) > 3 and row[3] else ""
                    bank = row[4].strip() if len(row) > 4 and row[4] else ""
                    ifsc = row[5].strip() if len(row) > 5 and row[5] else ""
                    if len(row) == 5:
                        ifsc = row[4].strip()
                        bank = "" # Guessing Bank column might be merged or missing in some rows, let's just grab what we can. 
                        # Actually the table is: # | Vendor Name | GSTIN | State | Bank | IFSC
                except IndexError:
                    continue
                
                # Re-check based on sample: ['1', 'Tata Consultancy Services Ltd', '27DNNPH8645X2Z2', 'Maharashtra', 'HDFC Bank', 'HDFC08433393']
                # Sometimes headers might not be parsed perfectly.
                if len(row) >= 6:
                    vendors[name] = {
                        "name": name,
                        "gstin": row[2],
                        "state": row[3],
                        "bank": row[4],
                        "ifsc": row[5]
                    }
                elif len(row) == 5: # If bank/ifsc merged
                    parts = row[4].split()
                    ifsc = parts[-1] if parts else ""
                    vendors[name] = {"name": name, "gstin": row[2], "state": row[3], "ifsc": ifsc}
    return vendors

def extract_all(pdf_path):
    cache_file = "parsed_data_cache.json"
    if os.path.exists(cache_file):
        print("Loading from cache...")
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    print("Starting extraction...")
    with pdfplumber.open(pdf_path) as pdf:
        data = {
            "vendors": _parse_vendor_master(pdf),
            "invoices": {},
            "pos": {},
            "bank_statements": {},
            "expense_reports": {},
            "credit_notes": {},
            "debit_notes": {}
        }
        
        current_invoice = None
        
        for i, page in enumerate(pdf.pages[4:], start=4):
            text = page.extract_text() or ""
            if not text.strip(): continue
            first_line = text.strip().split('\n')[0].strip()
            
            # --- TAX INVOICE ---
            if 'TAX INVOICE' in first_line:
                if '(Continued)' not in first_line:
                    # New invoice
                    inv = {"page": i+1, "items": [], "subtotal": 0, "cgst": 0, "sgst": 0, "grand_total": 0, "po_ref": None, "vendor_name": None, "vendor_dtl": {}, "bill_to": {}, "date": None, "ifsc": None}
                    
                    # Regex extractions
                    doc_no = re.search(r'Invoice No:\s*(INV-\d{4}-\d+)', text)
                    if doc_no: inv["invoice_no"] = doc_no.group(1)
                    else: continue
                    
                    po_ref = re.search(r'PO Reference:\s*(PO-\d{4}-\d+)', text)
                    if po_ref: inv["po_ref"] = po_ref.group(1)
                    
                    date_m = re.search(r'Date:\s*([\d/]+)', text)
                    if date_m: inv["date"] = date_m.group(1)
                    
                    # Vendor details 
                    v_name = re.search(r'Name:\s*(.*?)\n', text[text.find('VENDOR DETAILS'):text.find('BILL TO')])
                    if v_name: inv["vendor_name"] = v_name.group(1).strip()
                    
                    v_gstin = re.search(r'GSTIN:\s*([A-Z0-9]+)', text[text.find('VENDOR DETAILS'):text.find('BILL TO')])
                    if v_gstin: inv["vendor_dtl"]["gstin"] = v_gstin.group(1).strip()
                    
                    v_addr = re.search(r'Address:\s*(.*?)\n', text[text.find('VENDOR DETAILS'):text.find('BILL TO')])
                    if v_addr: inv["vendor_dtl"]["address"] = v_addr.group(1).strip()
                    
                    ifsc = re.search(r'IFSC:\s*([A-Z0-9]+)', text[text.find('BANK DETAILS'):] if 'BANK DETAILS' in text else text)
                    if ifsc: inv["ifsc"] = ifsc.group(1).strip()
                    
                    current_invoice = inv
                    data["invoices"][inv["invoice_no"]] = current_invoice
                else:
                    # Continuation
                    doc_no = re.search(r'Invoice No:\s*(INV-\d{4}-\d+)', text)
                    if doc_no and doc_no.group(1) in data["invoices"]:
                        current_invoice = data["invoices"][doc_no.group(1)]
                        # Get IFSC if on page 2
                        ifsc = re.search(r'IFSC:\s*([A-Z0-9]+)', text[text.find('BANK DETAILS'):] if 'BANK DETAILS' in text else text)
                        if ifsc: current_invoice["ifsc"] = ifsc.group(1).strip()
                
                # Tables
                tables = page.extract_tables()
                if tables:
                    for t in tables:
                        for row in t:
                            if not row or row[0] == '#' or 'Description' in str(row[1]): continue
                            if len(row) >= 7 and str(row[0]).isdigit():
                                current_invoice["items"].append({
                                    "desc": row[1],
                                    "hsn": row[2],
                                    "qty": clean_amount(row[3]),
                                    "unit": row[4],
                                    "rate": clean_amount(row[5]),
                                    "amount": clean_amount(row[6])
                                })
                
                # Totals
                subt = re.search(r'Subtotal:\s*n([\d,.]+)', text)
                if subt: current_invoice["subtotal"] = clean_amount(subt.group(1))
                cgst = re.search(r'CGST:\s*n([\d,.]+)', text)
                if cgst: current_invoice["cgst"] = clean_amount(cgst.group(1))
                sgst = re.search(r'SGST:\s*n([\d,.]+)', text)
                if sgst: current_invoice["sgst"] = clean_amount(sgst.group(1))
                gt = re.search(r'GRAND TOTAL:\s*n([\d,.]+)', text)
                if gt: current_invoice["grand_total"] = clean_amount(gt.group(1))
            
            # --- PURCHASE ORDER ---
            elif 'PURCHASE ORDER' in first_line:
                po = {"page": i+1, "items": [], "subtotal": 0, "gst": 0, "total": 0, "vendor_name": None}
                doc_no = re.search(r'PO Number:\s*(PO-\d{4}-\d+)', text)
                if doc_no: po["po_no"] = doc_no.group(1)
                else: continue
                
                date_m = re.search(r'Date:\s*([\d/]+)', text)
                if date_m: po["date"] = date_m.group(1)
                
                v_name = re.search(r'Name:\s*(.*?)\n', text[text.find('VENDOR'):text.find('SHIP TO')])
                if v_name: po["vendor_name"] = v_name.group(1).strip()
                
                tables = page.extract_tables()
                if tables:
                    for t in tables:
                        for row in t:
                            if not row or row[0] == '#' or 'Description' in str(row[1]): continue
                            if len(row) >= 7 and str(row[0]).isdigit():
                                po["items"].append({
                                    "desc": row[1],
                                    "qty": clean_amount(row[3]),
                                    "rate": clean_amount(row[5]),
                                    "amount": clean_amount(row[6])
                                })
                                
                subt = re.search(r'Subtotal:\s*n([\d,.]+)', text)
                if subt: po["subtotal"] = clean_amount(subt.group(1))
                gt = re.search(r'TOTAL:\s*n([\d,.]+)', text)
                if gt: po["total"] = clean_amount(gt.group(1))
                
                data["pos"][po["po_no"]] = po
                
            # --- BANK STATEMENT ---
            elif 'BANK STATEMENT' in first_line:
                bs = {"page": i+1, "transactions": [], "opening_balance": 0}
                doc_no = re.search(r'Statement ID:\s*(BS-\d{4}-\d+)', text)
                if doc_no: bs["stmt_id"] = doc_no.group(1)
                else: continue
                
                ob = re.search(r'Opening Balance:\s*n([\d,.]+)', text)
                if ob: bs["opening_balance"] = clean_amount(ob.group(1))
                
                tables = page.extract_tables()
                if tables:
                    for t in tables:
                        for row in t:
                            if not row or row[0] == 'Date' or 'Description' in str(row[1]): continue
                            if len(row) >= 7 and re.match(r'\d{2}/\d{2}/\d{4}', str(row[0])):
                                debit = clean_amount(row[4]) if row[4] != '-' else 0
                                credit = clean_amount(row[5]) if row[5] != '-' else 0
                                balance = clean_amount(row[6]) if row[6] != '-' else 0
                                bs["transactions"].append({
                                    "date": row[0],
                                    "desc": row[1],
                                    "type": row[2],
                                    "ref": row[3],
                                    "debit": debit,
                                    "credit": credit,
                                    "balance": balance
                                })
                data["bank_statements"][bs["stmt_id"]] = bs

            # --- EXPENSE REPORT ---
            elif 'EXPENSE REPORT' in first_line:
                er = {"page": i+1, "entries": [], "employee": None, "emp_id": None, "total": 0}
                doc_no = re.search(r'Report ID:\s*(EXP-\d{4}-\d+)', text)
                if doc_no: er["report_id"] = doc_no.group(1)
                else: continue
                
                emp = re.search(r'Employee:\s*(.*?)\n', text)
                if emp: er["employee"] = emp.group(1).strip()
                emp_id = re.search(r'Employee ID:\s*(.*?)\n', text)
                if emp_id: er["emp_id"] = emp_id.group(1).strip()
                
                tables = page.extract_tables()
                if tables:
                    for t in tables:
                        for row in t:
                            if not row or row[0] == '#' or 'Date' in str(row[1]): continue
                            if len(row) >= 6 and str(row[0]).isdigit():
                                er["entries"].append({
                                    "date": row[1],
                                    "category": row[2],
                                    "desc": row[3],
                                    "city": row[4],
                                    "amount": clean_amount(row[5])
                                })
                tot = re.search(r'TOTAL CLAIMED:\s*n([\d,.]+)', text)
                if tot: er["total"] = clean_amount(tot.group(1))
                data["expense_reports"][er["report_id"]] = er
                
            # --- CREDIT/DEBIT NOTES ---
            elif 'CREDIT NOTE' in first_line or 'DEBIT NOTE' in first_line:
                note = {"page": i+1, "type": "CREDIT" if 'CREDIT' in first_line else "DEBIT"}
                doc_no = re.search(r'(?:CN|DN) Number:\s*((?:CN|DN)-\d{4}-\d+)', text)
                if doc_no: note["doc_no"] = doc_no.group(1)
                else: continue
                
                ref = re.search(r'Original Invoice:\s*(INV-\d{4}-\d+)', text)
                if ref: note["ref_doc"] = ref.group(1)
                elif re.search(r'Reference:\s*((?:CN|DN|INV)-\d{4}-\d+)', text):
                    note["ref_doc"] = re.search(r'Reference:\s*((?:CN|DN|INV)-\d{4}-\d+)', text).group(1)
                    
                gt = re.search(r'TOTAL AMOUNT:\s*n([\d,.]+)', text)
                if gt: note["amount"] = clean_amount(gt.group(1))
                
                if note["type"] == "CREDIT":
                    data["credit_notes"][note["doc_no"]] = note
                else:
                    data["debit_notes"][note["doc_no"]] = note

    print(f"Extracted: {len(data['invoices'])} invs, {len(data['pos'])} POs, {len(data['bank_statements'])} BS, {len(data['expense_reports'])} EXPs")
    
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(data, f)
        
    return data

if __name__ == "__main__":
    d = extract_all("gauntlet.pdf")
    print("Invoices:", len(d["invoices"]))
    print("POs:", len(d["pos"]))
    print("Bank Statements:", len(d["bank_statements"]))
