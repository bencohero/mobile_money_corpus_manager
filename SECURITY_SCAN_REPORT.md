# Rapport SAST/SCA

Les outils prévus sont `bandit`, `pip-audit` et `gitleaks`, avec versions Python figées
dans `requirements-security.txt`. `scripts/security_scan.sh` échoue avec le code 2 si un
outil manque : une absence n’est pas comptée comme succès.

## Résultats de cette livraison

| Outil | Exécution | Résultat | Suite |
|---|---|---|---|
| Bandit 1.8.6 | exécuté après E.2 en conteneur Python 3.12 | 3 alertes LOW, liées à `subprocess` | appels FFmpeg bornés, `shell=False`, liste d’arguments et tests de seam |
| pip-audit 2.9.0 | exécuté sur `requirements.txt` après E.2 | aucune vulnérabilité connue | `python-jose` remplacé par `PyJWT==2.15.1`; `ecdsa` n’est plus dans l’arbre |
| Gitleaks v8.24.3 | scan brut historique puis scan release avec `.gitleaks.toml` | 2 détections brutes, 0 après exception ciblée | faux positifs : empreintes SHA-256 Graphify, aucun secret |

Les rapports JSON temporaires ont été inspectés puis retirés du worktree ; aucun secret ni
contenu sensible n'est publié. Les versions résolubles ont été mises à jour vers
`python-multipart==0.0.31`, `fastapi==0.143.0`/`starlette==1.7.0` et `pytest==9.0.3`. Le script historique
`scripts/security_checks.sh` conserve les contrôles de compilation et
de Compose, mais ses scanners optionnels ne constituent pas une preuve de scan. Le pipeline
de release doit donc appeler `scripts/security_scan.sh` et archiver ses rapports.

## Risques résiduels

`python-jose==3.5.0` (`GHSA-3qf3-8w2g-rqmx`) et `ecdsa==0.19.2` (`PYSEC-2026-1325`)
étaient les alertes E.1. L’audit des usages a confirmé un seul usage direct dans
`app/auth.py`; ils ont été retirés au profit de `PyJWT==2.15.1`. La validation impose
HS256 explicitement, exige `exp`, `sub` et `role`, et refuse les signatures, expirations,
algorithmes et claims malformés. Le pip-audit E.2 retourne désormais zéro alerte.

Les scripts applicatifs communs ont été déplacés dans `app/static/base.js`; les scripts
existants microphone/inscription restent externes. Les scripts spécifiques à une page
utilisent désormais un nonce CSP par réponse et les attributs `onchange`/`onsubmit` ont
été remplacés par des listeners externes. `script-src` ne contient plus `unsafe-inline`.
Le contrôle HTTP login et les tests Node microphone/transcripteur passent.
