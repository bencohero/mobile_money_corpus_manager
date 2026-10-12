# G4 — Validation fonctionnelle

## Résultats automatisés

La suite candidate complète a donné : **158 tests réussis, 1 ignoré, 8 warnings**, en 145,87 s. Le test ignoré concerne la validation Docker depuis le conteneur, explicitement non disponible; la validation Compose a été exécutée depuis l’hôte.

Les tests JavaScript d’interface ont donné **10 réussis, 0 échec**. Ils couvrent les identifiants sémantiques, l’état désactivé, l’ergonomie responsive participant, l’inscription, la capture audio, l’idempotence, la sélection de phrase et l’espace transcripteur.

La suite Python couvre les parcours d’administration/authentification, participant, ateliers multilingues, prises multiples, audio, transcription, vérification, export, autorisations, CSRF/IDOR, concurrence et limitation de débit. Les contrôles MinIO et de réconciliation ont également réussi.

## Vérifications d’exploitation

- `/ready` : HTTP 200 avec `status=ready`.
- Redémarrage PostgreSQL, MinIO et application : réussi.
- Schéma après redémarrage : `0008_rate_limit_buckets`.
- Comptages après tests : 21 participants, 19 enregistrements, 4 transcriptions, 8 historiques, 1 bucket; ces ajouts correspondent aux scénarios de test et ne remplacent pas les comptages de référence pré-tests.
- Réconciliation PostgreSQL/MinIO : `[]`.
- Objets MinIO après les scénarios : 38; les 30 objets de référence étaient présents avant les tests.

## Limite manuelle

Aucun navigateur graphique n’était disponible dans cette exécution. La validation visuelle Chrome Android aux largeurs 320/360/390/412 px et desktop reste donc à réaliser manuellement en préproduction avant promotion. Les tests JavaScript responsive automatisés sont verts, mais ne remplacent pas cette vérification visuelle.
