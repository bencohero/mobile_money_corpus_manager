# G8.6-R — Précontrôles actualisés

Date : 2026-10-13 UTC

| Contrôle | Résultat |
|---|---|
| Release | PASS — `mobile_money_corpus_manager_g8_5_r:8f688e8d312b2f0afb30f8a2766a6f8f25e5e5d6` |
| Alembic | PASS — `0008_rate_limit_buckets (head)` |
| `/ready`, `/health` | PASS — HTTP 200 avec Host approuvé |
| Accès public | PASS — app backend-only, aucun port publié ; Host non approuvé 400 |
| Sauvegarde | PASS — snapshot restic `a4b07220`, archive `20261012T235937Z`, intégrité attestée |
| Écritures concurrentes | PASS — `active_writes=0`, aucune écriture concurrente observée |
| `benco` | PASS — actif ADMIN ; login 303, `/users` 200, logout 303 |

Inventaire avant : users 21, participants 17, workshops 5, codes 6,
utterances 13, recordings 15, submissions 15, counters 15,
transcriptions 1, history 1, audits 119, buckets 1 ; MinIO 30 objets /
5 289 708 octets.

Tous les précontrôles sont passants. L’autorisation reste limitée aux données
de recette et ne constitue pas une ouverture publique.
