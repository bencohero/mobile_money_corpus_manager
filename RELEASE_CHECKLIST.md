# Release checklist

## Réalisé dans ce lot

- [x] État Git et tête Alembic inspectés ; branche dédiée conservée.
- [x] Aucune migration ni opération sur production exécutée.
- [x] Extraction audio et audit/CSRF effectuée sans changement de contrat HTTP.
- [x] Plan 0005→0008 et procédure de restauration rédigés.
- [x] Routes, modèles, services et dépendances cartographiés.

## Contrôles réalisés

- [x] Suite pytest complète exécutée deux fois dans l’environnement E.2 isolé : 158 passed, 1 skip technique.
- [x] Suite Node fonctionnelle exécutée ; tous les scripts `.test.cjs` passent.
- [x] Bandit, pip-audit et Gitleaks exécutés ; résultats expurgés documentés.
- [x] Restauration réelle d’une copie synthétique représentative et contrôle `0008` effectués.
- [x] Compose dédié, volumes et réseau E.1 vérifiés comme isolés de la production.
- [x] `python-jose`/`ecdsa` retirés après audit des usages ; contrats JWT testés.
- [x] CSP sans `unsafe-inline`, nonce par réponse et listeners externes vérifiés.
- [x] Rehearsal historique 0005→0008, arrêt contrôlé et restauration 0005 exécutés.
- [x] Tests négatifs exécutables isolément ; plus de dépendance à l’ordre d’intégration.

## Contrôles manquants ou non concluants

- [x] pip-audit E.2 : aucune vulnérabilité connue.
- [x] Deux détections Gitleaks qualifiées comme empreintes SHA-256 générées et exception ciblée appliquée.
- [x] CSP sans `unsafe-inline` ; les scripts spécifiques restants sont protégés par nonce.

## Validation humaine obligatoire

- [ ] Revue des diffs et des contrats HTTP.
- [ ] Validation des écarts de données et des objets MinIO orphelins.
- [ ] Approbation de la fenêtre d’indisponibilité et du plan de retour arrière.
- [ ] Autorisation explicite de déploiement séparée de la réussite de la refactorisation.

## Lot F — recette préproduction

- [x] Images runtime et test construites depuis l’arbre candidat.
- [x] Environnement isolé F préparé avec réseau et volumes dédiés ; aucun service de production arrêté.
- [x] Suite Docker complète : 158 passed, 1 skipped, 141,17 s.
- [x] Alembic vérifié sur la copie : `0008_rate_limit_buckets (head)`.
- [x] Backup/restore synthétique PostgreSQL + MinIO et SHA-256 vérifiés.
- [x] Réconciliation post-restore sans anomalie.
- [x] Comptages source/restauré comparés.
- [ ] Backup et migration sur données historiques réelles autorisés et exécutés.
- [ ] HTTPS/certificats/Traefik, Android et tests multi-workers validés sur VPS.
- [ ] Scanners Bandit, pip-audit et Gitleaks rejoués dans un environnement outillé.
- [ ] Revue humaine des écarts, fenêtre et retour arrière signée.

**Statut Lot F : BLOQUÉ — PRÊT POUR AUTORISATION après levée des contrôles manquants.**

Voir [PREPRODUCTION_VALIDATION_REPORT.md](PREPRODUCTION_VALIDATION_REPORT.md).
