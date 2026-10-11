# F.5A.5 — Décision et approbation

## Décision actuelle

**BLOQUÉ** — pas prêt pour autorisation de sauvegarde locale réelle.

La cause bloquante est factuelle : le conteneur applicatif cible
`mobile_money_corpus_manager_v0_1-app-1` est absent, donc son arrêt effectif et
l’absence d’un chemin d’écriture applicatif ne sont pas prouvés. Le script
`offline_app` refuse explicitement cette situation. Les services PostgreSQL 16
et MinIO sont actifs et sains, mais cela ne suffit pas à établir la cohérence
PostgreSQL/MinIO.

## Autorisation à obtenir après déblocage

La décision pourra devenir **PRÊT POUR AUTORISATION DE SAUVEGARDE LOCALE** si un
nouveau prévol lecture seule apporte :

1. l’application existante et arrêtée ;
2. zéro autre service ou montage sur les données cibles ;
3. zéro session/processus/client d’écriture détecté ou autorisé ;
4. DB `corpus`, bucket `mobile-money-corpus`, santé et révision `0005` confirmés ;
5. capacité et absence de sauvegarde concurrente confirmées ;
6. validation synthétique isolée du script et destination approuvée.

En attendant, aucune création de `/var/backups/mobile-money-corpus/`, aucune
sauvegarde réelle et aucun déploiement F5A4 ne sont autorisés.
