# Audit de coexistence VPS — F.2

Date de l’observation : 2026-10-11  
Mode : **lecture seule uniquement**.  
Version candidate de référence : `cb87475513721fc5816272ee41beaff3b9b13f8a`.

## Conclusion

**NO-GO pour créer une préproduction sur ce VPS sans préparation et autorisation
d’exploitation.** L’application opérationnelle est stable et ses données sont dans des
réseaux/volumes distincts du développement, mais le VPS porte déjà plusieurs stacks de
tests actifs, PostgreSQL est publié sur toutes les interfaces, l’API Traefik est publiée
sur `8090`, et la base opérationnelle observée est à `0005_workshop_attribution`, pas à
0008. Les sauvegardes observées sont locales au VPS ; aucune copie hors VPS n’est prouvée.

Aucune ressource n’a été supprimée, arrêtée, redémarrée ou modifiée. Aucune migration,
sauvegarde ou restauration n’a été exécutée.

## 1. Cartographie Docker

### Application opérationnelle

| Élément | Observation |
|---|---|
| Projet Compose | `mobile_money_corpus_manager_v0_1` |
| Fichier | `/home/sangouman/apps/mobile_money_corpus_manager_v0_1/docker-compose.yml` |
| Conteneurs | `app-1`, `db-1`, `minio-1`, tous actifs ; DB/MinIO healthy |
| App image | ID `sha256:c2e3e50e3e74…`, créée le 2026-10-07 ; aucune OCI revision Git |
| DB image | `postgres:16-alpine` |
| MinIO image | `RELEASE.2025-04-22T22-12-26Z` |
| Réseaux | `frontend` pour l’app ; `mobile_money_corpus_manager_v0_1_backend` pour app/DB/MinIO |
| Volumes | `mobile_money_corpus_manager_v0_1_pgdata`, `…_miniodata`, `…_tmpaudio` |
| Redémarrage | `unless-stopped` sur app, DB et MinIO |
| Publication | aucun port direct pour app/DB/MinIO ; exposition via Traefik |

L’image actuellement exécutée n’est donc pas démontrée comme étant la candidate
`cb874755…`; le conteneur a été créé avant la recette F.1 et ne porte pas de label Git.

### Développement

| Élément | Observation |
|---|---|
| Projet | `mobile_money_corpus_manager_dev` |
| Fichier | `docker-compose.dev.yml` dans le même répertoire Git |
| Conteneurs | app, DB et MinIO actifs depuis environ 27 h |
| Réseau | `mobile_money_corpus_dev_internal`, distinct de la production |
| Volumes | `mobile_money_corpus_dev_postgres_data`, `mobile_money_corpus_dev_minio_data` |
| Ports | app `127.0.0.1:8081`, MinIO `127.0.0.1:9100/9101` |
| Image app | `mobile_money_corpus_manager_dev-app`, sans revision Git vérifiable |

Le développement ne partage pas les volumes de production, mais il cohabite sur le même
hôte et consomme CPU, mémoire et espace disque.

### Tests et anciens lots

`docker compose ls` montre notamment les projets actifs `mobile-money-corpus-remediation-d1`,
`-d2`, `-d3`, ainsi que `-d` partiellement créé/exité. Ils utilisent les fichiers de test
du même dépôt et des réseaux/volumes nommés `mobile-money-corpus-*test`.

Les réseaux observés sont `mobile-money-corpus-c1-test`, `c1b-test` et `p0a2-test`.
Plusieurs bases PostgreSQL et MinIO de test tournent depuis environ 24 h. Le projet `d`
est incohérent : son DB est arrêté et son app est seulement `Created`, tandis que son
MinIO reste actif. Le réseau nommé `p0a2-test` contient encore un MinIO de cet ancien
lot. Aucun nettoyage n’a été effectué.

## 2. PostgreSQL, MinIO et données réelles

### Production opérationnelle

- Base : `corpus`, conteneur `mobile_money_corpus_manager_v0_1-db-1`.
- Volume PostgreSQL : `mobile_money_corpus_manager_v0_1_pgdata`, environ 65,83 MB.
- Révision observée sans migration : `0005_workshop_attribution`.
- Vérification directe de `alembic_version` : `0005_workshop_attribution`.
- Bucket : `mobile-money-corpus`.
- Volume MinIO : `mobile_money_corpus_manager_v0_1_miniodata`, environ 5,34 MB.
- Statistiques de tables sans lignes ni contenus affichés : participants 17,
  recordings 15, recording submissions 15, recording take counters 15,
  transcriptions 1, users 21, workshop codes 6, workshops 4, audit logs 114.

Ces nombres sont uniquement des métadonnées de capacité ; aucun identifiant, nom,
transcription ou objet audio n’a été affiché. Les compteurs historiques et relations
restent des données critiques à préserver ; aucune renumérotation ou réinitialisation
n’est autorisée.

### Partage constaté

