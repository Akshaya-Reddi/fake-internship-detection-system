# 🕵️ Job & Internship Fraud Detection System

A machine learning-powered web application that detects fraudulent job and internship postings using NLP, rule-based risk scoring, and a trained classification model.

🔗 **Live App:**
[https://fake-internship-detection-system.onrender.com](https://fake-internship-detection-system.onrender.com)

---

## 📌 Overview

Online job platforms often contain fake or misleading postings that exploit job seekers. This project aims to automatically detect such fraudulent listings using:

* Natural Language Processing (NLP)
* Machine Learning (SVM Model)
* Rule-based Risk Scoring System
* Blacklist-based company detection

---

## 🚀 Features

* 🔍 Analyze job descriptions, screenshots, or URLs
* 🧠 ML-based classification (Genuine / Fake / Likely Fake / Uncertain)
* 📊 Risk score dashboard (0–100)
* 🏢 Automatic blacklist detection & updates
* 🖼 OCR support for image-based job posts
* 🌐 URL scraping support (static content)
* 🧾 Scam type classification (Fee Scam, Phishing, etc.)

---

## 🧠 How It Works

### 1. Input Sources

* Job description (text)
* Screenshot (OCR via Tesseract)
* Job URL (HTML scraping)

### 2. Text Processing

* Lowercasing
* Removing URLs, symbols, numbers
* Normalization

### 3. Feature Extraction

* TF-IDF Vectorization (5000 features)
* Additional features:

  * Text length
  * Scam keyword count

### 4. Machine Learning Model

* Model Used: **Support Vector Machine (LinearSVC)**
* Handles imbalanced data using class weighting

### 5. Rule-Based Risk Scoring

| Feature                                   | Score     |
| ----------------------------------------- | --------- |
| Scam keywords                             | +20 each  |
| Hidden fees (deposit, charge)             | +40       |
| Psychological triggers                    | +10       |
| Urgency signals                           | +10       |
| WFH + No experience                       | +15       |
| Blacklisted company                       | +50       |
| Trusted domain                            | -10       |
| Legit signals (requirements, about, etc.) | -5 to -10 |

### 6. Final Decision Logic

* **≥ 60** → Fake Job
* **40–59** → Likely Fake
* **≤ 10 + ML confidence** → Genuine
* Else → Uncertain

---

## 📊 Model Performance

* Accuracy: ~95% (approximate)
* Precision: High for fake detection
* Recall: Balanced using class_weight
* F1 Score: Optimized for fraud detection

*(Note: Metrics depend on dataset split and preprocessing)*

---

## 🧾 Scam Types Detected

* 💰 Fee Scam
* 🎣 Phishing Scam
* 🏢 Fake Company Scam
* ⚠️ High Risk Scam

---

## 🛠 Tech Stack

* **Frontend:** Streamlit
* **Backend:** Python
* **ML/NLP:** Scikit-learn, TF-IDF
* **OCR:** Tesseract
* **Web Scraping:** BeautifulSoup
* **Deployment:** Render

---

## 📂 Project Structure

```
├── app.py                 # Streamlit web app
├── model.pkl              # Trained ML model
├── vectorizer.pkl         # TF-IDF vectorizer
├── blacklist.json         # Suspicious companies list
├── fake_job_postings.csv  # Dataset
├── README.md              # Project documentation
```

---

## 📦 Installation & Setup

### 1. Clone Repository

```
git clone https://github.com/your-username/fraud-detection.git
cd fraud-detection
```

### 2. Install Dependencies

```
pip install -r requirements.txt
```

### 3. Install Tesseract (Required for OCR)

* Linux:

```
sudo apt install tesseract-ocr
```

### 4. Run the App

```
streamlit run app.py
```

---

## 📌 Applications

* Job portal verification systems
* Resume/job screening tools
* Fraud detection in recruitment platforms
* Career guidance systems

---

## ✅ Advantages

* Combines ML + rule-based logic (high accuracy)
* Handles multiple input formats
* Real-time analysis
* Easy to use UI

---

## ⚠️ Limitations

* Dynamic websites may not load properly
* OCR accuracy depends on image quality
* Some genuine jobs may look suspicious (false positives)
* Rules are heuristic-based, not universally perfect

---

## 🔮 Future Scope

* Deep learning models (BERT, LSTM)
* Real-time API integration with job portals
* Browser extension for live detection
* Advanced company verification (LinkedIn/Glassdoor APIs)
* Multilingual support

---

## 📚 Dataset

* Source: Public fake job postings dataset
* Features used:

  * Title
  * Description
  * Requirements
  * Company profile
  * Fraud label (0/1)

---

## 📖 References

* Fake Job Postings Dataset (Kaggle)
* Research on fraud detection using NLP
* Scikit-learn documentation
* Tesseract OCR documentation

---

## 👨‍💻 Author

Akshaya
AI & ML Student
