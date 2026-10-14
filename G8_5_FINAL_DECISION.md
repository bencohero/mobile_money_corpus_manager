# G8.5 — Décision finale

## `BLOCKED`

La migration contrôlée de production ne peut pas commencer.

### Motifs bloquants

- La release autorisée `8f688e8d312b2f0afb30f8a2766a6f8f25e5e5d6` est disponible, mais le checkout réellement contrôlé est `b672697a34196841cd5fd9714520166b6edb345b` et l’image applicative active ne peut pas être reliée à la release autorisée.
- L’attestation externe coordonnée PostgreSQL/MinIO du snapshot restic `a4b07220` n’est pas fournie : l’attestation locale est `PENDING`.

### État conservé

- Base à `0005_workshop_attribution`.
- Archive locale `20261012T235937Z` intègre et manifeste conforme.
- Comptages historiques inchangés dans les contrôles locaux.
- Volumes PostgreSQL et MinIO conservés; aucune suppression/recréation.
- Aucune migration, aucun démarrage applicatif, aucun push Git, aucune ouverture publique et aucun dégel des écritures.

### Conditions de reprise

Obtenir une attestation externe vérifiable correspondant exactement à l’archive et au SHA du manifeste, incluant `restic check`, test de restauration isolée et conservation hors VPS de la clé. Revenir ensuite sur la release autorisée sans nettoyer le checkout, refaire les contrôles pré-migration et seulement alors exécuter explicitement `ALEMBIC_TARGET=0008_rate_limit_buckets scripts/migrate.sh`.
