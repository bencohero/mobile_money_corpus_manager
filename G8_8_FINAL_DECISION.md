# G8.8 — Décision finale

## Décision : NOT_READY_FOR_G8_8_EXECUTION_APPROVAL

### Contrôles réussis

- release, Alembic, volumes, réseau interne et healthchecks vérifiés ;
- espace VPS disponible vérifié ;
- codes 7–12 et absence d’inscription en attente inventoriés ;
- procédure de gel, critères d’intégrité, rollback et tests isolés préparés.

### Réserves bloquantes

1. aucune destination externe de sauvegarde n’est actuellement attestée ;
2. le format produit par `backup_local.sh` n’est pas aligné avec
   `scripts/restore.sh` ;
3. aucune restauration coordonnée PostgreSQL/MinIO isolée n’est encore prouvée.

### Actions nécessitant une nouvelle autorisation

- exécuter le backup production et le gel contrôlé ;
- restaurer PostgreSQL/MinIO dans des cibles isolées ;
- corriger ou approuver l’alignement des scripts backup/restore ;
- révoquer les codes 7–11 et fermer le code 12 ;
- exécuter les tests de seuil rate limiting ;
- modifier Traefik, ouvrir publiquement ou dégeler les écritures.

L’état final de production est inchangé : pas d’ouverture, pas de révocation,
pas de suppression, pas de migration, pas de redémarrage et pas de push distant.
