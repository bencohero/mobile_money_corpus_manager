# G5.1 — Validation responsive

| Largeur | Pages contrôlées | Overflow | Focus | Micro simulé |
|---:|---|---|---|---|
| 320 px | login, inscription, dashboard, corpus, audio, admin, export | OK | OK | OK |
| 360 px | mêmes parcours | OK | OK | OK |
| 390 px | mêmes parcours + upload simulé | OK | OK | OK + upload OK |
| 412 px | mêmes parcours | OK | OK | OK |
| 1280 px | mêmes parcours | OK | OK | OK |
| 1440 px | mêmes parcours | OK | OK | OK |

Contrôles DOM automatisés : `document.documentElement.scrollWidth <= innerWidth`, aucun chevauchement bloquant constaté, boutons et formulaires visibles, états désactivés vérifiés pendant la capture audio. Les captures complètes sont indexées dans `G5_1_SCREENSHOTS_INDEX.md`.
