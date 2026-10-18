# 📊 SalesPulse – AI Powered Smart Sales Forecasting System

## 🚀 Overview

SalesPulse is an AI-powered sales forecasting and analytics application designed to help businesses make data-driven decisions. It analyzes historical sales data to generate insights, detect trends, and predict future demand using time series modeling techniques.

The system supports dynamic datasets, performs validation, and provides interactive visualizations for better understanding of sales performance across products, regions, and time.

---

## 🎯 Key Features

### 📈 Forecasting

* Time-series forecasting using ARIMA-based models
* Supports **daily, weekly, and monthly forecasting**
* Forecast horizon can be set to **1, 3 (quarterly), 6 (half-yearly), or 12 months**
* Forecast charts focus on the selected future horizon; historical data is used for model training
* Select an analysis start and end date within the uploaded dataset's available date range
* KPIs, customer/business signals, and analysis tabs recalculate for the selected dates and active category, product, and location filters
* Forecasting trains on all available history independently of the selected analysis date range
* City/location forecasts are aligned to the dataset's latest date, even when a selected location has older observations
* Reliability metrics show their date window and contributing row count, with values displayed to two decimal places
* Forecast an individual city/location or all locations together when location data is available

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

Only three fields are required for sales forecasting and core analysis:

* **Date** — for example `OrderDate`, `date`, `Sale_Date`, or `transaction_date`
* **Quantity sold** — for example `Order Quantity`, `qty`, `units_sold`, or `amount`
* **Sale price** — for example `Sale Price`, `price`, `Unit Price`, `selling_price`,
  or `Price_INR`

The app detects common column-name variants and does not require `Region`. If both
`City` and `Region` are present, location analysis uses `City`; otherwise it uses
the available region/location field.

Optional columns enrich the analysis:

* **Product and category:** `Product_Name`, `Category`, `Sub_Category`, `Brand`
* **Customer reliability:** `Customer_Satisfaction`, `Rating`, `Reviews_Count`,
  `Return_Rate_Percent`, `Delivery_Days`, `Repeat_Customer`
* **Pricing and profitability:** `Discount_Percent`, `Final_Price_INR`,
  `Competitor_Price_INR`, `Profit_Margin_Percent`
* **Inventory and demand:** `Stock_Available`, `Demand_Level`, `Season`, `Weather`
* **Marketing and shopping funnel:** `Website_Visits`, `Cart_Additions`,
  `Conversion_Rate_Percent`, `Ad_Spend_INR`
* **Customer context:** `Customer_Age`, `Customer_Gender`, `Payment_Method`,
  `City`, `State`, `Region`

Available customer fields are summarized on the dashboard to show customer
satisfaction, reviews, returns, delivery experience, and repeat-customer share.



## 🧪 How to Use

1. Upload your dataset (CSV/XLSX)
2. Select the analysis start and end dates from within the dataset's date range
3. Select forecasting granularity (Daily/Weekly/Monthly) and a 1, 3, 6, or 12 month forecast horizon
4. Optionally filter by category, product, or city/location
5. Explore:

   * Forecast tab
   * Category analysis
   * Price insights
   * AI insights & history
6. View predictions and insights

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
live demo : https://piyush0s-salespulse-app-gqrl6b.streamlit.app/
---

## 📄 License

This project is for educational and demonstration purposes.

---

## 💡 Final Note

SalesPulse is designed not just as a project, but as a **real-world ready analytics system** capable of handling complex datasets and delivering actionable insights.
