
from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_home():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "running"


def test_health():
    response = client.get("/health")
    assert response.status_code == 200


def test_valid_order():
    response = client.get("/orders/ORD-101")

    assert response.status_code == 200
    assert response.json()["customer"] == "Priya Sharma"
    assert response.json()["status"] == "Out for Delivery"


def test_order_id_case_insensitive():
    response = client.get("/orders/ord-103")

    assert response.status_code == 200
    assert response.json()["cancellation_eligible"] is True


def test_unknown_order():
    response = client.get("/orders/ORD-999")

    assert response.status_code == 404
