# G3 — Rapport d’intégration contrôlée

## Candidate

- Branche : `g3-candidate`
- Base : `main@32edc87`
- Source examinée : `remediation-a-stabilisation-securite@b672697`
- Commit d’intégration applicative : `7d5c180` — `Integrate validated remediation candidate`.
- Un commit documentaire G3 suit ce commit et contient les cinq livrables de ce ticket.
- Worktree : `/home/sangouman/apps/mobile_money_corpus_manager_g3_candidate`

La branche a été créée par `git worktree add -b g3-candidate ... main`. Le worktree source,
la branche source et `main` ont été conservés. Aucun merge, cherry-pick ou déploiement n’a été
effectué.

## Méthode

Le diff `main → source` a été revu puis appliqué sélectivement sur la branche candidate. Les
changements applicatifs, migrations, modèles, services, tests et configurations de validation
ont été intégrés. Les scripts et preuves F5A6–F5A8 de `main` ont été exclus de l’intégration
afin de conserver la version validée.

Le `Dockerfile` candidat nécessitait `.env.dev.example`; ce fichier d’exemple non secret a été
ajouté en conservant `.env.dev` de `main`. Les fichiers générés `__pycache__` ont été exclus du
commit.

## Périmètre intégré

Le commit candidate couvre les fonctionnalités multilingues, sécurité/authentification,
transcription et historique, audio, export, pagination, rate limiting, audit, write-freeze,
migrations `0006`–`0008`, modèles ORM, tests et configurations isolées.

Les scripts de sauvegarde protégés sont inchangés par rapport à `main` et aucun secret réel
n’est présent dans les rapports G3.
