# G8.6-R — Inventaire exact des données de recette prévues

Date : 2026-10-13 UTC  
Statut : APPROUVÉ POUR CRÉATION APPLICATIVE LIMITÉE

## Périmètre prévu avant toute écriture

| Objet | Quantité prévue | Identifiant explicite / règle |
|---|---:|---|
| Atelier | 1 | libellé `G8_6_R_20261013` |
| Code d’atelier | 1 | code temporaire à usage limité, conservé hors des rapports publics |
| Participant | 1 | inscription publique via le code ; identifiant généré par l’application |
| Compte participant | 1 | créé par l’interface d’inscription |
| Compte TRANSCRIBER | 1 | `g86r-transcriber-20261013` via `/users` |
| Compte VALIDATOR | 1 | `g86r-validator-20261013` via `/users` |
| Phrases de recette | 2 | phrases actives existantes, sélectionnées sans modification historique |
| Conditions | 2 | `CLEAN` et `NOISE`, limitées aux soumissions de recette |
| Fichier audio | 2 | audio synthétique sans donnée personnelle ; deux octets WAV distincts |
| Clés d’idempotence | 3 | une par première prise, une par seconde prise, une clé rejouée |
| Export | 1 | export filtré par l’atelier de recette uniquement |

## Contraintes

- Aucun atelier, participant, compte, phrase, enregistrement ou objet historique
  ne sera réutilisé pour une écriture.
- Les phrases sont seulement référencées ; aucune phrase historique ne sera
  modifiée.
- Les données sont créées exclusivement par les interfaces applicatives
  autorisées, avec CSRF et sessions réelles.
- Aucun compte ADMIN ne sera créé.
- Les données de recette seront conservées ; aucun nettoyage n’est exécuté dans
  cette phase.
- Les identifiants et empreintes réellement produits seront ajoutés après
  création, sans secret, mot de passe, cookie ou jeton.

## État avant création

`users=21`, `participants=17`, `workshops=5`, `workshop_codes=6`,
`utterances=13`, `recordings=15`, `recording_submissions=15`,
`recording_take_counters=15`, `transcriptions=1`, `transcription_history=1`,
`audit_logs=119`, `rate_limit_buckets=1`.

MinIO : 30 objets et 5 289 708 octets selon le dernier inventaire attesté ;
empreinte d’inventaire `e2df54623dcfb1fce521c98f79a91dda4b184fe454a2bc756ffefa87a76e655c`.
