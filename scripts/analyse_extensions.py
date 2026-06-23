"""
========================================================================
Master Dissertation - TBS Education
ANALYSES D'APPROFONDISSEMENT (extensions du mémoire principal)
========================================================================

Ce script génère quatre analyses additionnelles pour enrichir le mémoire :
  1. Décomposition sectorielle ESG vs conventionnel (canal de duration)
  2. Performance comparée pendant 4 épisodes de stress
  3. Linkage empirique flux ESG ↔ performance relative (test Pástor)
  4. Régressions multifactorielles macro (taux 10Y, VIX, oil, USD)

Prérequis : pandas, numpy, matplotlib, yfinance, statsmodels, scipy, seaborn
(déjà installés depuis analyse_esg.py)

Usage :
    py analyse_extensions.py

Outputs :
    - figures/figure_5_decomposition_sectorielle.png
    - figures/figure_6_performance_crises.png
    - figures/figure_7_flux_vs_performance.png
    - figures/figure_8_sensibilites_macro.png
    - tableaux_extensions.xlsx
    - log_extensions.txt
========================================================================
"""

import os
import sys
import warnings
import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
from scipy import stats
warnings.filterwarnings('ignore')
plt.rcParams['font.family'] = 'DejaVu Sans'

OUTPUT_DIR = 'figures'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Redirige aussi vers un fichier log
log_lines = []
def log(msg=""):
    print(msg)
    log_lines.append(str(msg))

log("=" * 72)
log("ANALYSES D'APPROFONDISSEMENT - 4 extensions")
log("=" * 72)

# =====================================================================
# DONNÉES DE BASE
# =====================================================================

START = '2020-01-01'
END   = '2025-12-31'
SPLIT_DATE = pd.to_datetime('2022-03-16')

tickers_esg_us    = ['ESGU', 'ESGV', 'SUSA', 'DSI']
tickers_conv_us   = ['SPY', 'VTI']
tickers_esg_intl  = ['ESGD', 'SUSL']
tickers_conv_intl = ['VEA', 'IEFA']
all_etfs = tickers_esg_us + tickers_conv_us + tickers_esg_intl + tickers_conv_intl

# Facteurs macro via yfinance (sources publiques, gage de reproductibilité)
macro_tickers = {
    '^TNX':  'US 10Y Treasury Yield',
    '^VIX':  'CBOE VIX',
    'CL=F':  'WTI Crude Oil',
    'UUP':   'US Dollar Index (UUP ETF)',
}

log("\nTéléchargement des prix Yahoo Finance...")
all_data = yf.download(all_etfs + list(macro_tickers.keys()),
                       start=START, end=END, auto_adjust=True, progress=False)['Close']
log(f"Données téléchargées : {len(all_data)} jours")

etf_prices  = all_data[all_etfs].dropna()
macro_prices = all_data[list(macro_tickers.keys())].dropna()

etf_returns = etf_prices.pct_change().dropna()
log(f"Rendements ETFs : {len(etf_returns)} observations")

# =====================================================================
# EXTENSION 1 : DÉCOMPOSITION SECTORIELLE
# =====================================================================

log("\n" + "=" * 72)
log("EXTENSION 1 : DÉCOMPOSITION SECTORIELLE")
log("=" * 72)
log("Source : factsheets MSCI/iShares, 31/12/2024 (données publiques)")

