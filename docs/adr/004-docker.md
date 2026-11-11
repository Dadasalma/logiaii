# ADR 004 — Architecture de déploiement Docker

- **Statut :** Accepté
- **Date :** 11 novembre 2026
- **Projet :** LogiAI

## 1. Contexte

Le projet LogiAI dispose d'une API REST développée avec FastAPI et d'une interface web.
L'objectif de cet atelier est de conteneuriser ces composants et de permettre leur
déploiement avec une architecture simple et reproductible.

L'application doit également permettre à l'interface web de communiquer avec l'API
sans exposer directement l'adresse interne du conteneur API au navigateur.

## 2. Décisions

### 2.1 Conteneurisation de l'API

L'API est construite à partir de l'image `python:3.11-slim`.
Elle utilise Uvicorn pour exécuter FastAPI sur le port 8000 et écoute sur
`0.0.0.0` afin d'être accessible depuis les autres conteneurs.

Le port 8000 du conteneur est publié sur le port 8001 de la machine hôte.

### 2.2 Conteneurisation de l'interface web

L'interface web est servie par Nginx à partir de l'image `nginx:alpine`.
Le port 80 du conteneur est publié sur le port 8080 de la machine hôte.

### 2.3 Nginx comme reverse proxy

Nginx sert les fichiers statiques de l'interface web et redirige les requêtes
commençant par `/api/` vers `http://api:8000/`.

Le nom `api` correspond au nom du service Docker Compose.
La communication entre les conteneurs utilise donc le réseau interne Docker.

Le navigateur utilise une URL relative telle que `/api/v1/predict`.
Il communique ainsi avec la même origine que l'interface web, sans devoir connaître
l'adresse interne du conteneur API.

### 2.4 Orchestration avec Docker Compose

Docker Compose gère les deux services : `api` et `web`.

La directive `depends_on` avec `condition: service_healthy` permet d'attendre
que le healthcheck de l'API réussisse avant de démarrer le service web.

### 2.5 Vérification de santé

Un healthcheck exécute une requête HTTP vers `http://127.0.0.1:8000/health`
depuis le conteneur API.

Il est configuré avec :
- Intervalle : 30 secondes.
- Timeout : 5 secondes.
- Nombre de tentatives : 3.
- Période initiale : 10 secondes.

### 2.6 Données et configuration

Les dossiers `models` et `data` sont montés dans le conteneur API
pour rendre les fichiers accessibles à l'application.

Le fichier `.env` est utilisé par Docker Compose pour injecter les variables
d'environnement nécessaires à l'API au démarrage.

### 2.7 Choix entre COPY et volume pour le modèle

Le modèle est d'abord copié dans l'image Docker avec l'instruction `COPY models/ ./models/`.

Cependant, Docker Compose monte également le dossier local `models` dans `/app/models`.

Ce choix permet de conserver une copie du modèle dans l'image tout en facilitant son remplacement pendant le développement. Lorsqu'un modèle est modifié sur la machine hôte, le conteneur voit directement cette modification sans nécessiter une reconstruction de l'image.

Une alternative serait d'utiliser uniquement `COPY`. Cette solution rendrait l'image plus autonome et portable, mais chaque modification du modèle nécessiterait une reconstruction de l'image Docker.

Le volume a donc été retenu pour faciliter les expérimentations et les mises à jour du modèle.

### 2.8 Choix des ports publiés

Le port 8080 est utilisé comme point d'entrée principal de l'application à travers Nginx. Le port 8001 est également publié pour permettre de tester directement l'API FastAPI pendant le développement.

Une alternative serait de publier uniquement le port 8080. Cette solution limiterait l'accès direct à l'API et imposerait le passage par Nginx, ce qui serait préférable dans un environnement de production.

Pour cet atelier, les deux ports sont conservés afin de faciliter les tests et le débogage.

## 3. Alternatives étudiées

- Exécuter l'API et l'interface directement sur la machine : solution moins reproductible et dépendante de l'environnement local.
- Exposer directement l'API au navigateur : nécessite de gérer la communication entre origines et ne fournit pas le même point d'entrée que Nginx.
- Démarrer les services sans healthcheck : le service web pourrait démarrer avant que l'API soit réellement prête.
- Utiliser uniquement COPY pour le modèle : rend l'image autonome, mais nécessite une reconstruction après chaque mise à jour du modèle.
- Publier uniquement le port 8080 : limite l'accès direct à l'API, mais rend les tests directs plus difficiles.

## 4. Conséquences

### Avantages

- Déploiement reproductible avec Docker Compose.
- Séparation entre l'API et l'interface web.
- Point d'entrée principal pour l'interface web sur le port 8080, avec un accès direct à l'API sur le port 8001 pour les tests.
- Communication interne entre les conteneurs via le réseau Docker.
- Vérification automatique de la disponibilité de l'API.
- Conservation des données et modèles grâce aux volumes.

### Limites

- Le bon fonctionnement de l'application dépend de la disponibilité de l'API.
- La configuration des services et du reverse proxy doit rester cohérente.
- Le fichier `.env` doit être fourni séparément lors du déploiement.
- La publication du port 8001 permet de contourner Nginx et doit être réévaluée en production.

## 5. Conclusion

L'architecture retenue utilise Docker Compose pour orchestrer une API FastAPI
et une interface web servie par Nginx.

Nginx joue le rôle de reverse proxy, tandis que le healthcheck permet de vérifier
que l'API est prête avant le démarrage du service web.

Cette architecture répond aux objectifs de conteneurisation et de déploiement
de l'atelier 5.
