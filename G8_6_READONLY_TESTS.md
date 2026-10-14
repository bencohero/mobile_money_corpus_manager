# G8.6 — Tests sans écriture métier

## Résultats

| Test | Résultat observé |
|---|---|
| `/ready` avec hôte approuvé | 200, `{"status":"ready"}` |
| `/health` avec hôte approuvé | 200, `{"status":"ok"}` |
| Absence de session sur `/recordings`, `/participants`, `/users`, `/audio/1` | 401 |
| Page racine sans session | 303 vers `/login` |
| Hôte `evil.invalid` | 400 `Invalid host header` |
| Route inconnue | 404 |
| Paramètre requis absent sur `next-take` | 422 |
| Code d'atelier invalide | 400 |
| Pagination invalide non authentifiée | 401 avant accès aux données |
| Audio autorisé avec jeton participant propriétaire | 200 |
| Audio d'un autre participant | 403 |
| Audio avec rôle transcripteur | 200 |
| Audio avec plage `bytes=0-15` | 206, 16 octets |
| Plage hors limites | 416, sans corps |

## Contrôle des rôles par jetons de test en lecture

Les jetons ont été générés uniquement pour des requêtes GET, sans appel de
`POST /login` et donc sans ajout d'audit de connexion.

| Rôle | Autorisé | Refusé |
|---|---|---|
| ADMIN | recordings, participants, users, record, transcribe, export, audio, historique | aucun refus attendu sur ces routes |
| PARTICIPANT | recordings, record, audio de son participant | participants, users, transcribe, export, audio IDOR, historique IDOR |
| TRANSCRIBER | recordings, transcribe, audio, historique | participants, users, record, export |

Le participant utilisé pour l'IDOR n'était pas propriétaire de l'enregistrement
1 : `/audio/1` a répondu 403. Le participant propriétaire a reçu 200.

## Limite de portée

Les tests de transcription, vérification, export administratif et plusieurs
prises n'ont été exercés qu'au niveau de l'autorisation GET, pas par mutation.
Les écritures métier restent à exécuter uniquement après approbation explicite
d'une recette dédiée et d'une méthode de nettoyage démontrée.

