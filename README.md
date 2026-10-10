# Omokage — candidature Uchiha (Izuma)

Site de candidature pour le clan Uchiha : **Uchiha Izuma**, dix ans et demi, de la lignée d'Izuna, descendant de Setsuna.
Un enfant à qui tout le monde dit qu'il a le visage de son père, et qui ne reconnaît pas les visages.

Le site est statique : HTML, CSS et JavaScript natifs, sans dépendance ni étape de compilation.

## Ouvrir le site

- **Le plus simple** : double-cliquer sur `index.html`. Tout fonctionne, y compris la version texte.
- **Avec un petit serveur local** (plus proche de la version en ligne) :

  ```
  python -m http.server 4180
  ```

  puis ouvrir http://localhost:4180 dans le navigateur.

## Contenu

| Fichier | Rôle |
| --- | --- |
| `index.html` | Tout le texte de la candidature (récit, fiche, psychologie, relations, objectifs…). C'est le seul fichier à modifier pour changer le contenu. |
| `candidature.txt` | Version texte brut, prête à coller dans la section clan du launcher. Générée à partir de `index.html`. |
| `assets/css/style.css` | Direction artistique : papier, encre, vermillon, carnet. |
| `assets/js/main.js` | Apparitions, fil de navigation, planche de photographies, chapitre du soir, version texte. |
| `assets/img/` | Les images fournies (le site en affiche des recadrages en CSS, sans modifier les fichiers). |
| `assets/audio/theme-shisui.mp3` | Musique de fond, jouée en boucle à partir du premier clic du visiteur ; le bouton « Musique » la coupe. Pour la changer, remplacer ce fichier en gardant le même nom. |
| `tools/build.py` | Corrige la typographie française, met à jour les caractères japonais chargés et régénère `candidature.txt`. |

## Après une modification du texte

```
python tools/build.py
```

Le script n'utilise que Python (aucune installation supplémentaire). Il remet les espaces insécables et les apostrophes typographiques, et réécrit `candidature.txt`.

## Publier sur GitHub Pages

1. Créer un dépôt public sur GitHub et y envoyer le contenu du dossier (le fichier `.nojekyll` est déjà présent).
2. Dans le dépôt : **Settings → Pages → Branch : `main`, dossier `/ (root)`**.
3. Le site est en ligne au bout d'une minute environ, à l'adresse `https://<compte>.github.io/<dépôt>/`.

Pour afficher l'adresse du site en tête de la version texte, la renseigner dans `SITE_URL` en haut de `tools/build.py`, puis relancer le script.

## Crédits

Personnage, texte et site écrits pour cette candidature. Images : planches fournies par le joueur.
Typographies : Cormorant Garamond, Newsreader, Shippori Mincho, Patrick Hand (Google Fonts).
Naruto appartient à Masashi Kishimoto ; l'univers est utilisé dans le cadre d'un jeu de rôle non commercial.
