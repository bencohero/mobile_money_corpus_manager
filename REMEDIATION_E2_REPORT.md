# REMEDIATION E.2 — levée des blocages de sécurité et validation préproduction

Date : 2026-10-11  
Référence : `REMEDIATION_E1_REPORT.md`  
Environnement : Compose E.2 isolé, aucune production utilisée

## Décision finale

**VALIDÉ POUR REVUE PRÉPRODUCTION**.

La décision ne constitue pas une autorisation automatique de déploiement. La revue
humaine des diffs, la validation de la fenêtre d’indisponibilité et l’autorisation
d’exploitation restent obligatoires.

## 1. JWT et dépendances cryptographiques

L’audit Graphify et `rg` ont confirmé que `python-jose` n’était utilisé directement
que dans `app/auth.py`, pour encoder/décoder le cookie de session. Aucun autre appel
JOSE, Bearer token, issuer ou audience n’existait. `ecdsa` provenait de la chaîne
cryptographique de l’ancienne installation et n’était pas importé par l’application.

Les alertes E.1 étaient `GHSA-3qf3-8w2g-rqmx` sur `python-jose==3.5.0` et
`PYSEC-2026-1325` sur `ecdsa==0.19.2`. Le remplacement par PyJWT 2.10.1 a d’abord
été audité ; le scan a révélé des alertes supplémentaires sur cette version. La
dépendance a donc été fixée à `PyJWT==2.15.1`, qui passe le pip-audit E.2.

Contrats conservés ou renforcés dans `app/auth.py` :

- algorithme `HS256` explicitement autorisé et seul algorithme accepté ;
- signature et expiration vérifiées par PyJWT ;
- claims `exp`, `sub` et `role` obligatoires ;
- claims malformés, signature invalide, token expiré et algorithme différent refusés en 401 ;
- utilisateur inconnu ou inactif refusé en 401 ;
- aucun issuer/audience n’est ajouté, car ces claims ne faisaient pas partie du contrat
  existant et aucun émetteur/audience n’est configuré.

Tests ajoutés dans `tests/test_jwt_contract.py` : token valide, claims absents/malformés,
expiration, signature invalide, algorithme HS384 refusé et permissions d’utilisateur.

## 2. Gitleaks

Le scan brut historique Gitleaks v8.24.3 a produit deux détections `generic-api-key`,
toutes deux dans `graphify-out/cache/stat-index.json`, commit `99d81b7`, ligne JSON
unique. L’examen structurel a identifié uniquement l’empreinte SHA-256 du fichier
`scripts/generate_secret.sh` dans l’index statistique Graphify ; aucune valeur de secret,
mot de passe ou clé d’accès n’a été publiée dans ce rapport.

Une exception strictement limitée à `^graphify-out/cache/stat-index\.json$` a été ajoutée
dans `.gitleaks.toml`. Le scan release avec cette configuration retourne zéro détection.
Le fichier reste un artefact généré et ne doit pas être utilisé comme source de secrets.

## 3. CSP et templates

Modifications :

- `script-src` ne contient plus `unsafe-inline` ;
- nonce aléatoire par réponse HTTP, injecté dans les scripts inline spécifiques ;
- logique CSRF, soumission automatique et confirmation de suppression déplacées dans
  `app/static/base.js` ;
- scripts microphone et inscription conservés en fichiers externes ;
- attributs inline `onchange` et `onsubmit` supprimés ;
- les scripts spécifiques participant, transcripteur et capture restent nonce-protégés
  pendant la poursuite de leur extraction vers des fichiers statiques.

Preuves : le contrôle HTTP `/login` vérifie l’absence de `unsafe-inline`, la présence
de `script-src 'self' 'nonce-…'` et le chargement de `/static/base.js`. Les tests Node
participant, capture et transcripteur passent.

## 4. Migration 0005→0008

Un Compose distinct `docker-compose.e2-migration.yml` a créé une base et des volumes
MinIO dédiés. La base a été amenée exactement à `0005_workshop_attribution`, puis
alimentée avec un jeu synthétique réaliste :

