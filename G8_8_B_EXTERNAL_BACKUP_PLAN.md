# G8.8-B — Plan de sauvegarde externe Kubuntu

## Pré-requis constatés

`ssh` et `rsync` sont disponibles sur le poste courant. `restic` n’est pas
installé; son installation et la création du dépôt distant nécessitent une
action opérateur distincte. Aucun backup réel ne doit être transféré sans
autorisation explicite.

## Procédure proposée

1. Sur une archive validée, vérifier `MANIFEST.json`, `COMPLETE` ou les sommes
   du schema 1, puis calculer une empreinte indépendante :
   `sha256sum -b archive.tar.zst > archive.tar.zst.sha256`.
2. Vérifier l’empreinte et l’hôte SSH avant transfert : `ssh -o StrictHostKeyChecking=yes kubuntu@HOST hostname`.
3. Transférer vers un répertoire hors dépôt et hors volumes Docker, par exemple
   `rsync --archive --partial --protect-args archive.tar.zst archive.tar.zst.sha256 kubuntu@HOST:/srv/mobile-money-backups/incoming/`.
4. Sur Kubuntu, recalculer `sha256sum -c archive.tar.zst.sha256`, comparer la
   taille, le manifest et les sommes internes, puis déplacer vers un répertoire
   daté en lecture seule.
5. Après installation autorisée de restic, initialiser un dépôt chiffré avec
   une clé conservée séparément; vérifier `restic check`, `restic snapshots` et
   effectuer périodiquement un `restic restore` dans une cible isolée.

## Conservation

Conserver au moins trois générations validées, une copie hors VPS, les manifests
et les rapports de restauration. Ne jamais conserver les secrets dans l’archive
ou la ligne de commande. Le transfert réel, la destination, la clé restic et la
politique de rétention restent à approuver; aucune donnée réelle n’a été
transférée dans G8.8-B.
