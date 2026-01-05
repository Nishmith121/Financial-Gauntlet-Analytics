import os
import json
from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import List

# API key MUST be set via GEMINI_API_KEY environment variable
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

class ReportInsights(BaseModel):
    executive_summary: str
    trend_analysis: str
    risk_factors: List[str]
    recommended_actions: List[str]
    chart_title: str
    chart_labels: List[str]
    chart_values: List[float]

def generate_report(validation_report: dict, raw_text: str, overall_reasoning: str = "") -> str:
