# Procédure de remédiation de l’auto-inscription participant

Cette procédure corrige la dérive observée entre la base `0002_p0a_recording_sync`
et les migrations `0003_take_sequences`/`0004_participant_registration`. Elle est
prévue pour une fenêtre de maintenance et exige une sauvegarde PostgreSQL vérifiée.

## Préparation

```bash
git status --short
docker compose ps
for variable in APP_ENV WORKSHOP_CODE_SECRET POSTGRES_DB POSTGRES_USER; do
  if [[ -n "${!variable:-}" ]]; then echo "$variable=définie"; else echo "$variable=absente"; fi
done
```

`WORKSHOP_CODE_SECRET` doit être distinct du secret JWT, aléatoire et long d’au
moins 32 caractères. Sa valeur n’est jamais affichée ni journalisée.

## Sauvegarde et dry-run

Créer un dump custom hors du VPS si possible, puis vérifier son contenu avec
`pg_restore --list` et enregistrer son checksum. Le script refuse toute action si
le fichier est absent, vide ou illisible.

```bash
scripts/reconcile_participant_registration_schema.py \
  --backup /chemin/vers/postgres.dump --dry-run
```

Le script vérifie notamment la révision `0002_p0a_recording_sync`, l’absence de la
séquence et des objets `0004`, zéro participant, l’existence de `workshop_codes` et
l’absence d’une reprise antérieure. Aucun hash de code d’atelier n’est affiché.

## Fenêtre de maintenance

Arrêter les écritures applicatives, arrêter `app` en conservant `db`, puis relancer
le script avec confirmation explicite :

```bash
scripts/reconcile_participant_registration_schema.py \
  --backup /chemin/vers/postgres.dump \
  --apply --confirm RECONCILE-PARTICIPANT-REGISTRATION
```

La table prématurée est renommée en `workshop_codes_reconcile_backup`, ses index et
contraintes sont renommés pour éviter les collisions, puis Alembic applique la
chaîne complète. Les lignes sont recopiées dans la table canonique et le compte est
vérifié. La table de reprise est conservée jusqu’à la validation fonctionnelle;
elle ne doit être supprimée qu’après une décision d’exploitation documentée.

Ne pas utiliser `alembic stamp` et ne pas créer seulement la séquence à la main.

## Migration et vérifications

Avec l’image runtime corrigée :

```bash
docker compose run --rm --no-deps --entrypoint alembic app \
  -c /app/alembic.ini upgrade head
docker compose run --rm --no-deps --entrypoint alembic app \
  -c /app/alembic.ini current
```

La sortie doit être `0004_participant_registration (head)` (ou la migration
corrective ultérieure approuvée). Vérifier ensuite la séquence, la contrainte
`uq_users_participant_id`, l’index `ix_workshop_codes_active_window` et le nombre
de codes restaurés, sans sélectionner les empreintes.

```bash
docker compose up -d app
docker compose ps
docker compose logs --tail=100 app
```

Le démarrage refuse désormais une base en retard et n’exécute jamais `create_all()`.
Le test de fumée consiste à ouvrir `/participant/register`, créer un participant,
se connecter avec l’identifiant `MOS_NNN` et vérifier l’absence de secrets dans les
logs.

## Retour arrière

Conserver la base en échec pour analyse, produire si nécessaire un dump d’incident,
arrêter l’application, restaurer le dump pré-migration dans une base contrôlée,
valider la restauration et redéployer l’ancienne version compatible. Le downgrade
de `0004` n’est pas une procédure de retour arrière.
