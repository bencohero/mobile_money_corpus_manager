# G8 — Vérification de la sauvegarde pré-migration

## Capture locale

Une capture immédiate a été réalisée sans arrêt, démarrage ou modification des conteneurs de données :

- Archive : `/home/sangouman/mobile-money-corpus-backups/20261012T233614Z`
- État applicatif : `APP_ABSENT`
- Révision capturée : `0005_workshop_attribution`
- PostgreSQL : dump custom non vide, `pg_restore --list` valide, 144 entrées TOC
- MinIO : 30 objets source, 30 objets capturés
- Cohérence PostgreSQL/MinIO : 30 références, aucune référence manquante, aucun objet orphelin
- SHA-256 : `manifests/SHA256SUMS` validé ; marqueur `COMPLETE` validé
- Client MinIO : image locale approuvée, binaire SHA-256 `83938eded435e7c28c397ece1dc590b2a79626dd9354aae2107060fec559ae2b`

Comptages sauvegardés : users 21, participants 17, utterances 13, recordings 15, transcriptions 1, audit_logs 116.

## Réserve d’exécution

La première exécution du script versionné a échoué lors de la génération de `SHA256SUMS` à cause d’un séparateur NUL mal quoté ; elle a laissé l’artefact incomplet `/home/sangouman/mobile-money-corpus-backups/20261012T233537Z.incomplete`. La capture complète ci-dessus a été produite par une copie temporaire hors dépôt corrigeant uniquement ce défaut. Le script versionné n’a pas été modifié.

Cette réserve doit être corrigée et revalidée avant une opération de production considérée comme pleinement conforme au mécanisme validé.

## Attestation externe manquante

- `restic` n’est pas installé/disponible.
- Aucun dépôt restic configuré n’a été trouvé.
- Aucun montage Kubuntu, SSHFS, NFS, CIFS ou destination externe attestable n’est présent.
- Aucune copie indépendante n’a donc été transférée ni restaurée.

La sauvegarde historique F5A7.2 n’est pas utilisée comme substitut. Point d’arrêt obligatoire atteint : **aucune migration autorisée**.
