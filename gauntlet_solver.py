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
    
    # 2. Detection Phase
    findings = run_detectors(parsed_data)
    
    detect_time = time.time()
    print(f"Detection complete in {detect_time - extract_time:.2f} seconds. Found {len(findings)} needles.")
    
    # 3. Format Submission
    submission = {
        "team_id": team_name,
        "findings": findings
    }
    
    out_file = "submission.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(submission, f, indent=2)
        
    print(f"Submission saved to {out_file}")
    
if __name__ == "__main__":
    solve_gauntlet("gauntlet.pdf", team_name="Antigravity_Solver")
