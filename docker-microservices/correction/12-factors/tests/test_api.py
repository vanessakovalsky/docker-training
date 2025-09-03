# tests/test_api.py
import pytest
import requests
import time

class TestUserAPI:
    base_url = "http://localhost:8080"
    
    def test_health_check(self):
        response = requests.get(f"{self.base_url}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_create_user(self):
        user_data = {
            "name": "testuser",
            "email": "test@example.com"
        }
        response = requests.post(f"{self.base_url}/users", json=user_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == user_data["name"]
        assert data["email"] == user_data["email"]
        assert "id" in data
    
    def test_get_users(self):
        response = requests.get(f"{self.base_url}/users")
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "count" in data