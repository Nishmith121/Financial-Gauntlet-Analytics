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
    elif file_size_mb > 50:
        st.error(f"Error: File size ({file_size_mb:.2f} MB) exceeds the 50MB limit.")
        st.stop()

    with st.status("Executing Analytics Pipeline...", expanded=True) as status:
        st.write("Parsing Document & Extracting Raw Data Matrix...")
        try:
            extracted_data = extract_financial_data(uploaded_file)
            
            doc_type = extracted_data.get("type", "unknown")
            if doc_type == "unknown":
                st.warning("Format Unrecognized: This document does not strictly match standard financial schemas. Proceeding with generic anomaly detection, but manual review is required.", icon="")
            else:
                st.success(f"Document Successfully Classified: {doc_type.upper()}", icon="")

            st.write("Running Chronological Math & Anomaly Detection...")
            validation_report = validate_line_items(extracted_data)
        except Exception as e:
            st.error("Fatal Error: The extraction engine encountered a critical failure (e.g., password-protected or corrupted file).")
            with st.expander("View System Traceback"):
                st.text(str(e))
            st.stop()
        
        # --- NEW HACKATHON FEATURE: Human-in-the-Loop UI ---
        if validation_report.get("anomalies"):
            st.warning("Anomalies Detected! Review and fix the data extracted below to proceed.")
            # Show interactive grid
            edited_anomalies = st.data_editor(validation_report["anomalies"], use_container_width=True, key="hitl_editor")
            
            # Detect changes and re-validate dynamically
            if edited_anomalies != validation_report["anomalies"]:
                clean_edited = [{k: v for k, v in a.items() if k != "errors"} for a in edited_anomalies]
                clean_valid = [{k: v for k, v in v.items() if k != "errors"} for v in validation_report.get("valid_records", [])]
                
                doc_type = validation_report.get("doc_type")
                if doc_type == "invoice":
                    headers = list(clean_valid[0].keys()) if clean_valid else list(clean_edited[0].keys())
                    new_table = [headers]
                    for rec in clean_valid + clean_edited:
                        new_table.append([rec.get(h, "") for h in headers])
                    extracted_data["data"] = [new_table]
                elif doc_type == "logs":
                    extracted_data["data"] = clean_valid + clean_edited
                
                st.info("Modifications detected. Re-validating payload...")
                validation_report = validate_line_items(extracted_data)
                
                if not validation_report.get("anomalies"):
                    st.success("Issues Resolved! Continuing pipeline...")
                else:
                    st.error("Overcharge or Math Anomalies still present in the edited data.")
        
        st.write("Synthesizing Intelligence via Gemini 2.5 Flash...")
        report_json_str = generate_report(validation_report, extracted_data["text"], extracted_data.get("extraction_reasoning", ""))
        
        st.write("Rendering C-Suite PDF Final Report...")
        pdf_path = create_pdf_report(validation_report, report_json_str)
        
        st.write("Generating Tableau Data Extract (.hyper)...")
        doc_type_fmt = validation_report.get('doc_type', 'unknown').upper()
        hyper_path = create_hyper_extract(validation_report, output_filename=f"analytics_{doc_type_fmt}.hyper")
        
        st.write("Securing Payload via Immutable Audit Hash...")
        audit_hash = generate_audit_hash(validation_report)
        st.success(f"Audit Hash Generated: {audit_hash}")
        
        status.update(label=f"Pipeline Completed Successfully (Mode: {doc_type_fmt})", state="complete", expanded=False)

    st.markdown("---")

    # --- KPI DASHBOARD ---
    st.markdown("### Key Performance Indicators")
    col1, col2, col3 = st.columns(3)
    tot = len(validation_report.get("valid_records", [])) + len(validation_report.get("anomalies", []))
    anom = len(validation_report.get("anomalies", []))
    acc = validation_report.get("accuracy_score", 0.0)
    
    col1.metric("Total Records Parsed", f"{tot:,}")
    col2.metric("Anomalies Detected", anom, delta=f"-{anom}" if anom > 0 else "0", delta_color="inverse")
    col3.metric("Data Confidence Score", f"{acc * 100:.1f}%")

    st.markdown("<br>", unsafe_allow_html=True) # Spacer

    # --- MAIN CONTENT LAYOUT ---
    st.markdown("### 🧬 Deep Analysis")
    # Split the view: AI Insights on the left, Visuals on the right
    main_col1, main_col2 = st.columns([1.1, 1.9], gap="large")

    with main_col1:
        st.markdown("#### AI Executive Summary")
        try:
            insights = json.loads(report_json_str)
            with st.container(border=True):
                st.info(f"**Brief:** {insights.get('executive_summary', 'No summary available.')}", icon="")
                st.write(f"**Trend Analysis:** {insights.get('trend_analysis', 'Insufficient data for trends.')}")
                
                st.markdown("---")
                st.error("**Critical Risk Factors**")
                for risk in insights.get('risk_factors', []):
                    st.markdown(f"- {risk}")
                    
                st.markdown("<br>", unsafe_allow_html=True)
                
                st.success("**Recommended Actions**")
                for action in insights.get('recommended_actions', []):
                    st.markdown(f"- {action}")
                    
        except json.JSONDecodeError:
            st.warning("Failed to parse Structured AI Analytics output.")
            with st.expander("View Raw API Response"):
                st.text(report_json_str)

    with main_col2:
        st.markdown("#### Visual Telemetry")
        buf1, buf2 = create_charts(report_json_str)
        if buf1 and buf2:
            st.image(buf1, use_container_width=True)
            st.markdown("<br>", unsafe_allow_html=True) # Spacer
            st.image(buf2, use_container_width=True)
        else:
            st.warning("Insufficient numeric variance to render telemetry charts.", icon="")

    st.markdown("---")
    
    # --- FINAL EXPORT ---
    st.markdown("### Report Export")
    st.markdown("<p style='color: #8b949e; margin-bottom: 20px;'>Download the mathematically validated PDF report, the core database extract for Tableau, or the raw JSON data.</p>", unsafe_allow_html=True)
    
    col_dl1, col_dl2, col_dl3 = st.columns(3)
    with col_dl1:
        with open(pdf_path, "rb") as pdf_file:
            st.download_button(
                label="Download Validated C-Suite Report (.pdf)",
                data=pdf_file,
                file_name=f"Financial_Gauntlet_{doc_type_fmt}.pdf",
                mime="application/pdf"
            )
    with col_dl2:
        if hyper_path:
            with open(hyper_path, "rb") as hyper_file:
                st.download_button(
                    label="Download Tableau Extract (.hyper)",
                    data=hyper_file,
                    file_name=f"Financial_Gauntlet_{doc_type_fmt}.hyper",
                    mime="application/octet-stream"
                )
        else:
            st.warning("No tabular data generated to extract to Tableau.")
    with col_dl3:
        # Provide JSON download of the validated data and anomalies
        json_str = json.dumps(validation_report, indent=2)
        st.download_button(
            label="JSON Download Raw Data (.json)",
            data=json_str,
            file_name=f"Financial_Gauntlet_{doc_type_fmt}_raw.json",
            mime="application/json"
        )