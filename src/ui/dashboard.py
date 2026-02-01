"""Streamlit Web Dashboard for Options Terminal."""

import streamlit as st
import pandas as pd
import sys
import os
import time

# Add project root to path
sys.path.append(os.getcwd())

from src.data.database import get_db_engine
from src.utils.health import HealthMonitor
from src.analytics.portfolio import PortfolioManager

# Page Config
st.set_page_config(
    page_title="TOS Option Terminal",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title
st.title("🚀 Options Day-Trading Assistant")

# Sidebar
st.sidebar.header("Navigation")
page = st.sidebar.radio("Go to", ["Dashboard", "Scanner Results", "Trade Journal", "System Health"])

def load_data():
    """Load trade data from database."""
    engine = get_db_engine()
    try:
        # Load trades with SQL
        query = "SELECT * FROM trades ORDER BY timestamp DESC"
        df = pd.read_sql(query, engine)
        return df
    except Exception as e:
        st.error(f"Error loading database: {e}")
        return pd.DataFrame()

def show_metrics(df):
    """Display key metrics."""
    if df.empty:
        st.info("No trades found in database.")
        return

    # Filter for today's trades (assuming 'timestamp' column exists)
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        today = pd.Timestamp.now().date()
        todays_trades = df[df['timestamp'].dt.date == today]
    else:
        todays_trades = pd.DataFrame()

    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Trades (All Time)", len(df))
    with col2:
        st.metric("Trades Today", len(todays_trades))
    with col3:
        # Placeholder for active P&L logic
        st.metric("Open Strategies", "N/A") 
    with col4:
        # Placeholder
        st.metric("Win Rate", "N/A")

if page == "Dashboard":
    st.subheader("📊 Portfolio Overview")
    df = load_data()
    show_metrics(df)
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown("### Recent Activity")
        if not df.empty:
            st.dataframe(df[['timestamp', 'symbol', 'strategy', 'bias', 'score']].head(10), hide_index=True)
            
    with col_right:
        st.markdown("### Risk Distribution")
        if not df.empty:
            # Simple Chart: Strategy Distribution
            strategy_counts = df['strategy'].value_counts()
            st.bar_chart(strategy_counts)

elif page == "Scanner Results":
    st.subheader("🔍 Scanner Output")
    st.info("This view would show real-time scanner results if connected to the live loop.")
    # In a full app, we'd read from a 'scan_results' table or json file
    
elif page == "Trade Journal":
    st.subheader("📔 Trade Journal")
    df = load_data()
    
    if not df.empty:
        # Filters
        symbol_filter = st.text_input("Filter by Symbol")
        if symbol_filter:
            df = df[df['symbol'].str.contains(symbol_filter.upper())]
            
        st.dataframe(
            df, 
            column_config={
                "timestamp": st.column_config.DatetimeColumn("Time", format="D MMM, HH:mm"),
                "score": st.column_config.ProgressColumn("Score", min_value=0, max_value=100, format="%f"),
            },
            use_container_width=True
        )
    else:
        st.write("No trades recorded yet.")

elif page == "System Health":
    st.subheader("❤️ System Health")
    
    if st.button("Run Health Check"):
        with st.spinner("Checking system vitals..."):
            report = HealthMonitor.run_health_check()
            time.sleep(1) # Visual effect
            
        status = report.get('status', 'UNKNOWN')
        if status == 'HEALTHY':
            st.success(f"System Status: {status}")
        elif status == 'DEGRADED':
            st.warning(f"System Status: {status}")
        else:
            st.error(f"System Status: {status}")
            
        col1, col2, col3 = st.columns(3)
        col1.metric("API Latency", report.get('api_latency', 'N/A'))
        col2.metric("Database", "Connected" if report.get('database_connected') else "Error")
        col3.metric("Disk Status", report.get('disk', {}).get('status', 'Unknown'))
        
        st.json(report)
