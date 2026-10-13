# G8 — Démarrage applicatif

Statut : **NON EXÉCUTÉ**.

Le conteneur applicatif de production était absent avant l’opération et l’est resté. PostgreSQL et MinIO sont restés sains et inchangés. Aucun volume n’a été recréé et aucun service n’a été redémarré.

Contrôles réalisés sur la release `889fd5b018f038d6166d8ef0afa976426392fa79` :

- configuration Compose valide (`config --quiet`) ;
- `scripts/migrate.sh` présent ;
- migrations `0006_multilingual_participant_identity`, `0007_integrity_and_transcription_versions` et `0008_rate_limit_buckets` présentes ;
- startup applicatif vérifié statiquement : contrôle de révision, pas d’appel à `alembic upgrade` ;
- aucune image de release construite ou démarrée en production.

La readiness HTTP 200, les logs de démarrage et la confirmation d’absence de migration rejouée restent à exécuter après levée formelle du point d’arrêt sauvegarde.
