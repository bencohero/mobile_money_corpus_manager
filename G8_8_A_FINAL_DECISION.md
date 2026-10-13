# G8.8-A — Décision finale

## Décision : BACKUP_RESTORE_CONTRACT_VALIDATED

Le contrat est validé pour les schemas 1 et 2 : les producteurs synthétiques,
les sauvegardes historiques, les refus d’intégrité et les restaurations
coordonnées PostgreSQL/MinIO isolées ont réussi.

### Conditions avant usage opérationnel

1. intégrer `scripts/restore.sh` depuis ce worktree dans une release approuvée ;
2. fournir une image d’outillage contenant `python3`, `pg_restore` et `mc`
   épinglé par digest ;
3. aligner et revalider le Dockerfile d’outillage, dont l’URL `mc` actuelle
   retourne 410 ;
4. obtenir une autorisation distincte pour tout backup ou restore production ;
5. refaire un contrôle release/Alembic, gel, destination externe et rollback
   avant exécution réelle.

Aucun service, volume, secret, code de recette ou route publique de production
n’a été modifié. Aucun push distant n’a été effectué.
