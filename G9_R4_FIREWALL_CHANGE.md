# G9-R4 — Correction réseau proposée

Statut au 2026-10-13 : **PRÉPARÉE, NON APPLIQUÉE**

## Correction minimale

Bloquer TCP `8090` dans la chaîne Docker `DOCKER-USER`, pour IPv4 et IPv6,
en filtrant le port de destination original (`8090`) via conntrack. Cette
position est nécessaire car une règle UFW/INPUT seule peut être contournée par
le chemin de publication Docker et son DNAT/docker-proxy.

Exemple à exécuter uniquement par un opérateur root, après capture de l’état et
validation de la chaîne existante :

```sh
iptables  -I DOCKER-USER 1 -m conntrack --ctstate NEW -p tcp \
  -m conntrack --ctorigdstport 8090 -j DROP
ip6tables -I DOCKER-USER 1 -m conntrack --ctstate NEW -p tcp \
  -m conntrack --ctorigdstport 8090 -j DROP
```

La règle ne touche ni `22`, ni `80`, ni `443`, ni les réseaux applicatifs, et ne
modifie aucun fichier, conteneur, volume, Traefik, base, MinIO ou image. Les
connexions déjà établies ne doivent pas être coupées par cette règle limitée à
`NEW`; une nouvelle connexion au dashboard doit être refusée.

Avant application, vérifier que `DOCKER-USER` existe, que le backend iptables
est celui réellement utilisé et que l’ordre de priorité ne permet pas un
`ACCEPT` antérieur. Si la politique active est nftables native, traduire la
règle dans l’emplacement équivalent avant exécution; ne pas mélanger deux
politiques sans connaître leur ordre.

## Préconditions obligatoires

1. Session SSH principale et session de secours indépendantes confirmées.
2. Sorties root archivées : UFW, nftables, iptables/ip6tables, `ss`.
3. Règle Contabo vérifiée : `8090/tcp` refusé, `22/tcp`, `80/tcp` et `443/tcp`
   conservés.
4. Aucun client opérationnel identifié sur le dashboard public; accès admin de
   remplacement par tunnel SSH ou réseau privé si nécessaire.
5. Captures avant changement : santé app, route HTTPS, état Traefik, ports et
   empreintes des fichiers de configuration Traefik.

Ne pas exécuter `ufw deny 8090` seul sans preuve qu’UFW filtre effectivement le
chemin Docker. Ne pas modifier `docker-compose.yml`, `traefik.yml`,
`config.yml` ni redémarrer Traefik dans cette correction.

## Retour arrière

Capturer d’abord le numéro/empreinte de la règle ajoutée. En cas de perte d’un
accès autorisé ou d’un effet inattendu, supprimer uniquement cette règle par son
numéro ou avec la même spécification exacte, puis vérifier SSH, HTTPS et la
santé applicative. Ne pas restaurer toute la table de pare-feu et ne pas
réouvrir durablement `8090` sans restriction compensatoire.

## Vérification après application

Depuis un réseau extérieur indépendant : `8090` doit être `timeout` ou `refused`
en IPv4 et IPv6. Depuis le VPS ou le réseau Docker autorisé, vérifier séparément
les sondes locales nécessaires. Puis contrôler `80/443`, SSH, `/health`,
`/ready`, connexion, déconnexion et les journaux.
