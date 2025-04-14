# frontend/app.py
import streamlit as st
import requests
import json
import time
from typing import Dict, Any, List
import statistics

# Configuration
API_BASE_URL = "http://127.0.0.1:8000"

# Set page config
st.set_page_config(
    page_title="FaaS Platform",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar navigation
st.sidebar.title("☁️ FaaS Platform")
page = st.sidebar.radio("Navigate", ["Functions", "Metrics", "Comparison"])

# Create session state for storing data
if "functions" not in st.session_state:
    st.session_state.functions = []
if "selected_function" not in st.session_state:
    st.session_state.selected_function = None
if "function_code" not in st.session_state:
    st.session_state.function_code = ""

# API Functions
def get_functions():
    try:
        response = requests.get(f"{API_BASE_URL}/functions/")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error fetching functions: {response.text}")
            return []
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return []

def create_function(name, language, code, timeout):
    try:
        data = {
            "name": name,
            "language": language,
            "code": code,
            "timeout": timeout
        }
        response = requests.post(
            f"{API_BASE_URL}/functions/",
            headers={"Content-Type": "application/json"},
            data=json.dumps(data)
        )
        if response.status_code == 200:
            st.success(f"Function '{name}' created successfully")
            return True
        else:
            st.error(f"Error creating function: {response.text}")
            return False
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return False

def update_function(name, language, code, timeout):
    try:
        data = {
            "name": name,
            "language": language,
            "code": code,
            "timeout": timeout
        }
        response = requests.put(
            f"{API_BASE_URL}/functions/{name}",
            headers={"Content-Type": "application/json"},
            data=json.dumps(data)
        )
        if response.status_code == 200:
            st.success(f"Function '{name}' updated successfully")
            return True
        else:
            st.error(f"Error updating function: {response.text}")
            return False
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return False

def delete_function(name):
    try:
        response = requests.delete(f"{API_BASE_URL}/functions/{name}")
        if response.status_code == 200:
            st.success(f"Function '{name}' deleted successfully")
            return True
        else:
            st.error(f"Error deleting function: {response.text}")
            return False
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return False

def execute_function(name, runtime="docker", warm_start=False):
    try:
        data = {
            "runtime": runtime,
            "warm_start": warm_start
        }
        with st.spinner(f"Executing function '{name}' with {runtime}..."):
            response = requests.post(
                f"{API_BASE_URL}/functions/execute/{name}",
                headers={"Content-Type": "application/json"},
                data=json.dumps(data)
            )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error executing function: {response.text}")
            return None
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return None

def get_function_metrics(name):
    try:
        response = requests.get(f"{API_BASE_URL}/metrics/functions/{name}")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error fetching metrics: {response.text}")
            return None
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return None

def compare_runtimes(name, iterations=3):
    try:
        with st.spinner(f"Comparing runtimes for '{name}' ({iterations} iterations)..."):
            response = requests.get(
                f"{API_BASE_URL}/runtime/compare",
                params={"function_name": name, "iterations": iterations}
            )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error comparing runtimes: {response.text}")
            return None
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return None

# Function Management Page
def show_functions_page():
    st.title("Function Management")
    
    # Refresh function list
    if st.sidebar.button("🔄 Refresh Functions"):
        st.session_state.functions = get_functions()
    
    # Initial load of functions if empty
    if not st.session_state.functions:
        st.session_state.functions = get_functions()
    
    # Display functions in sidebar for selection
    st.sidebar.subheader("Your Functions")
    function_names = [func["name"] for func in st.session_state.functions]
    function_names.insert(0, "Create New Function")
    
    selected_function_name = st.sidebar.selectbox(
        "Select Function", 
        function_names,
        index=0
    )
    
    # Handle function creation
    if selected_function_name == "Create New Function":
        st.subheader("Create New Function")
        
        name = st.text_input("Function Name", key="new_name")
        language = st.selectbox(
            "Language", 
            ["python", "javascript"],
            key="new_language"
        )
        
        code_template = "print('Hello, World!')" if language == "python" else "console.log('Hello, World!');"
        code = st.text_area("Code", code_template, height=300, key="new_code")
        
        timeout = st.slider("Timeout (seconds)", 1, 300, 30, key="new_timeout")
        
        if st.button("Create Function"):
            if not name:
                st.error("Function name is required")
            elif not code:
                st.error("Function code is required")
            else:
                if create_function(name, language, code, timeout):
                    # Refresh function list
                    st.session_state.functions = get_functions()
    
    # Handle function editing/execution
    else:
        # Find the selected function
        func = next((f for f in st.session_state.functions if f["name"] == selected_function_name), None)
        if func:
            st.subheader(f"Function: {func['name']}")
            
            # Function details in columns
            col1, col2 = st.columns(2)
            with col1:
                language = st.selectbox(
                    "Language", 
                    ["python", "javascript"],
                    index=0 if func["language"] == "python" else 1,
                    key="edit_language"
                )
            with col2:
                timeout = st.slider(
                    "Timeout (seconds)", 
                    1, 300, 
                    int(func["timeout"]), 
                    key="edit_timeout"
                )
            
            code = st.text_area("Code", func["code"], height=300, key="edit_code")
            
            # Function actions
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Update Function"):
                    if update_function(func["name"], language, code, timeout):
                        # Refresh function list
                        st.session_state.functions = get_functions()
            with col2:
                if st.button("Delete Function"):
                    if delete_function(func["name"]):
                        # Refresh function list and reset selection
                        st.session_state.functions = get_functions()
                        st.rerun()
            
            # Function execution
            st.subheader("Execute Function")
            
            col1, col2 = st.columns(2)
            with col1:
                runtime = st.selectbox("Runtime", ["docker", "gvisor"], key="exec_runtime")
            with col2:
                warm_start = st.checkbox("Warm Start", value=False, key="exec_warm_start")
            
            if st.button("Execute Function"):
                result = execute_function(func["name"], runtime, warm_start)
                if result:
                    st.subheader("Execution Result")
                    
                    # Show status and metrics
                    status = result["result"]["status"]
                    status_color = "green" if status == "success" else "red"
                    st.markdown(f"Status: <span style='color:{status_color}'>{status}</span>", unsafe_allow_html=True)
                    
                    # Show execution metrics
                    metrics = result["result"]["metrics"]
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Init Time (ms)", metrics["initialization_time_ms"])
                    with col2:
                        st.metric("Execution Time (ms)", metrics["execution_time_ms"])
                    with col3:
                        st.metric("Total Time (ms)", metrics["total_time_ms"])
                    
                    # Show output
                    st.subheader("Standard Output")
                    st.code(result["result"]["stdout"])
                    
                    if result["result"]["stderr"]:
                        st.subheader("Standard Error")
                        st.code(result["result"]["stderr"])
                    
def calculate_function_stats(executions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate statistics for a list of function executions"""
    if not executions:
        return {
            "total_executions": 0,
            "success_rate": 0,
            "avg_initialization_time": 0,
            "min_initialization_time": 0,
            "max_initialization_time": 0,
            "avg_execution_time": 0,
            "min_execution_time": 0,
            "max_execution_time": 0,
            "avg_total_time": 0,
            "min_total_time": 0,
            "max_total_time": 0,
            "runtime_distribution": {"docker": 0, "gvisor": 0},
            "warm_vs_cold": {"warm": 0, "cold": 0}
        }
    
    # Calculate success rate
    successful = sum(1 for e in executions if e.get("success", False))
    success_rate = (successful / len(executions)) * 100 if executions else 0
    
    # Calculate time averages
    exec_times = [e["execution_time_ms"] for e in executions if "execution_time_ms" in e]
    init_times = [e["initialization_time_ms"] for e in executions if "initialization_time_ms" in e]
    total_times = [e["total_time_ms"] for e in executions if "total_time_ms" in e]
    
    return {
        "total_executions": len(executions),
        "success_rate": success_rate,
        "avg_initialization_time": sum(init_times)/len(init_times) if init_times else 0,
        "min_initialization_time": min(init_times) if init_times else 0,
        "max_initialization_time": max(init_times) if init_times else 0,
        "avg_execution_time": sum(exec_times)/len(exec_times) if exec_times else 0,
        "min_execution_time": min(exec_times) if exec_times else 0,
        "max_execution_time": max(exec_times) if exec_times else 0,
        "avg_total_time": sum(total_times)/len(total_times) if total_times else 0,
        "min_total_time": min(total_times) if total_times else 0,
        "max_total_time": max(total_times) if total_times else 0,
        "runtime_distribution": {
            "docker": sum(1 for e in executions if e.get("runtime") == "docker"),
            "gvisor": sum(1 for e in executions if e.get("runtime") == "gvisor")
        },
        "warm_vs_cold": {
            "warm": sum(1 for e in executions if not e.get("cold_start", True)),
            "cold": sum(1 for e in executions if e.get("cold_start", True))
        }
    }

# Metrics Visualization Page
def show_metrics_page():
    st.title("Function Metrics")
    
    # Get list of functions for selection
    functions = get_functions()
    function_names = [func["name"] for func in functions]
    
    if not function_names:
        st.warning("No functions found. Create a function first.")
        return
    
    selected_function = st.selectbox("Select Function", function_names)
    
    if selected_function:
        with st.spinner("Loading metrics..."):
            metrics_data = get_function_metrics(selected_function)
            
            if not metrics_data:
                st.warning(f"No metrics data available for {selected_function}")
                return
                
            # Convert metrics to the expected format
            executions = []
            for metric in metrics_data:
                executions.append({
                    "id": metric["id"],
                    "function_name": metric["function_name"],
                    "runtime": metric["runtime"],
                    "language": metric["language"],
                    "initialization_time_ms": metric["initialization_time_ms"],
                    "execution_time_ms": metric["execution_time_ms"],
                    "total_time_ms": metric["total_time_ms"],
                    "cold_start": metric["cold_start"],
                    "error": metric["error_message"],
                    "timestamp": metric["timestamp"],
                    "success": metric["status"] == "success"
                })
            
            # Calculate statistics
            stats = calculate_function_stats(executions)
            
            # Display metrics
            st.subheader(f"Metrics for {selected_function}")
            
            # Display summary statistics
            st.subheader("Summary Statistics")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Executions", stats["total_executions"])
                st.metric("Success Rate", f"{stats['success_rate']:.2f}%")
            with col2:
                st.metric("Avg Init Time (ms)", f"{stats['avg_initialization_time']:.2f}")
                st.metric("Min Init Time (ms)", stats["min_initialization_time"])
                st.metric("Max Init Time (ms)", stats["max_initialization_time"])
            with col3:
                st.metric("Avg Execution Time (ms)", f"{stats['avg_execution_time']:.2f}")
                st.metric("Min Execution Time (ms)", stats["min_execution_time"])
                st.metric("Max Execution Time (ms)", stats["max_execution_time"])
            
            # Prepare data for charts
            import pandas as pd
            import plotly.express as px
            
            df = pd.DataFrame(executions)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            
            # Execution time over time
            st.subheader("Execution Time Over Time")
            fig = px.line(
                df, 
                x="timestamp", 
                y="execution_time_ms",
                color="runtime",
                markers=True,
                title="Execution Time Trend"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Runtime distribution pie chart
            st.subheader("Runtime Distribution")
            runtime_counts = df["runtime"].value_counts().reset_index()
            runtime_counts.columns = ["Runtime", "Count"]
            fig = px.pie(runtime_counts, values="Count", names="Runtime")
            st.plotly_chart(fig, use_container_width=True)
            
            # Raw data
            with st.expander("View Raw Data"):
                st.dataframe(df)
            
def show_comparison_page():
    st.title("Runtime Comparison")
    
    # Get list of functions for selection
    functions = get_functions()
    function_names = [func["name"] for func in functions]
    
    if not function_names:
        st.warning("No functions found. Create a function first.")
        return
    
    selected_function = st.selectbox("Select Function", function_names)
    iterations = st.slider("Number of Iterations", 1, 10, 3)
    
    if st.button("Run Comparison"):
        comparison_data = compare_runtimes(selected_function, iterations)
        
        if comparison_data:
            st.subheader(f"Comparison Results for {selected_function}")
            
            st.json(comparison_data)
            
            # Display summary statistics
            docker_stats = comparison_data["docker"]
            gvisor_stats = comparison_data["gvisor"]
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Docker")
                st.metric("Avg Init Time (ms)", f"{docker_stats['avg_init_time_ms']:.2f}")
                st.metric("Avg Execution Time (ms)", f"{docker_stats['avg_exec_time_ms']:.2f}")
                st.metric("Avg Total Time (ms)", f"{docker_stats['avg_total_time_ms']:.2f}")
            with col2:
                st.subheader("gVisor")
                st.metric("Avg Init Time (ms)", f"{gvisor_stats['avg_init_time_ms']:.2f}")
                st.metric("Avg Execution Time (ms)", f"{gvisor_stats['avg_exec_time_ms']:.2f}")
                st.metric("Avg Total Time (ms)", f"{gvisor_stats['avg_total_time_ms']:.2f}")
            
            # Prepare data for charts
            import pandas as pd
            import plotly.express as px
            
            # Create comparison dataframe
            data = {
                "Runtime": ["Docker", "gVisor"],
                "Initialization Time (ms)": [docker_stats["avg_init_time_ms"], gvisor_stats["avg_init_time_ms"]],
                "Execution Time (ms)": [docker_stats["avg_exec_time_ms"], gvisor_stats["avg_exec_time_ms"]],
                "Total Time (ms)": [docker_stats["avg_total_time_ms"], gvisor_stats["avg_total_time_ms"]]
            }
            df = pd.DataFrame(data)
            
            # Plot comparison charts
            st.subheader("Initialization Time Comparison")
            fig = px.bar(
                df,
                x="Runtime",
                y="Initialization Time (ms)",
                color="Runtime",
                title="Average Initialization Time"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("Execution Time Comparison")
            fig = px.bar(
                df,
                x="Runtime",
                y="Execution Time (ms)",
                color="Runtime",
                title="Average Execution Time"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("Total Time Comparison")
            fig = px.bar(
                df,
                x="Runtime",
                y="Total Time (ms)",
                color="Runtime",
                title="Average Total Time"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Raw comparison data
            with st.expander("Raw Comparison Data"):
                st.json(comparison_data)

# Show selected page
if page == "Functions":
    show_functions_page()
elif page == "Metrics":
    show_metrics_page()
elif page == "Comparison":
    show_comparison_page()
