# G5.1 — Rapport de test navigateur

## Environnement

- Branche : `g5-hardening`
- Commit de départ vérifié : `2be2dbe`
- Stack : G5 isolée, application candidate, PostgreSQL/MinIO dédiés, aucun port publié.
- Chromium réel : Chrome for Testing 153, lancé hors du conteneur applicatif dans l’environnement `/tmp` de test.
- Résolutions : 320, 360, 390, 412, 1280 et 1440 px.

## Résultats finaux

- 72 contrôles Playwright exécutés.
- Débordements horizontaux : 0.
- Erreurs navigateur non attendues : 0.
- Focus clavier : vérifié à chaque résolution.
- Microphone simulé : démarrage/arrêt réussi aux 6 résolutions.
- Upload audio simulé : réussi à 390 px; message `Enregistré` observé.
- Autorisation `/help` pour le rôle administrateur : HTTP 403 attendu et vérifié.
- Captures : 48 fichiers dans `G5_1_artifacts/screenshots/`.

Les scénarios ont couvert login administration, inscription participant (page et formulaire), navigation dashboard/participants/enregistrements/enregistrement/export/équipe, transcription accessible depuis le corpus, états désactivés, messages d’état, focus et contrôle d’autorisation.

## Anomalie corrigée

La première exécution a détecté un débordement de `/recordings` sur toutes les largeurs mobiles, causé par le tableau et la barre de navigation. La branche a reçu un correctif CSS ciblé : tableau d’enregistrements adaptatif, colonnes secondaires masquées sur petit écran, retour à la ligne des identifiants et contraintes de largeur de navigation. La seconde exécution complète est verte.

## Limites

Le microphone était simulé par Chromium (`--use-fake-device-for-media-stream`); aucun périphérique physique n’a été utilisé. L’upload est donc une preuve de parcours avec audio synthétique, pas une preuve de qualité acoustique réelle.
