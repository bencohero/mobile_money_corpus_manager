# G9.1-R — Preuve Kubuntu/restic

Aucun transfert ni snapshot restic n’a été exécuté.

`restic` n’est pas installé sur l’hôte courant et aucun alias SSH Kubuntu avec
hostname réel, utilisateur, clé et chemin de dépôt n’est disponible dans la
configuration inspectée. Le transfert est donc bloqué avant toute capture.

## Direction obligatoire

Le transfert est tiré depuis Kubuntu. Le VPS ne pousse pas vers Kubuntu.

Sur Kubuntu, après autorisation et vérification de la clé d’hôte :

~~~bash
RUN_ID=IDENTIFIANT
ssh -o StrictHostKeyChecking=yes vps-prod \
  "test -d /var/backups/mobile-money-corpus/$RUN_ID"
mkdir -m 700 -p /srv/mobile-money-backups/incoming/"$RUN_ID"
rsync --archive --partial --protect-args \
  vps-prod:/var/backups/mobile-money-corpus/"$RUN_ID"/ \
  /srv/mobile-money-backups/incoming/"$RUN_ID"/
~~~

Recalculer côté VPS et Kubuntu les mêmes manifestes d’empreintes, puis exécuter
sha256sum --check côté Kubuntu. Une divergence arrête le run.

## Restic

~~~bash
export RESTIC_REPOSITORY=REPOSITORY_EXISTANT
export RESTIC_PASSWORD_FILE=/chemin/hors-depot/restic-password
restic backup /srv/mobile-money-backups/incoming/"$RUN_ID" \
  --tag mobile-money-corpus --tag g9.1-r --tag release-8f688e8
restic check
restic snapshots --tag g9.1-r
restic restore SNAPSHOT_ID --target /srv/mobile-money-backups/verify/"$RUN_ID"
~~~

Conserver snapshot ID, sorties de check, tailles, manifestes et opérateur. Les
secrets ne figurent jamais dans les commandes journalisées.
