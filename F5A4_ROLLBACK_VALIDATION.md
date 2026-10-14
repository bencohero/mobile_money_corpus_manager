# F5A4 — validation des incidents et du retour arrière

## Règle de sécurité

Le retour automatique vers l’ancienne image est interdit pendant `DRAINING` ou `FROZEN`. L’ancienne image ne contient pas le middleware et ignorerait le fichier d’état ; la démarrer dans cette phase rouvrirait silencieusement les écritures. En cas d’échec, conserver l’indisponibilité, préserver l’état partagé et réparer ou relancer la candidate.

## Scénarios contrôlés

| Scénario | Contrôle / résultat attendu |
|---|---|
| Échec de démarrage candidate | `docker inspect` doit montrer `unhealthy`/arrêt ; aucun retour automatique à l’ancienne image ; arrêt d’exploitation. |
| Montage absent ou non inscriptible | Le probe `docker run --user 10001:10001 ... check` échoue ; exposition interdite. |
| Redémarrage en `DRAINING` | L’état persiste en `DRAINING`; ne pas forcer `FROZEN`; reprendre après lecture du compteur ou abandon contrôlé. |
| Redémarrage en `FROZEN` | L’état persiste en `FROZEN`; les mutations restent refusées jusqu’à `unfreeze`. |
| JSON corrompu/perdu | Candidate F5A4 : contrôle en erreur, état non converti en `OPEN`, mutations refusées/maintenance à traiter. |
| Sauvegarde échouée après gel | Aucun `COMPLETE`; conserver `.incomplete`; rester gelé jusqu’à décision opérateur. |
| Retour arrière pendant gel | Refusé. Le rollback exige d’abord une reprise sûre ou un mécanisme de blocage externe approuvé séparément. |

## Preuves disponibles

- Tests F5A3 : deux processus, redémarrage pendant `FROZEN`, timeout de drainage, capture synthétique PostgreSQL/MinIO, échec MinIO et restauration isolée.
- Test F5A4 isolé : la candidate `f5a4-candidate:0005-freeze` retourne code 2 avec `WriteFreezeError: unreadable write-freeze state` sur JSON invalide, puis accepte un état `FROZEN` valide sans dépendre d’une epoch particulière.
- Aucun conteneur de production n’a été redémarré, gelé ou remplacé.

## Procédure de rollback autorisable

1. Déclarer l’incident et confirmer la phase via la candidate si elle répond.
2. Si `DRAINING`/`FROZEN`, ne pas démarrer l’ancienne image.
3. Conserver les journaux opérationnels sans secrets ni données personnelles.
4. Réparer le montage ou redéployer le même digest candidate.
5. Si un rollback ancien est indispensable, obtenir une approbation distincte pour une indisponibilité complète et vérifier qu’aucun gel de sauvegarde n’est actif ; le démarrage ancien ne doit jamais être automatique.
6. Après retour sain, valider `0005`, les conteneurs DB/MinIO inchangés et la reprise explicite des écritures.

