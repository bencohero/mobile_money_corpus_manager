# G11.1 — Manifeste des candidats de cache

**Statut :** `TARGETING NOT GUARANTEED`  
**Suppression exécutée :** aucune  
**Builder audité :** `default` / driver `docker`

## 1. Inventaire global

| Élément | Résultat |
|---|---:|
| Entrées BuildKit | 894 |
| Entrées `regular` | 857 |
| Entrées `source.local` | 37 |
| `Reclaimable=true` | 893 |
| `Shared=true` | 88 |
| `Reclaimable=false` | 1 |
| Champ `InUse` disponible | Non |
| Taille `docker system df` | 15,58 Gio |
| Récupérable annoncé par Docker | 10,61 Gio |

## 2. Présélection mécanique

La requête locale suivante a été évaluée sans suppression :

```text
Type=regular AND Reclaimable=true AND Shared=false
AND LastUsedAt affiché comme 8 weeks, 9 weeks, months ou year
```

Résultat : **51 entrées**, environ **3,09 Gio logiques**.

Cette liste n’est pas une liste supprimable. Les descriptions montrent des couches Superset, Node et Python d’une autre application hébergée. Leur suppression pourrait dégrader les reconstructions de Superset ou d’autres services. Le champ `InUse` manque, et `LastUsedAt=2 months ago` ne donne pas une date exacte. Les 51 entrées sont donc classées **À CONSERVER / À INVESTIGUER**, et non catégorie B validée.

## 3. Liste nominative de la présélection exclue

