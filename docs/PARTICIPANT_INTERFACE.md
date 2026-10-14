# Interface participant

## Parcours

Le participant s’inscrit avec un code d’atelier, reçoit un identifiant `MOS_NNN` généré par le serveur, se connecte puis suit le parcours : phrase à prononcer → enregistrement → écoute → envoi → phrase suivante.

Les écrans participant sont l’accueil, l’enregistrement, « Mes enregistrements » et l’aide. La navigation ne contient pas les fonctions de l’administration, de la transcription ou de la vérification.

## Écrans et messages

L’accueil affiche l’identifiant public et le nombre d’enregistrements envoyés. L’écran d’enregistrement affiche seulement la phrase, les boutons « Commencer l’enregistrement », « Arrêter », « Écouter », « Recommencer » et « Envoyer mon enregistrement ». Les états sont annoncés dans une zone `status` : envoi en cours, succès, traitement en cours, erreur réseau, microphone refusé ou absence de son.

Un atelier fermé ou expiré affiche « Cet atelier est terminé. Aucun nouvel enregistrement n’est possible. » Le contrôle est également réalisé côté serveur à l’ouverture, lors de la prévisualisation et lors de l’envoi.

## Sécurité et retry

Le rôle, l’identifiant et l’atelier ne sont jamais fournis par le participant à l’inscription. Le serveur rattache le compte et chaque enregistrement à l’atelier du code. Les routes d’enregistrement conservent le contrôle CSRF, du consentement, des permissions et de l’atelier actif.

Le numéro de prise reste attribué par le serveur. La clé d’idempotence est créée pour une nouvelle capture et conservée lors d’un retry du même blob ; un double clic ne crée donc pas une seconde soumission. Les états `PENDING`, `READY` et `ERROR` sont traduits en messages simples dans l’écran.

## Microphone et limites connues

Le navigateur doit autoriser le microphone et prendre en charge `MediaRecorder`. La capture reste en mémoire du navigateur ; aucun stockage vocal permanent local n’est ajouté. Une interruption réseau laisse la capture disponible pour un nouvel envoi avec la même clé.

## Tests manuels à effectuer

Sur Chrome Android, tester l’inscription, la copie de `MOS_NNN`, la connexion, le refus puis l’autorisation du microphone, l’écoute, la recommencement, l’envoi lent, l’interruption réseau, le double clic, la fermeture/réouverture du navigateur, un atelier désactivé et les largeurs 320, 360, 390 et 412 px. Vérifier aussi le clavier, le zoom à 200 % et un lecteur d’écran.
