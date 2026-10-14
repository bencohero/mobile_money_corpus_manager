# G1 — Inventaire Git

Date de l’audit : 2026-10-12. Audit réalisé en lecture seule.

## État constaté

- Branche courante : `remediation-a-stabilisation-securite`.
- HEAD : `b672697a34196841cd5fd9714520166b6edb345b` (`f5`).
- `main` et `origin/main` : `32edc8716869f67aee0c09123a93b0e454012f33` (`update backup script`).
- `dev` : `5457b1e` (`Implement multilingual workshop`).
- Worktree secondaire : `/tmp/mobile-money-corpus-manager-d34e`, détaché sur `d34e96a3f35ee267a7c62a1e79fe313209ba53e2`.
- Modifications locales préexistantes conservées : `.gitignore` et `graphify-out/cache/last_query_stamp`.
- `git diff --check` ne signale pas d’erreur. Aucun merge, cherry-pick ou suppression n’a été effectué.

## Provenance des lots

| Révision | Lot | Contenu principal | Présent dans `main` ? |
|---|---|---|---|
| `390cc74` | Interface participant | écran d’enregistrement participant | Non |
| `5457b1e` | Multilingue | identité/langue et migration `0006` | Non |
| `5377f43` | Remédiation A | sécurité applicative, santé, validations, stockage | Non |
| `9279a2a` | Remédiation B | transcription, versions, historique, migration `0007` | Non |
| `d34e96a` | Remédiations C/D | audio streaming, export, pagination, limitation de débit, migration `0008` | Non |
| `75eb4f8` | Remédiation E | authentification, CSP/JWT, audit, sauvegarde/restauration | Non |
| `cb87475` | Lot F | préparation préproduction | Non |
| `704f980` | F1 | contrôles VPS et scans de release | Non |
| `b672697` | F5 | gel des écritures, infrastructure candidate, sauvegarde locale et runbooks | Non |
| `32edc87` | F5A6–F5A8 | script/rapports de sauvegarde et artefacts de validation | Oui, dans `main` |

`main` est donc la base production connue, avec le travail F5 de sauvegarde déjà publié par `32edc87`, mais sans les remédiations A–F ni les migrations `0006` à `0008`.

## Écart de branches

- `main...dev` : `1` commit uniquement dans `main`, `2` uniquement dans `dev`.
- `main...remediation-a-stabilisation-securite` : `1` commit uniquement dans `main`, `9` uniquement dans la branche courante.
- La branche courante est une chaîne linéaire basée sur `dev`, puis A, B, C/D, E, F1 et F5. Elle n’est pas une simple copie de `main`.

## Préservation et limites

Les fichiers personnels et les sauvegardes F5A7.2 n’ont pas été ouverts, modifiés ou déplacés dans cet inventaire. L’existence d’un worktree détaché a été relevée ; il doit rester intact jusqu’à décision explicite. Les tests fonctionnels complets n’ont pas été assimilés à une preuve d’intégration production.

