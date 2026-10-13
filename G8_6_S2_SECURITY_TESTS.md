# G8.6-S2 — Tests de sécurité préparés

Les tests ci-dessous sont à exécuter après une autorisation explicite de
rotation. Aucun n'a été exécuté dans G8.6-S2.

| Test | Attendu |
|---|---|
| Exécution sans `--apply` | dry-run, aucune lecture du mot de passe, aucune écriture |
| `--apply` sans confirmation | refus avant ouverture de transaction d'écriture |
| cible différente de `benco` | refus |
| `APP_ENV` différent de production | refus |
| `benco` absent/inactif/non-ADMIN | refus et rollback |
| nombre d'ADMIN différent de 3 | refus et rollback |
| différence d'identité/rôle/état/participant | refus et rollback |
| hash d'un autre ADMIN modifié | refus et rollback |
| ancien mot de passe via `/login` | 401 après rotation |
| nouveau mot de passe via `/login` | 303 puis session normale |
| `/ready`, `/health`, hôte autorisé | 200 |
| hôte non autorisé | 400 |
| tables métier, volumes, objets MinIO | inchangés |

La validation `/login` doit être effectuée uniquement via le chemin normal de
l'application, avec cookie CSRF et sans afficher le secret. La connexion réussie
peut ajouter une trace d'audit et un bucket de rate limiting ; ces effets
techniques doivent être inclus dans le diff.

