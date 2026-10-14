# F5A3 — validation du gel des écritures

## Principe validé

Le fichier d’état contient `phase`, `active_writes` et `epoch`. Le verrou `flock` protège le compteur entre processus et les écritures sont atomiques (`fsync` puis `os.replace`). La validation ne compare ni JSON exact ni epoch codé en dur : `python -m app.write_freeze check --phase FROZEN` vérifie uniquement la phase demandée et `active_writes == 0`.

Le middleware intercepte `POST`, `PUT`, `PATCH` et `DELETE`. Une requête déjà admise incrémente le compteur, puis le décrémente en `finally`. Pendant `DRAINING`, les nouvelles écritures reçoivent `503` et `Retry-After: 5`; après drainage, l’état devient `FROZEN` et reste ainsi jusqu’à `unfreeze` explicite.

## Environnement de test

Tests exécutés dans le réseau Docker isolé `f5a3-isolated`, avec PostgreSQL `16-alpine`, MinIO `minio/minio:RELEASE.2025-04-22T22-12-26Z`, deux processus applicatifs candidate et des données synthétiques uniquement. Les bases utilisent des `tmpfs`; aucun volume de production n’a été utilisé.

## Résultats

| Scénario | Résultat |
|---|---|
| Deux processus et état partagé | PASS — `app-a` et `app-b` observent le même `FROZEN`. |
| Nouvelles écritures HTTP | PASS — `POST /logout` retourne `503` sur les deux processus. |
| Requête déjà engagée | PASS — compteur maintenu à `1`, puis drainage après libération. |
| Timeout de drain | PASS — timeout à 1 s retourne code 2 et laisse `DRAINING`, jamais `FROZEN`. |
| Redémarrage pendant le gel | PASS — état partagé reste `FROZEN`, POST toujours `503`. |
| Inscriptions concurrentes | PASS — 4 inscriptions synthétiques produisent 4 participants distincts et 4 journaux. |
| Upload audio réel | PASS — WAV synthétique converti et publié, état `READY`. |
| Idempotence | PASS — deux appels avec la même clé produisent une seule soumission et une seule prise. |
| Transcription | PASS — route candidate passe l’enregistrement à `TRANSCRIBED`. |
| Vérification | PASS — décision `VERIFIED` passe l’enregistrement et la transcription à `VERIFIED`. |
| PostgreSQL + MinIO pendant `FROZEN` | PASS — dump PostgreSQL, copie d’un objet synthétique, comptages et manifestes publiés. |
| Échec de copie MinIO | PASS — marqueur `INCOMPLETE`, aucun `COMPLETE`. |
| Cible inattendue | PASS — mode production sans confirmation explicite refusé avant capture. |
| Restauration isolée | PASS — dump restauré dans PostgreSQL 16 isolé, révision `0005`; objet MinIO restauré et comptage égal à 1. |

## Couverture des écritures

L’image active ne contient pas de worker séparé : les écritures PostgreSQL/MinIO sont dans les routes listées dans le rapport de compatibilité. Une future tâche asynchrone devra appeler le même gate avant toute mutation. Le gel applicatif ne remplace pas le contrôle de la destination de sauvegarde ni les manifestes.

## Limite obligatoire

Le test a démontré la persistance avec un montage d’état commun. La production ne doit pas être déployée sans ce montage, sans contrôle de son propriétaire/permissions et sans vérification post-redémarrage. Aucun gel réel n’a été déclenché.

