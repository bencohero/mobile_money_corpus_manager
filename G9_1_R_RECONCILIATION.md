# G9.1-R — Réconciliation

Aucune réconciliation réelle n’a été exécutée.

## Contrôles requis

Comparer les inventaires source et cible :

- révision Alembic 0008_rate_limit_buckets ;
- compteurs users, participants, workshops, workshop_codes, utterances,
  recordings, submissions, recording_take_counters, transcriptions,
  transcription_history et audit_logs ;
- chemins MinIO, nombre d’objets, tailles et ETag ;
- SHA-256 des fichiers exportés ;
- enregistrements, statuts, tailles et références audio.

Dans l’application isolée :

~~~bash
docker exec g91-r-restore-app-1 python -m alembic current
curl --fail --silent http://127.0.0.1:PORT/ready
curl --fail --silent http://127.0.0.1:PORT/health
docker exec g91-r-restore-app-1 python scripts/reconcile.py --json
~~~

Le résultat attendu est [] avec code 0. Toute absence, divergence d’empreinte,
objet orphelin, permission, timeout ou connexion vers production est bloquant.

