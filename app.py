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
from urllib.parse import urlparse

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
        res = requests.get(url, headers=headers, timeout=10)

        soup = BeautifulSoup(res.text, "html.parser")

        # Remove scripts/styles
        for tag in soup(["script", "style", "noscript"]):
            tag.extract()

        text = soup.get_text(separator=" ")

        # Clean excessive whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        # ❗ IMPORTANT: If text too small → likely JS page
        if len(text) < 500:
            return "JOB_PAGE_DYNAMIC_CONTENT_NOT_LOADED"

        return text

    except:
        return ""

def get_domain(url):
    try:
        return urlparse(url).netloc.lower()
    except:
        return ""
    
def extract_company_name(text):
    text = text.lower()

    patterns = [
        r'at ([a-zA-Z0-9\s]+)',
        r'company[:\-]\s*([a-zA-Z0-9\s]+)',
        r'([a-zA-Z0-9\s]+) is hiring',
        r'join ([a-zA-Z0-9\s]+)'
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            name = match.group(1).strip()
            # Avoid garbage extraction
            if len(name.split()) <= 5:
                return name

    return None
    
# BLACKLIST UPDATE

def update_blacklist(company_name, result):
    global suspicious_companies

    if not company_name:
        return

    # Only update if STRONG FAKE
    if "FAKE JOB DETECTED" not in result and "HIGH RISK" not in result:
        return

    company_name = company_name.lower().strip()

    if company_name not in suspicious_companies:
        suspicious_companies.append(company_name)

        try:
            with open("blacklist.json", "w") as f:
                json.dump(suspicious_companies, f, indent=4)
        except:
            pass

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

    # TEXT VECTOR
    text_vec = vectorizer.transform([cleaned])

    # FEATURES (IMPORTANT: MUST MATCH TRAINING)
    text_length = len(cleaned)

    scam_patterns = [
        "fee", "payment", "pay", "registration",
        "training fee", "onboarding fee",
        "refundable", "security deposit",
        "administrative charge", "processing fee",
        "limited seats", "apply now",
        "instant joining", "guaranteed placement",
        "exclusive program"
    ]

    scam_count = sum(1 for word in scam_patterns if word in cleaned)

    # BLACKLIST CHECK
    is_blacklisted = any(comp.lower() in cleaned for comp in suspicious_companies)

    trusted_domains = [
        "google.com",
        "linkedin.com",
        "indeed.com",
        "naukri.com",
        "zoho.com"
    ]

    # FINAL INPUT (MATCH TRAINING EXACTLY)
    extra = np.array([[text_length, scam_count]])
    final_input = hstack((text_vec, extra))

    # MODEL SCORE
    score = model.decision_function(final_input)[0]

    # ===============================
    # 🔥 RISK ENGINE (IMPROVED)
    # ===============================
    risk_points = 0

    # Base signals
    risk_points += scam_count * 20

    # Hidden fee detection (strong)
    if any(x in cleaned for x in ["refundable", "charge", "deposit", "processing"]):
        risk_points += 40

    # Psychological tricks
    if any(x in cleaned for x in ["limited seats", "apply now", "exclusive"]):
        risk_points += 10

    # Weak signals (controlled)
    if "urgent" in cleaned and scam_count >= 2:
        risk_points += 10

    if "work from home" in cleaned and "no experience" in cleaned:
        risk_points += 15

    # Blacklist
    if is_blacklisted:
        risk_points += 50

    # If domain is trusted → reduce risk
    if any(td in cleaned for td in trusted_domains):
        risk_points -= 10

    # ===============================
    # ✅ LEGITIMACY SIGNALS (NEW)
    # ===============================
    legit_score = 0

    if "website" in cleaned:
        legit_score += 10

    if "years of experience" in cleaned or "founded" in cleaned:
        legit_score += 10

    if "responsibilities" in cleaned:
        legit_score += 10

    if "requirements" in cleaned:
        legit_score += 10

    if "about" in cleaned:
        legit_score += 5

    if "certificate" in cleaned and "recommendation" in cleaned:
        legit_score += 5  # common but not strong

    # Internship but structured → reduce risk
    if "internship" in cleaned and "responsibilities" in cleaned and "requirements" in cleaned:
        risk_points -= 10

    # Reduce risk using legit score
    risk_points -= legit_score

    # ===============================
    # COMPANY DETECTION
    # ===============================
    company_name = extract_company_name(text)

    # ===============================
    # 🔥 FINAL DECISION (BALANCED)
    # ===============================
    if is_blacklisted:
        result = "🚨 HIGH RISK"

    elif risk_points >= 60:
        result = "⚠️ FAKE JOB"

    elif risk_points >= 40:
        result = "⚠️ LIKELY FAKE"

    elif risk_points <= 10 and score < -0.3:
        result = "✅ GENUINE"

    elif score < -0.8:
        result = "✅ GENUINE"

    else:
        result = "⚠️ UNCERTAIN"

    # Risk score (for dashboard)
    risk_score = max(0, min(100, risk_points))

    return result, scam_count, is_blacklisted, cleaned, risk_score, company_name

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
st.info("If you give only url, re-check it with text or screenshot to bypass dynamic content issues.")

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
        url_text = extract_text_from_url(url_input)

        #if url_text == "JOB_PAGE_DYNAMIC_CONTENT_NOT_LOADED":
            #st.warning("⚠️ This job page uses dynamic loading. Please paste job description or upload screenshot.")
        #else:
            #combined_text += " " + url_text

        combined_text += " " + url_text

    if not combined_text.strip():
        st.warning("Please provide input")
    else:

        result, scam_count, is_blacklisted, cleaned, risk_score, company_name = predict_job(combined_text)
        update_blacklist(company_name, result)

        # RESULT

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