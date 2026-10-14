# G1 — Évaluation des migrations

## Chaîne constatée

Sur la branche courante :

`0001_initial → 0002_p0a_recording_sync → 0003_take_sequences → 0004_participant_registration → 0005_workshop_attribution → 0006_multilingual_participant_identity → 0007_integrity_and_transcription_versions → 0008_rate_limit_buckets`

Les révisions `0006`, `0007` et `0008` proviennent respectivement de `5457b1e`, `9279a2a` et `d34e96a`. `main` s’arrête à `0005_workshop_attribution`.

## Compatibilité avec les données réelles

La sauvegarde F5A7.2 et sa restauration F5A8 ont été validées sur une copie isolée au niveau `0005`, avec les contrôles d’intégrité prévus. Cette validation ne constitue pas une exécution de migration. Aucune migration ne doit être lancée sur la production ni sur l’archive originale.

- `0006` ajoute la notion de langue et les séquences d’identité ; il nécessite une stratégie explicite pour les valeurs existantes.
- `0007` ajoute les contrôles d’intégrité, les versions et l’historique de transcription. Ses contrôles peuvent bloquer en présence d’orphelins ou de références invalides ; son downgrade est volontairement non automatique.
- `0008` ajoute l’état des quotas dans `rate_limit_buckets`. Il s’agit d’un état applicatif nouveau, non requis pour prouver la restauration de l’archive F5A7.2.

Les incompatibilités potentielles portent sur les modèles ORM, les FK, la nullabilité de `recording_id`, les valeurs par défaut de langue, les séquences et les permissions. Elles doivent être déterminées sur un clone temporaire de la restauration F5A8, jamais sur les services réels.

## Plan de validation isolée

1. Dupliquer la restauration F5A8 dans une base temporaire et conserver l’archive originale en lecture seule.
2. Exécuter les diagnostics de `0006` sans écriture, puis appliquer `0006` dans ce clone.
3. Vérifier comptages, contraintes, références, séquences et requêtes métier.
4. Appliquer `0007` uniquement si les diagnostics sont propres ; vérifier l’historique et la concurrence.
5. Appliquer `0008`, vérifier l’expiration et la concurrence des buckets.
6. Exécuter les tests applicatifs et MinIO sur des services isolés.
7. Conserver un snapshot du clone avant chaque lot pour retour arrière par restauration, pas par downgrade.

## Conclusion migration

La chaîne est linéaire mais sa compatibilité avec les données réelles n’est pas encore démontrée après `0005`. Aucun signal ne justifie une migration de production à ce stade.

