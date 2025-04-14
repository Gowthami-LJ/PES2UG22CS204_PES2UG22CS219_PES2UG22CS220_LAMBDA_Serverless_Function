# backend/routers/runtime_router.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List
import statistics

from ..database import get_db, Function, ExecutionMetric
from ..virtualization.runner import run_in_docker
from ..virtualization.gvisor_runner import run_in_gvisor

router = APIRouter(prefix="/runtime")

@router.get("/compare")
async def compare_runtimes(
    function_name: str = Query(..., description="Name of the function to compare"),
    iterations: int = Query(3, description="Number of iterations for comparison"),
    db: Session = Depends(get_db)
):
    """Compare performance between Docker and gVisor for a specific function"""
    # Get the function from the database
    function = db.query(Function).filter(Function.name == function_name).first()
    if not function:
        raise HTTPException(status_code=404, detail=f"Function {function_name} not found")
    
    # Execute with Docker
    docker_results = []
    for _ in range(iterations):
        result = run_in_docker(function.code, function.language, function.timeout, warm_start=False)
        if result["status"] == "success":
            docker_results.append(result["metrics"])
    
    # Execute with gVisor
    gvisor_results = []
    for _ in range(iterations):
        result = run_in_gvisor(function.code, function.language, function.timeout)
        if result["status"] == "success":
            gvisor_results.append(result["metrics"])
    
    # Calculate statistics
    docker_stats = calculate_runtime_stats(docker_results)
    gvisor_stats = calculate_runtime_stats(gvisor_results)
    
    return {
        "function_name": function_name,
        "iterations": iterations,
        "docker": docker_stats,
        "gvisor": gvisor_stats,
        "raw_results": {
            "docker": docker_results,
            "gvisor": gvisor_results
        }
    }

def calculate_runtime_stats(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate statistics from runtime results"""
    if not results:
        return {
            "count": 0,
            "avg_initialization_time": 0,
            "avg_execution_time": 0,
            "avg_total_time": 0
        }
    
    # Extract metrics
    init_times = [r["initialization_time_ms"] for r in results]
    exec_times = [r["execution_time_ms"] for r in results]
    total_times = [r["total_time_ms"] for r in results]
    
    # Calculate statistics
    return {
        "count": len(results),
        "avg_initialization_time": statistics.mean(init_times) if init_times else 0,
        "min_initialization_time": min(init_times) if init_times else 0, 
        "max_initialization_time": max(init_times) if init_times else 0,
        "avg_execution_time": statistics.mean(exec_times) if exec_times else 0,
        "min_execution_time": min(exec_times) if exec_times else 0,
        "max_execution_time": max(exec_times) if exec_times else 0,
        "avg_total_time": statistics.mean(total_times) if total_times else 0,
        "min_total_time": min(total_times) if total_times else 0,
        "max_total_time": max(total_times) if total_times else 0
    }
