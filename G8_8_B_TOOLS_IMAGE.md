# G8.8-B — Image d’outillage

`Dockerfile.tools` utilise désormais :

- PostgreSQL 16 Alpine : `sha256:cf78e76683b9ca8c5733cbbdce6c9262b45b6767934dd0a95e671f9a0fc20685` ;
- MinIO client : `quay.io/minio/aistor/mc@sha256:23511e340cbabf07e6a8b53f9c434975708f22f3c047d6beeddc17bf1a5aed88` ;
- `python3`, `pg_restore`, `mc`, `sha256sum`, Bash et certificats CA.

L’URL flottante `https://dl.min.io/client/mc/release/linux-amd64/mc` a été
supprimée. L’image locale construite est
`mobile-money-corpus-tools:g8-8-b-local@sha256:6f33d7802d969e86ba855696862e981d78305523e402a814b1c04ffbac64654f`.

Vérifications de build : Python 3.14.8, `pg_restore` 16.15, mc
`RELEASE.2026-09-19T15-24-59Z`, GNU coreutils/sha256sum 9.11. Les scripts de
sauvegarde et restauration sont syntaxiquement valides et le contrat passe
dans l’image avec un réseau Docker désactivé.
