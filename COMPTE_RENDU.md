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


# Atelier 5 — Conteneurisation et déploiement Docker

**Nom :** Salma ait dada
**Groupe :** G3

## 1. Environnement et premiers tests

Avant la conteneurisation, l'application LogiAI fonctionnait directement sur mon environnement local. L'API FastAPI et l'interface web étaient lancées séparément.

L'objectif de cet atelier est de faciliter le déploiement grâce à Docker, en isolant les services dans des conteneurs et en utilisant Docker Compose pour les orchestrer.

## 2. Architecture Docker retenue

L'application est organisée en deux services :

- **API :** conteneur basé sur `python:3.11-slim`, qui exécute FastAPI sur le port 8000.
- **Web :** conteneur basé sur `nginx:alpine`, qui sert l'interface web sur le port 80 et joue le rôle de reverse proxy.

Les deux services sont orchestrés avec Docker Compose.

| Service | Port conteneur | Port local |
|---|---:|---:|
| API | 8000 | 8001 |
| Web (Nginx) | 80 | 8080 |

Docker Compose configure les ports, les variables d'environnement, les volumes et le démarrage des services. Un healthcheck vérifie la disponibilité de l'API avant le démarrage du service Web.

## 3. Configuration et communication

Nginx sert l'interface web et redirige les requêtes commençant par `/api/` vers le service API.

La configuration utilise `http://api:8000/`. Le nom `api` correspond au nom du service dans Docker Compose et permet la communication entre les conteneurs.

L'interface utilise l'adresse `/api/v1/predict`. Cela permet de passer par Nginx sans exposer directement l'adresse interne du conteneur API au navigateur.

La clé API est transmise dans l'en-tête `X-API-Key`.

## 4. Tests réalisés

Les tests ont été effectués à travers Nginx, à l'adresse `http://localhost:8080`.

| Test | Résultat HTTP | Interprétation |
|---|---:|---|
| `/api/health` | 200 | L'API est disponible. |
| Prédiction sans clé | 401 | La clé API est obligatoire. |
| Prédiction avec une fausse clé | 401 | La clé est invalide. |
| Prédiction avec une clé valide | 200 | La prédiction fonctionne. |

Une requête de prédiction a également été vérifiée dans l'onglet Network du navigateur : `POST /api/v1/predict` a retourné `200 OK`.

## 5. Expériences Docker

Plusieurs expériences ont permis de comprendre le fonctionnement des conteneurs :

- **Sans fichier `.env` :** l'API démarre, mais une prédiction sans clé correctement configurée retourne 401.
- **Sans publication du port (`-p`) :** le conteneur fonctionne, mais le service n'est pas accessible directement depuis le navigateur sur le port local.
- **Avec Uvicorn sur `127.0.0.1` :** le service n'est pas accessible depuis l'extérieur du conteneur. Il faut utiliser `0.0.0.0`.
- **Avec un volume :** un fichier créé dans le dossier `models` sur l'hôte apparaît directement dans le conteneur. Sa suppression sur l'hôte est également visible dans le conteneur.

Ces expériences montrent la différence entre les ports internes et externes, ainsi que l'utilité des volumes Docker.

## 6. Healthcheck et gestion des services

Le healthcheck permet de vérifier régulièrement que l'API répond correctement à la route `/health`.

Lorsque l'API a été arrêtée, Nginx a retourné une erreur `502 Bad Gateway`, car le service backend était indisponible. Après le redémarrage de l'API, les requêtes ont de nouveau fonctionné.

La commande `docker compose logs --tail=30 api` permet de consulter les journaux du conteneur API.

## 7. Accès depuis un autre appareil

L'interface web a été accessible depuis un téléphone connecté au même réseau local, avec l'adresse :

`http://172.20.10.5:8080`

Cela montre que l'application peut être consultée depuis un autre appareil du réseau local.

## 8. Ressources des conteneurs

La commande `docker stats --no-stream` a permis d'observer les ressources utilisées :

| Conteneur | Mémoire utilisée | CPU |
|---|---:|---:|
| API | 159.8 MiB | 0.19 % |
| Web | 7.992 MiB | 0.00 % |

Ces mesures correspondent à une observation ponctuelle pendant les tests.

## 9. Questions de compréhension

**1. Quelle est la différence entre une image et un conteneur ?**

Une image est un modèle utilisé pour créer un conteneur. Un conteneur est une instance en cours d'exécution de cette image.

**2. Pourquoi le navigateur utilise-t-il `/api/v1/predict` et non `api:8000` ?**

Parce que `api` est un nom interne au réseau Docker. Le navigateur communique avec Nginx, qui transmet ensuite la requête à l'API.

**3. Pourquoi `depends_on` ne suffit-il pas à vérifier que l'API est prête ?**

Il peut contrôler l'ordre de démarrage, mais ne garantit pas à lui seul que l'API est opérationnelle. Le healthcheck permet de vérifier son état.

**4. Quelle est la différence entre `EXPOSE` et `-p` ?**

`EXPOSE` documente le port utilisé dans le conteneur. `-p` publie ce port pour le rendre accessible depuis l'hôte.

**5. Quelle est la différence entre `COPY` et un volume ?**

`COPY` ajoute des fichiers à l'image pendant sa construction. Un volume permet de partager des fichiers entre l'hôte et le conteneur.

## 10. Validation finale

Les vérifications suivantes ont été réalisées :

- `docker compose config --quiet` : configuration valide.
- Les deux conteneurs sont démarrés.
- Le healthcheck de l'API est opérationnel.
- Les requêtes de prédiction fonctionnent à travers Nginx.
- L'interface est accessible depuis le réseau local.
- Les tests Python : 42 réussis, 1 avertissement.

## 11. Pull Request

**Dépôt :** `Dadasalma/logiaii`

**Pull Request :** https://github.com/Dadasalma/logiaii/pull/1

**Branche source :** `atelier5`

**Branche cible :** `main`

**État :** Pull Request créée et ouverte.