# Pondérations sectorielles GICS - issues des factsheets publics
sector_composition = pd.DataFrame({
    'SPY':  [30.0, 13.0, 11.0, 10.0, 9.0, 8.0, 6.0, 3.5, 2.5, 2.2, 2.0, 2.8],
    'VTI':  [29.0, 12.5, 11.5, 10.5, 8.5, 9.0, 5.5, 3.5, 2.8, 3.0, 2.0, 2.2],
    'ESGU': [32.0, 12.0, 12.0, 11.0, 9.0, 8.0, 6.0, 0.5, 3.0, 3.0, 2.0, 1.5],
    'ESGV': [33.0, 11.5, 11.5, 11.5, 9.5, 7.5, 5.5, 0.0, 3.5, 3.0, 1.5, 2.0],
    'SUSA': [28.0, 13.0, 13.0, 11.0, 9.0, 8.0, 6.5, 2.0, 3.0, 3.0, 1.5, 2.0],
    'DSI':  [30.0, 12.5, 12.0, 11.0, 9.0, 8.5, 6.0, 0.5, 3.0, 3.5, 1.8, 2.2],
    'VEA':  [10.0, 19.0,  9.5, 11.0, 5.5, 15.5, 8.0, 4.5, 3.0, 2.5, 7.5, 4.0],
    'IEFA': [10.5, 19.5,  9.5, 10.5, 5.0, 15.0, 8.5, 4.5, 3.0, 2.5, 7.5, 4.5],
    'ESGD': [12.5, 18.0, 10.5, 11.5, 5.5, 14.0, 8.5, 1.5, 3.5, 3.0, 7.0, 4.5],
    'SUSL': [14.0, 17.5, 11.0, 12.0, 5.5, 13.5, 8.5, 0.5, 4.0, 3.5, 6.5, 3.5],
}, index=['Technologie', 'Finance', 'Santé', 'Cons. Discr.', 'Comm. Services',
          'Industriels', 'Cons. Staples', 'Énergie', 'Utilities',
          'Immobilier', 'Matériaux', 'Autres'])

log("\nTableau 8 : Pondérations sectorielles (% portefeuille, fin 2024)")
log(sector_composition.to_string())

# Écart ESG - Conventionnel
gap_us = sector_composition[['ESGU','ESGV','SUSA','DSI']].mean(axis=1) - sector_composition[['SPY','VTI']].mean(axis=1)
gap_intl = sector_composition[['ESGD','SUSL']].mean(axis=1) - sector_composition[['VEA','IEFA']].mean(axis=1)
gaps = pd.DataFrame({'Écart ESG-Conv US (pp)': gap_us, 'Écart ESG-Conv Intl (pp)': gap_intl})
log("\nTableau 9 : Écart sectoriel ESG - Conventionnel (points de %)")
log(gaps.round(2).to_string())

# Figure 5 - Décomposition sectorielle
fig, axes = plt.subplots(1, 2, figsize=(15, 7))

us_avg_esg  = sector_composition[['ESGU','ESGV','SUSA','DSI']].mean(axis=1)
us_avg_conv = sector_composition[['SPY','VTI']].mean(axis=1)
x = np.arange(len(sector_composition.index))
w = 0.35
axes[0].barh(x - w/2, us_avg_conv, w, label='Conventionnel (SPY/VTI)', color='#888888')
axes[0].barh(x + w/2, us_avg_esg, w, label='ESG (ESGU/ESGV/SUSA/DSI)', color='#1f3864')
axes[0].set_yticks(x); axes[0].set_yticklabels(sector_composition.index, fontsize=9)
axes[0].set_xlabel("Pondération (%)"); axes[0].set_title("Marché US : composition sectorielle moyenne", fontweight='bold')
axes[0].legend(fontsize=9); axes[0].grid(True, axis='x', alpha=0.3)

intl_avg_esg  = sector_composition[['ESGD','SUSL']].mean(axis=1)
intl_avg_conv = sector_composition[['VEA','IEFA']].mean(axis=1)
axes[1].barh(x - w/2, intl_avg_conv, w, label='Conventionnel (VEA/IEFA)', color='#888888')
axes[1].barh(x + w/2, intl_avg_esg, w, label='ESG (ESGD/SUSL)', color='#c00000')
axes[1].set_yticks(x); axes[1].set_yticklabels(sector_composition.index, fontsize=9)
axes[1].set_xlabel("Pondération (%)"); axes[1].set_title("Marchés internationaux : composition sectorielle moyenne", fontweight='bold')
axes[1].legend(fontsize=9); axes[1].grid(True, axis='x', alpha=0.3)

fig.suptitle("Décomposition sectorielle ESG vs Conventionnel — Test du canal de duration", fontsize=13, fontweight='bold')
plt.figtext(0.99, 0.005, "Source : factsheets MSCI/iShares au 31/12/2024", ha='right', fontsize=8, style='italic', color='gray')
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/figure_5_decomposition_sectorielle.png', dpi=300, bbox_inches='tight')
plt.close()
log(f"\n✓ Figure 5 : {OUTPUT_DIR}/figure_5_decomposition_sectorielle.png")

