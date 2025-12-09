# Financial Gauntlet Analytics 🚀

An intelligent, hybrid pipeline designed to ingest unstructured system logs and structured invoices to generate deep, mathematically-validated AI insights.

## 🌟 Key Features

*   **Multi-format Document Ingestion:** Process PDFs, Word documents, TXT files, system logs, CSVs, and images (PNG, JPG).
*   **Hybrid Extraction Engine:**
    *   **Heuristic/Regex Parsing:** Fast and precise extraction for standard formats.
    *   **Vision-Language Model (Gemini 2.5 Flash):** Fallback extraction for complex documents.
*   **Deterministic Validation (The Gauntlet):** A robust 20-rule anomaly detection pipeline that validates chronologies, math, and tax calculations.

## 🛠️ Technology Stack

*   **Frontend/App Framework:** Streamlit
*   **AI/LLM:** Google Gemini API (Gemini 2.5 Flash)
*   **Document Parsing:** pdfplumber, pytesseract, Pillow
*   **Data Validation:** Pydantic
*   **Visualization:** Matplotlib, Seaborn
*   **Human-in-the-Loop (HITL) UI:** An interactive interface to review, edit, and re-validate extracted data.
*   **AI Synthesis:** Generates executive summaries, trend analysis, and actionable recommendations.
