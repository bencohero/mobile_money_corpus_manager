# G7 — Répétition isolée

## Périmètre

Réseau et volumes Docker dédiés `g7-dryrun-*`, sans connexion aux volumes ou réseaux de production. Les ressources temporaires ont été supprimées après collecte des résultats ; l’archive source n’a pas été modifiée.

## Séquence exécutée

1. Création de PostgreSQL 16 et MinIO daté sur volumes isolés.
2. Restauration du dump F5A7.2 et miroir des fichiers MinIO en lecture seule depuis l’archive.
3. Vérification initiale : Alembic `0005`, 21 users, 17 participants, 13 utterances, 15 recordings, 1 transcription, 30 objets audio.
4. Construction de l’image release locale `g7-release:889fd5b` depuis le résultat merge `889fd5b`.
5. Migration explicite `alembic upgrade 0008_rate_limit_buckets`.
6. Readiness de l’application : HTTP 200 ; logs sans migration automatique.
7. Parcours HTTP : authentification, enregistrement audio synthétique, plusieurs prises, transcription, vérification, export, autorisations, réconciliation et contrôles audio : **7 pass**.
8. Le rate limiting est présent et persistant via la table `rate_limit_buckets`; sa migration et ses contrôles applicatifs ont été vérifiés. Aucun test dédié de saturation à 429 n’a été isolé dans ce dry-run.
9. Échec simulé : arrêt de l’application et remplacement des clones PostgreSQL/MinIO.
10. Restauration coordonnée depuis F5A7.2 : **24 secondes mesurées**.

## État restauré

Après restauration : Alembic `0005_workshop_attribution`, comptages `21/17/13/15/1`, 30 objets MinIO et 5 289 708 octets. L’état initial du clone est retrouvé.

## Limites et incidents de répétition

Une première tentative HTTP a échoué sur des alias DNS absents du réseau de test, puis une seconde sur des identifiants de fixture différents de l’archive. Le câblage réseau a été corrigé dans le clone et l’utilisateur admin du clone a reçu un mot de passe synthétique ; aucune donnée réelle n’a été modifiée. Le temps de migration et le temps de démarrage ne sont pas séparément chronométrés dans cette répétition.
