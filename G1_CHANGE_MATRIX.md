# G1 — Matrice des changements

| Lot / provenance | Catégorie | Dépendances | Risques principaux | Vérifications requises | État |
|---|---|---|---|---|---|
| `390cc74`, `5457b1e` | Participant, transcription, interface | modèle de langue, migration `0006` | incompatibilité avec schéma `0005`, régression UX | tests HTTP/UI, séquences multilingues sur clone restauré | À isoler |
| `5377f43` (A) | Sécurité, santé, validation, stockage | configuration, modèles existants | changement de comportement des contrôles et readiness | tests A, tests négatifs, scans, démarrage sans données réelles | À isoler |
| `9279a2a` (B) | Transcription et vérification | `0006`, modèle de transcription | concurrence, historique, FK et nullabilité | migration `0007`, tests de concurrence, historique et restauration | À isoler |
| `d34e96a` (C/D) | MinIO, audio, performance | API audio, règles de stockage, `0008` pour rate limit | range streaming, pagination, fuite de données, état rate-limit | WAV/range, export, pagination, rate-limit, tests MinIO isolés | À isoler |
| `75eb4f8` (E) | Authentification et sécurité | modèle utilisateur, middleware, audit | verrouillage, CSP/JWT, compatibilité clients | tests auth, scans, audit, tests de non-régression | À isoler |
| `cb87475`, `704f980` (F1) | Préproduction, observabilité | lots A–E stabilisés | faux positif de go/no-go, configuration divergente | checklist, scans, compose préprod | À isoler |
| `b672697` (F5) | Sauvegarde, gel d’écriture, infrastructure | services Docker et runbooks | gel incomplet, divergence avec script de `main` | tests synthétiques, revue opérateur, dry-run isolé | À comparer |
| `32edc87` (`main`) | Sauvegarde/restauration | schéma réel `0005`, archive F5A7.2 | divergence avec scripts de la branche courante | vérifier que le script retenu est celui validé F5A6–F5A8 | Référence |

## Changements déjà dans `main`

Le travail F5A6–F5A8 et les rapports associés sont présents dans `main` via `32edc87`. Les remédiations applicatives et les migrations `0006`–`0008` sont absentes de `main`. Elles ne doivent donc pas être considérées comme déployées ou validées sur la base de leur présence dans le worktree courant.

## Changements partiels ou incompatibles

Le point le plus sensible est le couplage entre modèles et migrations : la branche courante attend les champs/tables de langues, d’historique de transcription et de limitation de débit, alors que la base réelle sauvegardée a été validée au niveau `0005`. Les lots B, C/D et E ne sont donc pas intégrables fichier par fichier sans tests de schéma. Les fichiers de sauvegarde doivent rester ceux de `main` tant qu’un lot F5 distinct n’a pas été comparé et approuvé.

