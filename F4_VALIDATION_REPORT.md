# Rapport de validation F.4

Date : 2026-10-11  
Décision : **BLOQUÉ** pour exécution contrôlée sur production.

## 1. Vérifications réalisées

| Contrôle | Résultat | Preuve/limite |
|---|---|---|
| PostgreSQL Corpus vs PostgreSQL 18 | PASS | Corpus : `mobile_money_corpus_manager_v0_1-db-1`, réseau backend, aucune publication ; PostgreSQL 18 : projet `postgres`, `infra-network`, publication 5432 |
| Clients PostgreSQL 18 | PARTIEL | `pgadmin` déclaré dépendant mais `docker inspect` le montre sans réseau ; aucun autre client Docker sur `infra-network` observé ; vérification applicative complète à faire |
| Traefik dashboard | PASS | fichiers exacts identifiés ; `api.insecure: true`, `8090:8080`, aucune dépendance `api@internal` trouvée dans les fichiers inspectés |
| Santé services | PARTIEL | DB/MinIO Corpus healthy ; app, Traefik, PostgreSQL 18 et pgAdmin running sans healthcheck Docker exploitable |
| Ports effectifs | PASS | `ss` montre `0.0.0.0:5432`, `[::]:5432`, `0.0.0.0:8090`, `[::]:8090` |
| Pare-feu | BLOQUÉ | `ufw`/`nft` exigent root ; aucune conclusion de règle hôte ne peut être certifiée |
| Configurations candidates | PASS | Compose PostgreSQL/Traefik et YAML candidats validés ; aucun port PostgreSQL/8090 dans les candidats |
| Scripts synthétiques | PASS | `scripts/validate_backup_synthetic.sh` retourne `synthetic backup/restore passed`, sans données réelles |
| Gel des écritures | BLOQUÉ | aucun gate read-only/maintenance existant démontré ; design préparé mais non déployé |

## 2. Commandes de validation hors production

```bash
POSTGRES_PASSWORD='candidate-only' \
  docker compose -f f4-candidates/postgres/docker-compose.restricted.yml config --quiet
docker compose -f f4-candidates/traefik/docker-compose.yml config --quiet
bash scripts/validate_backup_synthetic.sh
```

La validation Traefik est un parsing YAML statique, car l’image `traefik:v3.7`
présente dans le VPS n’expose pas de sous-commande `check-config`; un démarrage
réel du candidat reste inutile pour ce ticket. Ces commandes ne ciblent aucun
projet Compose actif.

## 3. Écarts bloquants avant exécution

- validation root du pare-feu et test externe des ports ;
- identification et validation de tous les clients PostgreSQL 18, notamment pgAdmin ;
- preuve d’un accès administratif de secours ;
- destination hors VPS, clé publique de chiffrement et politique de rétention ;
- test isolé PostgreSQL/MinIO réel après le test factice ;
- gate de gel des écritures implémentée ou mode read-only approuvé et testable.

## 4. Autorisations

Exploitation : changements Compose, ports, redémarrages et fenêtre. Sécurité :
pare-feu, Traefik, accès administratif et chiffrement. Responsable données : gel,
sauvegarde, restauration et cohérence. Propriétaire applicatif : états PENDING,
drain et validation fonctionnelle.

Aucune migration, suppression, sauvegarde réelle, modification de pare-feu,
redémarrage ou changement de production n’a été exécuté dans F.4.
