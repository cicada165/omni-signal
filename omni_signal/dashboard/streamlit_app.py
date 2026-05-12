from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Omni Signal", layout="wide")
st.title("Omni Signal Dashboard (Offline)")
report_path = Path("reports/daily.md")
if report_path.exists():
    st.markdown(report_path.read_text(encoding="utf-8"))
else:
    st.info("No report yet. Run `omni-signal ingest-examples && omni-signal score`.")
