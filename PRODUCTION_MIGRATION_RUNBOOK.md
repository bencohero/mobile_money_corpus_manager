# Runbook de migration production 0005 → 0008 — F.3

Date : 2026-10-11  
Statut : **PRÊT POUR AUTORISATION — migration de production interdite dans ce ticket**

## 1. Constats et préconditions

La révision réelle observée est `0005_workshop_attribution`. Les migrations sont
linéaires : `0006_multilingual_participant_identity`, puis
`0007_integrity_and_transcription_versions`, puis `0008_rate_limit_buckets`.
Les downgrades du code refusent volontairement de rétrograder : les compteurs,
reçus, identités et historiques doivent être restaurés depuis une sauvegarde
coordonnée, pas reconstruits par downgrade.

Les validations synthétiques E.2 ont réussi en environnement isolé, mais ne prouvent
pas la compatibilité de toutes les données réelles. La production doit donc rester à
0005 jusqu’à validation de ce runbook et des signataires.

## 2. Procédure contrôlée

### Étape 1 — version réelle et gel

Capturer le SHA/digest de l’image, le commit réellement déployé, le projet Compose,
les volumes, `alembic current`, `/health`, `/ready`, les comptages et l’inventaire
MinIO. Comparer l’image au commit attendu ; l’audit ne démontre pas cette
équivalence. Annoncer une fenêtre, arrêter les écritures applicatives et attendre
les opérations audio/transcription en cours.

### Étape 2 — sauvegarde

Exécuter uniquement la procédure autorisée de `PRODUCTION_BACKUP_PLAN.md` : dump
PostgreSQL, copie MinIO, métadonnées des buckets, configuration nécessaire,
manifestes SHA-256 et copie chiffrée hors VPS. Vérifier la cohérence temporelle,
restaurabilité et présence hors VPS avant de continuer.

### Étape 3 — restauration isolée

Créer un projet Compose au nom inédit, réseau/volumes/bucket nouveaux, sans route
Traefik ni port public. Restaurer PostgreSQL et MinIO dans les cibles isolées avec
des outils de même version majeure. Ne jamais utiliser les volumes
`mobile_money_corpus_manager_v0_1_*`.

### Étape 4 — contrôle historique avant migration

Vérifier les comptages des utilisateurs, participants, ateliers, workshop codes,
recordings, submissions, take counters, transcriptions, audit logs et objets audio.
Contrôler les identifiants historiques, maxima des compteurs, relations orphelines,
langues inconnues, incohérences participant/atelier, objets manquants et objets
MinIO orphelins. Tout écart est bloquant et doit être validé par le responsable
données avant migration.

### Étape 5 — répétition 0006, 0007, 0008

Sur la copie uniquement, appliquer successivement les trois révisions et consigner
la sortie après chacune :

1. `0006_multilingual_participant_identity` : langues, identités, séquences et
   reçus d’inscription ; vérifier que les maxima existants ne diminuent pas.
2. `0007_integrity_and_transcription_versions` : les diagnostics non nuls doivent
   bloquer l’étape ; vérifier contraintes, version initiale et baseline de
   `transcription_history`.
3. `0008_rate_limit_buckets` : vérifier table, clé primaire, index d’expiration et
   contrainte de compteur.

Après chaque étape, comparer identifiants, compteurs, nombre d’enregistrements,
transcriptions et objets audio à l’état pré-migration. La cible finale doit être
`0008_rate_limit_buckets (head)`.

### Étapes 6 à 8 — fonctionnel et réconciliation

Vérifier login et permissions, capture/upload, lecture audio et Range, transcription
et correction, export et SHA-256, CSRF, rate limiting, `/health`, `/ready` et les
journaux. Réconcilier PostgreSQL/MinIO : chaque enregistrement référencé doit avoir
les objets attendus, chaque objet doit être expliqué, et les écarts doivent être
classés avant toute décision.

## 3. Critères d’arrêt

Arrêter immédiatement si la version ou l’image est inconnue, si une sauvegarde ou sa
restauration échoue, si les comptages/identifiants/compteurs/transcriptions divergent,
si un diagnostic 0007 est non nul, si un objet est manquant, si la readiness échoue,
si un secret ou volume de production apparaît dans la copie, ou si la capacité du
VPS passe sous le seuil approuvé. Aucun contournement manuel de migration n’est
autorisé.

## 4. Retour arrière

Avant ouverture des écritures, revenir à la copie restaurée 0005 si nécessaire.
Après migration de production autorisée, le retour arrière consiste à arrêter les
écritures, redéployer l’image précédente compatible et restaurer ensemble PostgreSQL
et MinIO depuis le même point de sauvegarde, puis refaire la réconciliation. Ne pas
mélanger une base restaurée avec un bucket plus récent. Le retour arrière doit être
exercé sur la copie isolée avant toute migration réelle.

## 5. Signatures requises

Responsable données : écarts historiques, identifiants, transcriptions et objets.
Exploitation : fenêtre, capacité, sauvegarde, restauration et retour arrière.
Sécurité : secrets, réseau, exposition et journaux. Produit : parcours fonctionnels
et exports. Le lancement réel est **BLOQUÉ jusqu’à ces validations** ; le runbook
est néanmoins **PRÊT POUR AUTORISATION**.
