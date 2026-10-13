# G8 — Smoke test production

Statut : **NON EXÉCUTÉ**.

Aucun compte de test n’a été utilisé en production et aucune donnée historique n’a été modifiée. Les parcours suivants restent à valider après migration et démarrage contrôlés : connexion/session, permissions, enregistrement audio, plusieurs prises, transcription, vérification, export, rate limiting, réconciliation PostgreSQL/MinIO et absence d’erreurs critiques.

Les essais G7 sur clone isolé ne constituent pas une recette production. Ils ont validé les parcours applicatifs sur une restauration séparée, mais ne remplacent ni la sauvegarde externe immédiate ni les contrôles post-migration de G8.

Résultat G8 : aucun endpoint public ouvert, aucun test de fumée production, aucun dégel d’écriture.
