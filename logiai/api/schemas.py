"""Les fiches techniques (schémas Pydantic) de l'API LogiAI."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Livraison(BaseModel):
    """Une livraison à évaluer : les 7 variables du contrat."""

    model_config = ConfigDict(extra="forbid")

    distance_km: float = Field(ge=1, le=1000, description="Distance du trajet (km)")
    poids_kg: float = Field(ge=0.5, le=3000, description="Poids de la livraison (kg)")
    heure_depart: int = Field(ge=0, le=23, description="Heure de départ")
    pluie_mm: float = Field(ge=0, le=100, description="Précipitations (mm)")
    trafic_index: float = Field(ge=0, le=10, description="Indice de trafic")
    nb_arrets: int = Field(ge=0, le=20, description="Nombre d'arrêts")
    type_vehicule: Literal["moto", "fourgon", "camion"]


class PredictionOut(BaseModel):
    probabilite_retard: float = Field(ge=0, le=1, description="Probabilité que la livraison soit en retard")
    alerte: bool = Field(description="True si la probabilité atteint le seuil")
    seuil: float = Field(description="Seuil d'alerte utilisé")
    model_version: str = Field(description="Version du modèle")
