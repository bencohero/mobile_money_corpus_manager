# G8.6-S3 — Prévol de rotation administrateur

Date : 2026-10-13 UTC. Rotation non exécutée.

## Contrôles

| Contrôle | Résultat |
|---|---|
| Image / release | PASS — `mobile_money_corpus_manager_g8_5_r:8f688e8d312b2f0afb30f8a2766a6f8f25e5e5d6` |
| Alembic | PASS — `0008_rate_limit_buckets (head)` |
| `/ready`, `/health` | PASS — HTTP 200 |
| Script | PASS — syntaxe valide ; SHA-256 `f541ef23b50ec7e0a140a9270aed219742f8e30884af92e8ad30afa15f7771ed` |
| Provenance runtime | PASS — SHA du script identique dans le conteneur exact |
| Dry-run runtime | PASS — aucune écriture annoncée |
| Tests négatifs | PASS — cible incorrecte et confirmation absente refusées |
| Sauvegarde | PASS — archive complète et `sha256sum -c` OK |
| benco | PASS — compte actif et rôle `ADMIN` |
| Autres ADMIN | PASS — `admin` et `laurent` actifs, inchangés |
| Accès public | PASS — aucun port publié, réseau backend uniquement |
| Gel métier | PASS — `active_writes=0`; aucune écriture métier envoyée |

Le premier dry-run lancé avec l'interpréteur hôte a échoué faute de SQLAlchemy
installé. Il n'a pas touché la base. Le dry-run et les tests négatifs ont ensuite
été exécutés avec succès dans le conteneur runtime exact.

## Manifeste avant étape 2

`users=21`, `participants=17`, `workshops=5`, `workshop_codes=6`,
`recordings=15`, `recording_submissions=15`, `recording_take_counters=15`,
`transcriptions=1`, `transcription_history=1`, `audit_logs=116`,
`rate_limit_buckets=1`.

MinIO : 30 objets, 5 289 708 octets. Les IDs ADMIN sont 1 (`admin`), 3
(`benco`) et 13 (`laurent`).

