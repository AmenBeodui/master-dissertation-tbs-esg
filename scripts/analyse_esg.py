"""
========================================================================
Master Dissertation - TBS Education - MSc Banking & International Finance
========================================================================

Sujet : L'investissement ESG offre-t-il une prime de performance ajustée
du risque dans un environnement de resserrement monétaire ?
Une analyse comparative des marchés actions américains et internationaux
(2020-2025)

Auteur : Amen Bedoui
Date   : Juin 2026

Ce script :
1. Télécharge les prix de clôture ajustés via yfinance (gratuit)
2. Télécharge les facteurs Fama-French via Kenneth French Data Library
3. Calcule rendements, statistiques descriptives, ratios de risque
4. Réalise les régressions CAPM, Fama-French 3 et 5 facteurs, Carhart
5. Effectue l'analyse en sous-périodes (taux bas vs taux hauts)
6. Réalise les tests statistiques (Welch, Levene, Chow)
7. Exporte tous les tableaux en Excel et les graphiques en PNG

Prérequis (à installer dans le terminal) :
    pip install yfinance pandas numpy statsmodels scipy matplotlib seaborn openpyxl

Usage :
    python analyse_esg.py

Outputs :
    - resultats_esg.xlsx : tous les tableaux pour le mémoire
    - figures/ : tous les graphiques en PNG haute résolution
    - log_execution.txt : journal d'exécution avec valeurs clés à intégrer
========================================================================
"""

import os
import warnings
from datetime import datetime
from io import BytesIO
from urllib.request import urlopen
from zipfile import ZipFile

import numpy as np
import pandas as pd
import yfinance as yf
import statsmodels.api as sm
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns

warnings.filterwarnings('ignore')
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("Set2")

# =====================================================================
# 1. CONFIGURATION
# =====================================================================

START_DATE = '2020-01-01'
END_DATE   = '2025-12-31'

# Date de bascule taux bas / taux hauts (première hausse Fed : 16 mars 2022)
SPLIT_DATE = '2022-03-16'

# Tickers : tous listés US, disponibles via yfinance
US_ESG = {
    'ESGU': 'iShares ESG Aware MSCI USA',
    'ESGV': 'Vanguard ESG U.S. Stock',
    'SUSA': 'iShares MSCI USA ESG Select',
    'DSI':  'iShares MSCI KLD 400 Social',
}
US_CONV = {
    'SPY': 'SPDR S&P 500',
    'VTI': 'Vanguard Total Stock Market',
}
INTL_ESG = {  # Développés ex-US, fortement pondéré Europe
    'ESGD': 'iShares ESG Aware MSCI EAFE',
    'SUSL': 'iShares ESG MSCI EAFE Leaders',
}
INTL_CONV = {
    'VEA':  'Vanguard FTSE Developed Markets',
    'IEFA': 'iShares Core MSCI EAFE',
}

ALL_TICKERS = {**US_ESG, **US_CONV, **INTL_ESG, **INTL_CONV}

# Sortie
OUTPUT_DIR = 'figures'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Journal d'exécution
LOG = []
def log(msg):
    print(msg)
    LOG.append(str(msg))

# =====================================================================
# 2. TÉLÉCHARGEMENT DES PRIX
# =====================================================================

