import os
import sys
import shutil
import subprocess
import time
import pandas as pd
import streamlit as st
import plotly.express as px
import numpy as np
from textblob import TextBlob

# ---------------- Streamlit Page Config ----------------
st.set_page_config(
    page_title="E-Commerce Competitor Strategy Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- Custom Styling ----------------
st.markdown("""
<style>
.main-header {font-size:2.3rem;color:#1f77b4;text-align:center;margin-bottom:1rem;}
.section-header {font-size:1.6rem;color:#2e86ab;margin-top:2rem;margin-bottom:1rem;}
.positive-sentiment { color:#28a745; }
.negative-sentiment { color:#dc3545; }
.neutral-sentiment  { color:#ffc107; }
</style>
""", unsafe_allow_html=True)


# ---------------- Orchestration (Scrape → Ingest → Notify) ----------------
def rotate_snapshots():
    """Copy today's CSVs to yesterday snapshots for diff-based notifications."""
    try:
        os.makedirs("My_docs", exist_ok=True)
        src_dst_pairs = [
            ("My_docs/mobile.csv", "My_docs/mobile_yesterday.csv"),
            ("My_docs/review.csv", "My_docs/review_yesterday.csv"),
        ]
        for src, dst in src_dst_pairs:
            if os.path.exists(src):
                shutil.copyfile(src, dst)
    except Exception as e:
        st.warning(f"Snapshot rotation issue: {e}")


def run_script(path):
    """Run a Python script with the current interpreter; surface concise errors."""
    try:
        subprocess.run([sys.executable, path], check=True)
    except subprocess.CalledProcessError as e:
        st.error(f"Failed running {path}: {e}")
        raise


def trigger_notifications():
    try:
        import notification as notif
        notif.check_price_drops()
        notif.check_negative_reviews()
    except Exception as e:
        st.warning(f"Notifications step encountered an issue: {e}")


def orchestrate_pipeline():
    """End-to-end run: rotate → scrape → ingest → notify. Runs once per session."""
    with st.spinner("Preparing latest data (scrape → ingest → notify)..."):
        rotate_snapshots()
        run_script("product.py")
        run_script("ingestion.py")
        # small pause to ensure files are flushed
        time.sleep(0.5)
        trigger_notifications()


# ---------------- Competitor Analyzer ----------------
class CompetitorAnalyzer:
    def __init__(self):
        self.products_df = None
        self.reviews_df = None

    def load_data(self,
                  products_file="data/cleaned_mobile.csv",
                  reviews_file="data/cleaned_reviews.csv") -> bool:
        """Load cleaned product & review datasets, apply schema normalization."""
        try:
            # Load product data
            if os.path.exists(products_file):
                self.products_df = pd.read_csv(products_file)
                self.products_df.rename(columns={
                    "mobilename": "product_name",
                    "sellingprice": "price",
                    "discountoffering": "discount",
                    "rating": "rating",
                    "productid": "product_id",
                    "source": "source"
                }, inplace=True)
            else:
                st.error(f"Missing {products_file}")
                return False

            # Load review data
            if os.path.exists(reviews_file):
                self.reviews_df = pd.read_csv(reviews_file)
                self.reviews_df.rename(columns={
                    "mobilename": "product_name",
                    "review": "review_text",
                    "rating": "rating",
                    "reviewdate": "date",
                    "productid": "product_id",
                    "source": "source"
                }, inplace=True)
            else:
                st.error(f"Missing {reviews_file}")
                return False

            # Convert data types
            self.products_df["price"] = pd.to_numeric(
                self.products_df["price"], errors="coerce")
            self.products_df["discount"] = pd.to_numeric(
                self.products_df["discount"], errors="coerce").fillna(0)
            self.products_df["rating"] = pd.to_numeric(
                self.products_df["rating"], errors="coerce").fillna(0)
            self.reviews_df["date"] = pd.to_datetime(
                self.reviews_df["date"], errors="coerce")

            return True
        except Exception as e:
            st.error(f"Error loading data: {e}")
            return False

    # ---------- Sentiment Analysis ----------
    def analyze_sentiment(self, text):
        """Classify text sentiment into positive, negative, or neutral."""
        polarity = TextBlob(str(text)).sentiment.polarity
        if polarity > 0.1:
            return "positive", polarity
        elif polarity < -0.1:
            return "negative", polarity
        else:
            return "neutral", polarity

    def get_sentiment_analysis(self, product_name):
        """Return sentiment distribution & average score for a given product."""
        df = self.reviews_df[self.reviews_df["product_name"] == product_name].copy()
        if df.empty:
            return None

        sentiments = []
        for r in df["review_text"]:
            s, sc = self.analyze_sentiment(r)
            sentiments.append({"sentiment": s, "score": sc})
        s_df = pd.DataFrame(sentiments)

        return {
            "total_reviews": len(df),
            "sentiment_distribution": s_df["sentiment"].value_counts().to_dict(),
            "average_sentiment_score": s_df["score"].mean(),
            "reviews_data": df
        }


# ---------------- Dashboard Sections ----------------
def product_analysis(analyzer, product_name):
    """Display product metrics, sentiment distribution, and recent reviews."""
    st.markdown('<div class="section-header">Product Analysis</div>', unsafe_allow_html=True)
    prod = analyzer.products_df.query("product_name == @product_name").iloc[0]

    # Basic product metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Price", f"₹{int(prod['price'])}")
    c2.metric("Discount", f"{prod['discount']}%")
    c3.metric("Rating", f"{prod['rating']}/5")
    c4.metric("Source", prod["source"])

    # Customer sentiment analysis
    st.subheader("Customer Sentiment")
    sdata = analyzer.get_sentiment_analysis(product_name)
    if sdata:
        col1, col2 = st.columns([2, 1])
        with col1:
            fig = px.pie(values=list(sdata["sentiment_distribution"].values()),
                         names=list(sdata["sentiment_distribution"].keys()),
                         title="Sentiment Distribution")
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.metric("Total Reviews", sdata["total_reviews"])
            st.metric("Avg Sentiment Score", f"{sdata['average_sentiment_score']:.2f}")

        st.markdown("### Recent Reviews")
        for _, r in sdata["reviews_data"].head(5).iterrows():
            sent, sc = analyzer.analyze_sentiment(r["review_text"])
            with st.expander(f"{r['userid']} - Rating: {r['rating']}"):
                st.write(r["review_text"])
                st.write(f"Sentiment: *{sent}* (score {sc:.2f})")
    else:
        st.info("No reviews available.")


def competitor_comparison(analyzer, product_name):
    """Compare product with competitors in same source and nearby price range."""
    st.markdown('<div class="section-header">Competitor Comparison</div>', unsafe_allow_html=True)

    source = analyzer.products_df.query("product_name==@product_name")["source"].iloc[0]
    comp = analyzer.products_df.query("source==@source and product_name!=@product_name")
    if comp.empty:
        st.info("No competitor data available.")
        return

    # Competitor price comparison chart
    fig = px.bar(comp, x="product_name", y="price", color="price",
                 title=f"Competitor Price Comparison ({source})")
    st.plotly_chart(fig, use_container_width=True)

    # Competitor table
    st.dataframe(comp[["product_name", "price", "discount", "rating", "url"]])

    # Interactive selection
    st.markdown("### Explore Competitors Near Selected Product Price")
    selected_product = st.selectbox("Select competitor product", comp["product_name"].unique())

    if selected_product:
        selected_price = comp.query("product_name==@selected_product")["price"].values[0]
        st.markdown(f"*Showing products around ₹{selected_price}*")

        lower_bound, upper_bound = selected_price * 0.8, selected_price * 1.2
        nearby_products = analyzer.products_df.query(
            "price >= @lower_bound and price <= @upper_bound"
        ).copy()

        sentiment_scores = []
        for prod in nearby_products["product_name"]:
            sentiment_info = analyzer.get_sentiment_analysis(prod)
            sentiment_scores.append(sentiment_info["average_sentiment_score"] if sentiment_info else np.nan)
        nearby_products["avg_sentiment"] = sentiment_scores
        nearby_products.sort_values(by="avg_sentiment", ascending=False, inplace=True)

        cols = ["product_name", "source", "price", "discount", "rating", "avg_sentiment", "url"]
        st.dataframe(nearby_products[cols])

        same_product_sources = analyzer.products_df.query("product_name==@selected_product")
        st.markdown(f"'{selected_product}' Price & Discount Across Sources:")
        st.dataframe(same_product_sources[["source", "price", "discount", "rating", "url"]])


def strategic_recommendations(analyzer, product_name):
    """Generate pricing, discount, sentiment, and review-based strategy suggestions."""
    st.markdown('<div class="section-header">Strategic Recommendations</div>', unsafe_allow_html=True)

    prod = analyzer.products_df.query("product_name==@product_name").iloc[0]
    sdata = analyzer.get_sentiment_analysis(product_name)
    avg_score = sdata["average_sentiment_score"] if sdata else 0
    total_reviews = sdata["total_reviews"] if sdata else 0

    strategy_lines = []

    if prod["price"] > 50000:
        strategy_lines.append(f"- High price (₹{prod['price']}). Consider limited-time discounts or EMI options.")
    elif prod["price"] < 20000:
        strategy_lines.append(f"- Competitive price (₹{prod['price']}) can be marketed aggressively.")

    if prod["discount"] < 5:
        strategy_lines.append(f"- Low discount ({prod['discount']}%). Increase for better customer pull.")
    elif prod["discount"] > 20:
        strategy_lines.append(f"- High discount ({prod['discount']}%). Maintain during campaigns.")

    if avg_score < 0:
        strategy_lines.append("- Negative sentiment detected. Investigate recurring complaints.")
    elif avg_score < 0.2:
        strategy_lines.append("- Neutral sentiment. Enhance product features or promotions.")
    else:
        strategy_lines.append("- Positive sentiment! Highlight strengths in campaigns.")

    if total_reviews < 10:
        strategy_lines.append("- Very few reviews. Encourage customers to share feedback.")
    elif total_reviews > 100:
        strategy_lines.append("- High review volume. Mine insights for product improvements.")

    sentiment_status = "Needs Improvement" if avg_score < 0.2 else "Good" if avg_score < 0.5 else "Excellent"
    sentiment_class = "negative-sentiment" if avg_score < 0.2 else "neutral-sentiment" if avg_score < 0.5 else "positive-sentiment"

    st.markdown(
        f"*Sentiment Status:* <span class='{sentiment_class}'>{sentiment_status}</span>",
        unsafe_allow_html=True
    )

    st.markdown("### Recommended Strategy")
    st.markdown("\n".join(strategy_lines))


def notifications_section(notifications_file="data/notifications.csv"):
    """Show alerts logged by notification system."""
    st.markdown('<div class="section-header">Notifications</div>', unsafe_allow_html=True)

    if not os.path.exists(notifications_file):
        st.info("No notifications available yet.")
        return

    df = pd.read_csv(notifications_file)
    if df.empty:
        st.info("No notifications to display.")
        return

    st.dataframe(df)

    # Highlight last 5 alerts
    st.markdown("### Recent Alerts")
    for _, row in df.tail(5).iterrows():
        st.write(f"- **[{row['timestamp']}]** {row['message']}")


# ---------------- Main App ----------------
def main():
    """Main entry point for Streamlit dashboard."""
    st.markdown('<div class="main-header">E-Commerce Competitor Strategy Dashboard</div>',
                unsafe_allow_html=True)

    # Run the end-to-end pipeline once per session
    if "pipeline_initialized" not in st.session_state:
        orchestrate_pipeline()
        st.session_state["pipeline_initialized"] = True

    analyzer = CompetitorAnalyzer()
    if not analyzer.load_data():
        st.stop()

    section = st.sidebar.radio("Navigate", [
        "Product Analysis",
        "Competitor Comparison",
        "Strategic Recommendations",
        "Notifications"
    ])
    product = st.sidebar.selectbox("Select Product", analyzer.products_df["product_name"].unique())

    if section == "Product Analysis":
        product_analysis(analyzer, product)
    elif section == "Competitor Comparison":
        competitor_comparison(analyzer, product)
    elif section == "Strategic Recommendations":
        strategic_recommendations(analyzer, product)
    elif section == "Notifications":
        notifications_section()


if __name__ == "__main__":
    main()
