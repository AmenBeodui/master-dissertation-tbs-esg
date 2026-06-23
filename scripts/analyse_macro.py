"""
========================================================================
Master Dissertation - TBS Education
ANALYSE MACRO - VERSION OFFLINE (sans dépendance internet)
========================================================================

Cette version contient les données Fed Funds Rate et ECB Deposit Rate
directement embarquées (issues des sources officielles Federal Reserve
et ECB). Aucune connexion internet requise pour générer le graphique.

Prérequis : pandas matplotlib (déjà installés)

Usage :
    py analyse_macro.py

Outputs :
    - figures/figure_0_taux_directeurs.png
    - figures/figure_1bis_flux_esg.png
========================================================================
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import warnings
warnings.filterwarnings('ignore')

OUTPUT_DIR = 'figures'
os.makedirs(OUTPUT_DIR, exist_ok=True)

SPLIT_DATE = pd.to_datetime('2022-03-16')

print("=" * 72)
print("ANALYSE MACRO (offline) — Graphique de contexte taux directeurs")
print("=" * 72)

# Fed Funds Effective Rate — Changements 2015-2025
fed_changes = [
    ('2015-01-01', 0.12), ('2015-12-17', 0.39),
    ('2016-12-15', 0.66),
    ('2017-03-16', 0.91), ('2017-06-15', 1.16), ('2017-12-14', 1.41),
    ('2018-03-22', 1.69), ('2018-06-14', 1.91), ('2018-09-27', 2.18), ('2018-12-20', 2.40),
    ('2019-08-01', 2.13), ('2019-09-19', 1.90), ('2019-10-31', 1.65),
    ('2020-03-03', 1.15), ('2020-03-16', 0.10),
    ('2021-01-01', 0.08),
    ('2022-03-17', 0.33), ('2022-05-05', 0.83), ('2022-06-16', 1.58), ('2022-07-28', 2.33),
    ('2022-09-22', 3.08), ('2022-11-03', 3.83), ('2022-12-15', 4.33),
    ('2023-02-02', 4.58), ('2023-03-23', 4.83), ('2023-05-04', 5.08),
    ('2023-07-27', 5.33),
    ('2024-09-19', 4.83), ('2024-11-08', 4.58), ('2024-12-19', 4.33),
    ('2025-09-18', 4.08), ('2025-12-15', 3.83),
]

# ECB Deposit Facility Rate — Changements 2015-2025
ecb_changes = [
    ('2015-01-01', -0.20),
    ('2015-12-09', -0.30),
    ('2016-03-16', -0.40),
    ('2019-09-18', -0.50),
    ('2022-07-27', 0.00), ('2022-09-14', 0.75), ('2022-11-02', 1.50), ('2022-12-21', 2.00),
    ('2023-02-08', 2.50), ('2023-03-22', 3.00), ('2023-05-10', 3.25),
    ('2023-06-21', 3.50), ('2023-08-02', 3.75), ('2023-09-20', 4.00),
    ('2024-06-12', 3.75), ('2024-09-18', 3.50), ('2024-10-23', 3.25), ('2024-12-18', 3.00),
    ('2025-03-12', 2.75), ('2025-06-11', 2.50), ('2025-09-17', 2.25),
]


def build_daily_series(changes, name, end_date='2025-12-31'):
    df = pd.DataFrame(changes, columns=['date', name])
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    daily_idx = pd.date_range(start=df.index.min(), end=end_date, freq='D')
    return df.reindex(daily_idx).ffill()


print("\nConstruction des séries quotidiennes Fed & BCE...")
fed = build_daily_series(fed_changes, 'Fed Funds Rate')
ecb = build_daily_series(ecb_changes, 'ECB Deposit Rate')
print(f"  ✓ Fed Funds Rate : {len(fed)} jours")
print(f"  ✓ ECB Deposit Rate : {len(ecb)} jours")

# ===== FIGURE 0 — Taux directeurs =====

fig, ax = plt.subplots(figsize=(14, 7))

ax.plot(fed.index, fed['Fed Funds Rate'],
        label='Fed Funds Rate (États-Unis)', color='#1f3864', linewidth=2.4)
ax.plot(ecb.index, ecb['ECB Deposit Rate'],
        label='ECB Deposit Facility Rate (Zone euro)', color='#c00000', linewidth=2.4)

ax.axvspan(pd.to_datetime('2015-01-01'), SPLIT_DATE,
           alpha=0.07, color='green',
           label='AVANT — Régime de taux accommodants')
ax.axvspan(SPLIT_DATE, pd.to_datetime('2025-12-31'),
           alpha=0.07, color='orange',
           label='APRÈS — Régime de resserrement monétaire')

ax.axvline(SPLIT_DATE, color='red', linestyle='--', linewidth=1.8, alpha=0.85)

ax.annotate('16 mars 2022\n1ère hausse Fed',
            xy=(SPLIT_DATE, 4.5),
            xytext=(pd.to_datetime('2022-09-01'), 4.5),
            fontsize=11, color='red', fontweight='bold',
            arrowprops=dict(arrowstyle='->', color='red', lw=1.2))

ax.annotate('Mars 2020\nCOVID', xy=(pd.to_datetime('2020-03-16'), 0.10),
            xytext=(pd.to_datetime('2018-06-01'), 2.5), fontsize=9, color='dimgray',
            arrowprops=dict(arrowstyle='->', color='gray', alpha=0.5))

ax.annotate('Juillet 2022\n1er relèvement BCE',
            xy=(pd.to_datetime('2022-07-27'), 0.0),
            xytext=(pd.to_datetime('2023-06-01'), -0.7), fontsize=9, color='darkred',
            arrowprops=dict(arrowstyle='->', color='darkred', alpha=0.5))

ax.set_title("Évolution des taux directeurs Fed et BCE (2015-2025)\nChangement de régime monétaire — cadre d'analyse avant/après",
             fontsize=13, fontweight='bold', pad=15)
ax.set_ylabel("Taux directeur (%)", fontsize=11)
ax.set_xlabel("")
ax.legend(loc='upper left', fontsize=10, framealpha=0.95)
ax.grid(True, alpha=0.3)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.axhline(0, color='black', linewidth=0.5, alpha=0.4)
ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

plt.figtext(0.99, 0.01,
            'Sources : Federal Reserve H.15 Statistical Release ; ECB Statistical Data Warehouse',
            ha='right', fontsize=8, style='italic', color='gray')

plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/figure_0_taux_directeurs.png', dpi=300, bbox_inches='tight')
plt.close()
print(f"\n✓ Figure 0 enregistrée : {OUTPUT_DIR}/figure_0_taux_directeurs.png")

# ===== FIGURE 1bis — Flux ESG =====

print("\n" + "=" * 72)
print("FIGURE FLUX ESG — Lecture du fichier flux_esg.csv")
print("=" * 72)

CSV_PATH = 'flux_esg.csv'

if os.path.exists(CSV_PATH):
    flux = pd.read_csv(CSV_PATH, parse_dates=['date'])
    print(f"\n✓ Fichier flux_esg.csv chargé : {len(flux)} observations")

    fig, ax = plt.subplots(figsize=(14, 7))

    width = 60
    if 'flux_us_mds' in flux.columns:
        ax.bar(flux['date'] - pd.Timedelta(days=15), flux['flux_us_mds'],
               width=width, label='Flux nets fonds ESG — États-Unis',
               color='#1f3864', alpha=0.85)
    if 'flux_eu_mds' in flux.columns:
        ax.bar(flux['date'] + pd.Timedelta(days=15), flux['flux_eu_mds'],
               width=width, label='Flux nets fonds ESG — Europe',
               color='#c00000', alpha=0.85)

    ax.axhline(0, color='black', linewidth=0.8)
    ax.axvline(SPLIT_DATE, color='red', linestyle='--', linewidth=1.5, alpha=0.85,
               label='Changement de régime monétaire (mars 2022)')

    ax.set_title("Flux nets trimestriels vers les fonds ESG — États-Unis vs Europe\nContraction des flux post-2022 (mécanisme Pástor-van der Beck)",
                 fontsize=13, fontweight='bold', pad=15)
    ax.set_ylabel("Flux nets (milliards USD)", fontsize=11)
    ax.set_xlabel("")
    ax.legend(loc='upper right', fontsize=10)
    ax.grid(True, alpha=0.3, axis='y')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.figtext(0.99, 0.01,
                'Source : Morningstar Global Sustainable Fund Flows reports (trimestriels)',
                ha='right', fontsize=8, style='italic', color='gray')

    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/figure_1bis_flux_esg.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ Figure 1bis enregistrée : {OUTPUT_DIR}/figure_1bis_flux_esg.png")
else:
    print(f"\n⚠ flux_esg.csv n'existe pas. Voir instructions_flux_esg.md.")

print("\n" + "=" * 72)
print("EXÉCUTION TERMINÉE — Aucune dépendance réseau requise")
print("=" * 72)
print("\nGraphiques générés dans le sous-dossier 'figures/' :")
print("  - figure_0_taux_directeurs.png (à insérer en INTRODUCTION)")
print("  - figure_1bis_flux_esg.png (à insérer en SECTION 3.3)")
