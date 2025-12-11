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
