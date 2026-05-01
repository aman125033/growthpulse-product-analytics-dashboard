# 📊 GrowthPulse: Product Analytics Dashboard

A senior-level product analytics dashboard built using SQL, Python, and Streamlit to analyze user funnel performance, retention behavior, and A/B testing impact.

---

## 🚀 Project Overview

This project simulates how product and growth teams analyze user behavior to drive business decisions.

It answers key leadership questions:

* Where are users dropping off in the funnel?
* Which segments are underperforming?
* How strong is user retention?
* Did the experiment improve conversion?
* What is the revenue opportunity?

---

## 📈 Key Features

### 1. Executive Summary

* KPI tracking (Users, Conversion, Revenue, Retention)
* Business health signals
* Revenue opportunity estimation

### 2. Funnel Analysis

* Conversion funnel visualization
* Drop-off identification
* Segment-level performance (device, country, campaign)
* Revenue opportunity by segment

### 3. Retention Analysis

* D1, D7, D30 retention tracking
* Cohort retention heatmap

### 4. A/B Testing

* Control vs Variant comparison
* Conversion lift calculation
* Statistical significance (p-value)
* Business recommendation

---

## 🛠️ Tech Stack

* Python (Pandas, NumPy)
* SQL (SQLite)
* Streamlit (Dashboard UI)
* Plotly (Visualization)
* SciPy (Statistical testing)

---

## ▶️ How to Run

```bash
python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

python scripts/generate_data.py
streamlit run app.py
```

---

## 💡 Why This Project Matters

This project demonstrates how analytics is used beyond reporting — to:

* drive product decisions
* prioritize growth opportunities
* quantify business impact

---

## 📌 Author

Aman Sachdeva