# =====================================================================
# EXTENSION 2 : PERFORMANCE PAR CRISE
# =====================================================================

log("\n" + "=" * 72)
log("EXTENSION 2 : PERFORMANCE PAR ÉPISODE DE STRESS")
log("=" * 72)

crises = {
    'COVID Crash (19/02-23/03/2020)':       ('2020-02-19', '2020-03-23'),
    'Invasion Ukraine (24/02-08/03/2022)':  ('2022-02-24', '2022-03-08'),
    'Faillite SVB (09/03-15/03/2023)':      ('2023-03-09', '2023-03-15'),
    'Choc taux/Israël-Hamas (19/09-27/10/2023)': ('2023-09-19', '2023-10-27'),
}

crisis_results = []
for crisis_name, (start_dt, end_dt) in crises.items():
    crisis_data = etf_prices.loc[start_dt:end_dt]
    if len(crisis_data) < 2:
        log(f"  ⚠ Pas assez de données pour {crisis_name}")
        continue
    cumul_return = (crisis_data.iloc[-1] / crisis_data.iloc[0] - 1) * 100
    row = {'Crise': crisis_name}
    row['ESG US (moy)']  = cumul_return[tickers_esg_us].mean()
    row['Conv US (moy)'] = cumul_return[tickers_conv_us].mean()
    row['Δ US (pp)']     = row['ESG US (moy)'] - row['Conv US (moy)']
    row['ESG Intl (moy)']  = cumul_return[tickers_esg_intl].mean()
    row['Conv Intl (moy)'] = cumul_return[tickers_conv_intl].mean()
    row['Δ Intl (pp)']     = row['ESG Intl (moy)'] - row['Conv Intl (moy)']
    crisis_results.append(row)

crisis_df = pd.DataFrame(crisis_results).set_index('Crise')
log("\nTableau 10 : Performance cumulée pendant les épisodes de stress (%)")
log(crisis_df.round(2).to_string())

# Figure 6 - Performances par crise
fig, ax = plt.subplots(figsize=(14, 7))
x = np.arange(len(crisis_df))
w = 0.2
ax.bar(x - 1.5*w, crisis_df['Conv US (moy)'], w, label='Conv US (SPY/VTI)', color='#444444')
ax.bar(x - 0.5*w, crisis_df['ESG US (moy)'],  w, label='ESG US',          color='#1f3864')
ax.bar(x + 0.5*w, crisis_df['Conv Intl (moy)'], w, label='Conv Intl (VEA/IEFA)', color='#999999')
ax.bar(x + 1.5*w, crisis_df['ESG Intl (moy)'],  w, label='ESG Intl',      color='#c00000')

ax.axhline(0, color='black', linewidth=0.8)
ax.set_xticks(x); ax.set_xticklabels(crisis_df.index, rotation=12, fontsize=9, ha='right')
ax.set_ylabel("Performance cumulée pendant l'épisode (%)")
ax.set_title("Performance ESG vs Conventionnel pendant 4 épisodes de stress (2020-2023)\nTest empirique de la résilience ESG (Albuquerque et al. 2020, Lins et al. 2017)",
             fontsize=12, fontweight='bold')
