# G8.1 — Correction du script de sauvegarde

## Résultat

La réserve G8 a été reproduite dans un test isolé : `printf '%s\\0'` écrit les deux caractères `\\` et `0`, pas un séparateur NUL. Cette représentation casse le flux pathname-safe attendu par `sort -z` / `xargs -0`.

Le script versionné [scripts/backup_local.sh](scripts/backup_local.sh) a reçu le correctif minimal suivant : le consommateur est désormais explicite avec `xargs --null --no-run-if-empty sha256sum`. Le producteur reste `find ... -print0`; aucun schéma, donnée, volume ou service n’a été modifié.

## Intégration

- HEAD avant correctif : `b672697` (`remediation-a-stabilisation-securite`).
- Patch de travail correctif : `b6c5c2efc301c903c3b59fd67c94d54ab92a7e1d57400785366cd65318855376` (SHA-256 du diff script + test au moment de la validation).
- Commit Git dédié : non créé dans cette session, afin de préserver les changements préexistants du worktree.
- Intégration release : à intégrer dans la prochaine release avant toute capture de production; aucune migration ni push distant n’a été effectué.

L’incohérence relevée dans G8 est conservée dans cette trace : le blob actuel contenait déjà `-print0 | sort -z | xargs -0`, alors que G8 déclarait le script non modifié. Le test ci-dessus et le durcissement explicite rendent le contrat vérifiable.
