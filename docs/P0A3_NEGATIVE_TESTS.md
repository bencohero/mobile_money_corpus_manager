# P0-A.3 Tests negatifs

La suite ajoute `tests/test_p0a3_negative.py`. Elle couvre la matrice HTTP des routes sensibles, IDOR audio/transcription, session absente/invalide, CSRF, fichiers vides/non audio/aléatoires/durée trop courte, concurrence sur une prise, compensation partielle, libération du sémaphore et divergences de taille/checksum/état dans la réconciliation.

Commande exécutée:
`docker compose -f docker-compose.test.yml run --rm --entrypoint pytest test -vv -ra`

17 tests ont été collectés et exécutés: 17 réussis, 0 échec, 0 ignoré, 3 avertissements. Les pannes réelles MinIO/DB, les timeouts ffmpeg/ffprobe, les limites de taille exactes, les propriétés WAV incorrectes, et toutes les anomalies artificielles demandées ne sont pas encore couverts; ils restent bloquants.
