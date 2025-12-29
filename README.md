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
*   **Immutable Audit Trail:** Generates SHA-256 cryptographic hashes to ensure data integrity.
*   **Enterprise Exports:**
    *   C-Suite PDF Reports with dynamic charts.
    *   Tableau Data Extracts (.hyper) for BI.
*   **Hackathon Mode:** Dedicated mode to run full pipeline on massive 1000-page ledgers.

## 🚀 Getting Started

### Prerequisites

1.  Python 3.9+
2.  Tesseract OCR installed on your system.
3.  A Google Gemini API Key.
### Installation

```bash
git clone https://github.com/Nishmith121/Financial-Gauntlet-Analytics.git
cd Financial-Gauntlet-Analytics
```
```bash
pip install -r requirements.txt
```
### Configure Environment Variables

Create a `.env` file:
```env
GEMINI_API_KEY=your_key_here
```
### Running the Application

```bash
python -m streamlit run app.py
```
