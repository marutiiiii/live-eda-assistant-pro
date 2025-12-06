# backend/main.py

import os
import uuid
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

import pandas as pd

from db import supabase
from eda_core import (
    dataset_overview,
    column_summary,
    outlier_report,
    correlation_analysis,
    detect_column_types,
)
from insights_engine import (
    generate_overview_insights,
    generate_column_insights,
    generate_correlation_insights,
)
from pdf_report import generate_pdf

# Create FastAPI app
app = FastAPI(title="Live EDA Assistant Backend", version="1.0")

# Allow Streamlit (different port) to call our backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # in production, narrow this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Path to /reports folder in project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
REPORTS_DIR = os.path.join(PROJECT_ROOT, "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

@app.get("/health")
def health_check():
    """Simple health check endpoint."""
    return {"status": "ok", "message": "Backend is running"}

@app.post("/api/analyze")
async def analyze_dataset(file: UploadFile = File(...)):
    """
    Main EDA endpoint:
    - Accepts CSV file
    - Runs EDA
    - Saves result + PDF in Supabase / local
    - Returns JSON summary to frontend
    """
    # 1. Read CSV into pandas DataFrame
    try:
        raw_bytes = await file.read()
        df = pd.read_csv(pd.io.common.BytesIO(raw_bytes))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Unable to read CSV: {e}")

    if df.empty:
        raise HTTPException(status_code=400, detail="Uploaded CSV is empty.")

    # 2. Run EDA core
    overview = dataset_overview(df)
    col_types = detect_column_types(df)
    col_summaries = column_summary(df)
    outliers = outlier_report(df)

    # Merge outlier % into column summaries for insights
    for col, info in col_summaries.items():
        if col in outliers:
            info["outlier_pct"] = outliers[col]["outlier_pct"]
        else:
            info["outlier_pct"] = 0.0

    corr_info = correlation_analysis(df)

    # 3. Generate insights
    overview_insights = generate_overview_insights(overview)
    col_insights = generate_column_insights(col_summaries)
    corr_insights = generate_correlation_insights(corr_info)

    # 4. Generate PDF report (bytes)
    analysis_id = str(uuid.uuid4())
    pdf_bytes = generate_pdf(
        overview=overview,
        col_summaries=col_summaries,
        outliers=outliers,
        overview_insights=overview_insights,
        col_insights=col_insights,
        corr_insights=corr_insights,
        file_name=file.filename,
    )

    # 5. Save PDF to /reports folder
    pdf_filename = f"{analysis_id}.pdf"
    pdf_path = os.path.join(REPORTS_DIR, pdf_filename)
    try:
        with open(pdf_path, "wb") as f:
            f.write(pdf_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save PDF: {e}")

    # 6. Save summary to Supabase (analyses table)
    db_record = {
        "id": analysis_id,
        "filename": file.filename,
        "created_at": datetime.utcnow().isoformat(),
        "overview": overview,
        "column_types": col_types,
        "column_summaries": col_summaries,
        "outliers": outliers,
        "correlations": {
            "strong_pairs": corr_info.get("strong_pairs", []),
        },
        "insights": {
            "overview": overview_insights,
            "columns": col_insights,
            "correlations": corr_insights,
        },
        "pdf_path": pdf_path,
    }

    try:
        response = supabase.table("analyses").insert(db_record).execute()
        # Optional: you can check response.data or response.error here
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to insert into Supabase: {e}")

    # 7. Return JSON response to frontend (Streamlit)
    return {
        "analysis_id": analysis_id,
        "filename": file.filename,
        "overview": overview,
        "column_types": col_types,
        "column_summaries": col_summaries,
        "outliers": outliers,
        "correlations": corr_info.get("strong_pairs", []),
        "insights": {
            "overview": overview_insights,
            "columns": col_insights,
            "correlations": corr_insights,
        },
    }

@app.get("/api/analysis/{analysis_id}")
def get_analysis(analysis_id: str):
    """
    Get a previously saved analysis from Supabase by ID.
    """
    try:
        response = supabase.table("analyses").select("*").eq("id", analysis_id).single().execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Analysis not found")
        record = response.data
        return record
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching analysis: {e}")

@app.get("/api/report/{analysis_id}")
def download_report(analysis_id: str):
    """
    Return the PDF file for a given analysis ID.
    """
    try:
        response = supabase.table("analyses").select("pdf_path").eq("id", analysis_id).single().execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Analysis not found")

        pdf_path = response.data.get("pdf_path")
        if not pdf_path or not os.path.exists(pdf_path):
            raise HTTPException(status_code=404, detail="PDF report not found on server")

        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename=f"eda_report_{analysis_id}.pdf",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching report: {e}")
