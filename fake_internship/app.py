import streamlit as st
import pickle
import numpy as np
import unicodedata
import json
import requests
from scipy.sparse import hstack
from PIL import Image
from bs4 import BeautifulSoup
import re
import pytesseract

pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

# UI CONFIG

st.set_page_config(page_title="Fraud Detector", layout="centered")

st.markdown("""
<style>
.stApp {
    background: linear-gradient(to right, #0f172a, #1e293b);
    color: white;
}

h1 {
    text-align: center;
    color: white;
}

.stButton button {
    background-color: #4f46e5;
    color: white;
    border-radius: 10px;
    padding: 0.6em 1.2em;
    font-weight: bold;
}

.stButton button:hover {
    background-color: #6366f1;
    transform: scale(1.02);
}

textarea {
    border-radius: 10px !important;
}
</style>
""", unsafe_allow_html=True)

# LOAD MODEL

model = pickle.load(open("model.pkl", "rb"))
vectorizer = pickle.load(open("vectorizer.pkl", "rb"))

# LOAD BLACKLIST

try:
    with open("blacklist.json", "r") as f:
        suspicious_companies = json.load(f)
except:
    suspicious_companies = [
        "bharat intern", "codsoft", "code alpha", "oasis infobyte",
        "wayspire", "interntech", "prodigy infotech", "octanet"
    ]

# HELPERS

def normalize_text(text):
    return unicodedata.normalize('NFKD', text)

def clean_text(text):
    text = text.lower()
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    text = re.sub(r'\d+', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_text_from_image(image):
    try:
        text = pytesseract.image_to_string(image, config="--psm 6")
        return text
    except:
        return ""

def extract_text_from_url(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, "html.parser")
        return soup.get_text()
    except:
        return ""

# BLACKLIST UPDATE

def update_blacklist(text, result):
    global suspicious_companies

    if "FAKE" not in result and "HIGH RISK" not in result:
        return

    words = text.lower().split()

    for w in words:
        if len(w) > 4 and ("intern" in w or "tech" in w):
            if w not in suspicious_companies:
                suspicious_companies.append(w)

    with open("blacklist.json", "w") as f:
        json.dump(suspicious_companies, f)

# SCAM TYPE

def classify_scam_type(text, scam_count, is_blacklisted):
    text = text.lower()

    if is_blacklisted:
        return "🏢 Fake / Suspicious Company Scam"
    if "fee" in text:
        return "💰 Fee Scam"
    if "whatsapp" in text or "telegram" in text:
        return "🎣 Phishing Scam"
    if scam_count >= 3:
        return "⚠️ High Risk Scam"
    return "✅ No Specific Scam Type"

# ===============================
# MODEL PREDICTION
# ===============================
def predict_job(text):

    cleaned = clean_text(normalize_text(text))

    text_vec = vectorizer.transform([cleaned])

    scam_keywords = [
        "fee", "payment", "register", "registration", "pay",
        "earn money", "quick money", "no experience",
        "limited seats", "urgent hiring", "work from home",
        "easy job", "instant joining", "training fee"
    ]

    scam_count = sum([1 for w in scam_keywords if w in cleaned])
    is_blacklisted = any(comp in cleaned for comp in suspicious_companies)

    extra = np.array([[len(cleaned), scam_count]])
    final_input = hstack((text_vec, extra))

    score = model.decision_function(final_input)[0]

    # Decision
    if is_blacklisted:
        result = "🚨 HIGH RISK"
    elif scam_count >= 3:
        result = "⚠️ FAKE JOB"
    elif score > 0.3:
        result = "⚠️ LIKELY FAKE"
    elif score < -0.2:
        result = "✅ GENUINE"
    else:
        result = "⚠️ UNCERTAIN"

    # Risk score
    risk_score = min(100,
        scam_count * 15 +
        (40 if is_blacklisted else 0) +
        (10 if "work from home" in cleaned else 0) +
        (10 if "no experience" in cleaned else 0) +
        (20 if "fee" in cleaned else 0)
    )

    return result, scam_count, is_blacklisted, cleaned, risk_score

# ===============================
# DASHBOARD VIEW (NEW)
# ===============================
def show_dashboard(risk_score, scam_count, is_blacklisted):

    st.subheader("📊 Risk Dashboard")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Risk Level", f"{risk_score}/100")

    with col2:
        level = "HIGH" if risk_score > 70 else "MEDIUM" if risk_score > 40 else "LOW"
        st.metric("Risk Category", level)

    with col3:
        st.metric("Blacklist Match", "YES" if is_blacklisted else "NO")

    # Visual bars (simple & understandable)
    st.markdown("### 📈 Risk Breakdown")

    st.progress(min(scam_count * 0.2, 1.0))
    st.caption("Scam Keywords Strength")

    st.progress(1.0 if is_blacklisted else 0.1)
    st.caption("Company Risk")

    st.progress(min(risk_score / 100, 1.0))
    st.caption("Overall Risk Score")

# ===============================
# UI
# ===============================
st.title("🕵️ Job & Internship Fraud Detector")
st.info("⚠️ Provide text, image, or URL of the SAME job posting.")

user_input = st.text_area("Paste Job Description")
uploaded_file = st.file_uploader("Upload Screenshot", type=["png", "jpg", "jpeg"])
url_input = st.text_input("Paste Job URL (Optional)")

if uploaded_file:
    st.image(uploaded_file, caption="Uploaded Image", use_container_width=True)

# ===============================
# RUN
# ===============================
if st.button("🔍 Analyze"):

    combined_text = ""

    if user_input:
        combined_text += user_input

    if uploaded_file:
        combined_text += " " + extract_text_from_image(Image.open(uploaded_file))

    if url_input:
        combined_text += " " + extract_text_from_url(url_input)

    if not combined_text.strip():
        st.warning("Please provide input")
    else:

        result, scam_count, is_blacklisted, cleaned, risk_score = predict_job(combined_text)

        update_blacklist(cleaned, result)

        # ===============================
        # RESULT
        # ===============================
        st.subheader("📊 Result")

        if "HIGH RISK" in result:
            st.error(result)
        elif "FAKE" in result:
            st.error(result)
        elif "GENUINE" in result:
            st.success(result)
        else:
            st.warning(result)

        # ===============================
        # DASHBOARD (NEW)
        # ===============================
        show_dashboard(risk_score, scam_count, is_blacklisted)

        # ===============================
        # SCAM TYPE
        # ===============================
        st.subheader("🧾 Scam Type")
        st.write(classify_scam_type(cleaned, scam_count, is_blacklisted))

        # ===============================
        # REASONS
        # ===============================
        st.subheader("🧠 Reasons")

        reasons = []

        if is_blacklisted:
            reasons.append("Company is in fraud database.")

        if scam_count >= 3:
            reasons.append("Multiple scam indicators detected.")

        if "no experience" in cleaned:
            reasons.append("No experience requirement is suspicious.")

        if "work from home" in cleaned:
            reasons.append("Work-from-home offers may be risky.")

        if scam_count == 0:
            reasons.append("No scam keywords detected.")

        for r in reasons:
            st.write("•", r)