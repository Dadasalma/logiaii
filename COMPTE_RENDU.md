# Compte rendu : TP API LogiAI

**Noms :** Salma ait dada 
**Groupe :** G3

## 1. Environnement et premiers tests

- **Résultat final de `python -m pytest -q` :** 42 tests réussis, 0 échec.
- **Pourquoi certains tests qui attendent un 422 passent-ils déjà, alors que rien n'est écrit ?**

FastAPI utilise automatiquement Pydantic pour valider les données reçues dans les requêtes. Les champs obligatoires, les types et certaines validations sont donc contrôlés automatiquement. Lorsqu'une donnée est invalide, FastAPI retourne une erreur HTTP 422.

## 2. Mon schéma

Les bornes sont définies à l'aide de Pydantic dans `logiai/api/schemas.py`.

| Variable | Min | Max | Pourquoi |
|---|---:|---:|---|
| distance_km | 1 | 1000 | Distance réaliste d'une livraison |
| poids_kg | 0.5 | 3000 | Poids positif et adapté aux véhicules |
| heure_depart | 0 | 23 | Une journée contient 24 heures |
| pluie_mm | 0 | 100 | Éviter les valeurs négatives ou irréalistes |
| trafic_index | 0 | 10 | Indice de trafic normalisé |
| nb_arrets | 0 | 20 | Nombre entier d'arrêts possibles |
| type_vehicule | — | — | Valeurs autorisées : moto, fourgon, camion |

## 3. Ma fonction predict()

Fichier : `logiai/predict.py`

```python
def predict(self, features: dict) -> dict:
    """features : un dictionnaire avec les 7 variables du contrat."""
    df = pd.DataFrame([features], columns=FEATURES)
    proba = float(self.model.predict_proba(df)[0, 1])
    return {
        "probabilite_retard": round(proba, 4),
        "alerte": proba >= self.threshold,
        "seuil": self.threshold,
        "model_version": self.version,
    }
```

Explication :

- Le dictionnaire contient les caractéristiques de la livraison.
- Pandas transforme ces caractéristiques en DataFrame.
- Le modèle calcule la probabilité de retard avec `predict_proba()`.
- La probabilité est comparée au seuil pour déterminer si une alerte doit être déclenchée.
- La fonction retourne la probabilité, l'alerte, le seuil et la version du modèle.

## 4. Quatre requêtes

| Requête | Code HTTP | Pourquoi |
|---|---:|---|
| Livraison normale | 200 | Les données sont valides et le modèle effectue la prédiction. |
| distance_km = -5 | 422 | La distance est inférieure à la borne minimale. |
| type_vehicule = "avion" | 422 | Le véhicule n'appartient pas aux valeurs autorisées. |
| Modèle absent | 503 | Le service ne peut pas effectuer de prédiction sans modèle chargé. |

## 5. Questions de compréhension

**1. Pourquoi charge-t-on le modèle au démarrage et pas à chaque requête ?**

Pour éviter de recharger le modèle à chaque demande. Cela améliore les performances et réduit le temps de réponse de l'API.

**2. Qui écrit le contrôle « pluie <= 100 », et où est-il écrit ?**

Le développeur définit cette règle dans le schéma Pydantic `Livraison`, dans `logiai/api/schemas.py`, avec `Field(ge=0, le=100)`. Pydantic applique automatiquement cette validation.

**3. Différence entre 422 et 503 ?**

- 422 : les données envoyées par le client sont invalides.
- 503 : le service est temporairement incapable de traiter la demande, par exemple lorsque le modèle est indisponible.

**4. Pourquoi une route `/v1/predict` plutôt que `/predict` ?**

Le préfixe `/v1` indique la version de l'API. Il permet de développer une nouvelle version sans casser les applications qui utilisent l'ancienne version.

**5. Que se passerait-il si la distance était déclarée `int` ?**

Les distances décimales ne seraient plus acceptées comme valeurs valides. On perdrait la précision nécessaire pour représenter des distances comme 12,5 km.

## 6. Décision : modèle absent

J'ai choisi de retourner une erreur HTTP 503 lorsque le modèle est absent.

Cette solution permet à l'API de démarrer même si le modèle n'est pas disponible. L'endpoint `/health` peut signaler que le modèle n'est pas chargé, tandis que l'endpoint de prédiction retourne 503.

L'autre solution consiste à empêcher le démarrage de l'application. Elle garantit que l'API ne fonctionne jamais sans modèle, mais rend également indisponibles les autres fonctionnalités du service.

## 7. Lien de la Pull Request

https://github.com/Dadasalma/logiai/pull/1

**État :** Pull Request créée et ouverte.

**Branche source :** `tp-api`

**Branche cible :** `main`

**Dernier commit :** `8dbd8c4`

**Validation :** 42 tests réussis.
