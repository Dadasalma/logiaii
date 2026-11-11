
"""Tests de sécurité de l'API LogiAI."""

from fastapi.testclient import TestClient

from logiai.api.main import app

API_HEADERS = {"X-API-Key": "test-user-key"}
ADMIN_HEADERS = {"X-API-Key": "test-admin-key"}

VALIDE = {
    "distance_km": 120.0,
    "poids_kg": 450.0,
    "heure_depart": 17,
    "pluie_mm": 8.0,
    "trafic_index": 7.5,
    "nb_arrets": 4,
    "type_vehicule": "camion",
}


def test_predict_sans_cle_refuse():
    with TestClient(app) as client:
        response = client.post("/v1/predict", json=VALIDE)
        assert response.status_code == 401


def test_predict_cle_invalide_refuse():
    with TestClient(app) as client:
        response = client.post(
            "/v1/predict",
            json=VALIDE,
            headers={"X-API-Key": "wrong-key"},
        )
        assert response.status_code == 401


def test_predict_cle_utilisateur_acceptee():
    with TestClient(app) as client:
        response = client.post(
            "/v1/predict",
            json=VALIDE,
            headers=API_HEADERS,
        )
        assert response.status_code == 200


def test_model_info_refuse_utilisateur():
    with TestClient(app) as client:
        response = client.get(
            "/v1/model-info",
            headers=API_HEADERS,
        )
        assert response.status_code == 403


def test_model_info_accepte_admin():
    with TestClient(app) as client:
        response = client.get(
            "/v1/model-info",
            headers=ADMIN_HEADERS,
        )
        assert response.status_code in (200, 404)
