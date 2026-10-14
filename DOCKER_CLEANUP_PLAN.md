# Plan de nettoyage Docker contrôlé — F.3

Date : 2026-10-11  
Statut : **PRÊT POUR AUTORISATION**  
Inventaire en lecture seule ; aucune commande `down`, suppression ou nettoyage n’a
été exécutée.

## 1. Production et développement à préserver

Ne pas toucher au projet `mobile_money_corpus_manager_v0_1` (`app-1`, `db-1`,
`minio-1`), à ses volumes `mobile_money_corpus_manager_v0_1_pgdata`,
`_miniodata`, `_tmpaudio`, ni à ses réseaux backend/frontend. Préserver aussi le
projet `mobile_money_corpus_manager_dev` et ses volumes `_dev_postgres_data`,
`_dev_minio_data` jusqu’à décision explicite : il est distinct mais actif et utile au
développement.

## 2. Stacks corpus historiques observés

| Projet actif | Fichiers Compose | Conteneurs | Réseau | Volumes principaux | Fonction/propriétaire |
|---|---|---|---|---|---|
| `mobile-money-corpus-remediation-d1` | `docker-compose.test.yml` + `docker-compose.c1.test.yml` | `mobile-money-corpus-remediation-d1-{app,db,minio}-test-1` | `mobile-money-corpus-c1-test` | `mobile-money-corpus-remediation-d1_c1-test-pgdata`, `...-miniodata` (et ressources restore/backup éventuelles) | validation C.1, propriétaire à confirmer |
| `mobile-money-corpus-remediation-d2` | `docker-compose.test.yml` + `docker-compose.c1b.test.yml` | `mobile-money-corpus-remediation-d2-{app,db,minio}-test-1` | `mobile-money-corpus-c1b-test` | `mobile-money-corpus-remediation-d2_c1b-test-pgdata`, `...-miniodata` (et ressources restore/backup éventuelles) | validation C.1b, propriétaire à confirmer |
| `mobile-money-corpus-remediation-d3` | `docker-compose.test.yml` + `docker-compose.c1.test.yml` | `mobile-money-corpus-remediation-d3-{app,db,minio}-test-1` | `mobile-money-corpus-c1-test` | `mobile-money-corpus-remediation-d3_c1-test-pgdata`, `...-miniodata` (et ressources restore/backup éventuelles) | validation D, nom de réseau partagé à auditer |
| `mobile-money-corpus-remediation-d` | `docker-compose.test.yml` | `mobile-money-corpus-remediation-d-{app,db,minio}-test-1` (`Created`/`Exited`/actif) | réseau historique, à confirmer | `mobile-money-corpus-remediation-d4_d-test-pgdata`, `...-miniodata` | lot incomplet, fonction/propriétaire à confirmer |

Les ressources historiques résiduelles incluent également le réseau
`mobile-money-corpus-p0a2-test` et les volumes `mobile-money-corpus-p0a2-test-*`,
les volumes `remediation-c1_*`, `remediation-c1b_*`, et le lot E.1
`mobile-money-corpus-e1-test-*`. Leur projet Compose n’est pas actif dans
`docker compose ls`, mais leur présence ne prouve pas qu’ils sont inutilisés.

Les stacks `c1`, `c1b`, `d1`, `d2` et `d3` ont des conteneurs PostgreSQL/MinIO
uniquement exposés sur leurs réseaux Docker, pas de publication hôte observée.
L’isolement doit néanmoins être revalidé par `docker inspect` avant toute action,
car des noms de réseaux historiques se recouvrent (`c1-test`).

## 3. Services hors périmètre corpus

Les projets `traefik`, `postgres`, `superset`, `crowdsec`, `vaultwarden`, `beszel`,
`bentopdf`, `it-tools` et `contab-agents` sont actifs mais ne sont pas des lots de
test du corpus. Ils ont leur propre propriétaire et procédure ; ne pas les arrêter
dans le cadre de ce ticket. Le projet `postgres` est précisément la source de la
publication hôte 5432 et relève du plan de sécurité, pas d’un nettoyage implicite.

## 4. Vérifications obligatoires par projet

Avant toute proposition d’arrêt : enregistrer projet/config files, état de chaque
conteneur, mounts, labels Compose, réseaux et endpoints ; comparer les volumes aux
volumes de production ; rechercher les attaches croisées aux réseaux `frontend` et
backend ; vérifier qu’aucun job, tunnel, script ou utilisateur ne l’utilise.
Identifier le propriétaire humain, la fonction, la date de dernière utilisation et
la preuve de reproductibilité. Une ressource partagée, inconnue ou attachée à
production bloque l’opération.

## 5. Séquence proposée, sans exécution

1. Obtenir les propriétaires et les décisions « conserver / archiver / supprimer ».
2. Exporter l’inventaire et, si les données ont une valeur, une sauvegarde autorisée
   des lots non productifs.
3. Arrêter un seul lot à la fois pendant une fenêtre validée, puis vérifier que la
   production et les services hors périmètre restent sains.
4. Archiver Compose, manifeste, logs nécessaires et empreintes dans un emplacement
   hors Docker ; conserver les volumes tant que la période de rétention n’est pas
   échue.
5. Supprimer uniquement après une seconde approbation, avec noms explicites et liste
   fermée des cibles. Aucun `docker system prune` global n’est autorisé.

## Risques, retour arrière et décision

Risques : suppression d’un volume contenant une preuve, collision de réseau, arrêt
d’un service partagé, saturation pendant l’archivage et mauvais projet Compose.
Retour arrière : restaurer le fichier Compose et les volumes archivés dans un projet
au nom neuf ; ne jamais recréer un volume de production par ambiguïté de nom. Si la
propriété ou l’isolation est inconnue, ne rien arrêter.

Autorisations requises : propriétaire de chaque lot, exploitation Docker et
responsable données si un volume contient des données corpus. Le plan est
**PRÊT POUR AUTORISATION** ; aucune commande de nettoyage ne doit être lancée dans
ce ticket.
