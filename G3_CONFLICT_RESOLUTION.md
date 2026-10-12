# G3 — Conflits et arbitrages

## Sauvegarde F5A6–F5A8

Le principal conflit est une divergence du système de sauvegarde :

- `main:scripts/backup_local.sh` : blob `2a8180b...`, version F5A6–F5A8 validée.
- source `scripts/backup_local.sh` : blob `0534d099...`, version différente.

Décision : conserver intégralement la version de `main`. Les fichiers `scripts/security_scan.sh`,
`scripts/validate_backup_synthetic.sh`, `tests/test_f5a6_synthetic.sh`, les rapports F5A6–F5A8
et les artefacts `backups/` de `main` sont également restés inchangés. Les nouveaux
`scripts/backup.sh` et `scripts/restore.sh` de la source n’ont pas été introduits.

Contrôle : `git diff main --` retourne aucun changement pour les scripts/tests F5 protégés.

## Configuration de développement

Le `Dockerfile` source copie `.env.dev.example`, mais le diff sélectif conservait `.env.dev`
de `main`. L’exemple non secret a donc été ajouté, sans remplacer ni exposer de configuration
réelle.

## Bytecodes et données

Les bytecodes produits pendant les tests ont été retirés du commit. Aucun fichier de sauvegarde,
volume de production, base de production ou bucket réel n’a été modifié.

