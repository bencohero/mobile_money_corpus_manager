# G8.6-S — Diagnostic du secret administrateur

Date : 2026-10-13 UTC. Diagnostic en lecture seule. Aucun hash, compte,
secret, variable d'environnement ou donnée métier n'a été modifié.

## Résultat cryptographique

La comparaison a été effectuée avec le vérificateur bcrypt de l'application,
sans afficher le secret ni le hash :

| Contrôle | Résultat |
|---|---|
| Variable `ADMIN_PASSWORD` du conteneur = valeur de `.env` | **oui** |
| Compte configuré présent | **oui** (`benco`, nom non secret) |
| Secret de `.env` valide pour `benco` | **non** |
| Secret de `.env` valide pour les autres comptes ADMIN | **non** |
| Nombre de comptes ADMIN | 3 |

La chronologie opérateur clarifie le constat : `.env` avait déjà reçu le nouveau
secret, mais le hash de `benco` était resté celui de l'ancienne valeur. La
connexion réussie après rotation avec la valeur actuelle de `.env` est donc le
résultat attendu de l'alignement manuel du hash, et non une anomalie.

## Comportement de la configuration

`Settings` charge `ADMIN_PASSWORD` depuis l'environnement / `.env`. La valeur
est utilisée pour :

- la validation de configuration production (longueur, valeurs interdites,
  cookie sécurisé) ;
- l'initialisation du compte admin dans `app/seed.py`.

Au démarrage, `app.main.startup()` appelle `seed(db)`. Dans `seed()` le compte
est créé uniquement si aucun utilisateur ne possède déjà
`settings.admin_username` :

```python
if not db.query(User).filter_by(username=settings.admin_username).first():
    db.add(User(password_hash=hash_password(settings.admin_password), ...))
```

Il n'existe pas de branche qui compare le hash existant à `ADMIN_PASSWORD`, ni
de branche qui le remplace. La variable est donc une valeur d'initialisation,
pas un mécanisme de synchronisation ultérieure. Modifier `.env` seul ne
changerait pas le hash d'un compte existant.

## État opérationnel vérifié

- Image : release `8f688e8d312b2f0afb30f8a2766a6f8f25e5e5d6`.
- Alembic : `0008_rate_limit_buckets (head)`.
- `/ready` et `/health` : HTTP 200.
- Public : accès maintenu fermé ; conteneur de recette sans port publié et
  attaché uniquement au backend.
- Gel : `active_writes=0`, `phase=OPEN`. `OPEN` est l'état technique de la
  porte de concurrence du middleware ; il ne constitue pas un dégel métier et
  aucune écriture métier n'est autorisée à cette étape.

## Conclusion

Le refus de connexion observé avant rotation était expliqué par la divergence
entre le nouveau secret d'environnement et l'ancien hash en base. La rotation
a corrigé cette divergence pour `benco` uniquement. Le code de démarrage ne
corrige toujours pas automatiquement les divergences futures.
