# G9-R3 — Résultats tests

Environnement Compose indépendant: réseau `g9r3-test-network` et volumes `g9r3-test-*`. Les volumes historiques `p0a2-*` n’ont pas été supprimés ni utilisés.

Migration appliquée explicitement sur la base neuve avant démarrage (`alembic upgrade head`); aucune migration implicite.

Suite complète: `162 passed, 1 skipped, 8 warnings` en 156,61 s.

Couverture: health/readiness, rôles, CSRF, sessions, inscription participant, enregistrement audio, plusieurs prises par phrase, transcription, validation, export, réconciliation, limites de débit et rejets d’entrées invalides.
