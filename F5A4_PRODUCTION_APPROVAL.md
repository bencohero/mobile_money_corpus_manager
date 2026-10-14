# F5A4 — fiche d’autorisation de déploiement

## Décision

**PRÊT POUR AUTORISATION DE DÉPLOIEMENT**, sous réserve des approbations distinctes listées ci-dessous. Cette décision n’autorise ni gel réel ni sauvegarde réelle.

## Cibles

| Élément | Valeur |
|---|---|
| Image active | `sha256:c2e3e50e3e74d2901cbe5308b77ac9c4d0dab660668b836f6bda4b23a49f2467` |
| Image candidate | `sha256:b1fb0b134d00cdcd02acab3c020163fec94f2cfb8e0bf3042087a8f5610de778` |
| Schéma | `0005_workshop_attribution (head)` |
| PostgreSQL | service `mobile_money_corpus_manager_v0_1-db-1`, `postgres:16-alpine` |
| MinIO | service `mobile_money_corpus_manager_v0_1-minio-1`, release `2025-04-22T22-12-26Z` |
| Bucket | `mobile-money-corpus` |
| Destination locale proposée | `/var/backups/mobile-money-corpus/`, à créer après approbation |

## Diff applicatif

La candidate provient de l’extraction de l’image active `0005`; elle ajoute le middleware `write_freeze`, son état partagé atomique, le contrôle `check`, et le comportement fail-closed sur état JSON illisible. Aucun changement métier, migration ou dépendance applicative n’est ajouté. Le runtime reste Python 3.12 avec les dépendances observées.

## Impact et durée

Le remplacement de l’ancienne image exige une indisponibilité contrôlée de l’application, car l’ancienne image ne possède pas de gate de gel. Les services PostgreSQL, MinIO et Traefik restent inchangés. Prévoir 2–5 minutes de remplacement, puis une fenêtre de sauvegarde gelée selon la taille observée et la capacité de `/var/backups/mobile-money-corpus/`.

## Critères d’arrêt immédiat

- `alembic current` différent de `0005_workshop_attribution (head)`.
- Digest candidat différent, image absente ou montage d’état incorrect.
- Candidate non saine, état illisible, compteur actif non nul après délai.
- Modification détectée sur DB, MinIO, Traefik ou volumes de données.
- Archive sans manifestes valides, sans `COMPLETE`, ou comptages PostgreSQL/MinIO incohérents.

## Approbations distinctes requises

- Autorisation de créer `/var/lib/mobile-money-corpus/write-freeze` avec propriétaire UID `10001`.
- Autorisation de remplacer uniquement `app` et d’accepter l’indisponibilité 2–5 minutes.
- Autorisation séparée de créer/utiliser `/var/backups/mobile-money-corpus/`.
- Autorisation explicite de geler les écritures et de lancer la sauvegarde réelle.
- Approbation séparée de tout rollback vers l’ancienne image pendant un incident.

## Reprise exigée

Après validation intégrale de la sauvegarde : `check --phase FROZEN`, `unfreeze`, `check --phase OPEN`, contrôle `/ready`, contrôle de la révision Alembic depuis le conteneur `app`, et confirmation que DB/MinIO/Traefik sont restés inchangés.