La production et le développement ont des volumes, réseaux, bases et buckets distincts.
La production partage toutefois le réseau frontal `frontend` avec Traefik et plusieurs
autres applications. Les stacks de tests ont leurs propres réseaux en théorie, mais les
noms explicites du Compose historique ont déjà produit des collisions de ressources entre
lots. Une préproduction ne doit pas réutiliser `docker-compose.test.yml` seul.

## 3. Réseau et Traefik

- Ports hôte observés : `80/tcp`, `443/tcp`, `8090/tcp` sur toutes les interfaces via
  Traefik ; `5432/tcp` PostgreSQL global sur `0.0.0.0` et IPv6 ; développement limité à
  `127.0.0.1:8081`, `9100`, `9101`.
- Route production : `Host(corpus-moore.bencoherolab.com)`, HTTPS, resolver `ovhcloud`,
  backend app port 8000.
- Certificats : `traefik/certs/acme.json` existe ; sa taille et son chemin ont été
  relevés, mais son contenu n’a pas été ouvert. La date d’expiration n’est donc pas
  déclarée vérifiée pour éviter l’exposition de données ACME.
- Traefik monte le socket Docker `/var/run/docker.sock`, le fichier de configuration,
  les logs et `acme.json`.
- `api.insecure: true` est configuré et le port dashboard `8090` est publié sur toutes
  les interfaces : **risque critique** d’exposition de l’API/dashboard.
- Le middleware CrowdSec définit des plages de proxys de confiance privées ; les secrets
  et clés n’ont pas été affichés.
- Dans le conteneur production, `TRUSTED_HOSTS`, `FORWARDED_ALLOW_IPS` et
  `COOKIE_SECURE` ne sont pas présents explicitement dans l’environnement inspecté ;
  les valeurs effectives peuvent venir des defaults/configuration et doivent être
  vérifiées par l’exploitation sans afficher de secrets.

## 4. Ressources VPS

- Hôte : uptime environ 24 jours ; 6 CPU visibles.
- Charge : `2.89 / 3.20 / 2.76` au moment de l’audit ; charge non négligeable.
- Mémoire : 11 GiB total, 7,8 GiB utilisés, 3,9 GiB disponibles ; aucun swap.
- Disque racine/Docker : 193 GiB, 98 GiB utilisés, 96 GiB libres.
- Docker : 58 images, 28 conteneurs, 27 volumes ; environ 11,32 GiB d’images,
  1,312 GiB de volumes et 12,81 GiB de build cache.
- Images non utilisées/reclaimable : environ 5,129 GiB ; cache reclaimable environ
  9,613 GiB. Aucun nettoyage n’a été exécuté.
- Le stack de tests historique consomme plusieurs centaines de MiB, notamment MinIO
  autour de 230–240 MiB par instance. Un seul petit stack supplémentaire est probablement
  possible en mémoire, mais sans swap et avec la charge actuelle ce n’est pas une garantie
  de sécurité pour l’application opérationnelle.

## 5. Sauvegardes

Cinq répertoires `before_corpus_reset_*` ont été trouvés dans le répertoire du projet,
datés du 2026-10-05, de taille approximative 56 KiB à 19 MiB. Ils contiennent des
archives PostgreSQL, des répertoires MinIO et des fichiers `SHA256SUMS` ; seuls noms,
tailles et dates ont été consultés.

Les éléments suivants ne sont pas prouvés : fréquence automatisée de sauvegarde métier,
copie chiffrée hors VPS, rétention, cohérence temporelle PostgreSQL/MinIO, test récent de
restauration historique et alerte d’échec. Le seul timer de backup trouvé est
`dpkg-db-backup.timer`, sans rapport avec le corpus. Les sauvegardes de corpus observées
sont dans le même arbre du VPS que le dépôt et ne constituent pas une copie hors site.

## 6. Git et release

- Worktree audité : `/home/sangouman/apps/mobile_money_corpus_manager_v0_1`.
- HEAD de ce worktree : `704f9807f4571f26a3e3791e6bc5b2d37541c622`.
- Le dépôt contient aussi le worktree détaché `/tmp/mobile-money-corpus-manager-d34e`.
- Le conteneur opérationnel est configuré par le Compose de ce dépôt, mais son image
  `c2e3e50e…` ne porte pas le SHA Git candidat et n’est pas prouvée équivalente à
  `cb874755…`.
- Développement et production utilisent le même répertoire Git comme source Compose,
  avec des projets Compose différents. Cela augmente le risque qu’une commande lancée
  depuis le dépôt cible le mauvais projet.

## 7. Matrice d’isolation

