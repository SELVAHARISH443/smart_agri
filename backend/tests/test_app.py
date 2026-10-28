import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app


def test_health_endpoint():
    client = app.test_client()
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_soil_prediction_endpoint():
    client = app.test_client()
    payload = {
        "N": 80,
        "P": 60,
        "K": 40,
        "pH": 6.5,
        "temperature": 28,
        "humidity": 70,
        "rainfall": 120,
        "soil_moisture": 25,
        "organic_carbon": 1.2,
    }
    response = client.post("/api/predict-soil", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["soil_class"] in {"Excellent", "Good", "Moderate", "Poor"}
    assert isinstance(data["soil_score"], (int, float))


def test_soil_image_analysis_endpoint():
    client = app.test_client()
    response = client.post(
        "/api/soil-analysis",
        data={"image": (b"fake-image-data", "soil.png")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["soil_type"] in {"Black Soil", "Red Soil", "Sandy Soil", "Clay Soil", "Loamy Soil", "Laterite Soil"}
    assert data["soil_health"] in {"Excellent", "Good", "Moderate", "Poor"}
