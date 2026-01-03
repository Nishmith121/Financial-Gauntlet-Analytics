import json
import time
from extractors import extract_all
from detectors import run_detectors

def solve_gauntlet(pdf_path, team_name="AI_Agents"):
    print("Starting Gauntlet Solver Pipeline...")
    
    start_time = time.time()
    
    # 1. Extraction Phase
    parsed_data = extract_all(pdf_path)
    
    extract_time = time.time()
    print(f"Extraction complete in {extract_time - start_time:.2f} seconds.")
