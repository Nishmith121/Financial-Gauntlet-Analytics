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
