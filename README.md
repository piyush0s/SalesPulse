# 📊 SalesPulse – AI Powered Smart Sales Forecasting System

## 🚀 Overview

SalesPulse is an AI-powered sales forecasting and analytics application designed to help businesses make data-driven decisions. It analyzes historical sales data to generate insights, detect trends, and predict future demand using time series modeling techniques.

The system supports dynamic datasets, performs validation, and provides interactive visualizations for better understanding of sales performance across products, regions, and time.

---

## 🎯 Key Features

### 📈 Forecasting

* Time-series forecasting using ARIMA-based models
* Supports **daily and weekly forecasting**
* Predicts future demand based on historical data

### 📊 Data Analysis

* Product-wise performance analysis
* Region-wise sales insights
* Seasonal trend detection
* Price vs demand analysis

### 🧠 AI Insights

* Automated insights generation
* Trend detection (growth/decline)
* Best-performing product & region identification

### ⚠️ Data Validation

* Detects:

  * Missing values
  * Invalid entries (negative price/units)
  * Incorrect data formats
* Shows user-friendly error notifications

### 📂 Flexible Data Input

* Upload any CSV/Excel dataset
* Works with dynamic data (no fixed size required)

---

## 🛠️ Tech Stack

| Category      | Technology Used     |
| ------------- | ------------------- |
| Frontend      | Streamlit           |
| Backend       | Python              |
| Data Handling | Pandas, NumPy       |
| Visualization | Matplotlib, Seaborn |
| ML Model      | ARIMA (statsmodels) |

---

## 📁 Dataset Requirements

Minimum required columns:

* `Date`
* `Units_Sold`
* `Price`
* `Region` 

Optional columns:

* `Product_ID`
* `Product_Name`
* `Revenue` 



## 🧪 How to Use

1. Upload your dataset (CSV/XLSX)
2. Select forecasting frequency (Daily/Weekly)
3. Choose number of periods to forecast
4. Explore:

   * Forecast tab
   * Category analysis
   * Price insights
   * AI insights & history
5. View predictions and insights

---

## ⚠️ Error Handling

The system handles common issues such as:

* `KeyError` (missing columns)
* Insufficient data for forecasting
* Invalid dataset format

Example:

```
Series too short for ARIMA → Requires at least 10+ observations
```

---

## 📌 Project Objectives

* Help small businesses understand sales patterns
* Enable smarter pricing and inventory decisions
* Provide easy-to-use AI forecasting tools

---

## 🔮 Future Enhancements

* LSTM/Deep Learning models
* Real-time dashboard integration
* API-based deployment
* User authentication system
* Cloud deployment (AWS/GCP)

---

## 👨‍💻 Author

**Piyush Sharma**
BCA Student | Data Science & AI Enthusiast

---

## 📄 License

This project is for educational and demonstration purposes.

---

## 💡 Final Note

SalesPulse is designed not just as a project, but as a **real-world ready analytics system** capable of handling complex datasets and delivering actionable insights.
