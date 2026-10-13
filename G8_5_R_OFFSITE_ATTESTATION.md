# G8.5-R — Attestation externe

## Statut : PASS — restauration de fichiers vérifiée

Attestation fournie par l’opérateur pour l’archive `20261012T235937Z` :

- Dépôt restic : `3ca53008`.
- Snapshot : `a4b07220`.
- `restic check --read-data` : PASS, aucune erreur; 3 snapshots et 6 packs lus.
- `restic restore --tag g8-predeploy` : PASS, 102 fichiers/dossiers restaurés.
- SHA-256 après restauration via `sha256sum -c manifests/SHA256SUMS` : PASS pour toutes les entrées.
- `COMPLETION.SHA256` : PASS.
- SHA-256 du manifeste : `041a3f62994f3839f1b35a4d758ac1f0ca645ac1e3bacd6a856340c172ff20a8`.
- Mot de passe restic : conservé sur Kubuntu, hors VPS, selon l’opérateur.

Cette preuve établit la récupérabilité et l’intégrité des fichiers restaurés depuis le snapshot restic. Elle ne constitue pas une preuve qu’une restauration complète et opérationnelle des services PostgreSQL et MinIO a été exécutée. Le rollback reste coordonné et doit restaurer PostgreSQL et MinIO ensemble dans une cible approuvée.
