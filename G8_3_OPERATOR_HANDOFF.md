# G8.3 — Remise à l’opérateur Kubuntu

## Archive prête au transfert

- Identifiant : `20261012T235937Z`
- Source VPS : `/home/sangouman/mobile-money-corpus-backups/20261012T235937Z`
- Taille observée : `5.5M`
- SHA-256 de `manifests/SHA256SUMS` : `041a3f62994f3839f1b35a4d758ac1f0ca645ac1e3bacd6a856340c172ff20a8`

Depuis Kubuntu, remplacer uniquement les placeholders de connexion et destination :

```bash
rsync -aHAX --numeric-ids --info=progress2 \
  <operateur>@<vps>:/home/sangouman/mobile-money-corpus-backups/20261012T235937Z/ \
  <destination-kubuntu>/20261012T235937Z/
```

Après transfert, l’opérateur doit vérifier le SHA-256, créer ou référencer le snapshot restic, exécuter `restic check`, restaurer dans une cible isolée et confirmer la conservation de la clé hors VPS. Aucun secret restic ne doit être transmis.

Point d’arrêt atteint : aucune migration ni reprise applicative avant retour de l’attestation Kubuntu.
