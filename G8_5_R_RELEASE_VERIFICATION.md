# G8.5-R — Vérification de la release

## Statut : PASS

- Worktree utilisé : `/tmp/g8-2-release`.
- HEAD exact : `8f688e8d312b2f0afb30f8a2766a6f8f25e5e5d6`.
- Worktree propre : PASS (`git status --porcelain` vide).
- Migrations présentes : `0005_workshop_attribution`, `0006_multilingual_participant_identity`, `0007_integrity_and_transcription_versions`, `0008_rate_limit_buckets`.
- Script présent et exécutable : `scripts/migrate.sh`.
- Interface confirmée : `ALEMBIC_TARGET=0008_rate_limit_buckets scripts/migrate.sh`.
- Aucun changement n’a été effectué dans le checkout utilisateur `/home/sangouman/apps/mobile_money_corpus_manager_v0_1`, resté sur `b672697a34196841cd5fd9714520166b6edb345b`.

La migration et la construction applicative de cette reprise utilisent exclusivement le worktree de release.
