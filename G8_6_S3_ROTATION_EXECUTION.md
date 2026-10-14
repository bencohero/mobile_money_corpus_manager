# G8.6-S3 — Exécution de rotation

## Statut : NON EXÉCUTÉE

La prévol est réussie, mais l'étape 2 est bloquante : aucun gestionnaire de
secrets disponible (`pass`, `vault`, `op`) et aucun canal d'injection masquée
opérateur utilisable dans cette session.

La commande approuvée n'a donc pas été appelée avec `--apply`. Aucun hash,
compte, volume, secret runtime ou donnée métier n'a été modifié.

La commande à exécuter après mise à disposition d'un canal approuvé est :

```sh
printf '%s\n' "$NEW_ADMIN_PASSWORD" | \
  docker exec -i mobile_money_corpus_manager_g8_5_r-app \
  python /var/tmp/rotate_admin_password.py \
  --apply --confirm-target benco --password-stdin
```

Le secret ne doit pas figurer dans les arguments, logs, rapports ou historique
shell. Cette commande reste une instruction opérateur, pas une action effectuée.

