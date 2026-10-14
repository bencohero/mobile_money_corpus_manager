# G8.6-R — Tests fonctionnels

Date : 2026-10-13 UTC  
Décision de test : PASS avec réserve documentaire sur les codes non consommés.

## Résultats

| Test | Résultat | Preuve |
|---|---|---|
| Atelier dédié et code applicatif | PASS | atelier id 6, libellé `G8_6_R_20261013` |
| Inscription participant | PASS | `MOS_018`, HTTP 200 |
| Code invalide | PASS | parcours public refusé ; HTTP 400 |
| Deux prises même phrase/condition | PASS | recordings 16/17, `T01/T02` |
| Numérotation indépendante | PASS | recording 18, autre phrase `T01` |
| Audio distinct | PASS | SHA-256 différents pour les trois WAV métier |
| Affichage Mes enregistrements | PASS | accès participant `/recordings` testé avec session réelle |
| Rejeu idempotent | PASS | clé `g86r-recording-20261013-a` retourne encore recording 16 |
| Transcription | PASS | recording 16, HTTP 303 |
| Correction et historique | PASS | version 1 vers 2, quatre lignes d’historique totales |
| Validation | PASS | validator, `VERIFIED`, HTTP 303 |
| Export limité | PASS | atelier 6 uniquement, archive ZIP valide |

Les prises de recette sont :

- `MOS_018_MOS_I01_U001_CLEAN_T01` — id 16 — vérifiée ;
- `MOS_018_MOS_I01_U001_CLEAN_T02` — id 17 — enregistrée ;
- `MOS_018_MOS_I02_U001_CLEAN_T01` — id 18 — enregistrée.

Les données historiques n’ont pas été modifiées.
