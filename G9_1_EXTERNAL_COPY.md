# G9.1 — Copie externe Kubuntu/restic

Cette procédure est préparée mais n’est pas exécutée automatiquement.

Préconditions : dépôt restic Kubuntu accessible, clé d’hôte SSH connue, fichier
de mot de passe restic hors dépôt en mode 0600, politique de rétention approuvée
et archive schema 2 validée.

~~~bash
RUN=/var/backups/mobile-money-corpus/IDENTIFIANT
SHA_FILE="$RUN.external.sha256"
find "$RUN" -type f -print0 | sort -z | xargs -0 sha256sum >"$SHA_FILE"
ssh -o StrictHostKeyChecking=yes kubuntu@KUBUNTU_HOST 'hostname && test -d /srv/mobile-money-backups'
rsync --archive --partial --protect-args "$RUN" "$SHA_FILE" \
  kubuntu@KUBUNTU_HOST:/srv/mobile-money-backups/incoming/
ssh -o StrictHostKeyChecking=yes kubuntu@KUBUNTU_HOST \
  'cd /srv/mobile-money-backups/incoming/IDENTIFIANT && sha256sum -c IDENTIFIANT.external.sha256'
~~~

KUBUNTU_HOST et les chemins sont des placeholders à faire relire. Aucun secret
ne doit apparaître dans une commande ou un manifest.

~~~bash
export RESTIC_REPOSITORY=REPOSITORY_CONFIGURE_SUR_KUBUNTU
export RESTIC_PASSWORD_FILE=/chemin/hors-depot/restic-password
restic unlock
restic backup /srv/mobile-money-backups/incoming/IDENTIFIANT \
  --tag mobile-money-corpus --tag g9.1 --tag release-8f688e8
restic check
restic snapshots --tag g9.1
~~~

Restaurer ensuite un snapshot dans un répertoire temporaire isolé, recalculer
les empreintes et joindre au dossier de preuve le résultat de restic check,
l’identifiant du snapshot, les tailles et les sommes. Conserver au moins trois
générations et une copie hors VPS selon la politique approuvée.

