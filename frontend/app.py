import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="Live EDA Assistant Pro", layout="wide")

BACKEND_URL = "http://127.0.0.1:8000"

# -----------------------------
# Title Section
# -----------------------------
st.title("📊 Live EDA Assistant Pro")
st.write("""
Upload a CSV or Excel file and get:
- Automated dataset analysis  
- Smart insights  
- Interactive visualizations  
- Downloadable PDF report  
- All backed by FastAPI + Supabase  
""")

# -----------------------------
# File Upload
# -----------------------------
uploaded_file = st.file_uploader("Upload CSV or Excel file", type=["csv", "xlsx", "xls"])

if uploaded_file is not None:
    st.success(f"File uploaded: {uploaded_file.name}")

    # Show preview
    try:
        if uploaded_file.name.endswith(".xlsx") or uploaded_file.name.endswith(".xls"):
            df = pd.read_excel(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file)

        st.subheader("🔍 Dataset Preview")
        st.dataframe(df.head())

    except Exception as e:
        st.error(f"Unable to preview file: {e}")
        st.stop()

    # Run EDA button
    if st.button("🚀 Run EDA Analysis"):
        with st.spinner("Running EDA on backend..."):
            try:
                files = {
                    "file": (
                        uploaded_file.name,
                        uploaded_file.getvalue(),
                        uploaded_file.type
                    )
                }

                response = requests.post(f"{BACKEND_URL}/api/analyze", files=files)
                
                if response.status_code == 200:
                    result = response.json()
                    st.session_state["analysis_result"] = result
                    st.success("EDA completed successfully!")
                else:
                    st.error(f"Backend error: {response.text}")
                    st.stop()

            except Exception as e:
                st.error(f"Error contacting backend: {e}")
                st.stop()

# -----------------------------
# Show Analysis Results
# -----------------------------
if "analysis_result" in st.session_state:
    result = st.session_state["analysis_result"]

    overview = result["overview"]
    col_types = result["column_types"]
    col_summaries = result["column_summaries"]
    outliers = result["outliers"]
    insights = result["insights"]
    correlations = result["correlations"]
    analysis_id = result["analysis_id"]

    st.header("📌 Analysis Summary")

    # ---------------------
    # Dataset Overview
    # ---------------------
    st.subheader("1️⃣ Dataset Overview")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Rows", overview["n_rows"])
    col2.metric("Columns", overview["n_cols"])
    col3.metric("Missing %", f"{overview['missing_pct']:.2f}%")
    col4.metric("Duplicate Rows", overview["duplicate_rows"])

    st.write("**Column Types:**")
    st.json(col_types)

    # ---------------------
    # Insights Section
    # ---------------------
    st.subheader("2️⃣ Insights")

    st.markdown("### 🔍 Dataset-Level Insights")
    for ins in insights["overview"]:
        st.write(f"- {ins}")

    st.markdown("### 🔍 Column-Level Insights")
    for ins in insights["columns"]:
        st.write(f"- {ins}")

    st.markdown("### 🔍 Correlation Insights")
    for ins in insights["correlations"]:
        st.write(f"- {ins}")

    # ---------------------
    # Visualizations Section
    # ---------------------
    st.subheader("3️⃣ Visualizations")

    tab1, tab2, tab3 = st.tabs(["Numeric Distribution", "Categorical Counts", "Correlations"])

    # Numeric plots
    with tab1:
        if col_types["numeric"]:
            numeric_col = st.selectbox("Select numeric column", col_types["numeric"])
            
            fig, ax = plt.subplots()
            sns.histplot(df[numeric_col], kde=True, ax=ax)
            ax.set_title(f"Distribution of {numeric_col}")
            st.pyplot(fig)

            fig2, ax2 = plt.subplots()
            sns.boxplot(x=df[numeric_col], ax=ax2)
            ax2.set_title(f"Boxplot of {numeric_col}")
            st.pyplot(fig2)
        else:
            st.info("No numeric columns detected.")

    # Categorical plots
    with tab2:
        if col_types["categorical"]:
            cat_col = st.selectbox("Select categorical column", col_types["categorical"])
            fig, ax = plt.subplots()
            df[cat_col].value_counts().plot(kind="bar", ax=ax)
            ax.set_title(f"Value counts for {cat_col}")
            st.pyplot(fig)
        else:
            st.info("No categorical columns detected.")

    # Correlation Heatmap
    with tab3:
        if col_types["numeric"] and len(col_types["numeric"]) >= 2:
            fig, ax = plt.subplots(figsize=(6, 4))
            sns.heatmap(df[col_types["numeric"]].corr(), annot=False, cmap="coolwarm", ax=ax)
            ax.set_title("Correlation Heatmap")
            st.pyplot(fig)
        else:
            st.info("Not enough numeric columns for correlation heatmap.")

    # ---------------------
    # PDF Report Download
    # ---------------------
    st.subheader("4️⃣ Download PDF Report")

    if st.button("📄 Download PDF Report"):
        with st.spinner("Fetching report..."):
            try:
                pdf = requests.get(f"{BACKEND_URL}/api/report/{analysis_id}")

                if pdf.status_code == 200:
                    st.download_button(
                        "⬇ Download Report",
                        data=pdf.content,
                        file_name=f"eda_report_{analysis_id}.pdf",
                        mime="application/pdf"
                    )
                else:
                    st.error("Error fetching PDF report.")

            except Exception as e:
                st.error(f"Error: {e}")
