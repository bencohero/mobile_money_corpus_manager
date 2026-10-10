# Remédiation D — sécurité, exploitation et qualité technique

Date : 2026-10-10  
Statut : **VALIDÉ**

## 1. Diagnostic initial

- Le dépôt contenait des modifications non commitées des lots A–C ; elles ont été conservées.
- La base du compose courant était à `0005_workshop_attribution`, tandis que le code attendait la tête `0007`. Aucun volume de production n’a été modifié ni migré.
- `app/rate_limit.py` utilisait des compteurs mémoire par processus, sans limite globale de cardinalité.
- Uvicorn lançait `--forwarded-allow-ips "*"`.
- Aucun middleware applicatif ne posait de politique cohérente d’en-têtes HTTP.
- Les colonnes historiques sont `timestamp without time zone`; `datetime.utcnow()` était utilisé dans plusieurs écritures.
- La migration historique 0005 n’a pas été modifiée.

## 2. Mesures appliquées

- Ajout de la migration `0008_rate_limit_buckets` : compteurs PostgreSQL atomiques, fenêtres expirables, index d’expiration et nettoyage opportuniste.
- Connexion, inscription et endpoint public de langue utilisent la limitation partagée ; le repli mémoire borné à 10 000 clés reste actif avant migration ou en cas d’indisponibilité DB.
- `GET /api/auth/workshop-language` limite les tentatives, renvoie une réponse générique pour codes invalides/inactifs/langues absentes et ne journalise que le scope d’abus, jamais le code.
- Ajout de `SecurityHeadersMiddleware` : CSP, `frame-ancestors`, `nosniff`, `Referrer-Policy`, HSTS conditionnel HTTPS, `Permissions-Policy` microphone et `X-Frame-Options`.
- Ajout de `TrustedHostMiddleware` ; en production, un wildcard est remplacé par `APP_HOST`.
- Remplacement de la confiance proxy wildcard par `FORWARDED_ALLOW_IPS`, par défaut `172.22.0.0/16` sur le réseau Traefik observé.
- Ajout de `app/time_utils.py` : nouvelles écritures en UTC naïf explicite, compatible avec les colonnes PostgreSQL historiques ; les entrées aware sont normalisées en UTC aux frontières d’administration.
- Ajout de `scripts/check_workshop_references.py`, diagnostic indépendant en lecture seule : aucune suppression ni réparation automatique.
- Ajout de `scripts/security_checks.sh` pour compilation, Compose, Bandit, pip-audit, Gitleaks et `npm audit` lorsque les outils et artefacts sont présents.

La CSP conserve `unsafe-inline` pour les scripts inline actuellement présents dans les templates ; le microphone et l’audio utilisent `media-src 'self' blob:`. Une extraction ultérieure des scripts vers des fichiers externes permettra de supprimer cette exception sans dégrader les pages existantes.

## 3. Architecture du rate limiting

Traefik ne fournit pas ici un compteur partagé suffisant entre plusieurs réplicas. Redis n’a donc pas été introduit. PostgreSQL, déjà obligatoire, est utilisé avec un `INSERT ... ON CONFLICT` atomique sur `(bucket_key, scope)`. Les compteurs expirés sont nettoyés opportunément ; le dictionnaire de secours est borné et ne désactive jamais la protection en cas d’échec de la DB.

Limites actuelles : login 10 échecs / 5 min par identifiant et IP, inscription 60 / 10 min par IP, langue d’atelier 20 / 10 min par IP. Les connexions légitimes ne consomment pas le compteur de login.

## 4. Configuration Traefik/FastAPI

Le VPS doit définir dans `.env` :

```env
APP_HOST=mobile-money-corpus.example.com
FORWARDED_ALLOW_IPS=172.22.0.0/16
COOKIE_SECURE=true
```

Le CIDR doit correspondre au réseau Docker partagé avec Traefik ; le vérifier avec `docker network inspect <réseau>`. Ne jamais remettre `*`. Les cookies de session restent `HttpOnly`, `Secure` en production et `SameSite=Strict`; le cookie CSRF reste lisible par le JavaScript et conserve `SameSite=Strict`.

## 5. Modifications de schéma

Une seule nouvelle migration est ajoutée : `0008_rate_limit_buckets`, descendante de `0007`. Elle ne touche pas les identifiants ni les données historiques. Déploiement : sauvegarde vérifiée, exécution contrôlée de `alembic upgrade head`, puis vérification de `alembic current`. Ne pas exécuter contre la base courante sans procédure de migration approuvée.

## 6. Résultats SAST/SCA

`scripts/security_checks.sh` a validé la compilation, les deux configurations Compose et l’absence d’artefact frontend applicable. Sur l’environnement d’exécution, Bandit, pip-audit et Gitleaks n’étaient pas installés ; le script les a signalés explicitement comme `SKIPPED` sans afficher de secrets. Aucun `package-lock.json` n’existe, donc `npm audit` est `NOT_APPLICABLE`.

## 7. Résultats des tests

- Suite Docker complète, environnement dédié D : **153 passed, 1 skipped**.
- Deuxième exécution complète : **153 passed, 1 skipped**.
- Tests Node : tous les tests `.test.cjs` passent.
- Revision observée dans l’environnement isolé : `0008_rate_limit_buckets (head)`.
- Les contrôles ciblent notamment les inscriptions, CSRF, audio Range, transcription, verrouillage optimiste, export, réconciliation, readiness/liveness et autorisations.

Le skip concerne uniquement un test qui exige le binaire Docker à l’intérieur du conteneur de test ; Compose lui-même a été validé depuis l’hôte.

## 8. Risques résiduels

- Les scanners externes doivent être installés dans CI pour produire un résultat SAST/SCA complet.
- La CSP contient encore `unsafe-inline` pour compatibilité avec les templates existants.
- Le CIDR `FORWARDED_ALLOW_IPS` est une configuration d’exploitation : il doit être réajusté si le réseau Docker Traefik change.
- La base courante observée à `0005` reste volontairement non migrée.

## 9. Instructions de déploiement

1. Sauvegarder PostgreSQL et MinIO selon le runbook existant.
2. Inspecter le CIDR du réseau Traefik et définir `FORWARDED_ALLOW_IPS` sans wildcard.
3. Déployer l’image et exécuter `alembic upgrade head` selon la procédure de maintenance, jamais par `stamp` ou modification de migration historique.
4. Vérifier `alembic current`, `/health`, `/ready`, les headers HTTPS et quelques tentatives répétées de codes invalides.
5. Exécuter `scripts/security_checks.sh` dans CI avec Bandit, pip-audit et Gitleaks installés.

## 10. Statut final

**VALIDÉ**, avec les risques résiduels documentés ci-dessus. Aucun secret réel, volume existant ou donnée de production n’a été modifié.
