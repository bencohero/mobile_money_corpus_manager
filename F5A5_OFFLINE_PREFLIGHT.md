# F.5A.5 — Prévol offline_app

Date du contrôle : 2026-10-11 (Europe/Berlin). Contrôles sans écriture.

## Décision

**BLOQUÉ** — le prévol ne permet pas de déclarer la cible réelle prête pour
autorisation de sauvegarde locale.

La cible PostgreSQL `mobile_money_corpus_manager_v0_1-db-1` et MinIO
`mobile_money_corpus_manager_v0_1-minio-1` sont actifs et sains. En revanche,
`mobile_money_corpus_manager_v0_1-app-1` est absent du moteur Docker, et non pas
un conteneur existant arrêté. L’arrêt effectif de l’application ne peut donc pas
être prouvé par le contrôle demandé. Le mode `offline_app` refuse ce cas.

## Preuves

| Contrôle | Résultat | Preuve |
|---|---|---|
| Conteneur applicatif cible | BLOQUÉ | `docker inspect mobile_money_corpus_manager_v0_1-app-1` : `no such object` |
| DB cible | PASS | conteneur actif, `postgres:16-alpine`, health `healthy` |
| MinIO cible | PASS | conteneur actif, `RELEASE.2025-04-22T22-12-26Z`, health `healthy` |
| Réseau cible | PASS partiel | backend cible contient seulement DB et MinIO ; l’app est absente |
| Autres stacks applicatives | OBSERVÉES | stacks `dev` et `remediation-d1/d2/d3` actives, réseaux/volumes distincts |
| Processus upload/transcription/réconciliation | PASS local | aucun processus correspondant observé lors du contrôle ; ce contrôle ne remplace pas l’attestation VPS |
| Clients externes en écriture | NON EXCLU | l’absence du conteneur applicatif empêche de prouver le chemin d’écriture autorisé ; aucune capture ne doit être lancée |
| Base `corpus` / bucket | NON REVALIDÉS ici | preuves antérieures dans `F5A1_BACKUP_PREFLIGHT_REPORT.md`, à reprendre dans la fenêtre approuvée |
| Alembic | OBSERVÉ antérieurement | `0005_workshop_attribution`; aucune migration exécutée |
| Disque | PASS indicatif | `/` : 193G total, 93G disponibles ; `/var/backups/mobile-money-corpus/` non créé |
| Sauvegarde concurrente | PASS local | aucun `pg_dump`, `pg_restore`, `mc mirror`, `rclone`, `restic` ou `borg` observé |

Le PostgreSQL hôte `postgres:18` et les stacks de test ne sont pas des cibles de
ce ticket. Ils ne peuvent pas être utilisés comme preuve pour la cible `corpus`.

## Conditions de déblocage

Le prochain prévol doit constater un conteneur applicatif cible existant en état
`exited` ou `dead`, aucun autre service du projet actif, aucun montage des volumes
`pgdata`/`miniodata` par un autre conteneur, aucun port hôte PostgreSQL/MinIO
publié, zéro session PostgreSQL externe et une attestation explicite de l’absence
de clients/processus autorisés à écrire. Aucun redémarrage applicatif n’est
autorisé par ce ticket.
