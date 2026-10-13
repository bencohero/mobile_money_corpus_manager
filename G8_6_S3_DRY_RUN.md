# G8.6-S3 — Dry-run et tests négatifs

## Résultats

Exécution dans `mobile_money_corpus_manager_g8_5_r-app` :

```text
DRY RUN: no password was read and no database change was made
dry-run: code retour 0
```

Tests négatifs :

```text
--apply --confirm-target laurent -> refus, code retour 1
--apply sans confirmation       -> refus, code retour 1
```

Ces contrôles n'ont pas lu de nouveau secret et n'ont pas ouvert de transaction
d'écriture. Les comptages DB et l'inventaire MinIO sont restés inchangés.

