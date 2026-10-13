# G8.7 — Audit des codes de l’atelier de recette

Date : 2026-10-13 UTC. Aucun secret de code n’est affiché.

| ID | Libellé | Actif | Utilisations | Limite | Expiré | Révoqué |
|---:|---|---|---:|---:|---|---|
| 7 | `G8_6_R_20261013` | oui | 0 | 1 | non | non |
| 8 | `G8_6_R_20261013_RETRY` | oui | 0 | 1 | non | non |
| 9 | `G8_6_R_20261013_CODE3` | oui | 0 | 1 | non | non |
| 10 | `G8_6_R_20261013_ACTIVE` | oui | 0 | 1 | non | non |
| 11 | `G8_6_R_20261013_FINALCODE` | oui | 0 | 1 | non | non |
| 12 | `G8_6_R_20261013_ACTIVE_FINAL` | oui | 1 | 1 | non | non |

## Plan proposé, non exécuté

Révoquer uniquement les codes 7 à 11 via l’interface admin, après autorisation
distincte et double vérification de l’absence de participant en attente. Le code
12, consommé, doit être désactivé ou conservé selon la décision de conservation
des données de recette ; aucune action n’est prise dans G8.7.

État observé : six codes actifs, cinq inutilisés, un consommé, aucun code
expiré/révoqué.
