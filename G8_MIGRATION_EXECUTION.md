# G8 — Exécution de migration

Statut : **NON EXÉCUTÉE**.

La production est restée sur `0005_workshop_attribution`. La commande explicite prévue par la release est :

```text
scripts/migrate.sh
ALEMBIC_TARGET=0008_rate_limit_buckets
```

Elle appelle explicitement `alembic upgrade` puis `alembic current`; aucune migration implicite n’est appelée par le démarrage applicatif. Le garde-fou de démarrage vérifie la révision courante et refuse une version de schéma non conforme.

La migration n’a pas été lancée, car la copie externe Kubuntu/restic de la sauvegarde immédiate n’est pas attestée. Aucune durée, journal de migration, table cible ou index post-migration ne peut donc être déclaré.

Contrôle post-préparation : `alembic_version` production reste `0005_workshop_attribution`.
