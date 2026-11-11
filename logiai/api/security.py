"""Authentification et autorisation de l'API LogiAI."""

import hmac
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, Header, HTTPException

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

API_KEY = os.getenv("LOGIAI_API_KEY")
ADMIN_KEY = os.getenv("LOGIAI_ADMIN_KEY")


def _egal(a: str, b: str | None) -> bool:
    """Compare deux clés de manière sécurisée."""
    return bool(b) and hmac.compare_digest(a, b)


def verify_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> str:
    """Vérifie la clé et retourne le rôle."""
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="Clé API manquante ou invalide",
        )

    if _egal(x_api_key, ADMIN_KEY):
        return "admin"

    if _egal(x_api_key, API_KEY):
        return "user"

    raise HTTPException(
        status_code=401,
        detail="Clé API manquante ou invalide",
    )


def require_admin(
    role: str = Depends(verify_api_key),
) -> str:
    """Autorise uniquement les administrateurs."""
    if role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Accès réservé à l'administrateur",
        )

    return role