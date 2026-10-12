# G3 — Mapping des commits

## Références

| Référence | Rôle examiné | Traitement G3 |
|---|---|---|
| `main@32edc87` | base de production connue et sauvegarde F5A6–F5A8 | base de `g3-candidate` |
| `390cc74` | écran d’enregistrement participant | déjà dans `main` |
| `5457b1e` | interface et atelier multilingues | intégré dans le commit candidate |
| `5377f43` | remédiation A / sécurité de base | intégré |
| `9279a2a` | transcription, vérification, versions | intégré |
| `d34e96a` | audio, export, pagination, rate limiting | intégré |
| `75eb4f8` | remédiation E | intégré |
| `cb87475` | préproduction et observabilité | intégré |
| `704f980` | validation F1 | intégré hors artefacts F5 protégés |
| `b672697` | état source G2/F5 | examiné, intégré sélectivement |

## Résultat Git

Les changements sélectionnés sont regroupés dans `7d5c180`. Aucun cherry-pick aveugle n’a été
réalisé. Le mapping est fonctionnel : migrations → modèles → services → routes/templates →
tests, avec vérification sur un clone de la sauvegarde F5A7.2.

