# Attribution des participants et enregistrements aux ateliers

La révision `0005_workshop_attribution` introduit `workshops`, séparé de `workshop_codes`.
Chaque code appartient à un atelier ; chaque participant et chaque enregistrement portent
un `workshop_id` persistant. Le `workshop_id` d’un enregistrement est un instantané et ne
change pas si un transfert administratif est ajouté ultérieurement.

## Diagnostic et migration

Exécuter le diagnostic en lecture seule sur une copie de la base :

```bash
python scripts/diagnose_workshop_migration.py
```

La migration rattache les lignes historiques à un atelier unique nommé
`Atelier historique — à confirmer`. Elle refuse de terminer si des lignes restent sans
rattachement. Elle ne modifie aucune migration déjà appliquée et son downgrade est bloqué
pour éviter une perte silencieuse de l’historique.

Procédure contrôlée : sauvegarde, arrêt des écritures, diagnostic, `alembic upgrade head`,
contrôle des contraintes et redémarrage de l’application. Ne jamais exécuter cette procédure
sur la base de production sans sauvegarde et validation de l’inventaire.

## Désactivation

La désactivation d’un atelier est administrative et auditée. La connexion et la lecture
restent possibles, mais les routes participant qui créent ou modifient des données renvoient
`403 Forbidden`. Les données et les objets audio existants sont conservés.

## Exports

Les filtres d’export utilisent `recordings.workshop_id`, jamais l’atelier courant du
participant. CSV, JSONL, ZIP et manifestes contiennent l’identifiant et le nom public de
l’atelier ; aucun code d’inscription ou HMAC n’est exporté.

## Retour arrière

Le downgrade Alembic n’est volontairement pas disponible. Le retour arrière opérationnel est
un arrêt des écritures, le déploiement de l’image précédente et la restauration de la sauvegarde
pré-migration dans une base contrôlée.
