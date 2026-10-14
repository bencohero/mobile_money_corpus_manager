# F5A8 — intégrité des données restaurées

## PostgreSQL

- Révision `alembic_version` : `0005_workshop_attribution`.
- Comptages restaurés : users 21, participants 17, utterances 13, recordings 15, transcriptions 1, audit_logs 115.
- Contraintes primaires/foreign keys/uniques : 157.
- Foreign keys : 24.
- Orphelins participants↔recordings : 0.
- Orphelins utterances↔recordings : 0.
- Orphelins recordings↔transcriptions : 0.
- Enregistrements `VERIFIED` : 0.
- Enregistrements `TRANSCRIBED` : 1.
- `pg_restore --list` a lu une archive custom PostgreSQL 16.15 contenant 133 entrées TOC.

Les vérifications métier ont été exécutées en lecture seule sur la base restaurée.

## MinIO

- Bucket temporaire : `f5a8-corpus`.
- Objets attendus : 30.
- Objets restaurés : 30.
- Taille attendue/restaurée : 5 289 708 / 5 289 708 octets.
- Objets manquants : 0.
- Objets supplémentaires : 0.
- Écarts de taille : 0.
- Références PostgreSQL vers objets restaurés : 30/30.

Les empreintes SHA-256 de l’archive source ont été validées. Les tailles de chaque objet restauré correspondent à celles de l’archive; les références PostgreSQL correspondent exactement à l’inventaire MinIO restauré.

## WAV

15 fichiers WAV restaurés ont été contrôlés avec `ffprobe` : 15 lisibles, 0 invalide. Aucun contenu audio ou identifiant personnel n’est reproduit dans ce rapport.

## Limites

Cette validation démontre la restauration dans PostgreSQL 16 et MinIO isolés. Elle ne constitue pas une restauration en production et ne valide pas une remise en service applicative complète. Aucun service de production n’a été utilisé comme cible.
