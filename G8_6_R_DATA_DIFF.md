# G8.6-R — Diff d’intégrité avant/après

| Objet | Avant | Après | Diff | Justification |
|---|---:|---:|---:|---|
| users | 21 | 24 | +3 | 2 comptes opérateurs recette + participant |
| participants | 17 | 18 | +1 | `MOS_018` |
| workshops | 5 | 6 | +1 | atelier recette id 6 |
| workshop_codes | 6 | 12 | +6 | un code actif consommé, cinq codes non consommés conservés après erreurs de capture |
| participant_registration_requests | 0 | 1 | +1 | inscription idempotente recette |
| recordings | 15 | 18 | +3 | recordings 16–18 |
| recording_submissions | 15 | 18 | +3 | trois clés de soumission |
| recording_take_counters | 15 | 17 | +2 | une séquence par phrase ; prises 1/2 et 1 |
| transcriptions | 1 | 2 | +1 | transcription recording 16 |
| transcription_history | 1 | 4 | +3 | création, correction, validation |
| audit_logs | 119 | 154 | +35 | authentifications, créations et opérations de recette/export |
| rate_limit_buckets | 1 | 1 | 0 | cardinalité technique stable |
| MinIO objets | 30 | 36 | +6 | raw + normalized pour trois prises |
| MinIO octets | 5 289 708 | 5 482 176 | +192 468 | audio synthétique recette |

Empreinte inventaire MinIO après :
`36bbac826b309e51dfbe56459a2081d76f4cdc5fd16835fcfa8b8a377f26d123`.

Aucun objet historique n’a été supprimé ou modifié. Les écarts correspondent
aux opérations listées ci-dessus.
