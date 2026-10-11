# F.4 — Conception du gel des écritures

Date : 2026-10-11  
Statut : **BLOQUÉ POUR PRODUCTION — mécanisme applicatif à valider**

## 1. Limite actuelle

L’application ne présente pas de commutateur de maintenance/read-only dédié dans le
Compose ou la configuration inspectée. Arrêter brutalement le conteneur n’est donc
pas retenu : cela peut laisser une réservation ou une compensation PostgreSQL/MinIO
indéterminée et ne donne pas une preuve de cohérence.

## 2. Mécanisme proposé

Mettre en place un verrou réversible en deux phases :

1. **Gate de trafic** : appliquer une configuration dynamique Traefik candidate qui
   renvoie `503` aux nouvelles requêtes du routeur Corpus, sans toucher à PostgreSQL,
   MinIO ni aux volumes. Cette gate doit être testée hors production et porter un
   identifiant/horodatage dans les logs.
2. **Drain contrôlé** : attendre la fin des requêtes déjà acceptées pendant un délai
   borné, puis vérifier en lecture seule PostgreSQL que les traitements actifs sont
   nuls. Si la gate Traefik ne suffit pas à contrôler les connexions persistantes,
   l’application doit recevoir un mode read-only explicite avant autorisation.

La gate bloque aussi les lectures pendant la fenêtre ; cela réduit la surface de
course et doit être annoncé aux utilisateurs. Aucun `docker stop` n’est requis.

## 3. Contrôles de fin de traitement

Après activation de la gate, exécuter sur une copie ou, seulement après autorisation,
sur PostgreSQL production avec une requête sans contenu métier :

```sql
SELECT count(*) FROM recordings WHERE sync_status = 'PENDING';
SELECT count(*) FROM recording_submissions WHERE state = 'PENDING';
SELECT count(*) FROM recordings WHERE sync_status NOT IN ('READY', 'ERROR');
```

Le premier et le deuxième compteur doivent être zéro après le délai de drain. Les
états `ERROR` sont conservés et réconciliés ; ils ne sont pas supprimés. Une
transcription `verification_status='PENDING'` est normalement un état métier de
revue et ne signifie pas nécessairement un traitement actif : il faut capturer son
compteur de référence et obtenir l’accord du responsable données avant de le traiter
comme un blocage.

Critère d’arrêt : compteur actif non nul après le délai approuvé, requête DB en
attente, objet MinIO manquant, échec de readiness ou nouvelle écriture observée.

## 4. Sauvegarde et réouverture

Quand la gate est active, les contrôles sont zéro et les compteurs de référence sont
consignés, exécuter la sauvegarde PostgreSQL puis MinIO dans la même fenêtre UTC,
produire les manifestes et vérifier les empreintes. Valider localement la lecture
des archives, puis rétablir le trafic et vérifier `/health`, `/ready`, une lecture
non destructive et l’absence de nouvelle anomalie. Retirer la gate seulement après
validation des archives ; ne pas la retirer automatiquement sur erreur.

## 5. Retour arrière

Si le drain ne converge pas, maintenir la gate, ne pas sauvegarder et escalader au
responsable applicatif. Si la gate provoque un comportement inattendu, retirer
uniquement la configuration candidate après capture des logs et rétablir la route
précédente. Si les archives sont incohérentes, maintenir l’écriture bloquée jusqu’à
une nouvelle décision ; ne jamais prétendre à une cohérence par simple horodatage.

## 6. Validation nécessaire

Le mécanisme est conceptuellement vérifiable mais n’est pas encore une capacité
production démontrée. Le propriétaire applicatif doit valider la gate ou fournir un
mode read-only intégré ; l’exploitation doit mesurer le drain ; le responsable
données doit valider les états PENDING et la fenêtre.
