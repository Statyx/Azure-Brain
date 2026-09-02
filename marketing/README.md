# Marketing — Azure-Brain teaser

`teaser-azure-brain-en.mp4` — 40,1 s · 1920×1080 · h264 · 30 fps · **sans piste audio**.

Dix boards typographiques enchaînés par des fondus de 0,5 s. Les durées sont **inégales et
délibérées** : la mise en place (boards 2-4) est resserrée pour que la révélation du brain
tombe à ~15 s au lieu de ~24 s, la révélation elle-même (board 5) respire, et le dernier
board est le plus long parce que rien ne s'enchaîne après lui. Le format reprend celui de
`Fab-Marketing-Campaign/marketing/teaser-c360.mp4`, lui aussi muet : le texte porte seul le
message.

## Pourquoi le script est ici

Le teaser de référence a été produit hors du dépôt et ne peut plus être remonté quand un
libellé change. `build_teaser.py` évite cette dérive : la copie, la mise en page et
l'encodage sont dans ce fichier. Changer une phrase est une réexécution, pas une fouille
archéologique.

## Remonter la vidéo

```
python build_teaser.py --boards    # les 10 PNG seulement
python build_teaser.py --sheet     # planche contact 2×5, pour relire la séquence
python build_teaser.py --render    # boards -> mp4 + first-frame.png
python build_teaser.py --all
```

Prérequis : Python 3.10+, `playwright` (avec `playwright install chromium`) et `ffmpeg`.
Le script trouve `ffmpeg`/`ffprobe` sur le disque même s'ils ne sont pas dans le `PATH`
du shell courant — utile juste après un `winget install Gyan.FFmpeg`, qui demande un
redémarrage du shell qu'une session longue ne fait jamais.

## Sources des fonds

| Origine | Chemin | Boards |
|---|---|---|
| Ce dépôt | `docs/proof/*.png` | 1, 2, 5, 7, 8, 9, 10 |
| `Fab-Marketing-Campaign` | `marketing/screenshots/*.png` | 3 |
| Aucune | dégradé seul | 4, 6 |

Les captures de `Fab-Marketing-Campaign` sont résolues dans le checkout voisin. Si les deux
dépôts ne sont pas côte à côte, poser `FABRIC_DEMO_ROOT` sur le dossier qui les contient.
Un fond manquant arrête le script avec le chemin fautif, il ne produit pas un board vide.

Le board 4 (Network Operations) est volontairement typographique : `Fab-Network-Operations`
ne contient aucune capture. Le board 6 (« No application. Nothing to run. ») l'est aussi,
mais par choix — mettre une architecture déployée derrière cette phrase l'aurait contredite.

## Deux règles à ne pas casser

Les deux images qui comptent le plus sont la première et la dernière, et **aucune des deux
ne doit être noire**.

- **Pas de fondu au noir au début.** La première image sert de vignette dans l'Explorateur,
  Teams, PowerPoint et les aperçus de lien. Une première image noire fait passer le lien
  pour cassé.
- **Pas de fondu au noir à la fin.** La lecture s'arrête sur la dernière image : c'est elle
  que laisse à l'écran un lecteur en pause, une boucle ou un écran de fin. Fondre au noir
  jette le message de clôture et termine sur rien.

`--render` extrait `first-frame.png` et `last-frame.png`, et **échoue** si la luminance
moyenne de la fin passe sous 20 (le noir en YUV plage réduite vaut 16). Un fondu final se
réintroduit facilement et reste invisible pour tout contrôle qui ne regarde que la durée.

- **Pas de piste audio.** `-an` est délibéré et aligne le teaser sur la référence.
