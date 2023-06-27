from fastapi.testclient import TestClient

from .constants import API_KEY
from .main import app

client = TestClient(app)


def test_auth_order_number_found(monkeypatch):

    response = client.post(
        "/api/auth/order-number",
        headers={"API_KEY": API_KEY},
        json={"order_number": "#1001"},
    )

    assert response.status_code == 200
    response_json = response.json()

    assert response_json.get("order_number") == "#1001"
    assert response_json.get("valid") is True


def test_auth_order_number_not_found():
    response = client.post(
        "/api/auth/order-number",
        headers={"API_KEY": API_KEY},
        json={"order_number": "qwerty"},
    )

    assert response.status_code == 200
    response_json = response.json()

    assert response_json.get("order_number") == "qwerty"
    assert response_json.get("valid") is False


def test_auth_order_number_not_found_without_order_number():
    response = client.post(
        "/api/auth/order-number",
        headers={"API_KEY": API_KEY},
        json={},
    )

    assert response.status_code == 422
