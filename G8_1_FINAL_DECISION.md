# G8.1 — Décision finale

## Statut : BLOCKED

Le correctif et ses tests isolés sont validés. La décision ne peut pas devenir `READY_TO_RESUME_G8` car la nouvelle sauvegarde de production et l’attestation externe Kubuntu/restic ne sont pas présentes. `FAILED` ne s’applique pas : aucun échec de capture de production n’a été provoqué.

Conditions de passage à `READY_TO_RESUME_G8` :

- une nouvelle archive identifiée, avec dump PostgreSQL, objets MinIO, manifestes, `SHA256SUMS`, `COMPLETE` et `COMPLETION.SHA256` validés;
- l’attestation externe correspond exactement à cette archive;
- le snapshot restic, `restic check`, le test de restauration et la conservation hors VPS de la clé sont attestés;
- décision opérateur explicite après réception de l’attestation.

Aucune migration, aucun redémarrage applicatif, aucun push distant, aucune suppression de volume et aucune ouverture publique n’ont été effectués.
