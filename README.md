# Mobile Money Corpus Manager v0.1

Application web collaborative pour gérer la collecte, l'enregistrement, la transcription et la validation d'un corpus vocal Mobile Money.

## Architecture

- FastAPI : backend + interface web
- PostgreSQL : métadonnées persistantes
- MinIO : stockage des fichiers audio
- FFmpeg : conversion serveur vers WAV PCM 16 bits / 16 kHz / mono
- Traefik : reverse proxy HTTPS
- Docker Compose : déploiement VPS

## Modèle clé

La numérotation est attribuée atomiquement par PostgreSQL pour chaque combinaison
`participant_id + utterance_id + condition` (1 à 999). Un rejet, une suppression ou un échec
après réservation conserve le numéro consommé. L'affichage navigateur est une estimation.
Les uploads utilisent une clé d'idempotence par capture ; `take_number` client est refusé.
Voir [numérotation, contrat API, migration 0003 et réconciliation](docs/TAKE_SEQUENCES.md).

Un **Participant** possède un `participant_code` stable, par exemple `MOS_S001`.
Ce participant peut produire **autant d'enregistrements que nécessaire**.

Relation :

Participant 1 ─── N Recording

Chaque enregistrement conserve :
- participant
- utterance / intention
- numéro de prise
- condition CLEAN / NOISY
- audio brut
- WAV normalisé
- durée
- statut
- transcription
- validation

Ainsi `MOS_S001` peut avoir `T01`, `T02`, `T03`, etc., sans jamais changer d'identifiant participant.

## Rôles

- `ADMIN` : participants, comptes, exports, tous les enregistrements.
- `PARTICIPANT` : enregistre et peut transcrire ses propres audios.
- `TRANSCRIBER` : transcrit les audios.
- `VALIDATOR` : valide ou renvoie les transcriptions.

## Démarrage VPS

```bash
cp .env.example .env
nano .env
docker compose up -d --build
```

Avant le démarrage, définissez au minimum dans `.env` :

```env
APP_HOST=mobile-money-corpus.votre-domaine.tld
TRAEFIK_CERT_RESOLVER=ovhcloud
```

Le réseau Docker externe utilisé par Traefik doit exister :

```bash
docker network create frontend
```

Puis ouvrir :

```text
https://APP_HOST
```

Le compte administrateur initial est défini dans `.env`.

**Changez impérativement** les mots de passe et `JWT_SECRET` avant le premier démarrage public.

## HTTPS obligatoire en production

L'accès microphone depuis le navigateur exige un contexte sécurisé. `localhost` fonctionne sans HTTPS, mais un VPS distant doit être exposé en **HTTPS**.

Pour la production, le `docker-compose.yml` publie directement l'application FastAPI via des labels Traefik sur le réseau externe `frontend`. PostgreSQL et MinIO restent sur un réseau Docker interne et ne sont pas exposés publiquement.

## Dépannage PostgreSQL

L'application construit l'URL PostgreSQL à partir de `POSTGRES_DB`, `POSTGRES_USER` et `POSTGRES_PASSWORD`. Ne dupliquez pas le mot de passe dans une variable `DATABASE_URL`.

Si les logs affichent `password authentication failed for user "corpus"`, le volume PostgreSQL a probablement été initialisé avec un ancien mot de passe. Changer `POSTGRES_PASSWORD` dans `.env` ne modifie pas automatiquement le mot de passe déjà stocké dans le volume PostgreSQL.

En environnement neuf ou sans données à conserver :

```bash
docker compose down -v
docker compose up -d --build
```

En environnement avec des données à conserver, connectez-vous à PostgreSQL avec l'ancien mot de passe puis exécutez :

```sql
ALTER USER corpus WITH PASSWORD 'nouveau_mot_de_passe';
```

## Flux atelier

1. Admin crée `MOS_S001` avec son compte participant.
2. Le participant se connecte.
3. Il choisit un scénario.
4. Il enregistre une prise.
5. Le navigateur envoie l'audio brut au serveur.
6. FFmpeg produit le WAV de référence 16 kHz mono PCM16.
7. Les deux fichiers sont stockés dans MinIO.
8. Le même participant peut créer T02, T03, etc.
9. Participant ou transcripteur saisit la transcription exacte.
10. Un validateur vérifie.
11. L'admin exporte le corpus pour le benchmark.

## Données sensibles

Ne stockez pas de noms civils dans `participant_code`.
Le consentement doit être enregistré avant toute collecte.
Les accès MinIO/PostgreSQL ne doivent pas être exposés publiquement.


## Paramètres de durcissement atelier

Les valeurs recommandées derrière Traefik HTTPS sont :

```env
COOKIE_SECURE=true
MAX_AUDIO_MB=50
FFMPEG_TIMEOUT_SECONDS=60
```

Pour un test local en HTTP uniquement, utilisez temporairement `COOKIE_SECURE=false`.
La migration `0003_take_sequences` répare aussi les bases estampillées `0002` dont la contrainte
de prise omet encore la condition. La déployer en maintenance, après sauvegarde et répétition
isolée, avec frontend et API ensemble. Ne pas modifier les migrations déjà appliquées.

## P0-A

Voir `docs/P0A_IMPLEMENTATION.md`, `docs/BACKUP_RESTORE.md` et `docs/INCIDENT_RUNBOOK.md` pour la configuration stricte, les migrations, la reconciliation et les procedures d exploitation. Les sauvegardes doivent etre stockees hors volumes applicatifs.

## P0-A.2
Validation d integration et reprise: voir docs/P0A2_INTEGRATION_RECOVERY.md et RAPPORT_VALIDATION_P0A2.md.
