# G8.6 — Précheck fonctionnel en production

Date du contrôle : 2026-10-13 UTC. Accès public maintenu fermé. Aucun push Git,
aucun redémarrage, aucune suppression de volume et aucun rollback n'ont été
effectués.

## Préconditions observées

| Élément | Preuve | Résultat |
|---|---|---|
| Image applicative | `mobile_money_corpus_manager_g8_5_r:8f688e8d312b2f0afb30f8a2766a6f8f25e5e5d6` | PASS |
| Label de release | `org.opencontainers.image.revision=8f688e8d312b2f0afb30f8a2766a6f8f25e5e5d6` | PASS |
| Alembic | `0008_rate_limit_buckets (head)` dans le conteneur applicatif | PASS |
| `/ready`, `/health` | HTTP 200 avec `Host: corpus-moore.bencoherolab.com` | PASS |
| PostgreSQL | conteneur existant, réseau backend, révision 0008 | PASS |
| MinIO | conteneur existant, bucket accessible | PASS |
| Archive pré-migration | `20261012T235937Z`, déjà attestée par G8.5-R | PASS documentaire |
| Snapshot restic | `a4b07220`, déjà attesté par G8.5-R | PASS documentaire |
| Accès public | l'app n'a aucun port publié et n'est pas attachée au réseau frontend/Traefik | PASS |
| Gel des écritures | exigence opérationnelle maintenue ; aucune écriture métier envoyée | PASS |

Le checkout courant est `b672697a34196841cd5fd9714520166b6edb345b`, différent de
la release exécutée. La correspondance de release est donc établie par l'image,
son label et les rapports G8.5-R, pas par le checkout utilisateur.

## État avant/après les contrôles

Les comptages observés après les contrôles sont : `users=21`,
`participants=17`, `utterances=13`, `recordings=15`, `transcriptions=1`,
`audit_logs=116`, `recording_submissions=15`, `recording_take_counters=15`.
MinIO contient 30 objets pour 5 289 708 octets.

Le middleware de gel présent dans l'image rapporte techniquement `phase=OPEN`,
mais la consigne opérationnelle de gel a été respectée : aucune requête de
création, upload, transcription, vérification, export ou suppression valide n'a
été envoyée.

## Effet de test identifié

`GET /api/auth/workshop-language?code=bad` est un endpoint de lecture fonctionnelle
qui appelle néanmoins le rate limiter persistant. Il a créé ou incrémenté un
seul bucket : `scope=workshop-language`, `event_count=1`, clé hachée
`d7bf42ae…575939f`, expiration `2026-10-13 00:45:37.626559 UTC`.
Cette trace technique est conservée ; aucun nettoyage destructif n'est tenté.

