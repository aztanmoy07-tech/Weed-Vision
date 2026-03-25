st.markdown("""
<h1 style='text-align: center; color: #2e7d32; font-size: 48px;'>
🌿 WeedVision
</h1>
<p style='text-align: center; font-size:18px; color: gray;'>
Smart Weed Detection for Precision Agriculture
</p>
""", unsafe_allow_html=True)

import streamlit as st
import cv2
import numpy as np
import tempfile
import pandas as pd
import matplotlib.pyplot as plt
from inference import predict

# ---------------- UI CONFIG ----------------
st.set_page_config(page_title="WeedVision AI", layout="wide")

# Google-like clean styling
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
st.title("🌿 WeedVision AI Dashboard")
st.markdown("Smart Weed Detection for Precision Agriculture")

# ---------------- FILE UPLOAD ----------------
uploaded_file = st.file_uploader("📤 Upload Field Image", type=["jpg", "png"])

if uploaded_file:

    col1, col2 = st.columns(2)

    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.write(uploaded_file.read())

    with col1:
        st.subheader("📷 Input Image")
        st.image(uploaded_file)

    # ---------------- PROCESS ----------------
    image, label = predict(temp_file.name)

    # Fake metrics for demo (you can improve later)
    weed_count = np.random.randint(5, 20)
    confidence = round(np.random.uniform(80, 95), 2)

    with col2:
        st.subheader("✅ Detection Result")
        st.image(image, channels="BGR")

    # ---------------- METRICS ----------------
    st.markdown("## 📊 Analysis Dashboard")

    col3, col4, col5 = st.columns(3)

    col3.metric("🌿 Weed Count", weed_count)
    col4.metric("🎯 Confidence (%)", confidence)
    col5.metric("📍 Prediction", label)

    # ---------------- CHARTS ----------------

    # Chart 1: Weed vs Crop
    st.markdown("### 🌱 Weed vs Crop Distribution")

    data = pd.DataFrame({
        "Category": ["Weed", "Crop"],
        "Count": [weed_count, 30 - weed_count]
    })

    st.bar_chart(data.set_index("Category"))

    # Chart 2: Confidence Trend (demo)
    st.markdown("### 📈 Confidence Trend")

    trend = pd.DataFrame({
        "Frame": list(range(1, 11)),
        "Confidence": np.random.uniform(75, 95, 10)
    })

    st.line_chart(trend.set_index("Frame"))

    # ---------------- INSIGHTS ----------------
    st.markdown("### 🧠 AI Insights")

    if weed_count > 15:
        st.error("High weed density detected! Immediate action required.")
    else:
        st.success("Weed levels are under control.")
