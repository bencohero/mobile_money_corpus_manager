# G8.7 — Matrice GO / NO-GO préouverture

## Décision actuelle : NO-GO

| Domaine | État | Condition de passage |
|---|---|---|
| Codes recette | RÉSERVE | révoquer 7–11 après autorisation ; décider du code 12 |
| Données recette | PASS inventaire | plan de conservation/nettoyage approuvé séparément |
| Rate limiting | PASS configuration / tests à préparer | tests négatifs limités autorisés et documentés |
| Réseau / Host / TLS | PASS fermé | nouvelle validation après activation explicite de la route |
| Cookies / CSRF / sessions | PASS recette | conserver les réglages vérifiés |
| Sauvegarde | NO-GO | backup production frais + restauration coordonnée PostgreSQL/MinIO |
| Rollback | NO-GO | preuve opérationnelle sur cible isolée |
| Gel des écritures | RÉSERVE | décision explicite sur le mécanisme de gel avant ouverture |

## Actions nécessitant une nouvelle autorisation

- révocation des codes inutilisés ;
- suppression éventuelle des données de recette ;
- exécution de tests rate limiting produisant des écritures ;
- backup production et restauration isolée ;
- modification Traefik, activation publique ou dégel général ;
- toute modification de secret, migration, redémarrage ou push distant.

Tant que les deux contrôles sauvegarde/rollback restent NO-GO, l’ouverture
publique n’est pas autorisée.
