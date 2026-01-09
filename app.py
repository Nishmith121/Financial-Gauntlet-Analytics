import streamlit as st
import json
from dotenv import load_dotenv
load_dotenv()
from report import create_charts, create_pdf_report
from ocr import extract_financial_data
from validator import validate_line_items
from llm import generate_report
from hyper_export import create_hyper_extract
from audit import generate_audit_hash

st.set_page_config(
    page_title="Financial Gauntlet | Analytics", 
    page_icon="", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom Premium CSS injecting Glassmorphism and sophisticated corporate colors
st.markdown("""
<style>
    /* Cyberpunk Dark Dashboard Theme */
    @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;600;700&family=Orbitron:wght@500;700&display=swap');

    .stApp {
        background-color: #050505;
        background-image: 
            radial-gradient(circle at 15% 50%, rgba(0, 255, 204, 0.04), transparent 25%),
            radial-gradient(circle at 85% 30%, rgba(255, 0, 85, 0.04), transparent 25%);
        color: #d1d5db;
        font-family: 'Fira Code', 'Courier New', monospace;
    }
    
    /* Center Container - Dark Glass & Glowing Borders */
    [data-testid="stAppViewBlockContainer"] {
        background: rgba(10, 10, 12, 0.85) !important;
        backdrop-filter: blur(12px);
        border-radius: 8px;
        padding: 48px !important;
        margin-top: 40px !important;
        margin-bottom: 40px !important;
        box-shadow: 0 0 20px rgba(0, 255, 204, 0.05), inset 0 0 0 1px rgba(0, 255, 204, 0.1);
        border: 1px solid rgba(0, 255, 204, 0.2);
    }
    
    /* Typography - Orbitron headers */
    h1, h2, h3 {
        color: #00ffcc !important;
        font-family: 'Orbitron', sans-serif !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        text-shadow: 0 0 10px rgba(0, 255, 204, 0.4);
        letter-spacing: 2px;
    }
    h4 {
        color: #ff0055 !important;
        font-family: 'Orbitron', sans-serif !important;
        font-weight: 600 !important;
        letter-spacing: 1px;
    }
    
    /* Upload Box - Dark Matrix Hologram */
    [data-testid="stFileUploader"] {
        width: 100%;
    }
    [data-testid="stFileUploaderDropzone"] {
        border-radius: 8px;
        border: 1px dashed #ff0055 !important;
        background: rgba(255, 0, 85, 0.05);
        padding: 32px !important;
        transition: all 0.3s ease-in-out;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    [data-testid="stFileUploaderDropzone"] * {
        color: #ffffff !important;
    }
    [data-testid="stFileUploaderDropzone"]:hover {
        border-color: #00ffcc !important;
        background: rgba(0, 255, 204, 0.05);
        box-shadow: 0 0 15px rgba(0, 255, 204, 0.2) inset;
    }
    
    /* Metric Cards - Hacker Consoles */
    [data-testid="stMetricValue"] {
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        color: #00ffcc !important;
        text-shadow: 0 0 8px rgba(0, 255, 204, 0.5);
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.9rem !important;
        font-weight: 600 !important;
        color: #9ca3af !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    div[data-testid="metric-container"] {
        background-color: #0a0a0c;
        border: 1px solid rgba(0, 255, 204, 0.2);
        border-radius: 4px;
        padding: 24px;
        box-shadow: inset 0 0 20px rgba(0, 0, 0, 0.5);
        text-align: center;
        transition: all 0.2s ease;
    }
    div[data-testid="metric-container"]:hover {
        border-color: #00ffcc;
        box-shadow: 0 0 15px rgba(0, 255, 204, 0.15), inset 0 0 10px rgba(0, 255, 204, 0.05);
        transform: translateY(-2px);
    }
    
    /* Buttons - Neon Reactor */
    .stDownloadButton > button, .stButton > button {
        background: transparent !important;
        color: #00ffcc !important;
        border: 1px solid #00ffcc !important;
        border-radius: 4px !important;
        padding: 12px 24px !important;
        font-family: 'Orbitron', sans-serif !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        width: 100%;
        text-transform: uppercase;
        letter-spacing: 2px;
        transition: all 0.3s ease !important;
        box-shadow: 0 0 10px rgba(0, 255, 204, 0.1);
    }
    .stDownloadButton > button:hover, .stButton > button:hover {
        background: rgba(0, 255, 204, 0.1) !important;
        box-shadow: 0 0 20px rgba(0, 255, 204, 0.4), inset 0 0 10px rgba(0, 255, 204, 0.2) !important;
        text-shadow: 0 0 5px #00ffcc;
    }

    /* Expander & Alerts - System Warnings */
    .streamlit-expanderHeader {
        background-color: #0a0a0c !important;
        border-radius: 4px !important;
        color: #00ffcc !important;
        font-family: 'Orbitron', sans-serif !important;
        font-weight: 600;
        border: 1px solid rgba(0, 255, 204, 0.3);
    }
    .stAlert {
        border-radius: 4px !important;
        border: 1px solid #ff0055;
        background-color: rgba(255, 0, 85, 0.05) !important;
        color: #f3f4f6 !important;
        box-shadow: 0 0 15px rgba(255, 0, 85, 0.1);
    }
    
    hr {
        border-color: rgba(0, 255, 204, 0.2) !important;
    }
    
    p {
        color: #9ca3af !important;
    }
</style>
""", unsafe_allow_html=True)

# Header Section
st.title("Financial Gauntlet Analytics")
st.markdown("<p style='font-size: 18px; color: #8b949e; margin-bottom: 30px;'>An intelligent, hybrid pipeline ingesting unstructured system logs and structured invoices to generate deep, mathematically-validated AI insights.</p>", unsafe_allow_html=True)

# Upload Section inside a stylish container
with st.container():
    colA, colB = st.columns(2, gap="large")
    with colA:
        st.markdown("### Document Intake")
        st.markdown("<p style='color: #9ca3af; font-size: 0.95rem; margin-bottom: 24px;'>Upload your Document (PDF, Word, TXT, log, Images) to begin analysis.</p>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Upload", label_visibility="collapsed", type=["pdf", "txt", "csv", "log", "png", "jpg", "jpeg", "docx", "doc"])
    with colB:
        st.markdown("### Hackathon Mode")
        st.markdown("<p style='color: #9ca3af; font-size: 0.95rem; margin-bottom: 26px;'>Run the robust 20-rule anomaly detection pipeline on the 1000-page <code>gauntlet.pdf</code>.</p>", unsafe_allow_html=True)
        st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True) # padding to ensure perfectly symmetric height alignment with the tall uploader container
        run_gauntlet = st.button("Execute Gauntlet Solver", use_container_width=True, type="primary")

