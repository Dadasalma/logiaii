
"""Tests des limites de validation de l'API LogiAI."""

import pytest
from fastapi.testclient import TestClient

from logiai.api.main import app

API_HEADERS = {"X-API-Key": "test-user-key"}

VALIDE = {
    "distance_km": 120.0,
    "poids_kg": 450.0,
    "heure_depart": 17,
    "pluie_mm": 8.0,
    "trafic_index": 7.5,
    "nb_arrets": 4,
    "type_vehicule": "camion",
}


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.mark.parametrize("champ,valeur", [
    ("distance_km", 1),
    ("distance_km", 1000),
    ("poids_kg", 0.5),
    ("poids_kg", 3000),
    ("heure_depart", 0),
    ("heure_depart", 23),
    ("pluie_mm", 0),
    ("pluie_mm", 100),
    ("trafic_index", 0),
    ("trafic_index", 10),
    ("nb_arrets", 0),
    ("nb_arrets", 20),
])
def test_bornes_valides(client, champ, valeur):
    donnees = {**VALIDE, champ: valeur}
    response = client.post(
        "/v1/predict",
        json=donnees,
        headers=API_HEADERS,
    )
    assert response.status_code == 200


@pytest.mark.parametrize("champ,valeur", [
    ("distance_km", 0),
    ("distance_km", 1001),
    ("poids_kg", 0.4),
    ("poids_kg", 3001),
    ("heure_depart", -1),
    ("heure_depart", 24),
    ("pluie_mm", -1),
    ("pluie_mm", 101),
    ("trafic_index", -1),
    ("trafic_index", 11),
    ("nb_arrets", -1),
    ("nb_arrets", 21),
])
def test_bornes_invalides(client, champ, valeur):
    donnees = {**VALIDE, champ: valeur}
    response = client.post(
        "/v1/predict",
        json=donnees,
        headers=API_HEADERS,
    )
    assert response.status_code == 422
