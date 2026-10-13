# G2 — Intégrité des données

## Référence sauvegarde

La sauvegarde F5A7.2 est cryptographiquement valide et cohérente : 30 objets capturés,
30 référencés, aucun objet manquant ni orphelin. Le dump annonce le schéma
`0005_workshop_attribution`.

## Diagnostics avant 0007

Les six diagnostics exécutés avant toute écriture de 0007 ont tous retourné zéro : langues
d’atelier inconnues, langues de participants inconnues ou nulles, participants orphelins,
enregistrements orphelins, soumissions orphelines et mismatch langue atelier/participant.

## Conservation avant tests applicatifs

| Contrôle | Résultat |
|---|---|
| Participants | 17 → 17 |
| Enregistrements | 15 → 15 |
| Transcriptions | 1 → 1 |
| Identités `MOS_001`…`MOS_017` | conservées, aucun renommage |
| Versions | 1 transcription à version 1 |
| Historique | 1 baseline pour 1 transcription |
| Objets MinIO restaurés | 30 |
| Réconciliation DB/MinIO | aucune anomalie après validation applicative |

Les tests applicatifs ont volontairement créé des données de test dans le clone; leur état
final n’est donc pas utilisé comme preuve de conservation de la sauvegarde. La réconciliation
finale reste propre (`[]`) et les objets créés par les scénarios ont été gérés par les tests.

## Concurrence et expiration

Les tests de concurrence de prises, d’idempotence et de limitation ont passé. La structure
des buckets permet la mise à jour atomique par clé composite et le nettoyage des lignes
expirées; aucun bucket n’était présent avant les tests. Les suppressions et références de
transcription ont été exercées sans violation de FK.

