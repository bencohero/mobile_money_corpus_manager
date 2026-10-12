# G3 — Rapport de validation

## Migration et données

Sur le clone G3 restauré depuis F5A7.2 :

| Étape | Révision | Participants | Enregistrements | Transcriptions |
|---|---|---:|---:|---:|
| restauration | `0005_workshop_attribution` | 17 | 15 | 1 |
| migration candidate | `0008_rate_limit_buckets (head)` | 17 | 15 | 1 |

Après migration : 1 entrée `transcription_history` baseline et 0 bucket initial. La
réconciliation PostgreSQL/MinIO retourne `[]`.

## Application

- Suite complète : **158 passed, 1 skipped, 8 warnings**.
- Tests HTTP, CSRF, IDOR, authentification et autorisations : PASS.
- Parcours participant/multilingue : PASS.
- Transcription, vérification, historique et audio : PASS.
- MinIO, export, audio et réconciliation : PASS.
- Concurrence et limitation de débit : PASS.
- `pip check` : `No broken requirements found`.
- `pip-audit -r requirements.txt` : `No known vulnerabilities found`.
- `docker compose ... config --quiet` : PASS.
- `bash -n scripts/*.sh` : PASS.
- `python3 -m compileall -q app migrations scripts` : PASS.
- `git diff --check` : PASS sur l’état final.

Le test ignoré est `test_dev_environment`, car le CLI Docker n’est pas installé dans le
conteneur de test; la configuration Compose a été validée depuis l’hôte. Les warnings sont
des dépréciations Python/Starlette non bloquantes.

