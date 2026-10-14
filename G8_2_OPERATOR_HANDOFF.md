# G8.2 — Remise opérateur Kubuntu

## État

Pas de transfert possible : l’archive locale n’a pas été créée. Ne pas exécuter la commande ci-dessous avant réception d’un identifiant et d’un chemin réels.

Commande rsync à adapter après création :

```text
rsync -aHAX --info=progress2 /home/sangouman/mobile-money-corpus-backups/<ARCHIVE_ID>/ <operateur>@<kubuntu>:/<destination-approuvee>/
```

L’opérateur devra communiquer, pour le même `ARCHIVE_ID` :

1. SHA-256 exact de l’archive;
2. identifiant du snapshot restic;
3. résultat `restic check`;
4. résultat du test de restauration dans une cible isolée;
5. confirmation que la clé de chiffrement reste hors VPS.

Ne transmettre aucun secret restic et ne pas installer restic sur le VPS.
