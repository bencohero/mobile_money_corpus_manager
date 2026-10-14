# G9 — Contrôles sécurité préouverture

## Résultat

BLOCKED.

## Échecs critiques

1. L’application active n’a aucun label Traefik et n’est attachée qu’au réseau
   mobile_money_corpus_manager_v0_1_backend, pas au réseau frontend.
2. HTTPS corpus-moore.bencoherolab.com répond 404 : aucune preuve de route
   applicative publique.
3. Traefik expose api.insecure=true et son port dashboard 8090 sur 0.0.0.0.
4. Les logs Traefik signalent des routeurs dupliqués avec configurations
   différentes et des erreurs CrowdSec 403.
5. La copie externe restic et la restauration isolée n’ont pas été validées.

## Contrôles favorables

- certificat TLS présenté pour corpus-moore.bencoherolab.com, émis par
  Let's Encrypt, période 2026-08-31 à 2026-11-29 ;
- PostgreSQL et MinIO ne publient pas de port hôte ;
- /ready et /health internes sont passants ;
- release et Alembic sont conformes.

Aucune correction Traefik, aucun redémarrage, aucune ouverture et aucune
modification de secret n’a été effectuée.

