# G5.1 — Décision finale

## Décision

**BROWSER_VERIFIED_WITH_WARNINGS**

## Motifs

La validation Chromium réelle est passée sur les six résolutions demandées : 0 débordement, 0 erreur navigateur non attendue, navigation clavier contrôlée, états désactivés vérifiés, microphone simulé fonctionnel et upload simulé réussi. Une anomalie responsive initiale sur `/recordings` a été corrigée dans `g5-hardening`, puis validée par une nouvelle exécution complète.

La réserve G5 peut être considérée comme levée pour la validation graphique automatisée. Les avertissements restants sont limités au microphone simulé — aucun test avec périphérique physique — et à la validation visuelle de données synthétiques plutôt que de données réelles. Aucun merge vers `main` ni déploiement n’est autorisé par ce ticket.
