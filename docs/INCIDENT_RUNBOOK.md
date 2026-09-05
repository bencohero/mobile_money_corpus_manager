# Runbook incident
PostgreSQL: conserver les logs, verifier le disque, basculer vers une copie isolee et restaurer sans toucher aux volumes courants.
MinIO: verifier la sante et le disque; ne pas supprimer les objets orphelins avant la reconciliation.
FFmpeg: verifier les timeouts, le stockage temporaire et la saturation; les utilisateurs doivent reessayer apres un 429 ou 422.
Secrets: generer avec python -c 'import secrets; print(secrets.token_urlsafe(48))', remplacer hors Git, redemarrer et verifier COOKIE_SECURE.
Disque: surveiller les volumes, /tmp/audio et BACKUP_DIR; conserver une marge libre et appliquer la retention.
Manuel VPS restant: tester HTTPS/microphone, rotation des logs, quotas Docker, restauration complete et alertes disque.
