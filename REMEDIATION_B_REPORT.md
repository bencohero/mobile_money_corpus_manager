# REMEDIATION B — intégrité multilingue et concurrence des transcriptions

## 1. Diagnostic initial

Le lot A était présent et l’arbre Git était propre au démarrage (`5377f43`). La révision attendue était `0006_multilingual_participant_identity`.

Les écarts DB-001 constatés étaient les suivants : `workshops.language_code` et `participants.language` étaient contrôlés par l’application mais pas entièrement par PostgreSQL ; `participants.language` n’avait pas de référence canonique FK ; l’atelier historique de 0005 pouvait rester sans langue, ce qui est volontaire et doit rester une décision humaine.

L’écart CONC-001 était direct : une transcription existante était modifiée puis commitée sans condition sur une version, sans historique métier et sans retour 409.

## 2. Migration ajoutée

`0007_integrity_and_transcription_versions` est chaînée après 0006 et ne modifie pas 0006. Elle :

- diagnostique les langues inconnues, les ateliers/participants incohérents et les références orphelines ;
- échoue avec les compteurs détaillés si une décision humaine est nécessaire ;
- ajoute `participants.language_code` canonique, FK vers `languages`, et FK `workshops.language_code` vers `languages` ;
- initialise les compteurs de version historiques à 1 sans renommer les identifiants ;
- crée `transcription_history` et une ligne `BASELINE` par transcription existante ;
- rend la liaison transcription-enregistrement détachable afin qu’une suppression d’audio conserve l’historique comme tombstone.

Aucune langue n’est attribuée automatiquement aux ateliers historiques sans information connue.

## 3. Concurrence et historique

Chaque transcription possède maintenant `version`. La sauvegarde effectue un `UPDATE ... WHERE id=? AND version=?` atomique ; une seule session peut donc avancer la version. Une version périmée renvoie HTTP 409 avec la version et le contenu courant, sans écraser le brouillon distant.

L’historique conserve transcription, anciennes/nouvelles valeurs, auteur, UTC, statut et versions précédente/nouvelle. Les contenus ne sont pas écrits dans les logs techniques. Les changements de statut de vérification avancent également la version et écrivent l’historique.

L’endpoint permissionné `/api/transcriptions/{id}/history` permet la consultation. L’espace transcripteur transmet la version chargée, intercepte le 409, conserve le texte local et affiche la version/contenu distant sans remplacement automatique.

## 4. Compatibilité historique

Les identifiants participants existants et les compteurs ne sont pas modifiés. `participants.language` historique est conservé ; `language_code` canonique est dérivé uniquement lorsqu’il correspond à une langue connue. Les ateliers historiques non attribués restent non attribués. Les suppressions d’audio ne suppriment plus les transcriptions ni leur historique.

Les nouveaux participants héritent exclusivement de la langue de l’atelier et leur identifiant est préfixé par cette langue. Les séquences restent indépendantes par langue.

## 5. Tests et résultats

Validation PostgreSQL/MinIO dans une base de test recréée depuis zéro :

- migration Alembic complète jusqu’à `0007_integrity_and_transcription_versions` ;
- vérification des colonnes, FK, table d’historique et version Alembic ;
- tests ciblés DB/concurrence/workflow : **24 passed** (dont 3 tests dédiés au lot B) ;
- suite complète après alignement des assertions historiques avec le contrat multilingue : **147 passed, 1 skipped** ; le test concurrentiel ajouté ensuite passe également dans le ciblage lot B ;
- `git diff --check` et compilation Python : OK.

Le scénario de conflit est couvert par le chemin atomique de version : deux lectures à la même version, première sauvegarde acceptée et incrémentée, seconde refusée 409 ; la valeur distante reste intacte et le brouillon local reste dans le formulaire.

## 6. Risques résiduels

- Les ateliers historiques sans langue restent volontairement indisponibles pour de nouvelles inscriptions jusqu’à attribution explicite.
- Les anciens clients qui n’envoient pas `version` bénéficient d’une compatibilité transitoire ; l’interface actuelle envoie systématiquement la version. Cette compatibilité devra être retirée après migration de tous les clients API.
- Les timestamps utilisent encore le mécanisme UTC historique `datetime.utcnow()` du projet ; cela produit des avertissements de dépréciation Python mais ne change pas le stockage UTC actuel.

## 7. Déploiement sûr et retour arrière

1. Faire un backup PostgreSQL et MinIO, puis restaurer ce backup dans une base de validation séparée.
2. Exécuter le diagnostic de 0007 sur la copie ; arrêter et faire décider toute ligne incompatible.
3. Avec les écritures de production arrêtées pendant la fenêtre de migration, exécuter `alembic upgrade head` uniquement sur la base ciblée après validation.
4. Vérifier `alembic_version`, les FK PostgreSQL, les compteurs, le nombre de participants/enregistrements/transcriptions et quelques historiques représentatifs.
5. Redémarrer l’application et tester un conflit avec deux sessions non privilégiées.

La migration n’est pas à exécuter directement sur la production sans cette copie validée. Le retour arrière applicatif se fait en désactivant les écritures et en restaurant le backup validé ; les downgrades destructifs sont volontairement bloqués pour ne pas perdre les compteurs, transcriptions ou historiques.
