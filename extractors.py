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
