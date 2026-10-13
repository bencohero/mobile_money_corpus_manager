# G8.6-S2 — Runbook de rotation du mot de passe `benco`

## Statut

Préparé uniquement. **Ne pas exécuter sans nouvelle autorisation explicite.**

## 1. Préparation

1. Maintenir l'accès public fermé et les écritures métier gelées.
2. Vérifier que l'image est la release
   `8f688e8d312b2f0afb30f8a2766a6f8f25e5e5d6` et qu'Alembic est
   `0008_rate_limit_buckets`.
3. Vérifier `/ready`, `/health`, les réseaux, les ports publiés, les volumes et
   le manifeste PostgreSQL/MinIO.
4. Vérifier la sauvegarde et le plan de récupération.
5. Vérifier que trois comptes `ADMIN` existent et que `benco` est actif.

## 2. Dry-run obligatoire

Depuis l'image exacte, sans secret :

```sh
python scripts/rotate_admin_password.py
```

Le résultat attendu est `DRY RUN` et aucune modification de base.

## 3. Rotation approuvée

Générer le nouveau secret dans le gestionnaire de secrets approuvé. Ne pas le
mettre dans Git, une variable persistante du shell, l'historique ou les logs.
Après nouvelle autorisation, l'opérateur peut exécuter :

```sh
printf '%s\n' "$NEW_ADMIN_PASSWORD" | \
  docker exec -i mobile_money_corpus_manager_g8_5_r-app \
  python scripts/rotate_admin_password.py \
    --apply --confirm-target benco --password-stdin
```

Le secret ne doit pas être fourni littéralement dans le runbook ou la commande
historique ; l'exemple ci-dessus suppose un mécanisme d'injection éphémère
approuvé. Vérifier la sortie `ROTATED` et le code retour zéro.

## 4. Validation par `/login`

1. Mettre à jour le secret runtime dans le gestionnaire autorisé, sans modifier
   encore les comptes ni les volumes.
2. Utiliser le formulaire normal `/login` avec CSRF et l'identifiant `benco`.
3. Vérifier que le nouveau secret donne 303/session et que l'ancien donne 401.
4. Vérifier `/ready`, `/health`, les logs sans secret, et l'état des trois
   comptes ADMIN.

## 5. Clôture

Comparer les manifestes. Les seules différences attendues sont le hash de
`benco`, les éventuelles traces d'audit de connexion et les buckets de rate
limiting. Aucun compte non ciblé, objet MinIO, volume ou donnée métier ne doit
changer. En cas d'écart, STOP et conserver l'état pour analyse ; aucun rollback
automatique.