if run_gauntlet:
    import json
    import os
    from extractors import extract_all
    from detectors import run_detectors
    import time
    
    with st.status("Executing 1000-page Gauntlet Pipeline...", expanded=True) as status:
        st.write("Extracting structured data from 1000 pages (Vendor Master, Purchase Orders, Invoices, Bank Statements, Expense Reports)...")
        st.write("This process employs pdfplumber layout analysis and will take several minutes to process all pages chronologically.")
        
        start_time = time.time()
        
        try:
            # Running extraction
            parsed_data = extract_all("gauntlet.pdf")
            ex_time = time.time()
            st.success(f"Extraction complete! Found {len(parsed_data['invoices'])} invoices, {len(parsed_data['pos'])} POs, {len(parsed_data['bank_statements'])} bank statements, {len(parsed_data['expense_reports'])} expense reports. ({ex_time - start_time:.1f}s)")
            
            st.write("Running 20-Rule Detection Engine (Easy, Medium, Evil Needles)...")
            findings = run_detectors(parsed_data)
            det_time = time.time()
            
            st.success(f"Detection complete! Found {len(findings)} anomalies. ({det_time - ex_time:.1f}s)")
            
            submission = {
                "team_id": "Antigravity_Solver",
                "findings": findings
            }
            
            out_file = "submission.json"
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(submission, f, indent=2)
                
            status.update(label=f"Gauntlet Completed - {len(findings)} Needles Found", state="complete", expanded=False)
            
            st.markdown("### Gauntlet Results")
            st.metric("Total Needles Detected", len(findings))
            
            # Show Findings Table
            import pandas as pd
            df = pd.DataFrame(findings)
            st.dataframe(df, use_container_width=True)
            
            st.markdown("### Download Submission")
            submission_json_str = json.dumps(submission, indent=2)
            st.download_button(
                label="Download submission.json",
                data=submission_json_str,
                file_name="submission.json",
                mime="application/json"
            )
        except Exception as e:
            st.error(f"Error executing gauntlet solver: {str(e)}")
            status.update(label="Gauntlet Failed", state="error", expanded=False)

if uploaded_file and not run_gauntlet:
    file_size_mb = uploaded_file.size / (1024 * 1024)
    if file_size_mb == 0:
        st.error("Error: Uploaded file is empty (0 bytes).")
        st.stop()
