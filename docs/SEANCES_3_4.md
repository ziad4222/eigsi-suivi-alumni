# Séances 3 et 4 : conduite du travail et état du rendu

État vérifié le 22 octobre 2026. Ce document complète l'énoncé fourni ; il ne
remplace pas le guide Word pédagogique, qui n'a pas été fourni et dont le lien
n'a pas pu être lu depuis l'environnement de travail.

## Partie A — Analyse et préparation

1. Lire le cadrage et le rapport S2 à la racine.
2. Installer Git, Node 22, pnpm, Python 3.12 ; suivre le README.
3. Exécuter l'interface et l'API dans deux terminaux.
4. Exécuter les contrôles de qualité avant de demander une évolution.
5. Relever les écarts : interface JavaScript au lieu de React/TypeScript,
   données locales au lieu d'un branchement complet, rôle de démonstration au lieu
   d'une authentification JWT. Ces points empêchent de certifier la conformité
   technique totale au rapport S2.

## Partie B — Instructions et agents

Les règles communes sont dans `.github/copilot-instructions.md`.
Dans VS Code, ouvrir le dépôt et utiliser Copilot en mode Agent avec le moteur
attribué par l'enseignant. La configuration des moteurs et les accès API doivent
être effectués dans l'environnement de l'étudiant ; aucune clé ne va dans Git.

Premier prompt :

> Lis les rapports de conception, le README et les instructions du workspace.
> Identifie les critères Must manquants et propose un PLAN avec les fichiers à
> modifier et les tests à exécuter. Ne modifie aucun fichier avant mon « OK ».

Ces prompts sont des propositions pour ce dépôt, pas une transcription du Word.

## Partie C — Construction et validation

Pour chaque évolution : plan, réponse OK, implémentation, vérification, bilan.

Prompt de construction :

> Sur la base de la conception validée, traite une user story à la fois. Propose
> d'abord le plan. Après mon OK, implémente et exécute les tests pertinents.
> Montre les résultats et les limites sans annoncer des tests non exécutés.

Prompt de revue :

> Vérifie le parcours alumni → consentement → correction/validation → annuaire
> → KPI, puis l'import/export CSV et le rechargement. Vérifie les droits côté
> serveur et distingue les simulations locales. Propose un plan de correction.

## Corrections et vérifications réalisées dans Codex

- Actions des boutons rendues accessibles depuis le module JavaScript.
- Blocage d'une publication sans consentement ou avec doublon non examiné.
- Examen explicite du doublon, motifs de correction/rejet et dates conservés.
- Contrôle de l'unicité lors de la modification d'une fiche.
- Échappement des valeurs utilisateur lors du rendu HTML.
- KPI recalculés, fraîcheur glissante, médiane issue des décisions datées.
- CSV : champs cités et multilignes, prévisualisation, erreurs par ligne,
  unicité et absence de consentement présumé.
- Export nominatif restreint dans la démo ; il reste nécessaire de faire
  appliquer les droits par une véritable authentification serveur.
- Tests frontend exécutant les fonctions et le DOM, tests API existants,
  lint frontend/backend et compilation frontend.
- Workflow GitHub Actions ajouté ; son résultat distant est à distinguer des
  contrôles locaux.

Le taux de couverture affiché utilise les fiches recensées de la démo comme
dénominateur. Le vrai référentiel des diplômés ciblés n'est pas disponible.
Le délai affiché est en jours calendaires, faute de calendrier institutionnel.

## Points restant nécessaires avant de déclarer le devoir terminé

| Point | État |
| --- | --- |
| Dépôt public | Vérifié par l'API GitHub le 22/10/2026 |
| Rapports de conception | Présents et lus |
| MVP local | Parcours corrigés ; données toujours dans le navigateur |
| API et base | Tests existants passent ; intégration complète à faire |
| JWT et RBAC réels | Non implémentés ; X-Role est déclaratif |
| Guide pédagogique Word | À fournir pour contrôler ses instructions exactes |
| Moteur retenu pour Ziad | Copilot Auto / Standard ; exécution à documenter dans VS Code |
| Exécutions individuelles Gemini/Auto/Grok | Non vérifiées ; aucune preuve fabriquée |
| Vidéo ZiadHarrasse.mp4 | Présente, 78 339 007 octets ; contenu/audio à revoir |
| Vidéos des autres membres | Absentes du dépôt inspecté ; Ahmed Cherif et Dev, contributions non vérifiées |
| Comparatif des moteurs | À renseigner à partir des véritables exécutions |
| Soumission sur la plateforme | Non effectuée |

## Comparatif à remplir pendant les vraies exécutions

Pour chaque étudiant : nom, moteur, date, commit de départ, user stories,
prompt, plan et OK, durée, erreurs, interventions manuelles, résultats des tests,
limites observées, commit final et fichier vidéo. Aucune de ces mesures ne doit
être déduite de l'existence du code ou de la vidéo.

## Démonstration et soumission

Suivre le scénario de `demo/README.md`, montrer les fonctionnalités réellement
présentes et expliquer les limites. Refaire la vidéo si elle ne correspond plus
à l'état final. Chaque étudiant doit filmer son MVP et préciser son moteur.

Après les vérifications, une personne du groupe soumet sur la plateforme :

```text
MAJ GIT (MVP) : https://github.com/ziad4222/eigsi-suivi-alumni
```
