# F.4 — Runbook d’exécution sécurité VPS

Date : 2026-10-11  
Statut : **BLOQUÉ POUR EXÉCUTION — PRÊT APRÈS AUTORISATION ET CONTRÔLES PRIVILÉGIÉS**

Ce runbook ne doit pas être exécuté tel quel sur les services actuels sans
autorisation écrite. Les candidats sont dans `f4-candidates/` et ne sont pas
montés par les projets actifs.

## 1. Cartographie et impacts

| Sujet | Cible | Dépendances | Impact potentiel |
|---|---|---|---|
| PostgreSQL 18 | projet `postgres`, conteneur `postgres`, `/home/sangouman/apps/postgres/docker-compose.yml` | `infra-network`, `pgadmin`, clients hors projet à identifier | pgAdmin ou un service externe peut perdre son accès ; le Corpus Manager n’utilise pas ce service |
| PostgreSQL production | `mobile_money_corpus_manager_v0_1-db-1`, PostgreSQL 16 | app sur `mobile_money_corpus_manager_v0_1_backend`, alias `mobile-money-corpus-db` | ne pas toucher ; aucune publication hôte |
| Traefik | projet `traefik`, conteneur `traefik` | réseau `frontend`, routes 80/443, ACME, CrowdSec, socket Docker, services labellisés | 8090 fermé ; 80/443 et routes HTTPS doivent rester disponibles |
| Dashboard | `api.insecure: true`, `dashboard: true`, `8090:8080` | utilisateurs et supervision à rechercher | accès administratif actuel perdu jusqu’à mise en place d’un tunnel/route protégée |
| Pare-feu | règles hôte | privilèges root requis | état effectif non vérifiable avec le compte courant |

Constat runtime : `5432` et `8090` écoutent sur `0.0.0.0` et IPv6. Les services
production DB/MinIO sont healthy ; app, Traefik, PostgreSQL 18 et pgAdmin sont
running, mais sans healthcheck Docker exploitable pour les trois derniers. `pgadmin`
apparaît sans réseau dans `docker inspect`, malgré sa déclaration Compose : son
accès réel doit être vérifié avant fermeture de 5432.

## 2. Préconditions obligatoires

1. Responsable exploitation, sécurité et propriétaire des services identifiés.
2. Fenêtre approuvée, accès SSH confirmé et session de secours indépendante.
3. Résultat root de `ufw status verbose`/`nft list ruleset`, `ss -lntp` et test depuis
   un hôte privé approuvé.
4. Liste des clients PostgreSQL 18 issue de `pg_stat_activity`, configs Compose et
   logs, avec pgAdmin explicitement classé utilisé/non utilisé.
5. Accès administratif de remplacement : tunnel SSH vers PostgreSQL, accès pgAdmin
   privé si nécessaire, et accès Traefik par tunnel local ou route HTTPS protégée.
6. Sauvegarde réelle autorisée et validée selon `BACKUP_IMPLEMENTATION_READINESS.md`.
7. Point de retour : empreintes des fichiers actifs et relevé santé/ports/routes.

## 3. Validation des candidats hors production

Commandes exactes depuis le dépôt, sans cible active :

```bash
POSTGRES_PASSWORD='candidate-only' \
  docker compose -f f4-candidates/postgres/docker-compose.restricted.yml config --quiet

docker compose -f f4-candidates/traefik/docker-compose.yml config --quiet

python3 - <<'PY'
from pathlib import Path
import yaml
for path in (Path("f4-candidates/traefik/traefik.yml"),
             Path("f4-candidates/traefik/config.yml")):
    yaml.safe_load(path.read_text())
print("Traefik YAML parse: PASS")
PY
```

Résultats attendus : configuration Compose sans erreur, aucun bloc `ports` dans
le candidat PostgreSQL, aucun `8090:8080` dans le candidat Traefik, `api.insecure`
à `false`, entrypoints 80/443 conservés. Le candidat ne contient pas encore de
route dashboard : elle doit être ajoutée seulement après choix de l’accès sécurisé.

## 4. Séquence autorisée proposée

### A. Avant changement

```bash
docker compose ls -a
docker ps --format '{{.Names}}|{{.Status}}|{{.Ports}}|{{.Label "com.docker.compose.project"}}'
ss -lntp
docker inspect postgres pgadmin traefik \
  mobile_money_corpus_manager_v0_1-app-1 \
  mobile_money_corpus_manager_v0_1-db-1 \
  mobile_money_corpus_manager_v0_1-minio-1
```

Capturer les sorties sans secrets. Vérifier `/health`, `/ready`, le domaine HTTPS,
la résolution DNS et les logs Traefik. Ne pas utiliser `docker compose down` ou
`up` avant l’approbation de l’étape suivante.

### B. PostgreSQL 18

Après validation des clients et de l’accès de secours, appliquer la copie candidate
dans le projet réellement propriétaire, avec un diff approuvé. La cible est la
suppression de la publication `5432:5432`; le réseau Docker reste disponible pour
pgAdmin si celui-ci est correctement rattaché. Vérifier localement puis depuis le
réseau privé approuvé. Le Corpus Manager doit rester inchangé.

### C. Traefik

Après validation des routes et de l’accès administratif, appliquer la configuration
avec `api.insecure: false` et sans `8090:8080`. Conserver le provider Docker, le
fichier dynamique, les certificats, CrowdSec, 80/443 et les labels applicatifs.
Vérifier la route `corpus-moore.bencoherolab.com`, `/health`, `/ready`, ACME et les
autres routeurs avant de fermer la fenêtre.

## 5. Critères d’arrêt et retour arrière

Arrêter si un client inconnu est découvert, si pgAdmin n’a plus son chemin approuvé,
si une route HTTPS, ACME, readiness ou service change d’état, si un volume de
production est ciblé, ou si un secret apparaît dans les sorties.

Retour arrière : restaurer les fichiers précédents par leurs chemins exacts et leurs
empreintes, rétablir uniquement le port concerné si l’accès de secours est perdu,
puis répéter les tests. Ne jamais restaurer un Compose entier ni toucher aux volumes
Corpus. Un retour arrière Traefik ne doit pas réactiver durablement le dashboard
public sans restriction compensatoire.

## 6. Disponibilité et responsables

La fermeture des ports ne devrait pas interrompre le trafic applicatif, mais peut
interrompre l’administration et pgAdmin. La modification Traefik peut provoquer un
rechargement bref ; prévoir une fenêtre de quelques minutes et une surveillance
continue. Exploitation exécute, sécurité valide l’exposition, propriétaires
PostgreSQL/Traefik valident les dépendances, propriétaire Corpus valide la santé.
