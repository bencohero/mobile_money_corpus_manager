# Runbook incident
PostgreSQL: conserver les logs, verifier le disque, basculer vers une copie isolee et restaurer sans toucher aux volumes courants.
MinIO: verifier la sante et le disque; ne pas supprimer les objets orphelins avant la reconciliation.
FFmpeg: verifier les timeouts, le stockage temporaire et la saturation; les utilisateurs doivent reessayer apres un 429 ou 422.
Secrets: generer avec python -c 'import secrets; print(secrets.token_urlsafe(48))', remplacer hors Git, redemarrer et verifier COOKIE_SECURE.
Disque: surveiller les volumes, /tmp/audio et BACKUP_DIR; conserver une marge libre et appliquer la retention.
Manuel VPS restant: tester HTTPS/microphone, rotation des logs, quotas Docker, restauration complete et alertes disque.
# Prises : réservations et idempotence

Depuis `0003_take_sequences`, les états PENDING/ERROR sont des réservations durables et les
numéros ne sont jamais recyclés. Voir [la procédure détaillée](TAKE_SEQUENCES.md) pour les
commits indéterminés, la réconciliation et le traitement manuel des orphelins historiques.
Ne pas purger les compteurs ou reçus pour débloquer un enregistrement.
