# Atelier 5 — Conteneurisation et déploiement Docker

## 1. Observation initiale

Avant la conteneurisation, le fonctionnement de LogiAI dépendait de plusieurs éléments installés et configurés sur la machine :

- Une version compatible de Python.
- Les dépendances du projet installées dans l'environnement virtuel.
- Un fichier `.env` contenant les clés API nécessaires.
- Le modèle entraîné disponible dans le dossier `models`.
- Le lancement manuel de l'API FastAPI et de l'interface web.

Ces éléments nécessitaient une configuration préalable de l'environnement.

Avec Docker, l'objectif est de rendre le déploiement plus reproductible. Un autre utilisateur peut construire et démarrer les services avec Docker Compose, à condition de disposer de Docker, des fichiers du projet, du modèle et de son propre fichier `.env`.

## 2. Architecture Docker retenue

L'architecture repose sur deux conteneurs :

- **API :** construite à partir de `python:3.11-slim`, elle exécute FastAPI avec Uvicorn sur le port 8000.
- **Web :** construite à partir de `nginx:alpine`, elle sert l'interface web et joue le rôle de reverse proxy.

Le fichier `docker-compose.yml` orchestre les deux services.

Les ports publiés sont :
- `8001:8000` pour accéder directement à l'API depuis la machine hôte.
- `8080:80` pour accéder à l'interface web à travers Nginx.

Nginx transmet les requêtes commençant par `/api/` au service `api` sur le réseau interne Docker.

Le healthcheck vérifie la disponibilité de l'API avant le démarrage du service web grâce à `depends_on` et `condition: service_healthy`.

Les dossiers `models` et `data` sont montés comme volumes pour rendre les fichiers accessibles dans le conteneur API.

Le fichier `.env` est injecté au démarrage avec `env_file` et n'est pas intégré à l'image Docker.

## 3. Expériences sur le lancement de l'API

### Expérience 1 : lancement sans fichier `.env`

**Commande utilisée :**

`docker run` sans option `--env-file`.

**Résultat observé :**

- L'endpoint `/health` retourne HTTP 200.
- Le modèle est chargé.
- Une requête de prédiction retourne HTTP 401.

**Explication :**

Le conteneur peut démarrer et charger le modèle, mais les variables d'environnement contenant la clé API ne sont pas injectées. L'authentification échoue donc lors de la prédiction.

Cette expérience montre l'importance de transmettre la configuration nécessaire au conteneur.

### Expérience 2 : lancement sans publication de port

**Commande utilisée :**

`docker run -d --name logiai-api-test --env-file .env logiai:1.0`

**Résultat observé :**

Le conteneur démarre correctement et affiche `8000/tcp`, mais l'accès à `localhost:8000` depuis la machine hôte échoue.

**Explication :**

La directive `EXPOSE 8000` dans le Dockerfile documente le port utilisé par l'application. Elle ne publie pas automatiquement ce port sur la machine hôte.

Pour rendre le service accessible depuis l'hôte, il faut utiliser l'option `-p`, par exemple `-p 8002:8000`.

### Expérience 3 : lancement avec Uvicorn sur 127.0.0.1

**Configuration testée :**

Uvicorn est lancé avec l'adresse `127.0.0.1` au lieu de `0.0.0.0`.

**Résultat observé :**

Le conteneur démarre et le port est publié avec `8002:8000`, mais la requête retourne une réponse vide.

**Explication :**

L'adresse `127.0.0.1` permet à l'application d'écouter uniquement sur l'interface locale du conteneur.

Docker doit pouvoir atteindre l'application à travers l'interface réseau du conteneur. Il faut donc utiliser `0.0.0.0` pour rendre Uvicorn accessible depuis l'extérieur du conteneur.

## 4. Configuration de Nginx et reverse proxy

Nginx sert l'interface web et joue le rôle de reverse proxy entre le navigateur et l'API FastAPI.

Dans la configuration, le bloc `location /api/` transmet les requêtes au service API grâce à :

`proxy_pass http://api:8000/;`

Lorsqu'un utilisateur effectue une requête vers :

`/api/v1/predict`

Nginx transmet la requête à FastAPI sous le chemin :

`/v1/predict`

Le nom `api` correspond au nom du service dans Docker Compose. Les conteneurs communiquent entre eux grâce au réseau interne Docker.

La clé API est transmise dans l'en-tête `X-API-Key`.

L'interface et l'API utilisent la même origine, ce qui évite une configuration CORS supplémentaire et une requête OPTIONS de pré-vérification dans le scénario testé.

## 5. Vérification des réponses HTTP

Les tests réalisés à travers Nginx ont donné les résultats suivants :

| Requête | Code HTTP | Explication |
|---|---:|---|
| GET `/api/health` | 200 | L'API est disponible. |
| POST `/api/v1/predict` sans clé | 401 | La clé API est absente. |
| POST `/api/v1/predict` avec une fausse clé | 401 | La clé API est invalide. |
| POST `/api/v1/predict` avec une clé valide | 200 | L'authentification réussit et la prédiction est effectuée. |

Ces tests confirment le bon fonctionnement du reverse proxy et du mécanisme d'authentification.

## 6. Accès à l'application depuis un téléphone

L'application est accessible depuis la machine hôte à l'adresse :

`http://localhost:8080`

Pour tester l'accès depuis un autre appareil connecté au même réseau, j'ai utilisé l'adresse IPv4 locale de la machine qui exécute Docker.

L'application a été accessible depuis le téléphone avec l'adresse :

