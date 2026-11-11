# LogiAI — Prédiction du risque de retard des livraisons

## 1. Présentation

LogiAI est un projet de prédiction du risque de retard d'une livraison. Il utilise un modèle de Machine Learning entraîné avec Scikit-learn et expose les prédictions à travers une API REST développée avec FastAPI.

L'API reçoit les caractéristiques d'une livraison et retourne :
- La probabilité de retard.
- Une alerte selon le seuil configuré.
- Le seuil utilisé.
- La version du modèle.

## 2. Technologies utilisées

- Python
- FastAPI et Uvicorn
- Scikit-learn
- Pandas et NumPy
- Pydantic
- Joblib
- Pytest et HTTPX
- Streamlit
- Python-dotenv

## 3. Installation

Créer et activer l'environnement virtuel sous Windows PowerShell :

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Installer les dépendances :

```powershell
python -m pip install -r requirements.txt
```

Si l'activation de l'environnement virtuel est impossible, utiliser directement l'interpréteur :

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 4. Configuration des clés API

Créer le fichier `.env` à partir du modèle :

```powershell
Copy-Item .env.example .env
```

Modifier `.env` et remplacer les valeurs d'exemple par deux clés secrètes distinctes :

```env
LOGIAI_API_KEY=your-user-secret-key
LOGIAI_ADMIN_KEY=your-admin-secret-key
```

Ne jamais publier le fichier `.env` ni partager ses clés.

## 5. Génération des données et entraînement

Générer le jeu de données :

```powershell
python -m logiai.dataset
```

Entraîner le modèle :

```powershell
python -m logiai.train
```

Ces commandes génèrent les fichiers nécessaires dans `data/` et `models/`.

## 6. Lancement de l'API

```powershell
python -m uvicorn logiai.api.main:app --reload
```

Documentation interactive :

http://localhost:8000/docs

Endpoints principaux :

| Méthode | Endpoint | Fonction |
|---|---|---|
| GET | `/health` | Vérifier l'état de l'API |
| POST | `/v1/predict` | Prédire le risque de retard |
| GET | `/v1/model-info` | Consulter les informations du modèle (administrateur) |

L'endpoint `/v1/predict` nécessite une clé utilisateur dans l'en-tête `X-API-Key`. L'endpoint `/v1/model-info` nécessite une clé administrateur.

## 7. Lancement de l'interface Streamlit

```powershell
python -m streamlit run streamlit_app.py
```

## 8. Exécution des tests

```powershell
python -m pytest -q
```

Les tests vérifient notamment :
- Le fonctionnement des endpoints.
- La validation des données.
- Les bornes numériques.
- Les réponses du modèle.
- L'authentification et les autorisations.

## 9. Structure générale du projet

```text
logiai/
├── data/
├── models/
├── logiai/
│   ├── api/
│   │   ├── main.py
│   │   ├── schemas.py
│   │   └── security.py
│   ├── config.py
│   ├── dataset.py
│   ├── train.py
│   └── predict.py
├── tests/
├── web/
├── streamlit_app.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

Les fichiers générés (`data/*.csv`, `models/`) et le fichier `.env` ne doivent pas être publiés dans le dépôt Git.