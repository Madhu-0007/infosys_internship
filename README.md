# 🛒 E-Commerce Competitor Strategy Dashboard  

A professional dashboard for analyzing **e-commerce competitors**, built with **Streamlit**.  
This tool empowers businesses to **scrape product data**, **analyze customer sentiment**, **compare competitors**,  
and **query documents using RAG** — all in one place.  

---

## 🚀 Features  

### 🔹 Data Collection  
- Automated product & review scraping from Flipkart using **Selenium + BeautifulSoup**.  
- Supports multiple products, categories, and competitor listings.  

### 🔹 Data Processing  
- Cleans, structures, and stores scraped data with **pandas**.  
- Prepares product & sentiment data for visualization and analysis.  

### 🔹 Interactive Dashboard (Streamlit)  
- **Product Analysis**: Explore product prices, discounts, ratings, and availability.  
- **Customer Sentiment**: Sentiment analysis of reviews using **TextBlob** with trend visualizations.  
- **Competitor Comparison**: Compare brands/competitors via pricing, discounts, ratings, and sentiment charts.  
- **Strategic Recommendations**: Auto-generated insights for competitive positioning.  

### 🔹 Document Q&A (RAG Module)  
- Load `.txt`, `.pdf`, `.csv`, or `.md` files.  
- Build embeddings using **Google Generative AI (Gemini)**.  
- Query documents with **Groq LLaMA 3** via FAISS vector search.  
- Retrieve citations and summarized answers from your data.  

---

## 🛠️ Tech Stack  

- **Python**  
- **Streamlit** (Dashboard)  
- **Selenium + BeautifulSoup** (Web scraping)  
- **pandas, numpy** (Data processing)  
- **Plotly / Matplotlib** (Charts & visualizations)  
- **TextBlob / Scikit-learn** (Sentiment analysis)  
- **LangChain + FAISS + Google GenAI + Groq** (RAG Document QA)  

---

## 📂 Project Structure  

```

ecommerce-competitor-dashboard/
│── README.md              # Project overview & usage
│── requirements.txt       # Dependencies
│── setup.md               # Setup guide / notes
│── .gitignore             # Ignore venv, __pycache__, data, etc.
│
├── env/                   # Environment variables
│   └── .env               # Contains API keys (Google, Groq, etc.)
│
├── my_docs/               # Input documents & scraped CSVs
│   ├── mobile.csv
│   ├── mobile_yesterday.csv
│   ├── review.csv
│   └── review_yesterday.csv
│
├── data/                  # Processed/cleaned data
│   ├── cleaned_mobile.csv
│   └── cleaned_reviews.csv
│
├── out/                   # Optional: reports, exports, plots
│
├── faiss_index/           # Vector index for RAG
│
├── scripts/               # Core Python modules
│   ├── ingestion.py       # Data cleaning & preprocessing
│   ├── products.py        # Scraper or product utilities
│   ├── notification.py    # Notifications / alerts
│   ├── model.py           # ML models (sentiment, etc.)
│   └── rag.py             # RAG Doc Q&A pipeline
│
└── main.py                # Streamlit dashboard (entry point)

````

## 📦 Installation

1. **Clone the repository**

```bash
git clone https://github.com/Madhu-0007/infosys_internship.git
cd infosys_internship
```

2. **Create a virtual environment (recommended)**

```bash
python -m venv venv
# Activate on macOS/Linux
source venv/bin/activate
# Activate on Windows
venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Set up environment variables**

Create a file at `env/.env` with:

```
GOOGLE_API_KEY=your_google_api_key
GROQ_API_KEY=your_groq_api_key
```

---

## ▶️ Running the App

### 1. Run the dashboard

```bash
streamlit run app.py
```

The app will launch in your browser at **[http://localhost:8501](http://localhost:8501)**.

### 2. Run document Q&A (RAG)

```bash
python doc_query_rag.py
```

* Place `.txt`, `.pdf`, `.csv`, or `.md` files in the `my_docs/` folder.
* The script will index your documents and let you ask custom questions.

---

## 📝 Example Usage

* **Product Analysis** → Explore competitor pricing, discounts, ratings.
* **Customer Sentiment** → View sentiment breakdowns & word clouds.
* **Competitor Comparison** → Compare multiple competitors interactively.
* **Recommendations** → Receive data-driven strategy insights.
* **Doc Q&A** → Ask questions like *"Summarize the reviews"* or *"What are competitors’ pricing strategies?"*.


