# F.5A.1 — Checklist d’autorisation

## Décision actuelle

**BLOQUÉ.** La revue ne peut pas autoriser la capture tant qu’un gel/drain vérifiable n’est pas disponible.

## Cibles

- [ ] Le changement référence exactement le projet Compose `mobile_money_corpus_manager_v0_1`.
- [ ] Le conteneur PostgreSQL est exactement `mobile_money_corpus_manager_v0_1-db-1`, base `corpus`, PostgreSQL 16.
- [ ] Le conteneur MinIO est exactement `mobile_money_corpus_manager_v0_1-minio-1`, bucket `mobile-money-corpus`.
- [ ] Les digests complets approuvés correspondent aux contrôles du jour.
- [ ] Le PostgreSQL 18 publié sur `5432` est explicitement exclu.

## Préflight sécurité

- [ ] Aucun backup/restore ou copie concurrente n’est actif.
- [ ] Les trois conteneurs cibles sont actifs et sains.
- [ ] Les labels Compose, réseaux et volumes sont conformes.
- [ ] `/var/backups/mobile-money-corpus/` est la destination approuvée, hors dépôt et hors volumes Docker.
- [ ] La destination n’est pas créée avant l’autorisation ; le propriétaire prévu est un compte opérateur dédié, mode `0700`.
- [ ] L’espace libre couvre dump PostgreSQL + objets MinIO + 20% + marge opérationnelle.
- [ ] Le nom UTC du run est nouveau ; aucune réécriture n’est possible.
- [ ] Le client MinIO et son digest sont approuvés ; endpoint et bucket sont contrôlés.

## Cohérence

- [ ] Un mécanisme de maintenance bloque les nouvelles écritures.
- [ ] Le drain est prouvé : requêtes en vol, uploads, transcriptions, validations et traitements asynchrones à zéro.
- [ ] Les comptages pré-capture sont conservés sans PII.
- [ ] Le dump PostgreSQL est lisible par `pg_restore --list`.
- [ ] Le nombre d’objets source et copiés correspond.
- [ ] Les SHA-256 sont calculés puis vérifiés avant publication atomique.
- [ ] La réconciliation post-capture est exécutée et réussit.

## Exploitation

- [ ] La reprise des écritures est explicitement autorisée par l’opérateur.
- [ ] Les services sont sains après reprise.
- [ ] Les journaux ne contiennent ni secrets, ni transcriptions, ni identifiants personnels, ni noms d’objets.
- [ ] Toute archive partielle reste marquée `INCOMPLETE` et n’est pas présentée comme sauvegarde valide.
- [ ] Aucun `restore.sh`, Alembic, arrêt/redémarrage non prévu, modification Traefik, volume ou pare-feu n’est exécuté.

## Signatures attendues

| Rôle | Nom | Date/heure UTC | Décision |
|---|---|---|---|
| Opérateur VPS | à renseigner | à renseigner | à renseigner |
| Responsable données | à renseigner | à renseigner | à renseigner |
| Relecteur technique | à renseigner | à renseigner | à renseigner |

Une case « cohérence » non cochée signifie **BLOQUÉ**, même si PostgreSQL, MinIO et les checksums répondent correctement séparément.
