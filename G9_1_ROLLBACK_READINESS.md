# G9.1 — Préparation au rollback

Avant capture : accès public fermé, écritures générales non ouvertes, release et
Alembic confirmés, archive non écrasable, destination externe vérifiée, opérateur
et fenêtre identifiés.

Ne jamais forcer FROZEN. Si le drain échoue, conserver DRAINING, collecter les
journaux sans secret et décider entre correction et reprise. Si la capture
échoue après le gel, conserver le répertoire incomplet pour analyse et ne
dégeler qu’après vérification de santé.

Après validation locale et externe seulement :

~~~bash
docker exec "$APP" python -m app.write_freeze unfreeze
docker exec "$APP" python -m app.write_freeze check --phase OPEN
~~~

Une restauration de production, un downgrade Alembic ou une restauration de
volume sont hors périmètre et exigent une autorisation distincte. Conserver
archive originale, sommes, snapshot restic, inventaires, réconciliation et
journaux.

