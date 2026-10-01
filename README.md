# EIGSI - Suivi Alumni

Plateforme MVP de collecte, validation, actualisation et pilotage des données Alumni de l'EIGSI. Le projet fournit une interface démontrable pour les quatre rôles du processus et une API REST prête à fonctionner avec PostgreSQL.

## Objectifs et périmètre du MVP

Le MVP remplace les fichiers dispersés par un référentiel cohérent et traçable. Il couvre le parcours : invitation, saisie du profil, consentement, contrôle, correction éventuelle, validation, publication dans l'annuaire et mise à jour des indicateurs.

Le périmètre comprend profil, consentement, doublons, validation, recherche, KPI, CSV, relances et journalisation. La recommandation de contacts par IA reste volontairement hors MVP.

## Fonctionnalités implémentées

- profil Alumni et consentement révocable ;
- annuaire avec recherche et filtres ;
- validation, correction, rejet motivé et détection de doublon ;
- dashboard Direction avec quatre KPI et répartition par promotion ;
- campagnes, import/export CSV et journal d'activité ;
- API de création, recherche, validation et agrégation des profils ;
- contrôle des rôles et contraintes d'unicité côté API ;
- schéma relationnel et migration Alembic initiale.

> L'interface utilise encore des données de démonstration stockées dans le navigateur. L'API et la base sont opérationnelles, mais leur branchement complet à chaque écran est une évolution identifiée du MVP.

## Acteurs et rôles

| Rôle | Responsabilités principales |
| --- | --- |
| Alumni | Compléter le profil, consentir, actualiser les informations et consulter le réseau. |
| Service Alumni | Contrôler les fiches, traiter les doublons, demander une correction, valider ou rejeter. |
| Direction | Consulter les KPI et les données agrégées. |
| Administrateur | Administrer les données, imports, exports, campagnes et traces. |

## Architecture et technologies

```text
Navigateur
  ├── frontend/ : Vite + HTML/CSS/JavaScript
  └── backend/  : FastAPI + Pydantic + SQLAlchemy
                         │
                         ├── PostgreSQL en production/Docker
                         └── SQLite pour le développement rapide
```

- **Frontend** : Vite, JavaScript, CSS responsive, Vitest et ESLint.
- **Backend** : Python, FastAPI, Pydantic, SQLAlchemy, Alembic, Pytest et Ruff.
- **Base** : PostgreSQL 16 ; SQLite pour les tests locaux.
- **Déploiement local** : Docker Compose.

## Prérequis

- Git ;
- Node.js 20 ou 22 avec Corepack/pnpm ;
- Python 3.11 ou 3.12 ;
- PostgreSQL 16, sauf avec SQLite ou Docker Compose ;
- Docker Desktop pour le lancement conteneurisé.

## Installation

```bash
git clone https://github.com/ziad4222/eigsi-suivi-alumni.git
cd eigsi-suivi-alumni
cp .env.example .env
```

Sous PowerShell : `Copy-Item .env.example .env`.

Frontend :

```bash
cd frontend
corepack enable
pnpm install
pnpm run build
```

Backend sous Linux/macOS :

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
```

Backend sous PowerShell :

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
```

## Configuration

Copier `.env.example` vers `.env`, puis renseigner localement :

| Variable | Description |
| --- | --- |
| `DATABASE_URL` | URL SQLAlchemy PostgreSQL ou SQLite. |
| `SECRET_KEY` | Secret fort utilisé par l'authentification future. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Durée de vie d'un jeton d'accès. |
| `CORS_ORIGINS` | Origines frontend autorisées, séparées par des virgules. |
| `POSTGRES_DB` | Nom de la base utilisée par Docker Compose. |
| `POSTGRES_USER` | Utilisateur PostgreSQL utilisé par Docker Compose. |
| `POSTGRES_PASSWORD` | Mot de passe PostgreSQL local utilisé par Docker Compose. |

Ne jamais committer `.env`. Les identifiants de `docker-compose.yml` servent uniquement au développement local.

## Base de données

Par défaut, l'API utilise `sqlite:///./alumni.db`. Pour PostgreSQL, renseigner `DATABASE_URL`, puis :

```bash
cd backend
alembic upgrade head
```

Pour créer une future migration :

```bash
alembic revision --autogenerate -m "description"
```

## Lancer la plateforme

Terminal 1 :

```bash
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Terminal 2 :

```bash
cd frontend
pnpm run dev
```

- interface : <http://localhost:4173> ;
- documentation API : <http://localhost:8000/docs> ;
- contrôle API : <http://localhost:8000/health>.

Avec Docker Compose :

```bash
docker compose up --build
```

## Tests et qualité

```bash
cd frontend
pnpm run lint
pnpm test
pnpm run build

cd ../backend
ruff check .
pytest -q
```

## Structure

```text
.
├── backend/                 # API, schéma, migrations et tests
├── frontend/                # Interface, styles et tests
├── demo/                    # Consignes et futures vidéos MP4
├── docs/screenshots/        # Captures finales validées
├── Rapport_Final_SI_Suivi_Alumni_EIGSI.pdf
├── S2_Rapport_Suivi_Alumni.pdf
├── .env.example
└── docker-compose.yml
```

## Captures d'écran

Les captures finales sont documentées dans [`docs/screenshots/`](docs/screenshots/README.md) : dashboard Direction, profil Alumni, validation Service Alumni et annuaire.

## Démonstration vidéo

Voir [`demo/README.md`](demo/README.md). Les vidéos doivent être ajoutées sous la forme `NomEtudiant.mp4` et rester sous 100 Mo. Aucun nom ni fichier vidéo artificiel n'est créé.

## Limites connues

- l'interface exploite encore `localStorage` et n'appelle pas tous les endpoints de l'API ;
- l'envoi d'e-mails, le SSO EIGSI et l'authentification JWT complète exigent les services institutionnels ;
- les données affichées sont fictives ;
- aucune vidéo d'étudiant ni capture définitive n'est versionnée ;
- les recommandations par IA sont hors MVP.

## Rapports

- [Session 1 - Cadrage fonctionnel](Rapport_Final_SI_Suivi_Alumni_EIGSI.pdf)
- [Session 2 - Conception technique](S2_Rapport_Suivi_Alumni.pdf)

## Contributeurs

Projet réalisé par l'équipe projet EIGSI. Les noms individuels seront ajoutés uniquement après validation par les étudiants concernés.
