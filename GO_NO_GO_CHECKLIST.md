# Go/No-Go checklist — F.1

Release : `cb87475513721fc5816272ee41beaff3b9b13f8a`

## Conditions techniques

- [x] SHA Git figé et worktree propre.
- [x] Images runtime/test/outils reconstruites et étiquetées avec le SHA.
- [x] Suite automatique candidate : 158 passed, 1 skipped.
- [x] Bandit, pip-audit et Gitleaks exécutés en Docker.
- [x] pip-audit sans vulnérabilité connue.
- [x] Gitleaks sans leak ; exception Graphify limitée et documentée.
- [ ] Bandit LOW accepté ou corrigé par le responsable sécurité.
- [ ] HTTPS, certificat, DNS, Traefik et TrustedHost vérifiés sur VPS.
- [ ] Cookies, CSP, proxy headers et rate limiting multi-workers vérifiés sur VPS.
- [ ] PostgreSQL/MinIO non exposés vérifiés depuis l’extérieur du VPS.
- [ ] Logs et gestion d’erreurs vérifiés sur VPS.

## Conditions fonctionnelles et données

- [ ] Recette manuelle desktop terminée.
- [ ] Recette Chrome Android terminée.
- [ ] Backup historique autorisé par le responsable données.
- [ ] Migration/restauration historique mesurée et réconciliée.
- [ ] Exports et empreintes SHA-256 validés sur copie historique.

## Signatures nécessaires

- [ ] Responsable données : __________________ date : __________
- [ ] Responsable exploitation : ______________ date : __________
- [ ] Responsable sécurité : __________________ date : __________
- [ ] Responsable produit : ___________________ date : __________

## Décision

**NO-GO tant que toutes les cases critiques et les quatre validations humaines ne
sont pas signées.** Cette checklist n’autorise aucune action automatique.