| ID | Taille | Dernière utilisation | Mutable | Motif d’exclusion |
|---|---:|---|---|---|
| `60406sutj1hbg0zo8ni6mj4xq` | 4,128 kB | 2 months ago | false | couche Superset/Python |
| `iy0fxkepx5f7ziuozjxvqpnax` | 4,128 kB | 2 months ago | false | couche Superset |
| `w5692xy72hobcq2ulexv49va3` | 8,192 kB | 2 months ago | true | mutable, provenance autre application |
| `8bc596aol34vxnldj7d0o8ekz` | 8,224 kB | 2 months ago | false | couche Superset |
| `k4fujbr07ne3o5hs44y6rq3b1` | 8,224 kB | 2 months ago | false | couche Superset |
| `ihwaqxm6qc7p1io3ucv1fziri` | 12,29 kB | 2 months ago | false | couche Superset |
| `s9x1y69tbp8p4snb5p8aep8v4` | 12,32 kB | 2 months ago | false | couche Superset |
| `jvs2r7ygbndl5mqxod07oz8zn` | 12,41 kB | 2 months ago | false | couche Superset |
| `wa4r5wz1vbh38gu5lv4dbyopu` | 16,5 kB | 2 months ago | false | couche Superset |
| `vdppw75pbt0juechgfirtc081` | 16,5 kB | 2 months ago | false | couche Superset |
| `3swejv7b3co6tbha5rd7jkg8v` | 16,63 kB | 2 months ago | false | base Python externe |
| `8g83vj1lq3clsdsal8ffqv1b3` | 20,51 kB | 2 months ago | false | couche Superset/Playwright |
| `mxlalism9pqv9xc9c8zq8qbwc` | 21,47 kB | 2 months ago | false | couche Superset |
| `estm6i7r9xss0gqhsy7v6knen` | 22,92 kB | 2 months ago | false | couche Superset |
| `q1t9w6946z9rdpv2wkkovwgt1` | 24,61 kB | 2 months ago | false | couche Superset |
| `woqnbl2w0180ofzlyngimpdzv` | 28,83 kB | 2 months ago | false | couche Superset |
| `qafdpifh800x46mcgdzczlktr` | 28,84 kB | 2 months ago | false | couche Superset |
| `iupinplqubsxrfo5jvjfalu2k` | 29,9 kB | 2 months ago | false | couche Superset |
| `lmeotk3fveq0d84kubcgh7nhi` | 37,13 kB | 2 months ago | false | couche Superset |
| `liai2b1juy2l0h8w6hgu185hq` | 42,27 kB | 2 months ago | false | couche Superset |
| `5i0mslejzi1j1zp6jnchq1wa9` | 66,77 kB | 2 months ago | false | couche Superset |
| `pdgra666rkj12gfas4sgq0wbz` | 67,15 kB | 2 months ago | false | couche Superset |
| `90ta453n4w16581glayn6zx5h` | 69,19 kB | 2 months ago | false | couche Superset |
| `hgpk6fzyw8dfb7l6aqbo66a06` | 72,95 kB | 2 months ago | false | base Node externe |
| `1jipb4m26rc4pccwqxipke0ls` | 76,01 kB | 2 months ago | false | couche Superset |
| `n3jnzqi0gbj7yvwc50xe0nw5i` | 149,1 kB | 2 months ago | false | couche Superset |
| `pg0hgqaey8m50hj07okctpcx7` | 172,2 kB | 2 months ago | false | couche Superset |
| `fr0n2tsppe29d7o88pcp0h0yo` | 317,6 kB | 2 months ago | false | couche Superset |
| `i7p14x6c6fq3czc6h64ercgt5` | 380,2 kB | 2 months ago | false | couche Superset |
| `owmw9rogkhzx8d87i2z8ube95` | 390,1 kB | 2 months ago | false | couche Superset |
| `yhf9ipcjd1nvdn4ixx8v4u294` | 482,9 kB | 2 months ago | false | couche Superset |
| `qt53bthu06ldefp65vd6hng9k` | 6,233 MB | 2 months ago | false | base Python externe |
| `l9v22bi8pjc6dcmo7mckxms6k` | 9,115 MB | 2 months ago | false | base Node externe |
| `jb63erdra1a3cpipusp5c631u` | 19,74 MB | 2 months ago | false | couche Superset |
| `h04w2mumjv89eqjs8hv9zv7f2` | 19,88 MB | 2 months ago | false | couche Superset |
| `kqfndgymm16v514s6r344xi7p` | 21,01 MB | 2 months ago | false | couche Superset |
| `8tnb3aalow0rbkt6pr168uy5b` | 23,94 MB | 2 months ago | false | couche Superset |
| `eqnxymu0q2xltrgvcdav6ecgj` | 24 MB | 2 months ago | false | couche Superset |
| `jq29omnncavlnkwhndn7rli2r` | 29,78 MB | 2 months ago | false | provenance non attribuée |
| `k9x13dr4mfy2u2bu79yy9t59a` | 54,26 MB | 2 months ago | false | couche Superset |
| `17k8tktq8t996t25o5miy3us6` | 62,74 MB | 2 months ago | false | base Python externe |
| `lduemispz1v3d1nlm8jl510wb` | 96,26 MB | 2 months ago | false | couche Superset |
| `ujv0rdywvsxx1151dgn4rzzml` | 115,6 MB | 2 months ago | false | couche Superset |
| `ptisqsqeqbajick3c34kj4msz` | 117,2 MB | 2 months ago | false | base Python externe |
| `ry60zofgtg7m8lq21j3p3kq67` | 128,3 MB | 2 months ago | false | couche Superset |
| `fg1r0xcpu8thpf2yiw1ylvf0z` | 131,8 MB | 2 months ago | false | couche Superset |
| `rxkp1yf1mhh0anzu516wjdw2w` | 191 MB | 2 months ago | false | couche Superset |
| `awwnhk9runjxoi4009k5fklrs` | 206,1 MB | 2 months ago | false | base Node externe |
| `n0n75avghv82fhhcpu8kgr2uh` | 400,5 MB | 2 months ago | false | couche Superset |
| `k8q6mo72acwn55kb7k1fomn86` | 482,7 MB | 2 months ago | false | couche Superset |
| `sii384ww1e7p8mfhgkey308s5` | 1,17 GB | 2 months ago | false | couche Superset |

Les descriptions sont des métadonnées de build, pas une preuve absolue de propriété ; elles suffisent néanmoins à exclure ces entrées du périmètre du Corpus Manager tant que le propriétaire Superset/infra n’a pas validé leur retrait.

## 4. Entrées explicitement exclues

- 88 entrées `Shared=true`.
- 37 entrées `source.local`, dont plusieurs récentes et mutables.
- 1 entrée `Reclaimable=false`, ID `ql50y7h3gan0s91o3xwro36ls`, 823,3 kB, sans date d’utilisation.
- Toutes les entrées utilisées récemment ou dont la date est inconnue.
- Toutes les couches décrites comme Superset, Node, Python externe ou appartenant à une autre application.
- Toutes les couches potentiellement nécessaires à production, développement, rollback G8.5-R ou validation utile.
- Toutes les images, conteneurs, volumes, réseaux et fichiers de sauvegarde : hors périmètre de ce manifeste.

## 5. Résultat de classification

| Catégorie | Nombre | Taille indicative | Décision |
|---|---:|---:|---|
| A — Protégé | 894 | 15,58 Gio logiques | conserver |
| B — Candidat démontré | 0 | 0 | aucun |
| C — Incertain / autre propriétaire | 51 présélectionnées + autres | ~3,09 Gio pour la présélection | conserver/investiguer |

**Aucun lot nominatif sûr n’est proposé.** La présélection de 51 entrées n’est pas une autorisation et ne doit pas être passée à `buildx prune`.
