import os
import json
import io
import matplotlib.pyplot as plt
import seaborn as sns
from fpdf import FPDF
import re

class PDFReport(FPDF):
    def header(self):
        self.set_font("helvetica", "B", 18)
        self.cell(0, 10, "Financial Gauntlet: Analytics Report", align="C", new_x="LMARGIN", new_y="NEXT")
        self.line(10, 22, 200, 22)
        self.ln(10)
    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

def create_charts(llm_json):
    sns.set_theme(style="whitegrid")
    buf1, buf2 = io.BytesIO(), io.BytesIO()

    try:
        insights = json.loads(llm_json)
        title = insights.get("chart_title", "Key Metrics Distribution")
        labels = insights.get("chart_labels", [])
        values = insights.get("chart_values", [])

        if labels and values and len(labels) == len(values):
