import sys
import os
import pytest
from fastapi.testclient import TestClient

# Add the parent directory to path so we can import the backend module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.main import app

@pytest.fixture
def client():
    # Create the client without any context manager
    test_client = TestClient(app)
    return test_client

def test_list_functions(client):
    response = client.get("/functions/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_function(client):
    function_data = {
        "name": "test_function",
        "language": "python",
        "code": "print('hello world')",
        "timeout": 30
    }
    # First try to delete if it exists (cleanup)
    client.delete(f"/functions/{function_data['name']}")
    
    # Now create
    response = client.post(
        "/functions/",
        json=function_data
    )
    assert response.status_code == 200
    assert response.json()["name"] == function_data["name"]
    
    # Clean up
    client.delete(f"/functions/{function_data['name']}")

def test_get_function(client):
    # Create a function first
    function_data = {
        "name": "test_get_function",
        "language": "python",
        "code": "print('hello world')",
        "timeout": 30
    }
    client.post("/functions/", json=function_data)
    
    # Now get it
    response = client.get(f"/functions/{function_data['name']}")
    assert response.status_code == 200
    assert response.json()["name"] == function_data["name"]
    
    # Clean up
    client.delete(f"/functions/{function_data['name']}")

def test_update_function(client):
    # Create a function first
    function_data = {
        "name": "test_update_function",
        "language": "python",
        "code": "print('hello world')",
        "timeout": 30
    }
    client.post("/functions/", json=function_data)
    
    # Update it
    update_data = {
        "language": "python",
        "code": "print('updated')",
        "timeout": 60
    }
    response = client.put(
        f"/functions/{function_data['name']}",
        json=update_data
    )
    assert response.status_code == 200
    
    # Verify update
    get_response = client.get(f"/functions/{function_data['name']}")
    assert get_response.json()["code"] == update_data["code"]
    
    # Clean up
    client.delete(f"/functions/{function_data['name']}")

def test_delete_function(client):
    # Create a function first
    function_data = {
        "name": "test_delete_function",
        "language": "python",
        "code": "print('hello world')",
        "timeout": 30
    }
    client.post("/functions/", json=function_data)
    
    # Delete it
    response = client.delete(f"/functions/{function_data['name']}")
    assert response.status_code == 200
    
    # Verify deletion
    get_response = client.get(f"/functions/{function_data['name']}")
    assert get_response.status_code == 404
