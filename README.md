# Master Dissertation TBS Education — Code & Données

**Auteur** : Amen Bedoui
**Programme** : MSc Banking & International Finance — TBS Education
**Promotion** : 2025-2026
**Date** : Juin 2026

---

## Titre du mémoire

**Impact du changement de régime de politique monétaire sur la performance comparée des stratégies d'investissement ESG et conventionnelles : une analyse avant/après sur les marchés actions américains et européens.**

---

## Contenu du dépôt

```
tbs_dissertation_package/
├── README.md                       <- Ce fichier
├── requirements.txt                <- Bibliothèques Python nécessaires
│
├── scripts/                        <- Code source Python
│   ├── analyse_esg.py             <- Pipeline principal (≈550 lignes)
│   ├── analyse_extensions.py      <- Section 3.7 : crises, sectoriel, flux, macro
│   └── analyse_macro.py           <- Régressions macro HAC Newey-West
│
├── data_lseg/                      <- Données primaires brutes
│   ├── etfs/                      <- 11 fichiers extraits, 10 retenus (LSEG Workspace)
│   │   ├── SPY.xlsx
│   │   ├── VTI.xlsx
│   │   ├── ESGU.xlsx
│   │   ├── ESGV.xlsx
│   │   ├── SUSA.xlsx
│   │   ├── DSI.xlsx
│   │   ├── SUSL.xlsx
│   │   ├── VEA.xlsx
│   │   ├── IEFA.xlsx
│   │   ├── ESGD.xlsx
│   │   └── VSGX.xlsx
│   │
│   ├── macro/                     <- Indicateurs macroéconomiques
│   │   ├── US_10_Y.xlsx           <- Taux 10Y US (LSEG)
│   │   ├── US10YT_RR.xlsx         <- Variante alternative
│   │   ├── CLc1.xlsx              <- WTI Oil (LSEG / NYMEX)
│   │   └── DXY.xlsx               <- US Dollar Index (LSEG / ICE)
│   │
│   ├── flux_esg.csv               <- Flux Morningstar (19 trimestres)
│   ├── instructions_flux_esg.md   <- Documentation flux ESG
│   └── prices_lseg_consolidated.xlsx  <- Données ETFs consolidées
│
└── outputs/                        <- Résultats générés
    ├── figures/                   <- 10 figures PNG (150-300 DPI)
    └── tables/                    <- Tableaux exportés
```

---

## Sources des données

### Données primaires

| Source | Type de données | Période |
|---|---|---|
| **LSEG Workspace** (Refinitiv Eikon) | Prix de clôture quotidiens des 10 ETFs | 02/01/2020 — 01/06/2026 |
| **LSEG Workspace** | Taux 10 ans US (US10YT=RR) | 2020-2026 |
| **LSEG Workspace** | WTI Oil (CLc1, NYMEX) | 2020-2026 |
| **LSEG Workspace** | US Dollar Index (.DXY, ICE) | 2020-2026 |
| **Yahoo Finance** (yfinance API) | VIX (^VIX, CBOE) | 2020-2026 |
| **Morningstar Global Sustainable Fund Flows** | Flux nets ESG par zone (US, Europe) | 2020 Q1 — 2024 Q4 |
| **Federal Reserve H.15** | Fed Funds Rate | 2015-2025 |
| **ECB Statistical Data Warehouse** | ECB Deposit Facility Rate | 2015-2025 |
| **Kenneth French Data Library** | Facteurs Fama-French 3, 5 et Carhart MOM | 2020-2026 |

> **Note sur la reproductibilité des indicateurs macro :** les fichiers LSEG
> (taux 10Y, WTI, DXY) constituent la **source primaire archivée** dans
> `data_lseg/macro/`. Pour permettre une exécution publique sans accès LSEG, le
> script `analyse_extensions.py` télécharge des proxys équivalents via yfinance
> (`^TNX` pour le 10Y, `CL=F` pour le WTI, `UUP` comme proxy du dollar). Les
> résultats sont quasi identiques ; les fichiers LSEG restent la référence du mémoire.

### Données secondaires (composition sectorielle)

| Source | Usage |
|---|---|
| Factsheets MSCI au 31/12/2024 | Décomposition sectorielle (Tableau 9, Figure 5) |
| Factsheets iShares.com, Vanguard.com, SSGA.com | Méthodologie ESG, TER, AUM, top 10 holdings (Tableau A3) |

