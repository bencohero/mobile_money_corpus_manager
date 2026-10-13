# G9 — Preuve externe restic

## Résultat

BLOCKED. Aucun transfert, snapshot restic, restic check ou restauration de
snapshot n’a été exécuté.

## Constats

- rsync et ssh existent localement ;
- restic n’est pas installé sur l’hôte courant ;
- aucun alias SSH Kubuntu réel n’est présent ;
- aucun dépôt de remplacement n’a été créé sur le VPS ;
- aucun fichier de sauvegarde réelle n’a été produit.

La procédure requise reste un pull depuis Kubuntu, après production d’une archive
validée :

~~~bash
ssh -o StrictHostKeyChecking=yes VPS_ALIAS \
  'test -d /var/backups/mobile-money-corpus/RUN_ID'
rsync --archive --partial --protect-args \
  VPS_ALIAS:/var/backups/mobile-money-corpus/RUN_ID/ \
  /srv/mobile-money-backups/incoming/RUN_ID/
sha256sum -c /srv/mobile-money-backups/incoming/RUN_ID/external.sha256
restic backup /srv/mobile-money-backups/incoming/RUN_ID --tag g9
restic check
restic restore SNAPSHOT_ID --target /srv/mobile-money-backups/verify/RUN_ID
~~~

Ces commandes restent préparatoires et ne doivent être lancées qu’après
identification vérifiée de VPS_ALIAS, du chemin Kubuntu et du dépôt.

