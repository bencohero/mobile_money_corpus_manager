# G8.6-S2 — Décision

## `READY_FOR_CONTROLLED_EXECUTION`

La commande de rotation et le runbook sont préparés, mais la rotation n'est
pas exécutée. Cette décision signifie uniquement que le dispositif est prêt à
être examiné et exécuté après une autorisation explicite ; elle ne constitue
pas une autorisation de production.

Le périmètre est limité à `benco`. Les deux autres comptes `ADMIN` sont protégés
par des contrôles d'identité, de rôle, d'état, de relation et de hash. Le
mécanisme bcrypt applicatif est réutilisé. La validation normale `/login`, le
manifeste avant/après et le maintien de l'accès public fermé sont obligatoires.

En l'absence de nouvelle autorisation, l'état reste inchangé : aucun secret,
compte, volume ou donnée métier n'a été modifié.