---

## Méthodologie

### Échantillon

10 ETFs sélectionnés selon la couverture géographique et le type de stratégie :

| Marché | Conventionnel | ESG |
|---|---|---|
| **États-Unis** | SPY, VTI | ESGU, ESGV, SUSA, DSI |
| **International (EAFE)** | VEA, IEFA | ESGD, SUSL |

> Remarque : le fichier `VSGX.xlsx` figure dans `data_lseg/etfs/` (donnée collectée
> lors de l'extraction LSEG) mais n'est **pas retenu** dans l'analyse finale, afin
> de conserver un appariement équilibré ESG/conventionnel par zone géographique.

### Date de rupture monétaire

**16 mars 2022** : première hausse du taux directeur de la Fed depuis décembre 2018.

### Méthodes économétriques

1. **Statistiques descriptives** : rendement annualisé, volatilité, skewness, kurtosis
2. **Ratios de performance ajustée du risque** : Sharpe, Sortino, Calmar, Drawdown maximum
3. **Tests sur la stabilité dans le temps** : tests de Welch (égalité des moyennes), test de Chow
4. **Régressions multifactorielles** :
   - CAPM (1 facteur)
   - Fama-French 3 facteurs : Mkt-Rf, SMB, HML
   - Fama-French 5 facteurs : ajout RMW, CMA
   - Carhart 4 facteurs : Mkt-Rf, SMB, HML, MOM
5. **Régressions macro** : excès rendement ESG-Conv sur Δ_TNX, Δ_VIX, Ret_Oil, Ret_USD
6. **Correction des erreurs standard** : Newey-West HAC avec 5 retards (gestion hétéroscédasticité + autocorrélation)
7. **Analyse événementielle** : 4 épisodes de stress (COVID, Ukraine, SVB, Israël-Hamas)

---

## Hypothèses testées

| # | Label | Énoncé | Verdict |
|---|---|---|---|
| **H1** | Illusion d'alpha ESG | La surperformance ESG pré-2022 est un biais factoriel (growth/large-cap/quality), pas un véritable alpha. | **Validée** (α ≈ 0 sur 6/6 régressions multifactorielles) |
| **H2** | Prime de flux conditionnelle | La performance ESG-Conv est conditionnée par le régime de flux. | **Validée** (Δ Sharpe : +0,037 → -0,043 coïncide avec inflexion flux Morningstar) |
| **H3** | SFDR comme protection asymétrique | Le SFDR fonctionne comme un « put » implicite : protection en crise, pas génération d'alpha. | **Validée** (asymétrie ×17 vs US sur SVB) |

---

## Installation et exécution

### Prérequis Python

```bash
pip install -r requirements.txt
```

### Exécution

```bash
# Pipeline principal (statistiques + régressions multifactorielles)
python scripts/analyse_esg.py

# Extensions (section 3.7 du mémoire)
python scripts/analyse_extensions.py

# Régressions macro avec HAC Newey-West
python scripts/analyse_macro.py
```

### Durée d'exécution

~ 2-3 minutes sur une machine standard (Lenovo X1 Carbon, i7).

### Outputs générés

- `outputs/resultats_esg.xlsx` : tous les tableaux (1 à 7)
- `outputs/tableaux_extensions.xlsx` : tableaux section 3.7 (9 à 12)
- `outputs/figures/*.png` : 10 figures en haute résolution
- `outputs/log_execution.txt` : journal détaillé avec toutes les valeurs clés

---

## Reproductibilité

Le script `analyse_esg.py` peut être exécuté en mode **autonome** (download Yahoo Finance + Fama-French Library) ou en mode **LSEG local** (lecture des fichiers `data_lseg/etfs/*.xlsx`). Le mode par défaut utilise yfinance pour la reproductibilité publique.

Pour le mode LSEG local, dé-commenter la fonction `load_lseg_etf()` au début de `analyse_esg.py`.

---

## Contact

**Amen Bedoui**
MSc Banking & International Finance
TBS Education — Promotion 2026

Apprentissage : ALGIZ (France, Monaco, Allemagne)

---

## Licence

Code distribué sous licence MIT pour usage académique et de recherche.
Données financières propriétaires (LSEG Workspace) : usage limité au cadre du mémoire académique.
