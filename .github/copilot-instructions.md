# Instructions du projet EIGSI Suivi Alumni

## Validation avant modification

Avant toute modification de fichier, proposer un PLAN précis : objectif, fichiers,
critères d'acceptation, commandes de vérification et limites. Attendre la réponse
explicite « OK » de l'étudiant. Les lectures et diagnostics sont possibles avant OK.
Si le périmètre change, présenter le nouveau plan avant les modifications associées.

## Sources et périmètre

- Lire README.md et les deux rapports PDF à la racine.
- Respecter US01 à US06 (Must), puis US07 et US08 (Should).
- Ne pas implémenter US10 (recommandations IA).
- Stack effective : Vite + JavaScript, FastAPI + SQLAlchemy, PostgreSQL/SQLite.
- La conception S2 prévoyait React/TypeScript : documenter cet écart, sans prétendre
  que le code actuel utilise ces technologies.
- L'interface actuelle utilise localStorage. Ne pas annoncer de persistance serveur
  ou d'authentification réelle tant que ces parcours ne sont pas implémentés et testés.
- X-Role est un mécanisme de démonstration, pas une authentification sécurisée.

## Règles métier

- Unicité de l'e-mail et du matricule ; ne jamais fusionner automatiquement.
- Consentement explicite et révocable, jamais déduit d'un import CSV.
- Une validation exige champs complets, consentement et examen des doublons.
- Correction/rejet : motif conservé, décision et date journalisées.
- KPI calculés à partir des données ; afficher « Non mesuré » si les dates manquent.
- Échapper les données dans le HTML et les attributs ; contrôler les données côté API.
- Ne jamais publier de secret, d'e-mail réel ou de clé Gemini/Grok dans le dépôt.

## Vérification

Frontend : `pnpm run lint`, `pnpm test`, `pnpm run build`.
Backend : `ruff check .`, `pytest -q`.
Exécuter les parcours dans le navigateur : soumission, consentement, correction,
validation, recherche, CSV, rechargement. Distinguer simulation locale et accès API.

## Comparatif de modèles

Chaque étudiant sélectionne son moteur dans Copilot Agent et réalise ses propres
exécutions. Conserver les plans et leurs validations OK, les erreurs, correctifs,
commandes et résultats. Ne jamais inventer des essais Gemini, Auto ou Grok.

## Livrable

Une vraie vidéo par étudiant dans demo/NomEtudiant.mp4, <= 100 000 000 octets.
Le dépôt reste public. Ne pas présenter une vidéo existante comme la preuve d'une
nouvelle exécution ou d'un moteur sans vérification.
