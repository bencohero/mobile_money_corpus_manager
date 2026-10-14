# G8.6 — Tests avec écritures contrôlées

## Statut

**NON EXÉCUTÉ — autorisation et périmètre de nettoyage non validés.**

Conformément aux restrictions G8.6, aucun dégel général, aucune création de
compte, aucun upload audio, aucune transcription, vérification, export ou
suppression n'a été effectué.

## Matrice de recette à autoriser ultérieurement

| Scénario | Écriture attendue | Nettoyage requis |
|---|---|---|
| Inscription participant | user, participant, association atelier, audit | supprimer uniquement les lignes dédiées après preuve FK |
| Enregistrement | submission, recording, take counter, deux objets MinIO | supprimer les lignes et les deux objets par identifiants exacts |
| Idempotence / prises | compteur, soumissions et éventuelles nouvelles prises | vérifier les clés d'idempotence avant nettoyage |
| Transcription / vérification | transcription, historique, audit | conserver l'historique si la politique l'impose |
| Rate limit | `rate_limit_buckets` | attendre expiration ou supprimer la seule clé hachée après preuve |
| Export administratif | audit et fichier temporaire/zip | identifier le chemin exact et supprimer seulement l'artefact dédié |

Avant exécution, il faut fournir des identités distinctes, un code d'atelier de
recette, des phrases dédiées, un pré-manifeste DB/MinIO et une approbation
explicite du périmètre. Aucun test de charge ni suppression massive ne doit
être ajouté à cette matrice.

