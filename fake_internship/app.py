import streamlit as st
import pickle
import numpy as np
import unicodedata
from scipy.sparse import hstack

# ===============================
# Load model & vectorizer
# ===============================
model = pickle.load(open("model.pkl", "rb"))
vectorizer = pickle.load(open("vectorizer.pkl", "rb"))

# ===============================
# Helper Functions
# ===============================
def normalize_text(text):
    return unicodedata.normalize('NFKD', text)

def clean_text(text):
    import re
    text = text.lower()
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    text = re.sub(r'\d+', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def predict_job(text):
    normalized = normalize_text(text)
    cleaned = clean_text(normalized)
    
    text_vec = vectorizer.transform([cleaned])
    
    text_length = len(cleaned)
    
    scam_keywords = [
        "fee", "payment", "register", "registration", "pay",
        "earn money", "quick money", "no experience",
        "limited seats", "urgent hiring", "work from home",
        "easy job", "instant joining", "training fee"
    ]
    
    suspicious_companies = [
        "bharat intern", "codsoft", "code alpha", "oasis infobyte",
        "wayspire", "interntech", "prodigy infotech", "octanet"
    ]
    
    scam_count = sum([1 for word in scam_keywords if word in cleaned])
    is_blacklisted = any(comp in cleaned for comp in suspicious_companies)
    
    extra = np.array([[text_length, scam_count]])
    final_input = hstack((text_vec, extra))
    
    score = model.decision_function(final_input)[0]
    
    # Decision logic
    if is_blacklisted:
        result = "🚨 HIGH RISK: Suspicious Company"
        color = "red"
    elif scam_count >= 3:
        result = "⚠️ FAKE JOB DETECTED"
        color = "red"
    elif score > 0.3:
        result = "⚠️ LIKELY FAKE JOB"
        color = "orange"
    elif scam_count == 0 and score < 0.2:
        result = "✅ GENUINE JOB"
        color = "green"
    elif score < -0.2:
        result = "✅ GENUINE JOB"
        color = "green"
    else:
        result = "⚠️ UNCERTAIN — NEED REVIEW"
        color = "orange"
    
    return result, score, scam_count, color

# ===============================
# UI DESIGN
# ===============================
st.set_page_config(page_title="Fraud Detector", layout="centered")

st.title("🕵️‍♂️ Job & Internship Fraud Detector")
st.markdown("### Detect fake job & internship postings instantly")

user_input = st.text_area("Paste Job Description Here", height=200)

if st.button("🔍 Analyze Job"):
    if user_input.strip() == "":
        st.warning("Please enter job description")
    else:
        result, score, scam_count, color = predict_job(user_input)
        
        # Result display
        if color == "red":
            st.error(result)
        elif color == "green":
            st.success(result)
        else:
            st.warning(result)
        
        st.write(f"**Confidence Score:** {round(score, 3)}")
        st.write(f"**Scam Indicators Detected:** {scam_count}")