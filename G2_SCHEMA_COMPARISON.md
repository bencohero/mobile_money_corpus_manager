# G2 — Comparaison schéma 0005 → 0008

| Objet / propriété | 0005 restauré | Après 0006 | Après 0007 | Après 0008 |
|---|---:|---:|---:|---:|
| Révision Alembic | 0005 | 0006 | 0007 | 0008 (head) |
| participants | 17 | 17 | 17 | 17 avant tests applicatifs |
| recordings | 15 | 15 | 15 | 15 avant tests applicatifs |
| transcriptions | 1 | 1 | 1 | 1 avant tests applicatifs |
| languages | absent | 4 | 4 | 4 |
| participant_language_sequences | absent | 4 (`MOS=17`) | 4 | 4 |
| participant_registration_requests | absent | 0 | 0 | 0 |
| transcription_history | absent | absent | 1 baseline | 1 |
| rate_limit_buckets | absent | absent | absent | 0 |

## Contraintes vérifiées

- Les identités historiques sont conservées et les identifiants publics restent uniques.
- `participants.language_code` est non nul, avec FK vers `languages(code)` et `ON DELETE RESTRICT`.
- `workshops.language_code` est nullable pour préserver les ateliers historiques, avec FK vers
  `languages(code)`.
- `transcriptions.version` est non nul, avec valeur par défaut 1.
- `transcriptions.recording_id` est nullable avec FK `ON DELETE SET NULL`.
- `transcription_history` référence strictement la transcription et l’auteur.
- `rate_limit_buckets` possède la PK `(bucket_key, scope)`, l’index `expires_at` et le check
  `event_count >= 0`.

Les séquences d’identité PostgreSQL et les clés étrangères ont été inspectées après chaque
étape; aucune erreur de contrainte n’a été observée.

