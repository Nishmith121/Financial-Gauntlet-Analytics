# Financial Gauntlet Analytics 🚀

An intelligent, hybrid pipeline designed to ingest unstructured system logs and structured invoices to generate deep, mathematically-validated AI insights. This application leverages advanced OCR, deterministic rule-based validation, and state-of-the-art LLMs to detect anomalies and provide actionable financial intelligence.

## 🌟 Key Features

*   **Multi-format Document Ingestion:** Process PDFs, Word documents, TXT files, system logs, CSVs, and images (PNG, JPG).
*   **Hybrid Extraction Engine:** 
    *   **Heuristic/Regex Parsing:** Fast and precise extraction for standard formats.
    *   **Vision-Language Model (Gemini 2.5 Flash):** Fallback extraction for complex, unstructured, or visually dense documents.
*   **Deterministic Validation (The Gauntlet):** A robust 20-rule anomaly detection pipeline that validates chronologies, math, tax calculations, and identifies sophisticated fraud attempts (e.g., duplicate invoices, synthetic vendors).
*   **Human-in-the-Loop (HITL) UI:** An interactive interface to review, edit, and re-validate extracted data and anomalies before final processing.
*   **AI Synthesis:** Generates executive summaries, trend analysis, and actionable recommendations based on validated data.
*   **Immutable Audit Trail:** Generates SHA-256 cryptographic hashes of the validation payload to ensure data integrity and tamper evidence.
*   **Enterprise Exports:**
    *   C-Suite PDF Reports with dynamic telemetry charts.
    *   Tableau Data Extracts (`.hyper`) for BI integration.
    *   Raw JSON data for further programmatic use.
*   **Hackathon Mode:** Dedicated mode to run the full pipeline on massive datasets (e.g., 1000-page ledgers) to extract structured data and find specific "needles" (anomalies).

## 🛠️ Technology Stack

*   **Frontend/App Framework:** Streamlit
*   **AI/LLM:** Google Gemini API (Gemini 2.5 Flash)
*   **Document Parsing:** pdfplumber, pytesseract, Pillow
*   **Data Validation:** Pydantic
*   **Visualization:** Matplotlib, Seaborn
*   **Reporting/Export:** fpdf2, Tableau Hyper API

## 🚀 Getting Started

### Prerequisites

1.  Python 3.9+
2.  Tesseract OCR installed on your system (required for image processing).
3.  A Google Gemini API Key.

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Nishmith121/Financial-Gauntlet-Analytics.git
    cd Financial-Gauntlet-Analytics
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Environment Variables:**
    Create a `.env` file in the root directory and add your Gemini API key:
    ```env
    GEMINI_API_KEY=your_actual_api_key_here
    ```

### Running the Application

Start the Streamlit server:
```bash
python -m streamlit run app.py
```
The application will be available in your browser at `http://localhost:8501`.

## 🔒 Security Note

**Do not commit your `.env` file or hardcode your API keys in the source code.** This repository is configured to ignore the `.env` file via `.gitignore`. Always use environment variables for sensitive credentials.

## 📄 License

This project is licensed under the MIT License.
