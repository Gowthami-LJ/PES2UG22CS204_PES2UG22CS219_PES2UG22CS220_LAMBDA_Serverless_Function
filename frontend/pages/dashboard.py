# frontend/pages/dashboard.py
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Configuration
API_BASE_URL = "http://127.0.0.1:8000"

# Set page title
st.set_page_config(
    page_title="System Dashboard",
    page_icon="📊",
    layout="wide"
)

# Page title
st.title("System Dashboard")

# Time range selector
time_range = st.selectbox(
    "Time Range",
    [1, 3, 7, 14, 30],
    index=2,
    format_func=lambda x: f"Last {x} days"
)

# Fetch system metrics
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_system_metrics(days):
    try:
        response = requests.get(f"{API_BASE_URL}/metrics/system?days={days}")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error fetching system metrics: {response.text}")
            return None
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return None

with st.spinner("Loading system metrics..."):
    system_data = get_system_metrics(time_range)

if not system_data:
    st.warning("No system metrics available. Please check if your backend is running.")
    st.stop()

# Extract data
system_stats = system_data["system_stats"]
function_stats
