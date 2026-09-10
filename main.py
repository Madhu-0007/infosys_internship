"""
main.py — Entry point for the E-Commerce Competitor Intelligence Pipeline.

Delegates to pipeline.py for the full end-to-end flow.
Run the dashboard separately with: streamlit run dashboard.py
"""

import pipeline

if __name__ == "__main__":
    pipeline.main()