| Environnement | Projet | Réseau | PostgreSQL / volume | MinIO / bucket-volume | Ports / domaine | Risque |
|---|---|---|---|---|---|---|
| Production | `mobile_money_corpus_manager_v0_1` | backend privé + `frontend` | `corpus` / `…_pgdata` | `mobile-money-corpus` / `…_miniodata` | Traefik 80/443, corpus-moore… | Critique : DB hôte 5432 et dashboard 8090 exposés ; DB à 0005 |
| Développement | `mobile_money_corpus_manager_dev` | `dev_internal` | volume dev distinct | volume/bucket dev distinct | localhost 8081/9100/9101 | Moyen : cohabitation ressources, même dépôt |
| Tests historiques | d/d1/d2/d3/c1/c1b | réseaux test multiples | volumes test distincts | volumes test distincts | pas de publication app, 5432 interne | Élevé : anciens lots actifs et collisions de noms |
| Préproduction envisagée | nouveau projet dédié | réseau unique `f1-preprod` | volume `f1-preprod-pgdata` | bucket/volume `f1-preprod` | aucun port public ; tunnel admin si besoin | Acceptable seulement après contrôle de capacité et secrets distincts |

## 8. Matrice des risques de perte/corruption

| Risque | Gravité | Preuve | Mesure obligatoire |
|---|---|---|---|
| Migration directe de la base à 0005 | Critique | révision observée 0005, données réelles présentes | dump + copie isolée + diagnostic + validation données |
| Mauvais projet Compose ciblé | Critique | même dépôt, nombreux projets | noms explicites, `docker compose ps` avant toute action, approbation humaine |
| Collision réseau/volume test | Élevée | p0a2/c1/c1b partagés par anciens lots | nouveau nom de projet, réseau et volumes sans noms historiques |
| Exposition PostgreSQL 5432 | Critique | écoute `0.0.0.0:5432` | fermeture contrôlée par exploitation et pare-feu, hors recette lecture seule |
| API Traefik 8090 publique | Critique | `api.insecure: true`, port 8090 | désactivation/protection Traefik, validation sécurité |
| Sauvegarde seulement locale | Critique | backups dans l’arbre VPS, aucun hors site prouvé | copie chiffrée hors VPS + test de restauration |
| Saturation mémoire/disque | Élevée | 7,8/11 GiB, 12,81 GiB cache, pas de swap | fenêtre validée, quotas, monitoring, aucune charge simultanée non approuvée |
| Image déployée non liée au SHA candidat | Élevée | image sans OCI Git revision | inventaire digest + plan de déploiement contrôlé |

## 9. Plan de recette sans interruption

1. Obtenir l’autorisation écrite exploitation, données et sécurité ; conserver un point
   de contrôle `/health`, `/ready`, état des conteneurs et espace disque.
2. Ne pas utiliser les noms `p0a2-test`, `c1-test`, `c1b-test` ni aucun volume existant.
   Utiliser un projet Compose inédit, par exemple `mobile-money-corpus-f1-preprod`,
   un réseau privé inédit et des volumes/buckets inédits.
3. Utiliser uniquement des données synthétiques ou une copie anonymisée autorisée.
   Aucun secret de production, aucun bucket de production, aucun domaine public.
4. Ne publier aucun port sur `0.0.0.0`. Si un navigateur est nécessaire, publier un
   port localhost contrôlé ou utiliser un tunnel approuvé ; ne pas ajouter de routeur
   Traefik.
5. Réutiliser seulement des images déjà construites et identifiées par digest/SHA ; ne
   pas lancer de rebuild sur le VPS opérationnel.
6. Démarrer au maximum un stack léger après mesure mémoire/disque et vérifier que les
   conteneurs opérationnels n’ont ni changement d’état ni nouveau montage.
7. Exécuter tests, `/health`, `/ready`, diagnostics et réconciliation uniquement sur les
   cibles préproduction. Toute migration doit viser la copie isolée et être explicitement
   approuvée.
8. Avant et après chaque étape, contrôler `docker ps`, `docker compose ls`, ports publiés,
   réseaux, espace disque, mémoire et état de l’application. Arrêter la recette si une
   ressource opérationnelle change, si l’espace passe sous le seuil approuvé ou si un
   secret/bucket de production est détecté.
9. Nettoyage ultérieur uniquement par une procédure approuvée, avec inventaire préalable ;
   aucune suppression n’est autorisée dans cet audit.

## 10. Actions nécessitant autorisation

- Toute consultation de contenu réel au-delà des métadonnées déjà lues.
- Sauvegarde réelle PostgreSQL + MinIO et copie chiffrée hors VPS.
- Restauration d’une copie réelle dans la préproduction.
- Migration 0005→0008 ou toute modification de schéma.
- Modification des ports 5432/8090, de Traefik, des certificats ou du pare-feu.
- Arrêt, redémarrage, suppression ou nettoyage de conteneurs/volumes/images.
- Test multi-workers, test de charge ou recette navigateur exposée.
- Déploiement d’une image correspondant à `cb874755…`.

## Recommandation finale

**NO-GO pour lancer la préproduction sur le VPS dans l’état observé.** Une préproduction
isolée est envisageable seulement avec un projet/réseau/volumes/bucket nouveaux, sans
Traefik ni ports publics, avec données synthétiques et capacité validée. La migration
réelle reste interdite jusqu’à sauvegarde cohérente, copie hors VPS, restauration testée,
diagnostic historique et approbations humaines.
