# G2 — Décision finale

## Décision : `MIGRATIONS_VERIFIED_WITH_WARNINGS`

Les données restaurées au schéma `0005_workshop_attribution` ont été migrées avec succès
jusqu’à `0008_rate_limit_buckets` dans un clone entièrement isolé. Les comptages critiques,
les identifiants, les relations, les versions de transcription, les contraintes et les
objets MinIO ont été vérifiés. L’application candidate fonctionne sur le schéma final et la
suite complète passe avec 158 tests réussis.

### Avertissements acceptés

1. Le test d’environnement Docker est ignoré dans le conteneur faute de CLI Docker; la
   configuration Compose a toutefois été validée depuis l’hôte.
2. Les tests produisent des données temporaires dans le clone; les comptages de conservation
   sont donc ceux relevés avant les tests applicatifs.
3. Les comptes restaurés ont des secrets historiques; le compte administrateur du clone a dû
   être réinitialisé pour exercer les scénarios HTTP. Cette action n’a concerné ni l’archive,
   ni la production.
4. Huit warnings de dépréciation sont restés non bloquants.

## Décision opérationnelle

Le blocage G1 relatif à la preuve de compatibilité des migrations est levé pour la candidate,
mais cette validation n’autorise aucun déploiement, merge, cherry-pick ou migration de
production. Toute intégration ultérieure doit conserver la procédure de sauvegarde coordonnée,
le gel des écritures et une restauration de secours.

