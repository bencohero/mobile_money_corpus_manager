# G8.8-B — Décision finale

## Décision : `BLOCKED`

L’outillage local et les restaurations isolées sont validés : image épinglée,
contrat schema 1/2, huit tests, backup-local, deux fixtures synthétiques et une
archive historique ont passé. La production n’a pas été modifiée.

La décision ne peut pas être `READY_FOR_BACKUP_EXECUTION_APPROVAL` car la
destination externe Kubuntu n’est pas vérifiée et `restic` n’est pas disponible.
Il manque aussi l’autorisation distincte de transfert et la preuve opérateur
de vérification SSH/dépôt chiffré. Aucun backup réel ne doit donc être exécuté.

Pour lever le blocage : installer/configurer restic sur Kubuntu, vérifier la
clé d’hôte SSH, effectuer un transfert d’une archive non réelle, vérifier les
empreintes sur Kubuntu, puis fournir l’attestation de conservation hors VPS.
