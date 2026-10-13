# G8.3 — Validation de la sauvegarde

## Contrôles PASS

| Contrôle | Résultat |
|---|---|
| `pg_restore --list` dans le conteneur PostgreSQL | PASS, 144 lignes TOC |
| Liste PostgreSQL du manifeste | PASS, correspondance exacte |
| Révision Alembic | `0005_workshop_attribution` |
| Objets MinIO source / capturés | `30 / 30` |
| Références audio / objets capturés | `30 / 30`, aucun manque, aucun orphelin |
| Comptages | users 21; participants 17; utterances 13; recordings 15; transcriptions 1; audit_logs 116 |
| `manifests/SHA256SUMS` | PASS, 41 entrées |
| `COMPLETE` | PASS |
| `COMPLETION.SHA256` | PASS avec nom `COMPLETE` |
| `MANIFEST.json` | PASS, format `f5a6-v1`, objets `30/30` |

Empreintes principales :

```text
manifests/SHA256SUMS  041a3f62994f3839f1b35a4d758ac1f0ca645ac1e3bacd6a856340c172ff20a8
COMPLETE              2dea7091c72aa35dca1869737f7e8c4471019a8069e01ffe171a6aef57b83f1c
COMPLETION.SHA256     8963398f9ac5eaeac98e318e4f5dd5328f9e627d8c016af508025d9a6202a4e6
postgres/corpus.dump  c7d34a272f22649ea3cb6af37ad2bb12a7ab7233c715a61a2a75f4509f3aa24d
```
