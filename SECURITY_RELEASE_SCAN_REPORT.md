# Security release scan — F.1

Date : 2026-10-11  
Release : `cb87475513721fc5816272ee41beaff3b9b13f8a`  
Environnement : conteneurs Docker éphémères, dépôt monté uniquement pour les rapports JSON ; aucune donnée de production.

## Commandes

```bash
docker run --rm -v "$PWD":/src -w /src python:3.12-slim \
  sh -c 'python -m pip install --no-cache-dir -q -r requirements-security.txt && \
  bandit -r app -f json -o security-reports-f1/bandit.json && \
  pip-audit -r requirements.txt -f json -o security-reports-f1/pip-audit.json'

docker run --rm -v "$PWD":/repo -w /repo zricethezav/gitleaks:v8.24.3 \
  detect --no-banner --redact --config=/repo/.gitleaks.toml \
  --report-format json --report-path=/repo/security-reports-f1/gitleaks.json --source=/repo
```

Versions : Bandit `1.8.6`, pip-audit `2.9.0`, Gitleaks `v8.24.3`, Python `3.12-slim`.
Les sorties JSON expurgées sont archivées dans `security-reports-f1/`.

## Résultats

| Scanner | Résultat | Détail |
|---|---|---|
| Bandit | Exécuté, réserve LOW | 3 LOW, 0 MEDIUM, 0 HIGH ; B404/B603 sur les appels subprocess FFmpeg |
| pip-audit | PASS | Aucune vulnérabilité connue, aucune correction proposée |
| Gitleaks | PASS | 12 commits analysés, aucun leak détecté |

L’exception `.gitleaks.toml` est limitée à `graphify-out/cache/stat-index.json`, qui
contient des empreintes SHA-256 générées et non des secrets. Gitleaks a terminé avec
le code 0 après application de cette exception. Aucun secret n’est présent dans les
rapports archivés.

## Décision sécurité

Les trois scanners obligatoires ont été exécutés. La réserve Bandit LOW doit être
acceptée par le responsable sécurité ou traitée avant un GO ; aucune vulnérabilité
HIGH/MEDIUM n’a été identifiée.
