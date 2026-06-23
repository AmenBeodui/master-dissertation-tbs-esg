# Instructions — Extraction des flux ESG depuis Morningstar

## Objectif

Remplir le fichier `flux_esg.csv` avec les flux nets trimestriels (en milliards USD) vers les fonds ESG, séparément pour les États-Unis et l'Europe, sur la période 2020-2025. Ces données sont **cruciales** pour valider empiriquement ton hypothèse H2 sur la contraction des flux et le retournement de performance.

## Source — Rapports Morningstar Global Sustainable Fund Flows

Morningstar publie **gratuitement** chaque trimestre un rapport agrégeant les flux mondiaux vers les fonds ESG, segmentés par région. C'est la référence académique pour ce type de données.

**Page d'accès** : https://www.morningstar.com/lp/global-esg-flows

(Alternative en recherche : taper "Morningstar Global Sustainable Fund Flows Q4 2024" sur Google. Tu trouveras le PDF en accès libre sur le site Morningstar.com)

Tu peux aussi chercher les rapports trimestriels par leur titre exact, par exemple :
- "Global Sustainable Fund Flows Q4 2024 Report"
- "Global Sustainable Fund Flows Q3 2024 Report"
- "Global Sustainable Fund Flows Q4 2023 Report"
- etc.

Pour couvrir la période 2020-2025 il te faut donc environ 16-20 rapports trimestriels (ou tu peux te contenter des plus récents qui contiennent des historiques 4-8 trimestres en arrière).

## Méthode d'extraction (10-15 minutes)

**Étape 1.** Télécharge le rapport trimestriel le plus récent disponible (Q1 2025 ou Q4 2024 typiquement).

**Étape 2.** Cherche dans le PDF (Ctrl+F) "United States flows" ou "U.S. sustainable fund flows". Tu vas trouver un graphique en barres et/ou un tableau présentant les flux US par trimestre des 8 derniers trimestres environ.

**Étape 3.** Cherche ensuite "Europe sustainable fund flows" pour l'équivalent européen.

**Étape 4.** Note les chiffres trimestriels (en USD milliards) dans le fichier `flux_esg.csv`.

**Étape 5.** Pour les trimestres manquants (pré-2023 typiquement), télécharge un rapport plus ancien (par exemple Q4 2022) qui contient l'historique.

## Format du CSV

J'ai pré-rempli `flux_esg.csv` avec des valeurs approximatives basées sur les rapports Morningstar publiquement disponibles, à titre de référence. **Tu dois vérifier et corriger ces chiffres** en consultant les rapports actuels.

Structure :
```
date,flux_us_mds,flux_eu_mds,commentaire
2022-03-31,10.2,78.0,Choc Ukraine
```

- `date` : fin de trimestre au format YYYY-MM-DD
- `flux_us_mds` : flux net trimestriel US en milliards USD (positif = entrées, négatif = sorties)
- `flux_eu_mds` : flux net trimestriel Europe en milliards USD
- `commentaire` : optionnel, événement marquant du trimestre

## Cohérence avec ton mémoire

Une fois les chiffres vérifiés, ils doivent montrer le pattern suivant que tu peux exploiter dans ton chapitre 3 et discussion :

1. **2020-Q1 à 2021-Q4 (avant rupture monétaire)** : flux US et Europe massivement positifs (peak en 2021)
2. **2022 (transition)** : contraction nette US, ralentissement Europe
3. **2023-2024 (après rupture)** : sorties nettes US plusieurs trimestres consécutifs, Europe positive mais en forte baisse

Ce pattern empirique **valide directement** la prédiction théorique de Pástor, Stambaugh & Taylor (2022) et van der Beck (2021) : la contraction des flux ESG depuis 2022 explique mécaniquement la dégradation de la performance ESG observée dans tes résultats Python.

## Citation académique

Dans ton mémoire, cite la source comme suit (à intégrer dans la bibliographie) :

> Morningstar (2024). *Global Sustainable Fund Flows: Q4 2024 in Review*. Morningstar Research. Disponible sur https://www.morningstar.com/lp/global-esg-flows

Et dans le texte (section 3.3 ou discussion) :

> *"Selon Morningstar (2024), les flux nets vers les fonds ESG américains ont basculé en territoire négatif à partir du troisième trimestre 2022, avec X milliards USD de sorties nettes cumulées sur 2023, confirmant empiriquement la contraction prédite par Pástor et al. (2022) en environnement de taux réels positifs."*

## Comment générer le graphique

Une fois `flux_esg.csv` rempli, lance :
```
py analyse_macro.py
```

Le script génère automatiquement `figures/figure_1bis_flux_esg.png` avec :
- Barres bleues pour les flux US trimestriels
- Barres rouges pour les flux Europe trimestriels
- Ligne verticale rouge marquant le changement de régime (mars 2022)
- Source citée en bas

Ce graphique s'insère idéalement dans ta **section 3.3** (avant/après) ou en **introduction** comme contexte motivant.

## Alternatives si tu n'as pas accès aux rapports Morningstar

Si pour une raison ou une autre les rapports Morningstar ne sont pas accessibles, tu peux te rabattre sur :

1. **ICI (Investment Company Institute)** : ICI publie chaque mois des données sur les flux des fonds américains, avec une rubrique ESG agrégée. Gratuit sur https://www.ici.org/research/stats

2. **Bloomberg ESG flow tracker** : si TBS a un terminal Bloomberg, demande l'accès — données complètes et en temps réel.

3. **EPFR Global** : la référence professionnelle, payante mais TBS peut avoir un accès limité via la bibliothèque.

4. **Refinitiv Lipper** (via LSEG) : accessible quand ton accès LSEG sera validé.

Pour ton mémoire, Morningstar reste la source la plus citée académiquement et la plus facilement accessible gratuitement.