`http://172.20.10.5:8080`

Cette vérification montre que l'application n'est pas uniquement accessible depuis le navigateur de la machine hôte. Elle peut également être consultée depuis un autre appareil du réseau local.

L'accès nécessite que Docker Compose soit démarré et que les appareils soient connectés au même réseau.

## 7. Test d'indisponibilité et de redémarrage de l'API

J'ai arrêté le service API avec :

`docker compose stop api`

Le service Web Nginx est resté démarré, mais une tentative de prédiction a retourné une erreur HTTP 502.

Cette erreur indique que Nginx ne pouvait plus communiquer avec le service API.

Ensuite, j'ai redémarré l'API avec :

`docker compose start api`

Après quelques secondes, le healthcheck a confirmé que l'API était de nouveau disponible avec l'état `healthy`.

Une nouvelle prédiction a fonctionné correctement.

La probabilité de retard observée était de 48,4 %, avec une alerte activée, car cette probabilité dépassait le seuil de 0,4.

Cette expérience montre l'intérêt du healthcheck pour surveiller la disponibilité du service API.

## 8. Observation des ressources avec Docker Stats

La commande utilisée est :

`docker stats --no-stream`

Elle permet d'observer la consommation des ressources des conteneurs.

| Conteneur | CPU | Mémoire utilisée | Nombre de processus |
|---|---:|---:|---:|
| logiai-web | 0,00 % | 7,992 MiB | 9 |
| logiai-api | 0,19 % | 159,8 MiB | 21 |

L'API consomme davantage de mémoire que le service Nginx, notamment parce qu'elle charge le modèle de machine learning et ses dépendances.

Cette commande permet de surveiller les ressources utilisées par chaque conteneur.

## 9. Vérification des volumes

Les dossiers `models` et `data` sont montés dans le conteneur API avec des volumes Docker.

J'ai vérifié le contenu du dossier `/app/models` depuis le conteneur.

J'ai ensuite créé un fichier `volume_test.txt` dans le dossier `models` sur la machine hôte.

Ce fichier est apparu immédiatement dans le conteneur, sans reconstruction de l'image Docker.

Après sa suppression sur la machine hôte, il a également disparu du conteneur.

**Conclusion :**

Le bind mount permet de partager les fichiers entre la machine hôte et le conteneur. Les modifications des fichiers montés sont visibles immédiatement.

À l'inverse, le code de l'application est copié dans l'image avec `COPY`. Une modification de ce code nécessite donc une reconstruction de l'image, par exemple avec `docker compose up -d --build`.

## 10. Consultation des logs

La commande utilisée est :

`docker compose logs --tail=30 api`

Les logs affichent notamment deux types de requêtes :

- `GET /health` avec le statut HTTP 200 : ces requêtes correspondent aux vérifications périodiques du healthcheck.
- `POST /v1/predict` avec le statut HTTP 200 : cette requête montre qu'une prédiction a été traitée correctement.

Un exemple observé :

`172.19.0.3 - "POST /v1/predict HTTP/1.1" 200 OK`

L'adresse IP correspond au conteneur Nginx qui transmet la requête à l'API.

Les logs permettent donc de suivre les requêtes reçues et de vérifier le fonctionnement du service.

## 11. Questions de compréhension

**1. Quelle est la différence entre une image Docker et un conteneur ?**

Une image Docker est un modèle contenant les éléments nécessaires à l'exécution d'une application. Un conteneur est une instance de cette image en cours d'exécution.

**2. Pourquoi le navigateur utilise-t-il `/api/v1/predict` et non `api:8000` ?**

Le navigateur utilise l'adresse accessible depuis la machine de l'utilisateur. Le nom `api` est un nom de service interne au réseau Docker. Nginx reçoit la requête du navigateur puis la transmet à l'API en utilisant ce nom interne.

**3. Pourquoi `depends_on` seul ne suffit-il pas ?**

`depends_on` peut définir l'ordre de démarrage des services, mais il ne garantit pas que l'API soit réellement prête à recevoir des requêtes.

Avec `condition: service_healthy`, Docker Compose attend que le healthcheck de l'API indique qu'elle est disponible avant de démarrer le service Web.

**4. Quelle est la différence entre `EXPOSE` et `-p` ?**

`EXPOSE` documente le port utilisé par le conteneur. `-p` publie réellement un port du conteneur sur la machine hôte.

**5. Quelle est la différence entre COPY et un bind mount ?**

`COPY` ajoute des fichiers dans l'image Docker pendant sa construction. Pour intégrer de nouvelles modifications, il faut reconstruire l'image.

Un bind mount partage directement un dossier de la machine hôte avec le conteneur. Les modifications sont visibles sans reconstruire l'image.

## 12. Validation finale

Les vérifications finales réalisées sont :

- La configuration Docker Compose est valide avec `docker compose config --quiet`.
- Les deux services API et Web fonctionnent.
- Le healthcheck de l'API indique que le service est disponible.
- Les requêtes de prédiction fonctionnent à travers Nginx.
- L'application est accessible depuis un téléphone connecté au même réseau.
- Les tests automatisés sont réussis : **42 passed, 1 warning**.

Le déploiement local de LogiAI repose sur Docker Compose, avec FastAPI pour l'API et Nginx pour servir l'interface et transmettre les requêtes.

## 13. Lien de la Pull Request Atelier 5

À compléter après la création de la Pull Request.

**Branche source :** `atelier5`

**Branche cible :** `main`

**Pull Request :** à compléter.

**Tag :** `tp5`