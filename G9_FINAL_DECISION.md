# G9 — Décision finale

## Décision : PUBLIC_OPEN_NO_GO

L’ouverture publique n’est pas autorisée par les preuves présentes.

## Raisons bloquantes

- sauvegarde finale réelle non produite ;
- copie externe restic non vérifiée ;
- restauration isolée non exécutée ;
- route HTTPS publique absente : HTTP 404 ;
- conteneur applicatif actif hors réseau frontend et sans labels Traefik ;
- dashboard/API Traefik insecure exposé sur 0.0.0.0:8090 ;
- anomalies Traefik et CrowdSec dans les journaux ;
- capacité mémoire faible et aucune swap, à surveiller avant changement ;
- le checkout courant est au commit b672697, pas à la release attendue ;
- le Compose du dépôt reconstruit l’application depuis ce checkout au lieu de
  pinner l’image release ;
- la configuration Compose résolue contient des valeurs de secrets par défaut
  ou de démonstration, donc elle ne peut pas être utilisée telle quelle.

## État réel préservé

- application sur la release attendue ;
- Alembic 0008 ;
- PostgreSQL et MinIO sains en interne ;
- état d’écriture OPEN avec active_writes=0 ;
- accès public applicatif non fonctionnel ;
- aucun changement de production, secret, route, réseau, volume ou données.

## Actions correctives obligatoires

1. Fournir et vérifier la destination Kubuntu/restic.
2. Produire et valider la sauvegarde schema 2.
3. Restaurer isolément et obtenir une réconciliation vide.
4. Utiliser un checkout exact de la release ou un override qui référence
   l’image release sans reconstruire depuis ce checkout.
5. Corriger la configuration Traefik et retirer l’exposition dashboard insecure.
6. Ne jamais utiliser les valeurs de secrets résolues par le Compose actuel.
7. Revalider TLS, route unique, protections et smoke tests.
8. Reprendre la décision uniquement avec preuves complètes.

Ne pas déclarer PUBLIC_OPEN_GO et ne pas ouvrir les écritures générales.
