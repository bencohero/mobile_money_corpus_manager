# G8.5 — Intégrité des données

## Statut : PASS local / BLOCKED opérationnel

Contrôles lecture seule réalisés le 2026-10-13 :

- Archive : `/home/sangouman/mobile-money-corpus-backups/20261012T235937Z`.
- SHA-256 de `manifests/SHA256SUMS` : `041a3f62994f3839f1b35a4d758ac1f0ca645ac1e3bacd6a856340c172ff20a8` (conforme).
- Vérification `sha256sum -c manifests/SHA256SUMS` : OK.
- Révision archive et base courante : `0005_workshop_attribution`.
- Comptages courants / archive : users 21; participants 17; utterances 13; recordings 15; transcriptions 1; audit_logs 116.
- Objets archive capturés / référencés : 30 / 30.
- `COMPLETE` présent; date de complétion archive : `2026-10-12T23:59:42Z`.
- Tables/colonnes/index attendus des révisions 0006–0008 : absents du schéma courant, cohérent avec l’état initial.

La cohérence des données historiques est donc préservée dans les contrôles locaux effectués. Une preuve indépendante de cohérence live MinIO et de restauration depuis le snapshot restic `a4b07220` reste manquante; elle est requise avant toute mutation de schéma. Aucun historique n’a été modifié.
