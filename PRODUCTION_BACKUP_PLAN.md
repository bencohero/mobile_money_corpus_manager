# Plan de sauvegarde de production — F.3

Date : 2026-10-11  
Statut : **PRÊT POUR AUTORISATION**  
Aucune sauvegarde réelle, copie hors VPS ou restauration n’a été exécutée.

## 1. Constats

La production est le projet `mobile_money_corpus_manager_v0_1` : PostgreSQL
`corpus`, volume `mobile_money_corpus_manager_v0_1_pgdata`, MinIO et bucket
`mobile-money-corpus`, volume `mobile_money_corpus_manager_v0_1_miniodata`.
L’audit a observé Alembic `0005_workshop_attribution`, des données historiques et
des sauvegardes locales `before_corpus_reset_*` dans l’arbre du VPS. Aucune copie
hors VPS, rotation, alerte ou test récent de restauration n’est démontré.

Les scripts existants `scripts/backup.sh` et `scripts/restore.sh` fournissent une
base pour une recette isolée, mais ne suffisent pas encore à prouver une sauvegarde
cohérente de production : ils ne figent pas les écritures, ne capturent pas toutes
les métadonnées MinIO ni une configuration complète, et la cible doit être validée
avant chaque invocation.

## 2. Périmètre à sauvegarder

1. PostgreSQL : dump custom de `corpus`, rôle/ownership nécessaires, version
   PostgreSQL, révision Alembic, extensions, paramètres utiles et manifeste des
   comptages. Ne pas afficher les lignes réelles dans les journaux.
2. MinIO : tous les objets du bucket `mobile-money-corpus`, taille, ETag si utile,
   SHA-256 recalculé en lecture, `Content-Type`, métadonnées et clés. Exporter la
   liste des buckets, politiques, utilisateurs/service accounts et configuration
   nécessaire à une restauration ; exclure les secrets en clair du manifeste.
3. Configuration : versions/digests d’images, fichiers Compose et overlays,
   `alembic.ini`, scripts d’exploitation, paramètres non secrets, noms de volumes,
   réseaux, domaines et procédures. Les secrets sont sauvegardés séparément dans un
   coffre chiffré ou régénérés selon la politique de l’exploitation.
4. Manifeste : horodatage UTC, fenêtre d’écriture, sources, tailles, compteurs,
   révision Alembic, versions outils, SHA-256 de chaque archive et objet, puis
   SHA-256 du manifeste lui-même.

## 3. Cohérence PostgreSQL/MinIO

Méthode recommandée : annoncer une fenêtre contrôlée, bloquer les nouvelles
écritures applicatives et attendre la fin des traitements audio/transcription
`PENDING`, puis capturer PostgreSQL et MinIO dans le même intervalle UTC. Consigner
les compteurs et le nombre d’objets avant/après. Réactiver les écritures seulement
après validation locale des archives.

Si l’arrêt des écritures est impossible, un mécanisme équivalent doit être démontré
avant autorisation : journal d’opérations, point de cohérence partagé et procédure
de réconciliation capable de distinguer objets antérieurs, postérieurs, orphelins et
enregistrements manquants. Un simple `pg_dump` suivi d’un `mc mirror` sans contrôle
de fenêtre n’est pas suffisant.

## 4. Copie hors VPS, chiffrement et rétention

Produire d’abord une copie locale temporaire avec permissions minimales, puis chiffrer
avant transfert avec une clé gérée hors VPS (KMS ou coffre approuvé ; à défaut,
`age`/clé publique dont la clé privée n’est jamais stockée sur le VPS). Transférer
par canal authentifié vers un stockage hors VPS avec versioning/immutabilité si
disponible. Ne pas réutiliser le répertoire Git comme destination durable.

Politique à faire approuver : sauvegarde quotidienne, rétention courte pour les
instantanés quotidiens, hebdomadaire et mensuelle pour l’historique, avec au moins
une copie hors site et une copie protégée contre la suppression. La rotation doit
supprimer uniquement des sauvegardes dont l’âge, l’empreinte et la présence d’une
copie de remplacement sont vérifiés.

## 5. Contrôles d’intégrité et restauration

Après création : vérifier `sha256sum -c`, tailles et nombre d’objets, lecture d’un
échantillon audio et cohérence des clés. Après transfert : vérifier l’empreinte de
l’archive chiffrée et du manifeste côté réception.

Restaurer uniquement dans un projet Compose isolé avec nouveaux volumes, réseau,
base, bucket et identifiants. Utiliser des outils PostgreSQL de même version majeure.
Restaurer la base et MinIO ensemble, vérifier `alembic current`, les comptages,
identifiants, compteurs de prises, transcriptions, historiques, relations et
réconciliation des objets. Tester ensuite login, lecture audio/Range, transcription,
export, permissions et readiness. Consigner durée, résultat et écarts.

## 6. Risques, autorisations et retour arrière

Risques : données incohérentes, fuite de secrets, sauvegarde illisible, capacité
insuffisante du VPS, écrasement d’un bucket, mélange d’époques PostgreSQL/MinIO et
fausse preuve de copie hors site. Autorisation requise du responsable données,
exploitation et sécurité ; autorisation séparée avant lecture de contenu réel et
avant restauration.

En cas d’échec de sauvegarde : ne pas réactiver les écritures si la cohérence n’est
pas établie, conserver les journaux sans secrets et recommencer après diagnostic.
En cas d’échec de restauration : détruire uniquement l’environnement isolé après
inventaire autorisé, conserver l’artefact pour analyse et ne rien toucher à la
production. Une restauration de production n’est pas un retour arrière acceptable
pour ce ticket.

## Décision

Le plan est **PRÊT POUR AUTORISATION** ; aucune sauvegarde réelle ne doit être
effectuée avant signature de la fenêtre, de la destination hors VPS, du chiffrement,
de la rétention et du test de restauration.
