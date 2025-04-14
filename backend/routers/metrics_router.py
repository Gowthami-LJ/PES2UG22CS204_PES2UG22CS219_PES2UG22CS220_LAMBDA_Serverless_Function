# backend/routers/metrics_router.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
import statistics
from datetime import datetime, timedelta

from ..database import get_db, ExecutionMetric, Function

router = APIRouter(prefix="/metrics")

@router.get("/function/{function_name}")
async def get_function_metrics(
    function_name: str,
    limit: int = Query(100, description="Limit the number of results"),
    days: Optional[int] = Query(None, description="Filter metrics from last N days"),
    db: Session = Depends(get_db)
):
    """Get detailed metrics for a specific function"""
    # Check if function exists
    function = db.query(Function).filter(Function.name == function_name).first()
    if not function:
        raise HTTPException(status_code=404, detail=f"Function {function_name} not found")
    
    # Query for metrics
    query = db.query(ExecutionMetric).filter(ExecutionMetric.function_name == function_name)
    
    # Apply time filter if specified
    if days:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = query.filter(ExecutionMetric.timestamp >= cutoff_date)
    
    # Get results with limit
    metrics = query.order_by(ExecutionMetric.timestamp.desc()).limit(limit).all()
    
    # Convert to dict format
    executions = []
    for metric in metrics:
        executions.append({
            "id": metric.id,
            "function_name": metric.function_name,
            "runtime": metric.runtime,
            "language": metric.language,
            "initialization_time_ms": metric.initialization_time_ms,
            "execution_time_ms": metric.execution_time_ms,
            "total_time_ms": metric.total_time_ms,
            "warm_start": metric.warm_start,
            "error": metric.error,
            "timestamp": metric.timestamp.isoformat(),
            "success": metric.error is None
        })
    
    # Calculate statistics
    stats = calculate_function_stats(executions)
    
    return {
        "function_name": function_name,
        "executions": executions,
        "statistics": stats
    }

@router.get("/system")
async def get_system_metrics(
    days: int = Query(7, description="Number of days to include in metrics"),
    db: Session = Depends(get_db)
):
    """Get system-wide metrics"""
    # Calculate date cutoff
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Get all metrics within time range
    metrics = db.query(ExecutionMetric).filter(ExecutionMetric.timestamp >= cutoff_date).all()
    
    # Get all functions
    functions = db.query(Function).all()
    
    # Convert to dict format
    executions = []
    for metric in metrics:
        executions.append({
            "id": metric.id,
            "function_name": metric.function_name,
            "runtime": metric.runtime,
            "language": metric.language,
            "initialization_time_ms": metric.initialization_time_ms,
            "execution_time_ms": metric.execution_time_ms,
            "total_time_ms": metric.total_time_ms,
            "warm_start": metric.warm_start,
            "error": metric.error,
            "timestamp": metric.timestamp.isoformat(),
            "success": metric.error is None
        })
    
    # Group by function name
    function_metrics = {}
    for execution in executions:
        fname = execution["function_name"]
        if fname not in function_metrics:
            function_metrics[fname] = []
        function_metrics[fname].append(execution)
    
    # Calculate statistics for each function
    function_stats = {}
    for fname, metrics in function_metrics.items():
        function_stats[fname] = calculate_function_stats(metrics)
    
    # Calculate system-wide statistics
    system_stats = {
        "total_functions": len(functions),
        "total_executions": len(executions),
        "executions_per_day": len(executions) / days if days > 0 else 0,
        "success_rate": sum(1 for e in executions if e["success"]) / len(executions) * 100 if executions else 0,
        "avg_execution_time": statistics.mean([e["execution_time_ms"] for e in executions]) if executions else 0,
        "avg_initialization_time": statistics.mean([e["initialization_time_ms"] for e in executions]) if executions else 0,
        "avg_total_time": statistics.mean([e["total_time_ms"] for e in executions]) if executions else 0,
        "runtime_distribution": {
            "docker": sum(1 for e in executions if e["runtime"] == "docker"),
            "gvisor": sum(1 for e in executions if e["runtime"] == "gvisor")
        },
        "language_distribution": {
            "python": sum(1 for e in executions if e["language"] == "python"),
            "javascript": sum(1 for e in executions if e["language"] == "javascript")
        }
    }
    
    return {
        "time_range": f"Last {days} days",
        "system_stats": system_stats,
        "function_stats": function_stats,
        "recent_executions": executions[:20]  # Return only the 20 most recent executions
    }

def calculate_function_stats(executions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate statistics for a list of function executions"""
    if not executions:
        return {
            "total_executions": 0,
            "success_rate": 0,
            "avg_execution_time": 0,
            "avg_initialization_time": 0,
            "avg_total_time": 0
        }
    
    # Calculate success rate
    successful = sum(1 for e in executions if e["success"])
    success_rate = (successful / len(executions)) * 100
    
    # Calculate time averages
    exec_times = [e["execution_time_ms"] for e in executions]
    init_times = [e["initialization_time_ms"] for e in executions]
    total_times = [e["total_time_ms"] for e in executions]
    
    return {
        "total_executions": len(executions),
        "success_rate": success_rate,
        "avg_execution_time": statistics.mean(exec_times) if exec_times else 0,
        "min_execution_time": min(exec_times) if exec_times else 0,
        "max_execution_time": max(exec_times) if exec_times else 0,
        "avg_initialization_time": statistics.mean(init_times) if init_times else 0,
        "min_initialization_time": min(init_times) if init_times else 0,
        "max_initialization_time": max(init_times) if init_times else 0,
        "avg_total_time": statistics.mean(total_times) if total_times else 0,
        "min_total_time": min(total_times) if total_times else 0,
        "max_total_time": max(total_times) if total_times else 0,
        "runtime_distribution": {
            "docker": sum(1 for e in executions if e["runtime"] == "docker"),
            "gvisor": sum(1 for e in executions if e["runtime"] == "gvisor")
        },
        "warm_vs_cold": {
            "warm": sum(1 for e in executions if e.get("warm_start")),
            "cold": sum(1 for e in executions if not e.get("warm_start"))
        }
    }