| Objet | Avant | Après 0008 |
|---|---:|---:|
| utilisateurs | 3 | 3 |
| participants | 1 | 1 |
| enregistrements | 1 | 1 |
| transcriptions | 1 | 1 |
| historique transcription | 0 | 1 baseline |

Les migrations `0006`, `0007` et `0008` ont été appliquées successivement. Résultats :

- révision finale `0008_rate_limit_buckets (head)` ;
- aucune référence atelier orpheline ;
- historique de transcription créé ;
- contrainte `ck_rate_limit_event_count_nonnegative` présente ;
- compteurs et identifiants historiques inchangés ;
- une langue d’atelier invalide a correctement bloqué `0007` avec diagnostic explicite ;
- sauvegarde custom PostgreSQL effectuée avant migration ;
- restauration de cette sauvegarde vérifiée en `0005` avec les mêmes compteurs.

Le client `pg_restore` du conteneur de test était plus récent que PostgreSQL 16 et a
émis un avertissement `transaction_timeout` ; la restauration des objets, de la version
Alembic et des données a néanmoins été vérifiée. L’exploitation devra utiliser des
outils PostgreSQL de même version majeure et consigner ce contrôle.

## 5. Fiabilité des tests

`tests/test_p0a3_negative.py` ne dépend plus de `test_integration_http.py`. Une fixture
locale prépare ses propres comptes, participant et enregistrement. Le module isolé
retourne `6 passed`.

Résultats finaux :

| Contrôle | Résultat |
|---|---|
| Suite Python complète 1 | `158 passed, 1 skipped, 8 warnings` |
| Suite Python complète 2 | `158 passed, 1 skipped, 8 warnings` |
| Tests JWT | inclus, PASS |
| Tests Node fonctionnels | PASS pour tous les `.test.cjs` |
| CSP HTTP | PASS |
| Compose config | PASS |
| Alembic | `0008_rate_limit_buckets (head)` |

Le skip Python est le contrôle Docker interne au conteneur ; le contrôle Compose hôte
est exécuté séparément et passe. Les warnings restants sont des dépréciations connues.

## 6. Scanners

- Bandit 1.8.6 : 3 LOW, 0 MEDIUM, 0 HIGH. Ils concernent les appels subprocess FFmpeg
  bornés et exécutés avec listes d’arguments et `shell=False`.
- pip-audit 2.9.0 : **0 vulnérabilité connue** sur `requirements.txt` avec PyJWT 2.15.1.
- Gitleaks v8.24.3 : 2 faux positifs dans le scan brut historique ; 0 dans le périmètre
  release avec l’exception ciblée. Aucun secret n’est reproduit dans les rapports.

Les résultats sont synthétisés dans `SECURITY_SCAN_REPORT.md`; les sorties temporaires
contenant des données de scan ne sont pas conservées dans le worktree.

## 7. Fichiers modifiés ou ajoutés

- `app/auth.py`, `requirements.txt` : remplacement JWT et validation stricte ;
- `app/main.py`, `app/templates/*`, `app/static/base.js` : CSP et suppression des handlers inline ;
- `tests/test_jwt_contract.py`, `tests/test_p0a3_negative.py`,
  `tests/record_capture.test.cjs` : contrats et indépendance des tests ;
- `.gitleaks.toml`, `docker-compose.e2-migration.yml` : périmètre sécurité et migration ;
- `SECURITY_SCAN_REPORT.md`, `RELEASE_CHECKLIST.md` : preuves et checklist actualisées.

## 8. Risques résiduels et préproduction

- Les trois alertes Bandit LOW doivent rester surveillées lors de la revue sécurité.
- L’extraction complète des scripts spécifiques nonce-protégés vers des fichiers externes
  est une amélioration future ; la CSP est déjà dépourvue de `unsafe-inline`.
- La restauration opérationnelle doit employer un `pg_restore` de même version majeure.
- Les validations humaines et l’autorisation de déploiement restent à effectuer.

**Statut : VALIDÉ POUR REVUE PRÉPRODUCTION — aucun déploiement ni changement de
production effectué.**
