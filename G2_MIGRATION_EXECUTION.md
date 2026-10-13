# G2 — Exécution isolée des migrations 0006 à 0008

## Périmètre

- Production de référence : `main@32edc87`.
- Candidate exécutée : `remediation-a-stabilisation-securite@b672697`.
- Sauvegarde : `/home/sangouman/mobile-money-corpus-backups/20261011T133947Z`.
- Clone Docker : projet `g2-clean`, réseau `g2-migration-network`.
- Volumes dédiés : `g2-migration-pgdata`, `g2-migration-miniodata`, sans montage de production.

L’archive originale n’a pas été modifiée. Aucun service de production, bucket réel, merge,
cherry-pick ou downgrade n’a été utilisé.

## Préparation et restauration

Le manifeste indique `COMPLETE`, `coherent=true`, schéma initial
`0005_workshop_attribution`, 30 objets capturés et 30 objets référencés. La vérification
`sha256sum -c manifests/SHA256SUMS` a validé tous les fichiers PostgreSQL, manifestes et
30 objets MinIO.

Le dump PostgreSQL a été restauré dans PostgreSQL 16 isolé et les 30 objets dans un bucket
MinIO de test. Avant migration : 21 utilisateurs, 17 participants, 15 enregistrements,
1 transcription; les identifiants `MOS_001` à `MOS_017` et leurs liens utilisateur étaient
cohérents.

Un snapshot PostgreSQL a été créé avant chaque étape :

| Point | Révision | Preuve snapshot |
|---|---|---|
| initial | 0005 | `snapshot_0005.dump`, SHA-256 `c9aea7d8af0bb579f33e9988f545dc62232d32bdb603719fdab2f336d0e8818f` |
| avant 0007 | 0006 | `snapshot_0006.dump`, SHA-256 `2db241155cfe469308fe443eb0af0e9dc156b67e1dcdef0658ab8ae3d3005476` |
| avant 0008 | 0007 | `snapshot_0007.dump`, SHA-256 `7667567ca47957c81b0699f78037616466241a0e6106cf671010337a95fd3805` |

## Résultats

1. `0006_multilingual_participant_identity` : succès. 17 participants conservés; quatre
   langues canoniques créées; séquences initialisées à `MOS=17`, `DYU=0`, `FR=0`, `FUL=0`;
   aucune identité renommée.
2. `0007_integrity_and_transcription_versions` : diagnostics préalables à zéro anomalie;
   succès. 17 participants, 15 enregistrements et 1 transcription conservés; version de
   transcription à 1; 1 entrée d’historique `BASELINE`; FK `recording_id` passée à
   `ON DELETE SET NULL` et nullable.
3. `0008_rate_limit_buckets` : succès. Révision finale
   `0008_rate_limit_buckets (head)`; table, clé primaire composite, index d’expiration et
   contrainte `event_count >= 0` présents.

Les downgrades des trois migrations n’ont pas été tentés, conformément au code qui impose
une restauration coordonnée plutôt qu’un downgrade destructif.

## Anomalies non bloquantes

La première exécution applicative a rencontré 11 échecs HTTP `401` car les comptes restaurés
utilisaient leurs mots de passe historiques. Le compte `admin` du clone uniquement a été
réinitialisé avec le secret de test déjà injecté; aucune donnée de l’archive ni production
n’a été touchée. La seconde exécution complète a passé 158 tests.

