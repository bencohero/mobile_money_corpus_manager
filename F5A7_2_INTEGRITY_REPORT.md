# F5A7.2 — rapport d’intégrité

## État

Capture finale vérifiée : `/home/sangouman/mobile-money-corpus-backups/20261011T133947Z`. L’archive incomplète de la première tentative reste conservée séparément.

## Contrôles réalisés

- Cibles Docker, images, labels, réseaux et volumes : conformes.
- PostgreSQL 16.15 et MinIO : sains.
- Application : arrêtée.
- Alembic : `0005_workshop_attribution`.
- Sessions PostgreSQL concurrentes : zéro observée.
- Source MinIO : 30 objets.
- Références PostgreSQL `raw_object`/`wav_object` : 30.
- Écart préalable détecté : aucun par comptage et listing source.
- Client MinIO digesté : vérifié et fonctionnel en lecture seule.
- Tests synthétiques : 10 réussis.

Dump créé : 60 629 octets, SHA-256 `c03d2e8a4072fe572b2400cb2fb990d59c8926b5f921defc234cf5d255982d21`.

## Vérifications finales

- `manifests/SHA256SUMS` : toutes les entrées `OK`.
- `COMPLETION.SHA256` : conforme à `COMPLETE`.
- `pg_restore --list` : lisible ; archive custom PostgreSQL 16.15 ; 133 entrées TOC.
- Révision Alembic : `0005_workshop_attribution`.
- Comptages : users 21, participants 17, utterances 13, recordings 15, transcriptions 1, audit_logs 115.
- MinIO source/destination : 30 / 30 objets.
- Taille source/destination : 5 289 708 / 5 289 708 octets.
- Objets manquants, supplémentaires ou tailles divergentes : 0 / 0 / 0.
- Rapport de cohérence : `coherent=true`.
- Recherche de motifs de secrets dans l’archive : aucun motif trouvé.

## Contrôles non exécutés

La première tentative a échoué avec EOF dans `pg_restore --list`; le défaut stdin a été corrigé avant la nouvelle tentative autorisée. L’archive finale a ensuite passé tous les contrôles ci-dessus.

Cette validation ne constitue pas une restauration réelle de l’archive et ne permet pas de la qualifier de restaurée en production. La restauration doit rester isolée.
