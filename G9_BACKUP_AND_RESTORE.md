# G9 — Sauvegarde et restauration

## État

PUBLIC_OPEN_NO_GO. Aucune sauvegarde finale, aucun gel, aucun restore et aucun
dégel n’ont été exécutés dans G9.

## Précontrôles observés

- application : mobile_money_corpus_manager_g8_5_r-app ;
- release : 8f688e8d312b2f0afb30f8a2766a6f8f25e5e5d6 ;
- Alembic : 0008_rate_limit_buckets ;
- PostgreSQL : accepting connections ;
- MinIO : health live réussi ;
- application interne : /ready et /health réussis avec Host approuvé ;
- gel : OPEN, active_writes=0, epoch=0 ;
- sessions PostgreSQL autres que le contrôle : 1 ;
- outillage G8.8-B : présent.

## Blocages

La destination restic/Kubuntu n’est pas exploitable depuis cet hôte : restic est
absent et aucun endpoint SSH Kubuntu réel n’est configuré. La sauvegarde finale
ne peut donc pas être capturée puis transférée et vérifiée.

La phase de gel n’a pas été engagée. Aucun volume ou service de production n’a
été modifié. La condition BACKUP_AND_RESTORE_VALIDATED n’est pas atteinte.