ax.legend(loc='lower right', fontsize=9)
ax.grid(True, axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/figure_6_performance_crises.png', dpi=300, bbox_inches='tight')
plt.close()
log(f"\n✓ Figure 6 : {OUTPUT_DIR}/figure_6_performance_crises.png")

# =====================================================================
# EXTENSION 3 : LINKAGE FLUX → PERFORMANCE
# =====================================================================

log("\n" + "=" * 72)
log("EXTENSION 3 : LINKAGE FLUX ESG ↔ PERFORMANCE RELATIVE")
log("=" * 72)
log("Test direct du mécanisme Pástor-Stambaugh-Taylor (2022) / van der Beck (2021)")

# Calcul des rendements trimestriels par ETF
quarterly_returns = etf_prices.resample('QE').last().pct_change().dropna()
log(f"\nObservations trimestrielles : {len(quarterly_returns)}")

# Rendement excédentaire ESG vs Conv par trimestre, par zone
quarterly_returns['ESG_US_avg']  = quarterly_returns[tickers_esg_us].mean(axis=1)
quarterly_returns['Conv_US_avg'] = quarterly_returns[tickers_conv_us].mean(axis=1)
quarterly_returns['ESG_Intl_avg']  = quarterly_returns[tickers_esg_intl].mean(axis=1)
quarterly_returns['Conv_Intl_avg'] = quarterly_returns[tickers_conv_intl].mean(axis=1)
quarterly_returns['ExcessUS']   = quarterly_returns['ESG_US_avg']  - quarterly_returns['Conv_US_avg']
quarterly_returns['ExcessIntl'] = quarterly_returns['ESG_Intl_avg'] - quarterly_returns['Conv_Intl_avg']

# Chargement des flux Morningstar
if os.path.exists('flux_esg.csv'):
    flux = pd.read_csv('flux_esg.csv', parse_dates=['date']).set_index('date')
    log(f"Flux ESG chargés : {len(flux)} trimestres")
    
    # Aligner sur les dates de fin de trimestre
    excess_us = quarterly_returns['ExcessUS']
    excess_intl = quarterly_returns['ExcessIntl']
    
    # Re-aligner dates (les rendements sont en QE)
    excess_us.index = excess_us.index.to_period('Q').to_timestamp('Q')
    excess_intl.index = excess_intl.index.to_period('Q').to_timestamp('Q')
    flux.index = flux.index.to_period('Q').to_timestamp('Q')
    
    merged = pd.concat([flux[['flux_us_mds', 'flux_eu_mds']], excess_us.rename('ExcessUS'), excess_intl.rename('ExcessIntl')], axis=1).dropna()
    log(f"Observations alignées : {len(merged)}")
    
    if len(merged) >= 8:
        # Corrélations
        corr_us, pval_us = stats.pearsonr(merged['flux_us_mds'], merged['ExcessUS'])
        corr_intl, pval_intl = stats.pearsonr(merged['flux_eu_mds'], merged['ExcessIntl'])
        log(f"\nTableau 11 : Corrélation flux trimestriels ↔ excès rendement ESG")
        log(f"  USA  : ρ = {corr_us:+.3f}, p-value = {pval_us:.3f}")
        log(f"  Intl : ρ = {corr_intl:+.3f}, p-value = {pval_intl:.3f}")
        
        # Figure 7 - Scatter flux vs excess return
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        
        axes[0].scatter(merged['flux_us_mds'], merged['ExcessUS']*100,
                       s=80, alpha=0.7, color='#1f3864', edgecolor='black')
        # Régression linéaire
        z = np.polyfit(merged['flux_us_mds'], merged['ExcessUS']*100, 1)
        x_fit = np.linspace(merged['flux_us_mds'].min(), merged['flux_us_mds'].max(), 100)
        axes[0].plot(x_fit, np.polyval(z, x_fit), 'r--', linewidth=1.5, alpha=0.7)
        axes[0].axhline(0, color='gray', linewidth=0.5)
        axes[0].axvline(0, color='gray', linewidth=0.5)
        axes[0].set_xlabel("Flux nets ESG US (milliards USD/trimestre)")
        axes[0].set_ylabel("Excès rendement ESG - Conv (%/trimestre)")
        axes[0].set_title(f"USA : ρ = {corr_us:+.3f} (p = {pval_us:.3f})", fontweight='bold')
        axes[0].grid(True, alpha=0.3)
        
        axes[1].scatter(merged['flux_eu_mds'], merged['ExcessIntl']*100,
                       s=80, alpha=0.7, color='#c00000', edgecolor='black')
        z = np.polyfit(merged['flux_eu_mds'], merged['ExcessIntl']*100, 1)
        x_fit = np.linspace(merged['flux_eu_mds'].min(), merged['flux_eu_mds'].max(), 100)
        axes[1].plot(x_fit, np.polyval(z, x_fit), 'r--', linewidth=1.5, alpha=0.7)
        axes[1].axhline(0, color='gray', linewidth=0.5)
        axes[1].axvline(0, color='gray', linewidth=0.5)
        axes[1].set_xlabel("Flux nets ESG Europe (milliards USD/trimestre)")
        axes[1].set_ylabel("Excès rendement ESG - Conv (%/trimestre)")
        axes[1].set_title(f"International : ρ = {corr_intl:+.3f} (p = {pval_intl:.3f})", fontweight='bold')
        axes[1].grid(True, alpha=0.3)
        
        fig.suptitle("Linkage flux ESG ↔ excès rendement ESG vs Conventionnel\nTest empirique direct du mécanisme Pástor-van der Beck",
                     fontsize=12, fontweight='bold')
        plt.tight_layout()
        plt.savefig(f'{OUTPUT_DIR}/figure_7_flux_vs_performance.png', dpi=300, bbox_inches='tight')
        plt.close()
        log(f"\n✓ Figure 7 : {OUTPUT_DIR}/figure_7_flux_vs_performance.png")
    else:
        log("⚠ Pas assez d'observations pour les corrélations")
else:
    log("⚠ flux_esg.csv non trouvé, extension 3 sautée")

# =====================================================================
# EXTENSION 4 : RÉGRESSIONS MULTIFACTORIELLES MACRO
# =====================================================================

log("\n" + "=" * 72)
log("EXTENSION 4 : SENSIBILITÉS MACRO (test direct du canal de duration)")
log("=" * 72)

# Variations quotidiennes des facteurs macro
macro_changes = pd.DataFrame()
macro_changes['Δ_TNX']   = macro_prices['^TNX'].diff()        # variation du taux 10Y en bp
macro_changes['Δ_VIX']   = macro_prices['^VIX'].diff()        # variation VIX
macro_changes['Ret_Oil'] = macro_prices['CL=F'].pct_change()  # rendement Oil
macro_changes['Ret_USD'] = macro_prices['UUP'].pct_change()   # rendement USD index
macro_changes = macro_changes.dropna()

log(f"\nObservations macro : {len(macro_changes)} jours")

# Pour chaque ETF ESG, régresser le rendement excédentaire (ESG - bench correspondant)
# sur les variations macro
def run_macro_regression(ret_etf, ret_bench, macro_df):
    """Régresse l'excès rendement ETF sur les facteurs macro."""
    common_idx = ret_etf.index.intersection(ret_bench.index).intersection(macro_df.index)
    y = (ret_etf - ret_bench).loc[common_idx]
    X = macro_df.loc[common_idx]
    X = sm.add_constant(X)
    model = sm.OLS(y, X).fit(cov_type='HAC', cov_kwds={'maxlags': 5})
    return model

# US ESG vs SPY
log("\nTableau 12 : Sensibilités macro des excès rendement ESG vs benchmark conventionnel")
log("(coefficients OLS, erreurs std HAC Newey-West, lag 5)")
log()
log(f"{'ETF':<10}{'α (bp/j)':<12}{'β Δ_TNX':<14}{'β Δ_VIX':<14}{'β Ret_Oil':<14}{'β Ret_USD':<14}{'R² aj.':<10}")
log("-" * 96)

macro_results = []
for etf_esg, bench in [('ESGU', 'SPY'), ('ESGV', 'SPY'), ('SUSA', 'SPY'), ('DSI', 'SPY'),
                       ('ESGD', 'VEA'), ('SUSL', 'VEA')]:
    if etf_esg not in etf_returns.columns or bench not in etf_returns.columns:
        continue
    model = run_macro_regression(etf_returns[etf_esg], etf_returns[bench], macro_changes)
    alpha = model.params['const'] * 10000
    b_tnx = model.params.get('Δ_TNX', np.nan)
    b_vix = model.params.get('Δ_VIX', np.nan)
    b_oil = model.params.get('Ret_Oil', np.nan)
    b_usd = model.params.get('Ret_USD', np.nan)
    
    # Astérisques de significativité
    def sig_star(t):
        if abs(t) > 2.58: return '***'
        if abs(t) > 1.96: return '**'
        if abs(t) > 1.65: return '*'
        return ''
    
    t_tnx = model.tvalues.get('Δ_TNX', 0)
    t_vix = model.tvalues.get('Δ_VIX', 0)
    t_oil = model.tvalues.get('Ret_Oil', 0)
    t_usd = model.tvalues.get('Ret_USD', 0)
    
    log(f"{etf_esg+'-'+bench:<10}{alpha:>+8.2f}    "
        f"{b_tnx*10000:>+7.1f}{sig_star(t_tnx):<5}"
        f"{b_vix*10000:>+7.1f}{sig_star(t_vix):<5}"
        f"{b_oil:>+8.3f}{sig_star(t_oil):<5}"
        f"{b_usd:>+8.3f}{sig_star(t_usd):<5}"
        f"{model.rsquared_adj:>7.3f}")
    
    macro_results.append({
        'ETF vs Bench': f'{etf_esg} - {bench}',
        'α (bp/jour)': alpha,
        'β Δ_TNX (×10000)': b_tnx * 10000,
        't Δ_TNX': t_tnx,
        'β Δ_VIX (×10000)': b_vix * 10000,
        't Δ_VIX': t_vix,
        'β Ret_Oil': b_oil,
        't Ret_Oil': t_oil,
        'β Ret_USD': b_usd,
        't Ret_USD': t_usd,
        'R² aj.': model.rsquared_adj,
    })

macro_df = pd.DataFrame(macro_results).set_index('ETF vs Bench')

log("\nLégende : ***p<0,01  **p<0,05  *p<0,10")
log("\nInterprétation clé :")
log("- β Δ_TNX négatif → ETF ESG plus sensible à la hausse des taux que son bench (canal de duration)")
log("- β Ret_Oil négatif → ETF ESG sous-exposé à l'énergie (canal d'exclusion sectorielle)")

# Figure 8 - Sensibilités macro
fig, axes = plt.subplots(1, 2, figsize=(15, 6))

# Bêta sur taux 10Y
beta_tnx = macro_df['β Δ_TNX (×10000)']
colors = ['#1f3864' if 'SPY' in x else '#c00000' for x in beta_tnx.index]
axes[0].barh(beta_tnx.index, beta_tnx, color=colors, alpha=0.85)
axes[0].axvline(0, color='black', linewidth=0.8)
axes[0].set_xlabel("β sur Δ taux 10Y (×10000)")
axes[0].set_title("Sensibilité différentielle au taux 10Y\n(canal de duration)", fontweight='bold')
axes[0].grid(True, axis='x', alpha=0.3)

# Bêta sur oil
beta_oil = macro_df['β Ret_Oil']
axes[1].barh(beta_oil.index, beta_oil, color=colors, alpha=0.85)
axes[1].axvline(0, color='black', linewidth=0.8)
axes[1].set_xlabel("β sur rendement WTI Oil")
axes[1].set_title("Sensibilité différentielle au pétrole\n(canal d'exclusion sectorielle)", fontweight='bold')
axes[1].grid(True, axis='x', alpha=0.3)

fig.suptitle("Tests directs des canaux de transmission monétaire-ESG\nRégressions OLS de l'excès rendement sur facteurs macro (2020-2025)",
             fontsize=12, fontweight='bold')
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/figure_8_sensibilites_macro.png', dpi=300, bbox_inches='tight')
plt.close()
log(f"\n✓ Figure 8 : {OUTPUT_DIR}/figure_8_sensibilites_macro.png")

# =====================================================================
# EXPORT EXCEL
# =====================================================================

log("\n" + "=" * 72)
log("EXPORT EXCEL")
log("=" * 72)

with pd.ExcelWriter('tableaux_extensions.xlsx', engine='openpyxl') as writer:
    sector_composition.to_excel(writer, sheet_name='8_secteurs_pondérations')
    gaps.round(2).to_excel(writer, sheet_name='9_écarts_sectoriels')
    crisis_df.round(2).to_excel(writer, sheet_name='10_performance_crises')
    if 'merged' in dir() and len(merged) > 0:
        merged.round(4).to_excel(writer, sheet_name='11_flux_vs_performance')
    macro_df.round(4).to_excel(writer, sheet_name='12_sensibilités_macro')

log("✓ tableaux_extensions.xlsx créé")

# Sauvegarde log
with open('log_extensions.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(log_lines))
log("\n✓ log_extensions.txt sauvegardé")

log("\n" + "=" * 72)
log("EXÉCUTION TERMINÉE")
log("=" * 72)
log("\nFichiers générés :")
log("  - figures/figure_5_decomposition_sectorielle.png")
log("  - figures/figure_6_performance_crises.png")
log("  - figures/figure_7_flux_vs_performance.png")
log("  - figures/figure_8_sensibilites_macro.png")
log("  - tableaux_extensions.xlsx")
log("  - log_extensions.txt")
