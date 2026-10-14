# G6.1 — Revalidation sécurité

## Environnement et commandes

Scans exécutés dans des conteneurs éphémères avec le dépôt monté en lecture seule et un `/tmp` temporaire :

```text
python:3.12-slim
pip check
pip-audit 2.10.1 -r requirements.txt
bandit 1.9.4 -r app
zricethezav/gitleaks:v8.28.0 detect --no-git --source=/repo
git diff --binary 32edc87..31070e2 | gitleaks detect --pipe
```

Versions observées : Python 3.12.15, pip 26.2.1, Bandit 1.9.4, pip-audit 2.10.1, Gitleaks v8.28.0.

## Résultats

- `pip check` : `No broken requirements found`.
- `pip-audit` : `No known vulnerabilities found`.
- Gitleaks dépôt complet : aucune fuite détectée, environ 77,16 MB analysés.
- Gitleaks diff de release : aucune fuite détectée, environ 25,40 MB analysés.
- Recherche complémentaire de clés privées, tokens AWS/GitHub/Slack : aucune occurrence.
- Aucun secret n’est copié dans ce rapport.

## Bandit

Bandit ne remonte aucune sévérité haute. Les quatre alertes sont connues et acceptées formellement pour cette promotion :

| ID | Sévérité | Localisation | Impact / justification | Disposition |
|---|---|---|---|---|
| B404 | Low | `app/audio_processing.py:4` | Import `subprocess`; surface de risque générale, pas une vulnérabilité en soi | Accepté ; commandes ffmpeg contrôlées par le code |
| B603 | Low | `app/audio_processing.py:23` | Appel subprocess potentiellement non sûr | Accepté ; arguments construits par l’application, pas d’entrée shell libre |
| B404 | Low | `app/main.py:1` | Import `subprocess` pour le traitement audio | Accepté ; même justification, aucun shell arbitraire |
| B108 | Medium | `app/write_freeze.py:25` | Chemin par défaut sous `/tmp` pour l’état du gel | Accepté avec réserve ; chemin configurable par `WRITE_FREEZE_STATE_FILE`, permissions et conteneur contrôlés |

Aucune alerte critique ou haute n’est présente. B108 doit rester une dette technique : préférer à terme un répertoire runtime créé avec permissions explicites.

## Compose et dépendances critiques

Les configurations G5/test et Compose avec variables synthétiques sont valides. La configuration de production dépend volontairement d’un `.env` externe absent du dépôt ; aucun fichier secret n’a été créé. Les tests de migration et de garde refusent toujours toute migration implicite au démarrage.
