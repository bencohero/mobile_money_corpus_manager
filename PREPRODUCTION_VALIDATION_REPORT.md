# Rapport de validation préproduction — Lot F

Date de recette : 2026-10-11  
Périmètre : dépôt local, données synthétiques du stack Docker isolé.  
Production : aucune connexion, migration, sauvegarde ou écriture exécutée.

## Décision

**BLOQUÉ — pas d’autorisation de déploiement.**

Le cœur applicatif est validé dans le stack isolé, mais la release ne peut pas être
autorisée tant que les contrôles manuels VPS, Android, HTTPS/certificats et les scanners
de sécurité ne sont pas rejoués et signés. Ce statut n’entraîne aucune migration ni aucun
déploiement automatique.

## Tests réussis

- État Git initial propre hors artefacts générés ; scripts `backup.sh`, `restore.sh`,
  `reconcile.py` et les fichiers Compose sont versionnés.
- `docker compose config --quiet` production et test : réussi.
- Images construites : runtime, `app-test`, `test` et `tools`.
- Stack F isolé démarré avec `docker-compose.test.yml` + `docker-compose.preprod.yml`.
  Réseau : `mobile-money-corpus-f-lot`; volumes : `mobile-money-corpus-f-lot-*`.
- Suite Docker : **158 passed, 1 skipped, 8 warnings, 141,17 s**.
- `alembic current` : `0008_rate_limit_buckets (head)`.
- Backup synthétique PostgreSQL + MinIO : 8 objets audio, manifeste SHA-256 créé.
- Restore synthétique vers PostgreSQL/MinIO dédiés : réussi.
- Réconciliation après restore : `[]`.
- Comptages source/restauré identiques : langues 4, participants 4, ateliers 5,
  utterances 13, recordings 4, transcriptions 3.
- Tests Node : tous les fichiers `.test.cjs` passés.
- Compilation Python et contrôle de syntaxe : réussis.

## Tests échoués ou non concluants

- Le premier démarrage du Compose historique a échoué sur un ancien volume PostgreSQL
  corrompu et sur des noms de ressources partagés avec d’autres lots. La surcharge
  `docker-compose.preprod.yml` corrige l’isolation sans arrêter ces ressources.
- `bash scripts/security_checks.sh` n’a pas terminé : Bandit est absent de l’hôte.
  Par conséquent Bandit, pip-audit et Gitleaks ne sont pas une preuve Lot F.

## Contrôles non réalisés

- Sauvegarde de données réelles : non réalisée, aucune autorisation n’ayant été fournie.
- Migration/restauration sur une copie historique réelle : non réalisée.
- Certificat HTTPS, ACME/Traefik, TrustedHost et en-têtes proxy sur VPS : non réalisés.
- Parcours navigateur physique ordinateur et Chrome Android : non réalisés.
- Test multi-workers du rate limiting, exposition réseau externe PostgreSQL/MinIO et
  tests de charge VPS : non réalisés.
- Scanners sécurité dans un environnement outillé : à rejouer.

## Risques résiduels et décisions humaines

1. Un responsable données doit autoriser et superviser un backup réel hors volumes de
   production, puis valider les écarts historiques et objets MinIO orphelins.
2. Un responsable exploitation doit valider la fenêtre estimée de 30–60 minutes,
   les certificats, le DNS, la configuration Traefik et le plan de retour arrière.
3. Un responsable sécurité doit signer les résultats Bandit, pip-audit et Gitleaks
   rejoués sur l’artefact candidat.
4. Un responsable produit doit signer les parcours desktop/Android, transcription,
   conflits, exports et permissions.

## Durées et artefacts

- Build images Docker : réussi ; durée non instrumentée dans cette recette.
- Suite pytest Docker : 141,17 s.
- Backup MinIO synthétique : moins d’une seconde d’exécution de transfert, 144,23 KiB.
- Restore MinIO synthétique : moins d’une seconde d’exécution de transfert, 144,23 KiB.
- Durée réelle de migration/restauration historique : non mesurée.
- Les services et volumes F ont été arrêtés et supprimés après la recette ; les ressources
  des autres lots n’ont pas été arrêtées.

## Référence de release

La version candidate est le commit de référence créé avec ce rapport, la checklist et
la surcharge Compose F. Le SHA exact est affiché par `git rev-parse HEAD` après commit
et doit être reporté dans la demande d’autorisation de déploiement. Aucun tag ni push
automatique n’est effectué.
