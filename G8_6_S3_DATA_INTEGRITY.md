# G8.6-S3 — Intégrité des données

## Diff final après validation HTTP

| Élément | Avant rotation | Après clôture | Diff |
|---|---:|---:|---:|
| users | 21 | 21 | 0 |
| participants | 17 | 17 | 0 |
| workshops | 5 | 5 | 0 |
| workshop_codes | 6 | 6 | 0 |
| recordings | 15 | 15 | 0 |
| recording_submissions | 15 | 15 | 0 |
| recording_take_counters | 15 | 15 | 0 |
| transcriptions | 1 | 1 | 0 |
| transcription_history | 1 | 1 | 0 |
| audit_logs | 116 | 118 | +2 LOGIN attendus |
| rate_limit_buckets | 1 | 1 | cardinalité stable |
| MinIO objets | 30 | 30 | 0 |
| MinIO octets | 5 289 708 | 5 289 708 | 0 |

Les trois comptes ADMIN restent `admin`, `benco`, `laurent`, actifs et avec les
mêmes rôles. Leurs hashes sont présents au format bcrypt ; aucun hash ni secret
n'est affiché. Les deux audits supplémentaires sont des `LOGIN` de `benco`,
cohérents avec la validation opérateur et la validation de clôture.

L'inventaire MinIO reste identique au manifeste précédent : 30 objets,
5 289 708 octets, empreinte
`e2df54623dcfb1fce521c98f79a91dda4b184fe454a2bc756ffefa87a76e655c`.

La variable runtime `ADMIN_PASSWORD` correspond à la valeur de `.env`, sans
affichage ni modification. Aucun volume, objet historique ou donnée métier n'a
été modifié.

