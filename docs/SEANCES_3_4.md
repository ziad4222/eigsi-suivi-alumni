# Séances 3 et 4 — Bilan du MVP

État vérifié le 22 octobre 2026.

## Partie A — Analyse et préparation

Les deux rapports de conception présents à la racine ont été lus. Le développement
reprend les parcours Alumni, Service Alumni, Direction et Administrateur. Le README
décrit l'installation Python/Node, les migrations et le démarrage en deux terminaux.

Le guide Word pédagogique n'a pas été fourni et son lien n'a pas pu être lu :
ce bilan ne peut donc pas certifier ses instructions détaillées. La stack effective
est JavaScript/Vite et FastAPI/SQLAlchemy, avec SQLite localement et PostgreSQL prévu
dans Docker. React/TypeScript prévus dans le rapport S2 ne sont pas utilisés.

## Partie B — Instructions et agents du workspace

Les instructions communes sont dans `.github/copilot-instructions.md` : proposer un
plan, attendre « OK », puis modifier les fichiers et vérifier les résultats.

Prompt de départ suggéré, qui ne remplace pas le guide Word :

> Lis le cadrage, la conception S2, le README et les instructions du workspace.
> Propose un plan précis avec les fichiers concernés et les tests à exécuter.
> Ne modifie aucun fichier avant mon « OK ».

Membres déclarés par l'utilisateur : Ziad Harrasse, Ahmed Cherif et Dev.
Moteur retenu pour Ziad : Copilot Auto/Standard. Les corrections de cette livraison
ont été réalisées dans Codex. L'exécution de l'Agent Copilot avec Auto/Standard
reste à documenter dans VS Code. Les moteurs et contributions des autres membres
ne sont pas vérifiés. Aucun résultat Gemini/Grok n'est inventé.

Pour comparer les modèles, conserver pour chaque vraie exécution : nom, moteur,
date, commit de départ, prompts, plans et OK, durée, erreurs, corrections manuelles,
résultats des tests, commit final et vidéo correspondante.

## Partie C — Construction et validation

L'interface principale charge `connected.js` et appelle l'API. Les données métier
sont enregistrées en base, indépendamment du navigateur. La connexion utilise un
JWT en cookie HttpOnly et une session serveur révocable. Les rôles proviennent
du compte en base ; `X-Role` est ignoré et le sélecteur de rôle est désactivé.

Parcours réalisés :

- Création d'un compte Alumni ; les comptes privilégiés sont créés par la CLI.
- Saisie et modification du profil personnel avec validation des champs.
- Consentement daté, retrait immédiat de l'annuaire après révocation.
- Unicité e-mail et matricule en base, examen humain explicite sans fusion automatique.
- Correction/rejet motivé ; validation, auteur et horodatage enregistrés.
- Annuaire professionnel filtré, sans e-mail, matricule ou commentaires privés.
- KPI agrégés calculés côté serveur ; actualisation après validation.
- Import CSV prévisualisé, validation serveur, bilan par ligne, sans consentement présumé.
- Export filtré réservé à l'Admin, neutralisation des formules de tableur et journalisation.
- Campagnes en brouillon ciblant les profils non confirmés depuis plus de 365 jours ;
  suivi des confirmations postérieures, sans prétendre envoyer de véritables e-mails.

## Vérifications effectuées

- 13 tests frontend, incluant les tests historiques du DOM de la démo locale.
- 10 tests API : identité, rôles, propriété des profils, workflow complet, révocation,
  expiration et déconnexion, import/export filtré et campagnes.
- ESLint, Ruff et compilation Vite réussis.
- Migration SQLite testée sur installation neuve et sur le schéma précédent 0001.
- Navigateur : connexion Alumni, profil lu depuis la base, connexion Service,
  examen d'unicité, validation, publication dans l'annuaire et KPI de la Direction.
- Les données et la validation restent présentes après redémarrage du backend.
- Le workflow GitHub Actions est fourni ; aucun résultat distant n'est annoncé
  sans exécution observable. Docker/PostgreSQL n'ont pas été exécutés localement.

Les captures `docs/screenshots/` montrent des données fictives du parcours connecté.

## Limites à connaître

Pas de SSO, d'e-mail de vérification, de récupération de mot de passe, de refresh
token ou d'envoi d'e-mails. Les comptes importés sont verrouillés en attente d'un
processus d'invitation non implémenté. Avant une ouverture publique du service,
configurer HTTPS/cookie sécurisé, clé stable, anti-abus et sauvegardes.

La couverture utilise les fiches recensées faute de référentiel institutionnel
des diplômés ciblés ; délais calendaires et fraîcheur à 365 jours.

## Vidéos et soumission

La vidéo `demo/ZiadHarrasse.mp4` est présente : 78 339 007 octets, sous 100 Mo.
Son contenu/audio n'a pas été revu ; elle doit être vérifiée ou refaite pour cette
version connectée. Les vidéos d'Ahmed Cherif et Dev sont absentes du dépôt inspecté.
Une vidéo et une véritable exécution du moteur attribué restent nécessaires par
étudiant. L'existence de ce code ne prouve pas ces exécutions.

Scénario : connexion Alumni → profil et consentement → déconnexion → connexion
Service → examen, correction ou validation → annuaire → connexion Direction et
KPI → connexion Admin, CSV et journal. Montrer les limites réelles de l'application.

Une personne du groupe doit encore déposer sur la plateforme pédagogique :

```text
MAJ GIT (MVP) : https://github.com/ziad4222/eigsi-suivi-alumni
```

La soumission pédagogique n'a pas été effectuée par Codex. Le rendu complet dépend
encore des vidéos, de la preuve des exécutions individuelles et du guide Word.
