# G9 — Traefik et ouverture

## Résultat

NON EXÉCUTÉ — ouverture interdite par les échecs de précontrôle.

L’application courante ne possède pas la configuration Traefik attendue :
pas de labels de route et pas de rattachement au réseau frontend. La
configuration Compose du dépôt décrit une route, mais elle ne correspond pas
au conteneur réellement actif; elle ne peut pas être appliquée implicitement.

La configuration Traefik actuellement observée contient aussi api.insecure=true
et un binding public du dashboard sur le port 8090. Ceci doit être corrigé et
revalidé avant toute publication.

## Conditions avant modification

- sauvegarde réelle et copie restic validées ;
- restauration isolée et réconciliation à zéro ;
- plan de changement et rollback Traefik relu ;
- dashboard/API non public ;
- route unique HTTPS vers l’application exacte ;
- PostgreSQL, MinIO et ports internes non publiés ;
- validation de configuration avant tout redémarrage contrôlé.

Aucune commande de modification n’a été exécutée.