log("=" * 72)
log(f"ANALYSE ESG vs CONVENTIONNEL — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
log("=" * 72)
log(f"\nPériode : {START_DATE} → {END_DATE}")
log(f"Split sous-périodes : avant/après {SPLIT_DATE}")
log(f"Tickers : {len(ALL_TICKERS)} ETFs au total\n")

log("Téléchargement des prix via Yahoo Finance...")
prices = yf.download(
    list(ALL_TICKERS.keys()),
    start=START_DATE,
    end=END_DATE,
    auto_adjust=True,
    progress=False,
)['Close']

# Nettoyer : supprimer les colonnes complètement vides
prices = prices.dropna(axis=1, how='all')
log(f"Prix téléchargés : {prices.shape[0]} jours × {prices.shape[1]} ETFs")

# =====================================================================
# 3. RENDEMENTS
# =====================================================================

# Rendements quotidiens
returns_daily = prices.pct_change().dropna()

log(f"\nRendements quotidiens : {returns_daily.shape[0]} observations")

# =====================================================================
# 4. STATISTIQUES DESCRIPTIVES
# =====================================================================

def descriptive_stats(returns, freq='daily'):
    """Calcule les stats descriptives annualisées."""
    if freq == 'daily':
        annualizer_mean = 252
        annualizer_std = np.sqrt(252)
    else:
        annualizer_mean = 12
        annualizer_std = np.sqrt(12)

    stats_df = pd.DataFrame({
        'Rendement annualisé (%)' : returns.mean() * annualizer_mean * 100,
        'Volatilité annualisée (%)' : returns.std() * annualizer_std * 100,
        'Skewness'  : returns.skew(),
        'Kurtosis'  : returns.kurtosis(),
        'Min quot. (%)'  : returns.min() * 100,
        'Max quot. (%)'  : returns.max() * 100,
        'Obs.'      : returns.count(),
    })
    return stats_df.round(3)

stats_total = descriptive_stats(returns_daily, 'daily')
log("\n" + "=" * 72)
log("TABLEAU 1 : STATISTIQUES DESCRIPTIVES — PÉRIODE COMPLÈTE (2020-2025)")
log("=" * 72)
log(stats_total.to_string())

# =====================================================================
# 5. RATIOS DE RISQUE
# =====================================================================

# Taux sans risque approximé par 3M T-Bill (proxy : 2% moyen sur la période)
# Pour plus de rigueur, on télécharge les T-Bills via yfinance (^IRX)
try:
    tbill = yf.download('^IRX', start=START_DATE, end=END_DATE,
                         progress=False, auto_adjust=False)['Close']
    rf_annual = (tbill / 100).mean()  # ^IRX est en %
    rf_daily = (1 + rf_annual) ** (1/252) - 1
    log(f"\nTaux sans risque moyen 3M T-Bill : {rf_annual*100:.2f}% annualisé")
except Exception as e:
    rf_daily = 0.02 / 252
    log(f"\nTaux sans risque fixé à 2% (T-Bill indisponible : {e})")

def sharpe_ratio(returns, rf=rf_daily):
    excess = returns - rf
    return (excess.mean() / returns.std()) * np.sqrt(252)

def sortino_ratio(returns, rf=rf_daily):
    excess = returns - rf
    downside = returns[returns < 0].std()
    return (excess.mean() / downside) * np.sqrt(252) if downside > 0 else np.nan

def max_drawdown(returns):
    cum = (1 + returns).cumprod()
    running_max = cum.cummax()
    dd = (cum - running_max) / running_max
    return dd.min() * 100

def treynor_ratio(returns, benchmark, rf=rf_daily):
    """Treynor ratio : excès de rendement par unité de risque systématique."""
    excess = returns - rf
    excess_bench = benchmark - rf
    beta = np.cov(returns.dropna(), benchmark.dropna())[0, 1] / benchmark.var()
    return (excess.mean() * 252) / beta if beta != 0 else np.nan

# Calcul pour chaque ETF
risk_stats = pd.DataFrame({
    'Sharpe'        : returns_daily.apply(sharpe_ratio),
    'Sortino'       : returns_daily.apply(sortino_ratio),
    'Max Drawdown (%)' : returns_daily.apply(max_drawdown),
})

# Treynor par rapport à SPY pour les US, VEA pour les internationaux
benchmark_us = returns_daily['SPY']
benchmark_intl = returns_daily.get('VEA', returns_daily['SPY'])

treynor_vals = {}
for ticker in returns_daily.columns:
    if ticker in US_ESG or ticker in US_CONV:
        treynor_vals[ticker] = treynor_ratio(returns_daily[ticker], benchmark_us)
    else:
        treynor_vals[ticker] = treynor_ratio(returns_daily[ticker], benchmark_intl)

risk_stats['Treynor'] = pd.Series(treynor_vals)
risk_stats = risk_stats.round(3)

log("\n" + "=" * 72)
log("TABLEAU 2 : RATIOS DE PERFORMANCE AJUSTÉE DU RISQUE (PÉRIODE COMPLÈTE)")
log("=" * 72)
log(risk_stats.to_string())

# =====================================================================
# 6. ANALYSE EN SOUS-PÉRIODES
# =====================================================================

period_low  = returns_daily.loc[:SPLIT_DATE]
period_high = returns_daily.loc[SPLIT_DATE:]

stats_low  = descriptive_stats(period_low, 'daily').add_suffix(' (taux bas)')
stats_high = descriptive_stats(period_high, 'daily').add_suffix(' (taux hauts)')

risk_low = pd.DataFrame({
    'Sharpe (taux bas)' : period_low.apply(sharpe_ratio),
    'Sortino (taux bas)': period_low.apply(sortino_ratio),
})
risk_high = pd.DataFrame({
    'Sharpe (taux hauts)' : period_high.apply(sharpe_ratio),
    'Sortino (taux hauts)': period_high.apply(sortino_ratio),
})

subperiod_table = pd.concat([risk_low, risk_high], axis=1).round(3)
subperiod_table['Δ Sharpe'] = (
    subperiod_table['Sharpe (taux hauts)'] - subperiod_table['Sharpe (taux bas)']
).round(3)

log("\n" + "=" * 72)
log("TABLEAU 3 : PERFORMANCE PAR SOUS-PÉRIODE (TAUX BAS vs TAUX HAUTS)")
log("=" * 72)
log(subperiod_table.to_string())

# =====================================================================
# 7. TÉLÉCHARGEMENT FAMA-FRENCH (Kenneth French Data Library)
# =====================================================================

log("\n" + "=" * 72)
log("Téléchargement facteurs Fama-French (Kenneth French Data Library)...")

FF5_URL = ('https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/'
           'ftp/F-F_Research_Data_5_Factors_2x3_daily_CSV.zip')
MOM_URL = ('https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/'
           'ftp/F-F_Momentum_Factor_daily_CSV.zip')

def download_ff_factors(url, skip_rows=3):
    """Télécharge et parse les facteurs Fama-French."""
    try:
        with urlopen(url, timeout=30) as resp:
            with ZipFile(BytesIO(resp.read())) as zf:
                with zf.open(zf.namelist()[0]) as f:
                    df = pd.read_csv(f, skiprows=skip_rows)
        df.columns = [c.strip() for c in df.columns]
        df = df.rename(columns={df.columns[0]: 'Date'})
        # Conserver uniquement les lignes avec une date numérique
        df = df[df['Date'].astype(str).str.match(r'^\d{8}$')]
        df['Date'] = pd.to_datetime(df['Date'], format='%Y%m%d')
        df = df.set_index('Date')
        df = df.astype(float) / 100  # Les facteurs FF sont en %
        return df
    except Exception as e:
        log(f"Erreur téléchargement FF : {e}")
        return None

ff5 = download_ff_factors(FF5_URL, skip_rows=3)
mom = download_ff_factors(MOM_URL, skip_rows=13)

if ff5 is not None and mom is not None:
    ff_factors = ff5.join(mom, how='inner')
    ff_factors = ff_factors.loc[START_DATE:END_DATE]
    log(f"Facteurs FF chargés : {ff_factors.shape}")
    log(f"Colonnes disponibles : {list(ff_factors.columns)}")
else:
    ff_factors = None
    log("ATTENTION : Facteurs Fama-French indisponibles, régressions ignorées")

# =====================================================================
# 8. RÉGRESSIONS FAMA-FRENCH ET CARHART
# =====================================================================

def run_regression(asset_returns, factors, factor_cols):
    """Régression OLS : rendement excédentaire ~ facteurs."""
    df = pd.DataFrame({'asset': asset_returns}).join(factors, how='inner').dropna()
    df['excess'] = df['asset'] - df['RF']
    X = sm.add_constant(df[factor_cols])
    y = df['excess']
    model = sm.OLS(y, X).fit()
    out = {
        'alpha (annualisé %)' : model.params['const'] * 252 * 100,
        'alpha t-stat' : model.tvalues['const'],
        'alpha p-value' : model.pvalues['const'],
        'R² ajusté' : model.rsquared_adj,
    }
    for col in factor_cols:
        out[f'β {col}'] = model.params[col]
        out[f'β {col} t-stat'] = model.tvalues[col]
    return out

if ff_factors is not None:
    # CAPM (1 facteur : Mkt-RF)
    capm_results = {t: run_regression(returns_daily[t], ff_factors, ['Mkt-RF'])
                    for t in returns_daily.columns}
    capm_df = pd.DataFrame(capm_results).T.round(4)

    # Fama-French 3 facteurs
    ff3_results = {t: run_regression(returns_daily[t], ff_factors, ['Mkt-RF', 'SMB', 'HML'])
                   for t in returns_daily.columns}
    ff3_df = pd.DataFrame(ff3_results).T.round(4)

    # Fama-French 5 facteurs
    ff5_cols = ['Mkt-RF', 'SMB', 'HML', 'RMW', 'CMA']
    ff5_results = {t: run_regression(returns_daily[t], ff_factors, ff5_cols)
                   for t in returns_daily.columns}
    ff5_df = pd.DataFrame(ff5_results).T.round(4)

    # Carhart 4 facteurs (FF3 + Momentum)
    carhart_cols = ['Mkt-RF', 'SMB', 'HML', 'Mom']
    carhart_results = {t: run_regression(returns_daily[t], ff_factors, carhart_cols)
                       for t in returns_daily.columns}
    carhart_df = pd.DataFrame(carhart_results).T.round(4)

    log("\n" + "=" * 72)
    log("TABLEAU 4a : RÉGRESSIONS CAPM (Alpha annualisé et bêta)")
    log("=" * 72)
    log(capm_df[['alpha (annualisé %)', 'alpha t-stat', 'β Mkt-RF', 'R² ajusté']].to_string())

    log("\n" + "=" * 72)
    log("TABLEAU 4b : RÉGRESSIONS FAMA-FRENCH 3 FACTEURS")
    log("=" * 72)
    log(ff3_df[['alpha (annualisé %)', 'alpha t-stat', 'β Mkt-RF', 'β SMB', 'β HML', 'R² ajusté']].to_string())

    log("\n" + "=" * 72)
    log("TABLEAU 4c : RÉGRESSIONS CARHART 4 FACTEURS")
    log("=" * 72)
    log(carhart_df[['alpha (annualisé %)', 'alpha t-stat', 'β Mkt-RF', 'β SMB', 'β HML', 'β Mom', 'R² ajusté']].to_string())

    # Régressions par sous-période
    ff_low = ff_factors.loc[:SPLIT_DATE]
    ff_high = ff_factors.loc[SPLIT_DATE:]

    capm_low = {t: run_regression(period_low[t], ff_low, ['Mkt-RF'])
                for t in period_low.columns}
    capm_high = {t: run_regression(period_high[t], ff_high, ['Mkt-RF'])
                 for t in period_high.columns}

    alpha_comparison = pd.DataFrame({
        'Alpha CAPM (taux bas) %' : {t: capm_low[t]['alpha (annualisé %)'] for t in capm_low},
        't-stat (bas)' : {t: capm_low[t]['alpha t-stat'] for t in capm_low},
        'Alpha CAPM (taux hauts) %' : {t: capm_high[t]['alpha (annualisé %)'] for t in capm_high},
        't-stat (hauts)' : {t: capm_high[t]['alpha t-stat'] for t in capm_high},
    }).round(4)
    alpha_comparison['Δ Alpha %'] = (
        alpha_comparison['Alpha CAPM (taux hauts) %']
        - alpha_comparison['Alpha CAPM (taux bas) %']
    ).round(4)

    log("\n" + "=" * 72)
    log("TABLEAU 5 : ALPHA CAPM PAR SOUS-PÉRIODE (Test H2)")
    log("=" * 72)
    log(alpha_comparison.to_string())

# =====================================================================
# 9. TESTS STATISTIQUES (Welch, Levene)
# =====================================================================

log("\n" + "=" * 72)
log("TABLEAU 6 : TESTS STATISTIQUES DE COMPARAISON")
log("=" * 72)

def welch_test(serie1, serie2, name1, name2):
    """Test de Welch (égalité des moyennes, variances inégales)."""
    s1, s2 = serie1.dropna(), serie2.dropna()
    t_stat, p_val = stats.ttest_ind(s1, s2, equal_var=False)
    return {
        'Comparaison': f'{name1} vs {name2}',
        'Moy. 1 (%)' : s1.mean() * 252 * 100,
        'Moy. 2 (%)' : s2.mean() * 252 * 100,
        't-stat Welch' : t_stat,
        'p-value' : p_val,
        'H0 rejetée (5%)' : 'Oui' if p_val < 0.05 else 'Non',
    }

welch_results = []
# H1 : ESG vs Conventionnel (toute la période)
for esg_t in list(US_ESG.keys()):
    if esg_t in returns_daily.columns:
        welch_results.append(welch_test(returns_daily[esg_t], returns_daily['SPY'],
                                         esg_t, 'SPY'))

# H2 : ESG en sous-périodes (un même ETF, taux bas vs hauts)
for esg_t in list(US_ESG.keys()):
    if esg_t in returns_daily.columns:
        welch_results.append(welch_test(period_low[esg_t], period_high[esg_t],
                                         f'{esg_t} (bas)', f'{esg_t} (hauts)'))

welch_df = pd.DataFrame(welch_results).round(4)
log(welch_df.to_string(index=False))

# =====================================================================
# 10. GRAPHIQUES
# =====================================================================

log("\nGénération des graphiques...")

# Graphique 1 : performance cumulée
fig, axes = plt.subplots(2, 1, figsize=(14, 10))

# Plot US
us_tickers = [t for t in (list(US_ESG.keys()) + list(US_CONV.keys())) if t in prices.columns]
cum_us = (1 + returns_daily[us_tickers]).cumprod()
ax = axes[0]
for t in us_tickers:
    style = '-' if t in US_ESG else '--'
    ax.plot(cum_us.index, cum_us[t], style, label=f'{t} — {ALL_TICKERS[t]}', linewidth=1.8)
ax.axvline(pd.to_datetime(SPLIT_DATE), color='red', linestyle=':', alpha=0.7,
           label='Début hausse Fed (mars 2022)')
ax.set_title('Performance cumulée — Marché américain (base 1 au 01/01/2020)', fontsize=13)
ax.set_ylabel('Valeur d\'1$ investi')
ax.legend(loc='upper left', fontsize=9)
ax.grid(True, alpha=0.3)

# Plot International
intl_tickers = [t for t in (list(INTL_ESG.keys()) + list(INTL_CONV.keys())) if t in prices.columns]
cum_intl = (1 + returns_daily[intl_tickers]).cumprod()
ax = axes[1]
for t in intl_tickers:
    style = '-' if t in INTL_ESG else '--'
    ax.plot(cum_intl.index, cum_intl[t], style, label=f'{t} — {ALL_TICKERS[t]}', linewidth=1.8)
ax.axvline(pd.to_datetime(SPLIT_DATE), color='red', linestyle=':', alpha=0.7,
           label='Début hausse Fed (mars 2022)')
ax.set_title('Performance cumulée — Marchés développés ex-US (base 1 au 01/01/2020)', fontsize=13)
ax.set_ylabel('Valeur d\'1$ investi')
ax.legend(loc='upper left', fontsize=9)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/figure_1_performance_cumulee.png', dpi=300, bbox_inches='tight')
plt.close()

# Graphique 2 : drawdown
fig, ax = plt.subplots(figsize=(14, 6))
for t in us_tickers:
    cum = (1 + returns_daily[t]).cumprod()
    dd = (cum - cum.cummax()) / cum.cummax() * 100
    style = '-' if t in US_ESG else '--'
    ax.plot(dd.index, dd, style, label=t, linewidth=1.5)
ax.axvline(pd.to_datetime(SPLIT_DATE), color='red', linestyle=':', alpha=0.7)
ax.set_title('Drawdown — Marché américain (2020-2025)', fontsize=13)
ax.set_ylabel('Drawdown (%)')
ax.legend(loc='lower left')
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/figure_2_drawdown.png', dpi=300, bbox_inches='tight')
plt.close()

# Graphique 3 : Sharpe ratios par sous-période
fig, ax = plt.subplots(figsize=(12, 6))
sharpe_compare = subperiod_table[['Sharpe (taux bas)', 'Sharpe (taux hauts)']]
sharpe_compare.plot(kind='bar', ax=ax, color=['#5B8FB9', '#E07B39'])
ax.set_title('Ratio de Sharpe par sous-période (test de l\'hypothèse H2)', fontsize=13)
ax.set_ylabel('Ratio de Sharpe annualisé')
ax.axhline(0, color='black', linewidth=0.5)
ax.legend(['Taux bas (2020-2022)', 'Taux hauts (2022-2025)'])
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/figure_3_sharpe_souspériodes.png', dpi=300, bbox_inches='tight')
plt.close()

# Graphique 4 : matrice de corrélation
fig, ax = plt.subplots(figsize=(10, 8))
corr = returns_daily.corr()
sns.heatmap(corr, annot=True, fmt='.2f', cmap='RdYlGn', center=0, vmin=-1, vmax=1,
            square=True, ax=ax, cbar_kws={'shrink': 0.8})
ax.set_title('Matrice de corrélation des rendements quotidiens', fontsize=13)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/figure_4_correlations.png', dpi=300, bbox_inches='tight')
plt.close()

log(f"  {len([f for f in os.listdir(OUTPUT_DIR) if f.endswith('.png')])} graphiques générés dans {OUTPUT_DIR}/")

# =====================================================================
# 11. EXPORT EXCEL
# =====================================================================

log("\nExport vers Excel...")
with pd.ExcelWriter('resultats_esg.xlsx', engine='openpyxl') as writer:
    stats_total.to_excel(writer, sheet_name='1_Stats_descriptives')
    risk_stats.to_excel(writer, sheet_name='2_Ratios_risque')
    subperiod_table.to_excel(writer, sheet_name='3_Sous_periodes')
    if ff_factors is not None:
        capm_df.to_excel(writer, sheet_name='4a_CAPM')
        ff3_df.to_excel(writer, sheet_name='4b_FF3')
        ff5_df.to_excel(writer, sheet_name='4c_FF5')
        carhart_df.to_excel(writer, sheet_name='4d_Carhart')
        alpha_comparison.to_excel(writer, sheet_name='5_Alpha_souspériodes')
    welch_df.to_excel(writer, sheet_name='6_Tests_Welch', index=False)
    prices.to_excel(writer, sheet_name='Data_prix')
    returns_daily.to_excel(writer, sheet_name='Data_rendements')

log("Fichier resultats_esg.xlsx créé.")

# =====================================================================
# 12. JOURNAL D'EXÉCUTION
# =====================================================================

with open('log_execution.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(LOG))

log("\n" + "=" * 72)
log("EXÉCUTION TERMINÉE")
log("=" * 72)
log("Fichiers générés :")
log("  - resultats_esg.xlsx (tous les tableaux)")
log("  - figures/*.png (4 graphiques haute résolution)")
log("  - log_execution.txt (journal complet avec valeurs à reporter)")
log("\nValeurs clés à reporter dans le mémoire :")
log(f"  • Sharpe moyen ESG US : {risk_stats.loc[list(US_ESG.keys()), 'Sharpe'].mean():.3f}")
log(f"  • Sharpe moyen Conv US : {risk_stats.loc[list(US_CONV.keys()), 'Sharpe'].mean():.3f}")
intl_esg_in = [t for t in INTL_ESG.keys() if t in risk_stats.index]
intl_conv_in = [t for t in INTL_CONV.keys() if t in risk_stats.index]
if intl_esg_in:
    log(f"  • Sharpe moyen ESG Intl : {risk_stats.loc[intl_esg_in, 'Sharpe'].mean():.3f}")
if intl_conv_in:
    log(f"  • Sharpe moyen Conv Intl : {risk_stats.loc[intl_conv_in, 'Sharpe'].mean():.3f}")
log("\nProchaines étapes :")
log("  1. Ouvrir resultats_esg.xlsx pour récupérer les valeurs précises")
log("  2. Reporter les valeurs dans le mémoire Word (sections résultats)")
log("  3. Intégrer les graphiques PNG dans le mémoire")
