"""L'API LogiAI avec authentification et autorisation."""

import json
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException

from logiai.api.schemas import Livraison, PredictionOut
from logiai.api.security import require_admin, verify_api_key
from logiai.config import INFO_PATH, MODEL_PATH
from logiai.predict import Predictor

state: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    if MODEL_PATH.exists():
        state["predictor"] = Predictor(MODEL_PATH)
    yield
    state.clear()


app = FastAPI(
    title="LogiAI",
    version="1.0.0",
    description="Prédit le risque de retard d'une livraison.",
    lifespan=lifespan,
)


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": "predictor" in state}


@app.post("/v1/predict", response_model=PredictionOut)
def predict(
    livraison: Livraison,
    _: str = Depends(verify_api_key),
):
    predictor = state.get("predictor")

    if predictor is None:
        raise HTTPException(
            status_code=503,
            detail="Modèle de prédiction indisponible",
        )

    return PredictionOut(**predictor.predict(livraison.model_dump()))


@app.get("/v1/model-info")
def model_info(_: str = Depends(require_admin)):
    if not INFO_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="Informations du modèle introuvables",
        )

    with INFO_PATH.open(encoding="utf-8") as file:
        return json.load(file)