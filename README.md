# 🛒 Shopping Browser Assistance — Assignment Project

A FastAPI and Streamlit-based web application that scrapes real-time product listings from **Amazon** and **Flipkart**, allowing users to compare prices, ratings, and reviews through an intuitive web interface.

---

## 📌 Features

- 🔍 **Product Search**: Fetch and display real-time product listings from Amazon and Flipkart.
- ⚡ **Asynchronous Multi-Agent Scraping**: Concurrent scraping pipeline built with `Selenium`, `BeautifulSoup`, and `aiohttp`.
- 📊 **Comparison Table**: Side-by-side comparison of product details including price, ratings, and source.
- 🎛️ **Sorting & Filtering**: Sort products by price or rating and filter by platform.
- 🖥️ **Interactive UI**: Streamlit-based front-end styled with custom CSS for a clean shopping research experience.

---

## 🛠️ Tech Stack

- **Backend**: FastAPI, Python Asyncio, Selenium, BeautifulSoup, aiohttp
- **Frontend**: Streamlit with custom CSS
- **Tools**: Pandas, Pillow, Requests

---

## 📂 Project Structure

├── app.py # Streamlit frontend app
├── pain.py # Scraping agents for Amazon and Flipkart
├── requirements.txt # Python dependencies
├── README.md # Project overview


---

## 🚀 How to Run

1. **Install dependencies**

```bash
pip install -r requirements.txt 
```
2. Run the application
````
streamlit run app.py
````
