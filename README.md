# EIGSI — Suivi Alumni

MVP connecté : les profils, consentements, validations, campagnes et traces sont
enregistrés par FastAPI dans SQLite ou PostgreSQL. L'interface principale utilise
les endpoints `/api` ; le navigateur ne contient plus la base métier.

## Fonctionnalités

- Inscription Alumni, connexion, cookie JWT HttpOnly, sessions révocables et expiration.
- Rôles vérifiés en base : Alumni, Service Alumni, Direction, Administrateur.
- Création et mise à jour du profil personnel, champs contrôlés, matricule unique.
- Consentement daté et révocable ; retrait immédiat de l'annuaire à la révocation.
- Examen de l'unicité, correction/rejet motivé, validation horodatée et auteur réel.
- Annuaire des profils validés consentants, recherche et filtres combinables.
- Quatre KPI calculés côté serveur, répartition par promotion.
- Import CSV avec prévisualisation et bilan par ligne ; export filtré réservé à l'Admin.
- Campagnes préparées pour les profils de plus de 365 jours et suivi des confirmations.
- Journal d'activité serveur. Aucun e-mail réel n'est envoyé.

## Installation locale (PowerShell)

Prérequis : Git, Node.js 22, pnpm, Python 3.12.

```powershell
git clone https://github.com/ziad4222/eigsi-suivi-alumni.git
cd eigsi-suivi-alumni
Copy-Item .env.example .env
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
alembic upgrade head
python -m app.bootstrap --demo
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Le bootstrap demande un mot de passe choisi localement et crée quatre comptes
fictifs : `alumni@example.com`, `service@example.com`, `direction@example.com`,
`admin@example.com`. Il conserve les comptes déjà présents. Un profil fictif
Alumni est initialement en attente de validation.

Dans un deuxième terminal, à la racine du dépôt :

```powershell
cd frontend
pnpm install --frozen-lockfile
pnpm run dev
```

- Interface : http://localhost:4173
- Documentation API : http://localhost:8000/docs
- Santé : http://localhost:8000/health

Le proxy Vite transmet `/api` au backend. `API_TARGET` peut remplacer
`http://127.0.0.1:8000` ; Docker utilise `http://backend:8000`.

Pour créer un compte privilégié individuel : `python -m app.bootstrap --email
responsable@example.com --role SERVICE` (commande sur une ligne depuis backend).
L'inscription publique crée toujours un compte ALUMNI, jamais un rôle privilégié.

## Configuration et données

`.env` n'est jamais committé. Renseigner `SECRET_KEY` avec une valeur aléatoire
longue pour conserver les sessions après redémarrage. Sans clé configurée, une clé
éphémère est créée et les utilisateurs doivent se reconnecter après redémarrage.
`ACCESS_TOKEN_EXPIRE_MINUTES` vaut 30. Sous HTTPS, activer `COOKIE_SECURE=true`.
Les mots de passe sont hachés avec scrypt ; les jetons restent en cookie HttpOnly.
`X-Role` est ignoré : seul le compte authentifié décide des droits.

L'API n'expose dans l'annuaire ni e-mail, ni matricule, ni commentaire de contrôle.
Le Service Alumni et l'Admin peuvent accéder aux fiches privées ; la Direction
consulte les données agrégées et l'annuaire professionnel.

Pour PostgreSQL/Docker, renseigner `POSTGRES_PASSWORD` et les variables PostgreSQL
dans `.env`, puis `docker compose up --build`. Initialiser les comptes avec
`docker compose exec backend python -m app.bootstrap --demo`.
Le lancement Docker/PostgreSQL n'a pas été exécuté sur cette machine ; les tests
et migrations ont été vérifiés avec SQLite.

## Qualité et démonstration

```powershell
cd frontend
pnpm run lint
pnpm test
pnpm run build
cd ../backend
ruff check .
pytest -q
```

Le workflow `.github/workflows/quality.yml` exécute ces contrôles et vérifie la
taille des MP4. La suite comprend les anciens tests de la démo locale et les tests
API du parcours connecté : propriété du profil, droits, publication, révocation,
import/export et invalidation des sessions. Voir `docs/SEANCES_3_4.md` pour le bilan.

## Limites explicites

- L'interface reste en JavaScript/Vite ; la conception S2 prévoyait React/TypeScript.
- Pas de SSO, d'e-mail de vérification, de récupération de mot de passe ni de refresh
  token ; à expiration, l'utilisateur se reconnecte. La protection anti-abus et les
  sauvegardes sont à configurer avant une ouverture publique du service.
- Les comptes importés sont verrouillés (`INVITATION_PENDING`) ; la distribution
  d'invitations et l'activation des comptes ne sont pas implémentées.
- Les campagnes restent préparées en base ; les confirmations ultérieures sont
  comptées, sans prétendre mesurer une livraison d'e-mails.
- La couverture utilise les fiches recensées comme dénominateur, faute de référentiel
  institutionnel des diplômés ciblés. Délais en jours calendaires et fraîcheur à 365 jours.
- Les anciennes fonctions locales sont conservées dans `frontend/public/app.js`
  pour référence et tests ; seule `connected.js` est chargée par l'interface.
- Les recommandations IA sont hors MVP.

## Rendu pédagogique

Rapports de cadrage et S2 présents à la racine. Instructions de travail dans
`.github/copilot-instructions.md`. Vidéo existante : `demo/ZiadHarrasse.mp4`,
78 339 007 octets. Elle doit être revue ou refaite pour montrer cette version connectée.

Membres déclarés : Ziad Harrasse, Ahmed Cherif et Dev. Moteur retenu pour Ziad :
Copilot Auto/Standard. Les corrections ici ont été réalisées dans Codex ; les
exécutions individuelles Gemini/Auto/Grok et les contributions des autres membres
ne sont pas attestées. Les vidéos manquantes et résultats comparatifs ne sont pas inventés.

Message de soumission, une fois le rendu contrôlé :

```text
MAJ GIT (MVP) : https://github.com/ziad4222/eigsi-suivi-alumni
```
