# G9 — Surveillance

## Résultat

Surveillance post-ouverture non démarrée, car l’ouverture est NO-GO.

Les ressources observées sont un signal de prudence : environ 303 MiB de RAM
libre, aucune swap, et 85 GiB libres sur le disque système. Aucun déploiement
ou nettoyage n’a été lancé.

Les erreurs récentes observées dans Traefik comprennent des configurations de
routeurs dupliquées et des refus 403 lors des métriques CrowdSec. Elles doivent
être résolues ou explicitement acceptées avant publication.

Après une ouverture validée, surveiller sans secrets :

- /ready et /health ;
- HTTP 4xx/5xx ;
- authentifications ;
- erreurs d’upload et d’enregistrement ;
- PostgreSQL, MinIO, CPU, RAM, disque et inodes ;
- erreurs Traefik et CrowdSec.

Conserver les journaux et arrêter immédiatement l’exposition en cas d’anomalie
critique.

