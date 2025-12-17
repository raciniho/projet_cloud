# Rapport d'Architecture Microservice MinIO

## Vue d'ensemble
Ce projet implémente un microservice REST pour la gestion de fichiers, utilisant une architecture conteneurisée avec Docker Compose. Le système est composé de trois services principaux interconnectés.

![Architecture Diagram](https://mermaid.ink/img/pako:eNptkMFOwzAMhl_F8gmp4wV44LQTQ0wIt01IHC6tW9XYSRwUBap3x0m7DozT_Pnz2_9fMsolzZARRWfrWAc9iwvG-1N2BC-WiyfQcArfUIdq-74_gO_BwRkc4RMa0EMD1-B78DAA9-DjCDrwz2_BwzN4eAMdDLAG39_AFRzAAHvw_RNcwQ1s4ADW4PsXuIIH2MABbMH3L3AFn6dp-vQ8Td_e0_TjI03fP9L04zNNP7_S9OsvTb_9pukP_4x-h2XG2JgS1sFaU0Jjra0l42OOS_bRejLKeGusNfaYom-t9XRYj4yx1lqbz9F7a63N5-iDtTY_v_QxRe-ttTZ_fvlDdH5-A6pIf0E)

### Services

1.  **API Services (FastAPI)**
    *   **Rôle**: Point d'entrée unique pour le client. Gère la logique métier, la validation, et l'orchestration.
    *   **Technologies**: Python 3.10, FastAPI, Uvicorn, SQLModel.
    *   **Port interne**: 8000.

2.  **Stockage Objet (MinIO)**
    *   **Rôle**: Stockage persistant et performant des fichiers binaires. Compatible S3.
    *   **Configuration**: Persistance locale via volume Docker `minio_data`.
    *   **Ports**: 9000 (API), 9001 (Console).

3.  **Base de Données (PostgreSQL)**
    *   **Rôle**: Stockage structuré des métadonnées des fichiers (taille, hash, type mime, dates).
    *   **Mode**: Asynchrone (AsyncPG) pour des performances non-bloquantes avec FastAPI.
    *   **Port**: 5432.

## Flux de Données

### 1. Upload de Fichier
Lorsqu'un utilisateur envoie un fichier sur `POST /files/upload` :
1.  L'API reçoit le flux de données.
2.  Elle calcule à la volée le hash **SHA-256** et la taille du fichier.
3.  Elle transmet le fichier au service **MinIO** avec un nom unique (UUID).
4.  Une fois le stockage confirmé, elle enregistre les métadonnées dans **PostgreSQL**.
5.  Elle retourne l'objet métadonnée complet au client.

### 2. Téléchargement (Download)
Lors d'une requête `GET /files/{id}` :
1.  L'API vérifie l'existence de l'ID dans **PostgreSQL**.
2.  Elle récupère le nom de l'objet MinIO associé.
3.  Elle ouvre un flux de lecture depuis **MinIO**.
4.  Elle stream la réponse directement au client (StreamingResponse) pour minimiser l'usage mémoire.

## Modèle de Données (FileMetadata)

| Champ | Type | Description |
|-------|------|-------------|
| `id` | UUID | Clé primaire unique |
| `filename` | String | Nom original du fichier |
| `size` | Integer | Taille en octets |
| `content_type` | String | Type MIME (ex: image/png) |
| `hash` | String | Empreinte SHA-256 pour intégrité |
| `upload_date` | DateTime | Timestamp d'upload |
| `minio_object_name` | String | Identifiant interne dans MinIO |

## Sécurité et Performance
*   **Hashage** : Garantit l'intégrité des fichiers.
*   **Async/Await** : Utilisation complète des capacités asynchrones de Python pour gérer de multiples requêtes I/O (DB et Réseau) sans bloquer le thread principal.
*   **Containerisation** : Isolation complète des services via Docker.
