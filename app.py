
import streamlit as st
import tempfile
import pandas as pd
import numpy as np

# Safe import (prevents crash if file missing)
try:
    from Yolo_inference import detect_weeds
except:
    st.error("yolo_inference.py file is missing!")
    st.stop()

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="WeedVision", layout="wide")

# ---------------- STYLING ----------------
st.markdown("""
<style>
body {
    background-color: #f5f7fa;
}
h1, h2, h3 {
    font-family: 'Roboto', sans-serif;
}
.stButton>button {
    background-color: #2e7d32;
    color: white;
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

# ---------------- TITLE ----------------
st.markdown("""
<h1 style='text-align: center; color: #2e7d32; font-size: 48px;'>
🌿 WeedVision
</h1>
<p style='text-align: center; font-size:18px; color: gray;'>
Smart Weed Detection for Precision Agriculture
</p>
""", unsafe_allow_html=True)

st.markdown("---")

# ---------------- FILE UPLOAD ----------------
uploaded_file = st.file_uploader("📤 Upload Field Image", type=["jpg", "png"])

if uploaded_file:

    # Save uploaded file temporarily
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.write(uploaded_file.read())

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📷 Input Image")
        st.image(uploaded_file)

    # ---------------- DETECTION ----------------
    try:
        image, weed_count, confidence = detect_weeds(temp_file.name)
    except Exception as e:
        st.error(f"Detection Error: {e}")
        st.stop()

    with col2:
        st.subheader("✅ Detection Output")
        st.image(image, channels="BGR")

    # ---------------- METRICS ----------------
    st.markdown("## 📊 Dashboard")

    col3, col4, col5 = st.columns(3)

    col3.metric("🌿 Weed Count", weed_count)
    col4.metric("🎯 Avg Confidence (%)", confidence)
    col5.metric("📍 Status", "Weeds Detected" if weed_count > 0 else "Clean Field")

    # ---------------- CHART ----------------
    st.markdown("### 🌱 Weed vs Crop Distribution")

    total_area = 30  # assumed field segments for visualization
    crop_count = max(0, total_area - weed_count)

    data = pd.DataFrame({
        "Category": ["Weed", "Crop"],
        "Count": [weed_count, crop_count]
    })

    st.bar_chart(data.set_index("Category"))

    # ---------------- TREND ----------------
    st.markdown("### 📈 Confidence Trend")

    trend = pd.DataFrame({
        "Frame": list(range(1, 11)),
        "Confidence": np.linspace(max(60, confidence - 10), confidence, 10)
    })

    st.line_chart(trend.set_index("Frame"))

    # ---------------- INSIGHTS ----------------
    st.markdown("### 🧠 Insights")

    if weed_count > 15:
        st.error("High weed density detected! Immediate action required.")
    elif weed_count > 5:
        st.warning("Moderate weed presence detected.")
    else:
        st.success("Low weed presence. Field is mostly clean.")

else:
    st.info("👆 Upload an image to start detection")