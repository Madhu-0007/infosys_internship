"""
ui/styles.py — Dark Trading Terminal CSS and theme injection.
"""
import streamlit as st


def inject_terminal_css():
    """Injects high-contrast dark trading terminal styles into the Streamlit app."""
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700;800&family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"], .stApp {
    background-color: #0d1117 !important;
    color: #e6edf3 !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

.mono {
    font-family: 'JetBrains Mono', monospace !important;
}

header[data-testid="stHeader"] {
    background-color: #0d1117 !important;
}
div[data-testid="stToolbar"] {
    color: #8b949e !important;
}

/* Trading Topbar */
.terminal-topbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.85rem 1.4rem;
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    margin-bottom: 1.2rem;
}
.terminal-title {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.2rem;
    font-weight: 800;
    color: #f0f6fc;
    letter-spacing: 0.5px;
    display: flex;
    align-items: center;
    gap: 0.6rem;
}
.terminal-pulse {
    width: 10px;
    height: 10px;
    background-color: #22c55e;
    border-radius: 50%;
    box-shadow: 0 0 10px #22c55e;
    display: inline-block;
}

/* KPI Cards */
.kpi-card {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 1rem 1.25rem;
    height: 100%;
}
.kpi-label {
    font-size: 0.72rem;
    color: #8b949e;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 0.35rem;
    font-weight: 600;
}
.kpi-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.6rem;
    font-weight: 800;
    color: #f0f6fc;
    margin-bottom: 0.2rem;
}
.kpi-sub {
    font-size: 0.78rem;
    color: #8b949e;
}

/* Department & Brand Headers */
.department-banner {
    background: #161b22;
    border-left: 4px solid #38bdf8;
    padding: 0.6rem 1rem;
    border-radius: 4px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.15rem;
    font-weight: 800;
    color: #f0f6fc;
    margin-top: 1.8rem;
    margin-bottom: 0.8rem;
}
.brand-group-header {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    margin-top: 1.2rem;
    margin-bottom: 0.7rem;
    padding-bottom: 0.3rem;
    border-bottom: 1px solid #21262d;
}
.brand-group-title {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.05rem;
    font-weight: 700;
    color: #c9d1d9;
}
.brand-count-badge {
    background: #21262d;
    border: 1px solid #30363d;
    color: #8b949e;
    font-size: 0.72rem;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 12px;
    font-family: 'JetBrains Mono', monospace;
}

/* Product Card Elements */
.price-box-fk, .price-box-az {
    background: #0d1117;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 0.55rem;
}
.price-box-winner {
    border-color: #22c55e !important;
    box-shadow: 0 0 10px rgba(34, 197, 94, 0.15);
}
.cheaper-badge {
    background: rgba(34, 197, 94, 0.15);
    border: 1px solid #22c55e;
    color: #22c55e;
    font-size: 0.7rem;
    font-weight: 700;
    padding: 2px 7px;
    border-radius: 4px;
    font-family: 'JetBrains Mono', monospace;
}
.unmatched-box {
    background: rgba(239, 68, 68, 0.08);
    border: 1px dashed #ef4444;
    color: #ef4444;
    padding: 0.5rem;
    border-radius: 6px;
    font-size: 0.76rem;
    font-family: 'JetBrains Mono', monospace;
    text-align: center;
}
.spec-chip {
    background: #21262d;
    color: #c9d1d9;
    border: 1px solid #30363d;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 0.7rem;
    font-family: 'JetBrains Mono', monospace;
    margin-right: 4px;
    margin-bottom: 4px;
    display: inline-block;
}
.confidence-badge-high {
    background: rgba(34, 197, 94, 0.15);
    border: 1px solid #22c55e;
    color: #22c55e;
    font-size: 0.65rem;
    font-weight: 700;
    padding: 1px 5px;
    border-radius: 3px;
    font-family: 'JetBrains Mono', monospace;
}
.confidence-badge-med {
    background: rgba(245, 158, 11, 0.15);
    border: 1px solid #f59e0b;
    color: #f59e0b;
    font-size: 0.65rem;
    font-weight: 700;
    padding: 1px 5px;
    border-radius: 3px;
    font-family: 'JetBrains Mono', monospace;
}
.confidence-badge-low {
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid #ef4444;
    color: #ef4444;
    font-size: 0.65rem;
    font-weight: 700;
    padding: 1px 5px;
    border-radius: 3px;
    font-family: 'JetBrains Mono', monospace;
}
.edge-box {
    background: #0d1117;
    border-left: 3px solid #22c55e;
    padding: 0.45rem 0.65rem;
    border-radius: 0 4px 4px 0;
    font-size: 0.76rem;
    color: #c9d1d9;
    margin: 0.45rem 0;
}
.thumbnail-box {
    width: 44px;
    height: 44px;
    background: #21262d;
    border: 1px solid #30363d;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.35rem;
    flex-shrink: 0;
}
.savings-banner {
    background: linear-gradient(135deg, rgba(34, 197, 94, 0.14) 0%, rgba(34, 197, 94, 0.03) 100%);
    border: 1px solid #22c55e;
    border-radius: 8px;
    padding: 1.25rem;
    text-align: center;
    margin: 1.2rem 0;
}
.savings-amount {
    font-family: 'JetBrains Mono', monospace;
    font-size: 2.3rem;
    font-weight: 800;
    color: #22c55e;
    margin: 0.3rem 0;
}
.recommendation-box {
    background: #161b22;
    border: 1px solid #38bdf8;
    border-radius: 6px;
    padding: 0.8rem 1rem;
    margin: 1rem 0;
}
.link-btn {
    display: inline-block;
    background: #21262d;
    color: #58a6ff !important;
    text-decoration: none !important;
    padding: 4px 10px;
    border-radius: 4px;
    border: 1px solid #30363d;
    font-size: 0.75rem;
    font-weight: 600;
    margin-right: 6px;
}
.link-btn:hover {
    background: #30363d;
    border-color: #58a6ff;
}
div.stButton > button {
    background-color: #21262d !important;
    color: #c9d1d9 !important;
    border: 1px solid #30363d !important;
    border-radius: 6px !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
}
div.stButton > button:hover {
    background-color: #30363d !important;
    border-color: #8b949e !important;
    color: #f0f6fc !important;
}
</style>
""",
        unsafe_allow_html=True,
    )
