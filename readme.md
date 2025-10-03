# 🛒 E-Commerce Competitor Strategy Dashboard

A professional dashboard for analyzing **e-commerce competitors**, built with **Python**.  
This tool empowers businesses to **scrape product data**, **analyze customer sentiment**, **compare competitors**,  
and **query documents using Retrieval-Augmented Generation (RAG)** — all in one place.

---

## 🚀 Features

- **Automated Data Collection**  
  Scrape product listings and reviews from Flipkart with Selenium and BeautifulSoup.
- **Data Processing & Sentiment Analysis**  
  Clean, structure, and analyze data using pandas and TextBlob.
- **Interactive Dashboard**  
  Visualize product, pricing, discount, and sentiment insights.
- **Competitor Comparison**  
  Compare multiple brands on pricing, ratings, discounts, and more.
- **Strategic Recommendations**  
  Auto-generated insights for competitive positioning.
- **Document Q&A (RAG Module)**  
  Query `.txt`, `.pdf`, `.csv`, or `.md` documents using Google GenAI and Groq LLaMA 3.
- **Email Alerts**  
  Receive notifications for significant competitor changes or events.

---

## 🛠️ Tech Stack

- Python (core language)
- Selenium + BeautifulSoup (web scraping)
- pandas, numpy (data processing)
- TextBlob (sentiment analysis)
- Streamlit (dashboard)
- Plotly / Matplotlib (visualizations)
- FAISS, LangChain, Google GenAI, Groq (RAG Document QA)
- Email (for alerts)

---

## 📂 Project Structure

```
infosys_internship/
├── __pycache__/
├── data/
├── env/
├── my_docs/
│   ├── mobile_yesterday.csv
│   ├── mobile.csv
│   ├── review_yesterday.csv
│   └── review.csv
├── out/
├── ingestion.py
├── main.py
├── model.py
├── notification.py
├── products.py
├── rag.py
├── readme.md
├── requirements.txt
```

---

## 📦 Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/Madhu-0007/infosys_internship.git
   cd infosys_internship
   ```

2. **(Optional) Create a virtual environment**

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

4. **Configure environment variables and email settings**

   Place your API keys and email credentials in the appropriate configuration file or as environment variables (see code for details).

---

## ▶️ Usage

1. **Run the main dashboard**

   ```bash
   python main.py
   ```

2. **Document Q&A (RAG)**

   - Place `.txt`, `.pdf`, `.csv`, or `.md` files in the `my_docs/` folder.
   - Use the RAG pipeline to query your documents.

3. **Email Alerts**

   - Email notifications will be sent automatically for key competitor events based on your configuration.

---

## 📝 Example Use Cases

- **Product Analysis:** Explore and compare pricing, discounts, ratings, and availability.
- **Customer Sentiment:** Analyze sentiment trends from reviews.
- **Competitor Comparison:** Interactive charts for multi-brand comparison.
- **Document Q&A:** Ask questions like "Summarize the reviews" or "What are competitors’ pricing strategies?"
- **Strategic Recommendations:** Receive actionable insights for your business.

---

## 🤝 Contributing

Contributions are welcome! Fork the repository and submit a pull request.

---

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## 👤 Contact

Developed by [Madhu-0007](https://github.com/Madhu-0007).