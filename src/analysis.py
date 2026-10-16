"""
ICCIT 2026 - Group 03
Analysis script. Put this file and responses.csv in the same folder and run it.
At the end it prints a REPORT block - copy that whole block and send it back.
"""

import os, warnings
import numpy as np, pandas as pd
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold, KFold
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression, Ridge, LogisticRegression
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.svm import SVR, SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import (mean_squared_error, mean_absolute_error, r2_score,
                             accuracy_score, precision_score, recall_score,
                             f1_score, roc_auc_score, roc_curve, confusion_matrix)

warnings.filterwarnings('ignore')
RS = 42
np.random.seed(RS)

DATA_FILE = 'responses.csv'
OUT = 'output'
os.makedirs(OUT, exist_ok=True)

LOG, REPORT = [], []
def say(*a):
    s = ' '.join(str(x) for x in a); print(s); LOG.append(s)
def rep(*a):
    s = ' '.join(str(x) for x in a); REPORT.append(s)
def head(t):
    say('\n' + '=' * 70); say(t); say('=' * 70)

CONS = {'PA': ['PA1','PA2','PA3'], 'PE': ['PE1','PE2','PE3'], 'PT': ['PT1','PT2','PT3'],
        'MP': ['MP1','MP2','MP3'], 'SC': ['SC1','SC2','SC3'], 'DS': ['DS1','DS2','DS3'],
        'AIL': ['AIL1','AIL2','AIL3'], 'CT': ['CT1','CT2','CT3'],
        'ACB': ['ACB1','ACB2','ACB3'], 'NWOM': ['NWOM1','NWOM2','NWOM3']}
ITEMS = [i for v in CONS.values() for i in v]

COLS = (['TIMESTAMP','CONSENT','AGE','GENDER','EDU','OCC','SM_HOURS','EXP_FREQ',
         'BIRTH_HALF','MANIP_CHECK']
        + CONS['PA'] + CONS['PE'] + CONS['PT'] + CONS['MP'] + CONS['SC']
        + CONS['DS'] + CONS['AIL'] + ['AC1']
        + CONS['CT'] + CONS['ACB'] + ['AC2'] + ['PIR_RAW'] + CONS['NWOM'])

FREQ_MID = {'Never': 0, 'Once or twice': 1.5, '3 to 5 times': 4,
            '6 to 10 times': 8, 'More than 10 times': 12}

# ---------------------------------------------------------------- 1. LOAD
head('1. LOADING')
if DATA_FILE.lower().endswith(('.xlsx', '.xls')):
    df = pd.read_excel(DATA_FILE)
else:
    df = pd.read_csv(DATA_FILE)

if len(df.columns) != len(COLS):
    say('PROBLEM: the file has %d columns, the script expects %d.' % (len(df.columns), len(COLS)))
    say('Send this whole list to Saikat. Do not guess the mapping.')
    for i, c in enumerate(df.columns):
        say('  %3d  %s' % (i, str(c)[:75]))
    raise SystemExit

df.columns = COLS
n_raw = len(df)
say('Loaded %s   Raw responses: %d' % (DATA_FILE, n_raw))

# ---------------------------------------------------------------- 2. CLEAN
head('2. SCREENING')
counts = {}
df = df[df['CONSENT'].astype(str).str.startswith('Yes')].copy()
counts['no consent'] = n_raw - len(df)

for c in ITEMS + ['AC1', 'AC2', 'PIR_RAW']:
    df[c] = pd.to_numeric(df[c].astype(str).str.extract(r'(\d)')[0], errors='coerce')
for c in ['AGE', 'SM_HOURS']:
    df[c] = pd.to_numeric(df[c], errors='coerce')

b = len(df); df = df.dropna(subset=ITEMS + ['AC1','AC2','AGE','SM_HOURS'])
counts['incomplete'] = b - len(df)
# Attention checks are NOT used for exclusion. They were embedded inside
# Likert grids whose columns show bare numerals, and respondents read them as
# statements to agree with rather than as instructions. Section 4b reports the
# evidence for that. Excluding on them removes most of an attentive sample.
b = len(df); df = df[df[ITEMS].nunique(axis=1) > 1]
counts['straight-lining'] = b - len(df)
b = len(df); df = df[df['SM_HOURS'] > 0]
counts['no social media use'] = b - len(df)

df = df.reset_index(drop=True)
N = len(df)
for k, v in counts.items():
    say('  removed - %-26s %d' % (k, v))
say('Valid cases: %d' % N)

sentence = ('Of %d responses received, ' % n_raw
            + ', '.join('%d %s' % (v, k) for k, v in counts.items() if v)
            + ', leaving %d valid cases.' % N)
say('\nSENTENCE FOR THE PAPER:'); say('"' + sentence + '"')

# ---------------------------------------------------------------- 3. DERIVE
head('3. DERIVED VARIABLES')
df['CONTENT_TYPE'] = (df['BIRTH_HALF'] == 'July to December').astype(int)
df['EXP_FREQ_NUM'] = df['EXP_FREQ'].map(FREQ_MID)
for n, it in CONS.items():
    df[n] = df[it].mean(axis=1)
df['CT_100'] = (df['CT'] - 1) / 4 * 100
df['PIR'] = df['PIR_RAW'] * 10
df['ACB_BIN'] = (df['ACB'] > 3.0).astype(int)
exp = np.where(df['CONTENT_TYPE'] == 1, 'An AI tool', 'A human creator')
df['MANIP_PASS'] = (df['MANIP_CHECK'] == exp).astype(int)

nH = int((df['CONTENT_TYPE'] == 0).sum()); nA = int((df['CONTENT_TYPE'] == 1).sum())
mp = df['MANIP_PASS'].mean() * 100
bal = df['ACB_BIN'].value_counts(normalize=True).sort_index() * 100
say('Human: %d   AI: %d' % (nH, nA))
say('Manipulation check passed: %.1f%%' % mp)
say('ACB_BIN split - 0: %.1f%%   1: %.1f%%' % (bal.get(0, 0), bal.get(1, 0)))

# ---------------------------------------------------------------- 4. RELIABILITY
head('4. RELIABILITY')
def alpha(f):
    k = f.shape[1]
    tv = f.sum(axis=1).var(ddof=1)
    return np.nan if tv == 0 else (k / (k - 1)) * (1 - f.var(ddof=1).sum() / tv)

rows = []
for n, it in CONS.items():
    a = alpha(df[it])
    rows.append({'Construct': n, 'Mean': round(df[n].mean(), 2), 'SD': round(df[n].std(), 2),
                 'Alpha': round(a, 3), 'OK': 'Yes' if a >= 0.70 else 'NO'})
rel = pd.DataFrame(rows)
say(rel.to_string(index=False))
rel.to_csv('%s/table_reliability.csv' % OUT, index=False)
weak = rel[rel['OK'] == 'NO']['Construct'].tolist()
if weak:
    say('\nBelow 0.70: %s  -- report the real value, do not drop items.' % weak)

# ---------------------------------------------------------------- 4b. AC DIAGNOSTIC
head('4b. ATTENTION CHECK DIAGNOSTIC (reported, not used for exclusion)')
ac1p = (df['AC1'] == 2).mean() * 100
ac2p = (df['AC2'] == 5).mean() * 100
say('  AC1 pass rate : %.1f%%   mean response %.2f' % (ac1p, df['AC1'].mean()))
say('  AC2 pass rate : %.1f%%   mean response %.2f' % (ac2p, df['AC2'].mean()))
say('  Random responding would give a mean near 3.00 and a flat distribution.')
say('  Centred means plus acceptable alphas indicate the items failed, not the')
say('  participants. This goes in Section III-E as a measurement limitation.')

# ---------------------------------------------------------------- 5. CMB
head('5. COMMON METHOD BIAS (Harman)')
X0 = df[ITEMS].astype(float)
X0 = (X0 - X0.mean()) / X0.std(ddof=1)
ev = np.linalg.eigvalsh(np.corrcoef(X0.values.T))[::-1]
harman = ev[0] / ev.sum() * 100
say('First factor explains %.1f%% of variance' % harman)
say('Below 50%% means common method bias is unlikely to explain the results.')

# ---------------------------------------------------------------- 6. DESCRIPTIVES
head('6. DESCRIPTIVES AND GROUP BALANCE')
desc = df[['AGE','SM_HOURS','EXP_FREQ_NUM'] + list(CONS) + ['CT_100','PIR']] \
    .describe().T[['mean','std','min','max']].round(2)
desc.columns = ['Mean','SD','Min','Max']
say(desc.to_string()); desc.to_csv('%s/table_descriptives.csv' % OUT)

say('\nGroup balance (should NOT be significant):')
bal_lines = []
for c in ['AGE', 'SM_HOURS']:
    a_, b_ = df[df.CONTENT_TYPE == 0][c], df[df.CONTENT_TYPE == 1][c]
    _, p = stats.ttest_ind(a_, b_, equal_var=False)
    flag = '  <-- IMBALANCED' if p < .05 else ''
    say('  %-12s p = %.3f%s' % (c, p, flag)); bal_lines.append('%s p=%.3f' % (c, p))
for c in ['GENDER', 'EDU', 'OCC']:
    ct = pd.crosstab(df[c], df['CONTENT_TYPE'])
    if ct.shape[0] > 1:
        _, p, _, _ = stats.chi2_contingency(ct)
        flag = '  <-- IMBALANCED' if p < .05 else ''
        say('  %-12s p = %.3f%s' % (c, p, flag)); bal_lines.append('%s p=%.3f' % (c, p))

# ---------------------------------------------------------------- 7. HYPOTHESES
head('7. HYPOTHESIS TESTS')
h = df[df.CONTENT_TYPE == 0]['CT_100']; a = df[df.CONTENT_TYPE == 1]['CT_100']
t, p1 = stats.ttest_ind(h, a, equal_var=False)
sp = np.sqrt(((nH-1)*h.var(ddof=1) + (nA-1)*a.var(ddof=1)) / (nH+nA-2))
d = (h.mean() - a.mean()) / sp
vh, va = h.var(ddof=1)/nH, a.var(ddof=1)/nA
dfw = (vh+va)**2 / (vh**2/(nH-1) + va**2/(nA-1))
se = np.sqrt(vh+va); crit = stats.t.ppf(.975, dfw); diff = h.mean() - a.mean()
lo, hi = diff - crit*se, diff + crit*se

say('H1 - consumer trust by condition (Welch t-test)')
say('  Human  M=%.2f SD=%.2f n=%d' % (h.mean(), h.std(), nH))
say('  AI     M=%.2f SD=%.2f n=%d' % (a.mean(), a.std(), nA))
say('  t(%.2f) = %.3f, p = %.4f, d = %.3f, 95%% CI [%.2f, %.2f]' % (dfw, t, p1, d, lo, hi))
say('  H1 %s' % ('SUPPORTED' if p1 < .05 else 'NOT SUPPORTED'))
if p1 >= .05:
    say('  A null result is publishable here - use Discussion VERSION B.')
else:
    say('  Use Discussion VERSION A.')

ct = pd.crosstab(df['CONTENT_TYPE'], df['ACB_BIN'])
chi2, p2, dof, _ = stats.chi2_contingency(ct)
say('\nCondition x anti-consumption: chi2(%d) = %.3f, p = %.4f' % (dof, chi2, p2))

say('\nH2 / H3 - correlations with consumer trust:')
cr = []
for c in ['PA','PE','PT','MP','SC','DS','AIL','SM_HOURS','EXP_FREQ_NUM','AGE']:
    r, p = stats.pearsonr(df[c], df['CT_100'])
    cr.append({'Predictor': c, 'r': round(r, 3), 'p': round(p, 4),
               'sig': '***' if p < .001 else '**' if p < .01 else '*' if p < .05 else ''})
cor = pd.DataFrame(cr).sort_values('r', key=abs, ascending=False)
say(cor.to_string(index=False)); cor.to_csv('%s/table_correlations.csv' % OUT, index=False)
r_ds, p_ds = stats.pearsonr(df['DS'], df['CT_100'])

r4, p4 = stats.pearsonr(df['CT_100'], df['ACB'])
say('\nH4 - trust vs anti-consumption: r = %.3f, p = %.4f' % (r4, p4))

# ---------------------------------------------------------------- 8. FEATURES
head('8. FEATURES AND VIF')
X = pd.DataFrame(index=df.index)
X['CONTENT_TYPE'] = df['CONTENT_TYPE']
for c in ['PA','PE','PT','MP','SC','DS','AIL']:
    X[c] = df[c]
X['AGE'] = df['AGE']; X['SM_HOURS'] = df['SM_HOURS']; X['EXP_FREQ'] = df['EXP_FREQ_NUM']
X['GENDER_M'] = (df['GENDER'] == 'Male').astype(int)

dropped = []
for c in list(X.columns):
    if X[c].value_counts(normalize=True).max() > 0.85 and c != 'CONTENT_TYPE':
        dropped.append(c); X = X.drop(columns=[c])
if dropped:
    say('Dropped for near-zero variance: %s' % dropped)

ratio = len(X) / X.shape[1]
say('Predictors: %d   Observations: %d   Ratio: %.1f' % (X.shape[1], len(X), ratio))
if ratio < 10:
    say('  Ratio below 10 - report cross-validated metrics only.')

vifs = []
for i, c in enumerate(X.columns):
    others = X.drop(columns=[c])
    r2 = LinearRegression().fit(others, X[c]).score(others, X[c])
    vifs.append({'Variable': c, 'VIF': round(1 / (1 - r2) if r2 < .9999 else 999, 2)})
vif = pd.DataFrame(vifs).sort_values('VIF', ascending=False)
say(vif.to_string(index=False)); vif.to_csv('%s/table_vif.csv' % OUT, index=False)
vmin, vmax = vif['VIF'].min(), vif['VIF'].max()

# ---------------------------------------------------------------- 9. REGRESSION
head('9. REGRESSION - consumer trust')
y = df['CT_100']
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=.2, random_state=RS)
kf = KFold(5, shuffle=True, random_state=RS)
rows = []
for name, m in [('Linear Regression', LinearRegression()), ('Ridge Regression', Ridge(alpha=1.0)),
                ('Random Forest', RandomForestRegressor(n_estimators=300, random_state=RS)),
                ('SVR', SVR(kernel='rbf', C=10))]:
    pipe = Pipeline([('s', StandardScaler()), ('m', m)])
    cv = cross_val_score(pipe, X, y, cv=kf, scoring='r2')
    pipe.fit(Xtr, ytr); pr = pipe.predict(Xte)
    rows.append({'Model': name, 'CV R2': round(cv.mean(), 3), 'CV SD': round(cv.std(), 3),
                 'Test R2': round(r2_score(yte, pr), 3),
                 'RMSE': round(np.sqrt(mean_squared_error(yte, pr)), 3),
                 'MAE': round(mean_absolute_error(yte, pr), 3)})
regt = pd.DataFrame(rows).sort_values('CV R2', ascending=False)
say(regt.to_string(index=False)); regt.to_csv('%s/table_regression.csv' % OUT, index=False)
best_reg = regt.iloc[0]

# ---------------------------------------------------------------- 10. CLASSIFICATION
head('10. CLASSIFICATION - anti-consumption')
yb = df['ACB_BIN']
if yb.value_counts().min() < 10:
    say('Only %d cases in the smaller class - classification skipped.' % yb.value_counts().min())
    say('Check the screening step above; this usually means too many rows were dropped.')
    raise SystemExit
Xtr, Xte, ytr, yte = train_test_split(X, yb, test_size=.2, stratify=yb, random_state=RS)
skf = StratifiedKFold(5, shuffle=True, random_state=RS)
rows, rocs = [], {}
for name, m in [('Logistic Regression', LogisticRegression(max_iter=2000)),
                ('Decision Tree', DecisionTreeClassifier(max_depth=5, random_state=RS)),
                ('Random Forest', RandomForestClassifier(n_estimators=300, random_state=RS)),
                ('SVM', SVC(kernel='rbf', C=10, probability=True, random_state=RS)),
                ('k-NN', KNeighborsClassifier(n_neighbors=7))]:
    pipe = Pipeline([('s', StandardScaler()), ('m', m)])
    cv = cross_val_score(pipe, X, yb, cv=skf, scoring='roc_auc')
    pipe.fit(Xtr, ytr); pr = pipe.predict(Xte); pb = pipe.predict_proba(Xte)[:, 1]
    tn, fp, fn, tp = confusion_matrix(yte, pr).ravel()
    rows.append({'Model': name, 'CV AUC': round(cv.mean(), 3), 'CV SD': round(cv.std(), 3),
                 'Accuracy': round(accuracy_score(yte, pr), 3),
                 'Precision': round(precision_score(yte, pr, zero_division=0), 3),
                 'Recall': round(recall_score(yte, pr, zero_division=0), 3),
                 'Specificity': round(tn/(tn+fp) if (tn+fp) else 0, 3),
                 'F1': round(f1_score(yte, pr, zero_division=0), 3),
                 'Test AUC': round(roc_auc_score(yte, pb), 3)})
    rocs[name] = roc_curve(yte, pb)
clst = pd.DataFrame(rows).sort_values('CV AUC', ascending=False)
say(clst.to_string(index=False)); clst.to_csv('%s/table_classification.csv' % OUT, index=False)
best_cls = clst.iloc[0]

# ---------------------------------------------------------------- 11. IMPORTANCE
head('11. FEATURE IMPORTANCE')
rf = RandomForestRegressor(n_estimators=500, random_state=RS).fit(X, y)
imp = pd.DataFrame({'Feature': X.columns, 'Importance': rf.feature_importances_.round(4)}) \
        .sort_values('Importance', ascending=False)
say(imp.to_string(index=False)); imp.to_csv('%s/table_importance.csv' % OUT, index=False)
top3 = ', '.join(imp.head(3)['Feature'])
ct_imp = float(imp[imp.Feature == 'CONTENT_TYPE']['Importance'].iloc[0])

h5 = N >= 180
say('\nH5 - importance by condition:')
if h5:
    for g, lbl in [(0, 'Human'), (1, 'AI')]:
        msk = df['CONTENT_TYPE'] == g
        r = RandomForestRegressor(n_estimators=500, random_state=RS).fit(X[msk], y[msk])
        s = pd.Series(r.feature_importances_, index=X.columns).sort_values(ascending=False)
        say('  %s (n=%d) top 5: %s' % (lbl, msk.sum(), ', '.join(s.head(5).index)))
else:
    say('  N = %d. Too small to split. DROP H5 and Section IV-E from the paper.' % N)

# ---------------------------------------------------------------- 12. FIGURES
head('12. FIGURES (IEEE single-column, 300 dpi)')

# IEEE single column is about 3.5 inches wide. Figures are drawn at that size
# so the text inside stays readable after the template shrinks them.
plt.rcParams.update({'font.size': 8, 'axes.titlesize': 9, 'axes.labelsize': 8,
                     'xtick.labelsize': 7, 'ytick.labelsize': 7, 'legend.fontsize': 6.5,
                     'font.family': 'serif'})

# Fig 1 - trust by condition
fig, ax = plt.subplots(figsize=(3.5, 2.6))
bp = ax.boxplot([h, a], tick_labels=['Human', 'AI'], widths=.55, patch_artist=True)
for patch, col in zip(bp['boxes'], ['#d9d9d9', '#9e9e9e']):
    patch.set_facecolor(col)
for med in bp['medians']:
    med.set_color('black')
ax.set_ylabel('Consumer trust (0-100)')
ax.set_xlabel('Attributed source')
ax.grid(axis='y', alpha=.3, linewidth=.5)
ax.set_axisbelow(True)
fig.tight_layout()
fig.savefig('%s/fig1_trust.png' % OUT, dpi=300, bbox_inches='tight')
plt.close(fig)

# Fig 2 - ROC curves, distinguishable in black and white
fig, ax = plt.subplots(figsize=(3.5, 2.9))
styles = ['-', '--', '-.', ':', (0, (3, 1, 1, 1))]
for (name, (fpr, tpr, _)), st in zip(rocs.items(), styles):
    auc = clst[clst.Model == name]['Test AUC'].iloc[0]
    ax.plot(fpr, tpr, linestyle=st, color='black', linewidth=1.1,
            label='%s (%.2f)' % (name, auc))
ax.plot([0, 1], [0, 1], color='grey', linewidth=.6, linestyle=':')
ax.set_xlabel('False positive rate'); ax.set_ylabel('True positive rate')
ax.legend(loc='lower right', frameon=False)
ax.grid(alpha=.3, linewidth=.5); ax.set_axisbelow(True)
fig.tight_layout()
fig.savefig('%s/fig2_roc.png' % OUT, dpi=300, bbox_inches='tight')
plt.close(fig)

# Fig 3 - feature importance
fig, ax = plt.subplots(figsize=(3.5, 2.9))
t10 = imp.head(10).iloc[::-1]
ax.barh(t10['Feature'], t10['Importance'], color='#7a7a7a', edgecolor='black', linewidth=.4)
ax.set_xlabel('Relative importance')
ax.grid(axis='x', alpha=.3, linewidth=.5); ax.set_axisbelow(True)
fig.tight_layout()
fig.savefig('%s/fig3_importance.png' % OUT, dpi=300, bbox_inches='tight')
plt.close(fig)

say('Saved fig1_trust.png, fig2_roc.png, fig3_importance.png')
say('All three are 3.5 inches wide at 300 dpi and readable in black and white.')

# ---------------------------------------------------------------- 12b. TABLES
head('13. TABLES READY TO PASTE')
TBL = []
def tline(*a):
    s = ' '.join(str(x) for x in a); TBL.append(s)

tline('TABLE I.  DESCRIPTIVE STATISTICS AND RELIABILITY')
tline('Construct\tItems\tMean\tSD\tAlpha')
name_map = {'PA': 'Perceived authenticity', 'PE': 'Perceived expertise',
            'PT': 'Perceived transparency', 'MP': 'Message persuasiveness',
            'SC': 'Source credibility', 'DS': 'Dispositional skepticism',
            'AIL': 'AI literacy', 'CT': 'Consumer trust',
            'ACB': 'Anti-consumption', 'NWOM': 'Negative word-of-mouth'}
for _, r in rel.iterrows():
    tline('%s\t3\t%.2f\t%.2f\t%.3f'
          % (name_map[r['Construct']], r['Mean'], r['SD'], r['Alpha']))
tline('')
tline('TABLE II.  REGRESSION PERFORMANCE - CONSUMER TRUST')
tline('Model\tCV R2\tCV SD\tTest R2\tRMSE\tMAE')
for _, r in regt.iterrows():
    tline('%s\t%.3f\t%.3f\t%.3f\t%.3f\t%.3f'
          % (r['Model'], r['CV R2'], r['CV SD'], r['Test R2'], r['RMSE'], r['MAE']))
tline('')
tline('TABLE III.  CLASSIFICATION PERFORMANCE - ANTI-CONSUMPTION')
tline('Model\tCV AUC\tAccuracy\tPrecision\tRecall\tSpecificity\tF1')
for _, r in clst.iterrows():
    tline('%s\t%.3f\t%.3f\t%.3f\t%.3f\t%.3f\t%.3f'
          % (r['Model'], r['CV AUC'], r['Accuracy'], r['Precision'],
             r['Recall'], r['Specificity'], r['F1']))

for l in TBL:
    say(l)
with open('%s/TABLES.txt' % OUT, 'w') as f:
    f.write('\n'.join(TBL))
say('')
say('Saved to output/TABLES.txt - columns are tab separated, so pasting into')
say('Word and using Insert > Table > Convert Text to Table builds the table.')

# ---------------------------------------------------------------- REPORT
rep('=============== REPORT - COPY EVERYTHING BELOW ===============')
rep('')
rep('SAMPLE')
rep('  Raw responses          : %d' % n_raw)
for k, v in counts.items():
    rep('  Removed, %-22s: %d' % (k, v))
rep('  VALID N                : %d' % N)
rep('  Human condition        : %d' % nH)
rep('  AI condition           : %d' % nA)
rep('  Manipulation pass rate : %.1f%%' % mp)
rep('  ACB_BIN split          : %.1f%% / %.1f%%' % (bal.get(0, 0), bal.get(1, 0)))
rep('')
rep('  Sentence for Section IV-A:')
rep('  "%s"' % sentence)
rep('')
rep('RELIABILITY (Cronbach alpha)')
for _, r in rel.iterrows():
    rep('  %-6s mean %.2f  SD %.2f  alpha %.3f  %s'
        % (r['Construct'], r['Mean'], r['SD'], r['Alpha'], r['OK']))
rep('  Constructs below 0.70  : %s' % (weak if weak else 'none'))
rep('')
rep('ATTENTION CHECKS (reported, not used for exclusion)')
rep('  AC1 pass rate          : %.1f%%  (mean response %.2f)' % (ac1p, df['AC1'].mean()))
rep('  AC2 pass rate          : %.1f%%  (mean response %.2f)' % (ac2p, df['AC2'].mean()))
rep('')
rep('COMMON METHOD BIAS')
rep('  Harman first factor    : %.1f%%' % harman)
rep('')
rep('GROUP BALANCE (p-values, should all be above .05)')
rep('  ' + '   '.join(bal_lines))
rep('')
rep('H1 - TRUST BY CONDITION')
rep('  Human  M = %.2f  SD = %.2f' % (h.mean(), h.std()))
rep('  AI     M = %.2f  SD = %.2f' % (a.mean(), a.std()))
rep('  t(%.2f) = %.3f   p = %.4f   d = %.3f' % (dfw, t, p1, d))
rep('  95%% CI of difference   : [%.2f, %.2f]' % (lo, hi))
rep('  RESULT                 : %s' % ('SUPPORTED' if p1 < .05 else 'NOT SUPPORTED'))
rep('  DISCUSSION VERSION     : %s' % ('A' if p1 < .05 else 'B'))
rep('')
rep('CHI-SQUARE, condition x anti-consumption')
rep('  chi2(%d) = %.3f   p = %.4f' % (dof, chi2, p2))
rep('')
rep('H2 / H3 - CORRELATIONS WITH TRUST')
for _, r in cor.iterrows():
    rep('  %-14s r = %+.3f  p = %.4f %s' % (r['Predictor'], r['r'], r['p'], r['sig']))
rep('  H3 (skepticism)        : r = %+.3f, p = %.4f -> %s'
    % (r_ds, p_ds, 'SUPPORTED' if (p_ds < .05 and r_ds < 0) else 'NOT SUPPORTED'))
rep('')
rep('H4 - TRUST vs ANTI-CONSUMPTION')
rep('  r = %+.3f   p = %.4f   -> %s' % (r4, p4, 'SUPPORTED' if p4 < .05 else 'NOT SUPPORTED'))
rep('')
rep('FEATURES')
rep('  Predictors used        : %d' % X.shape[1])
rep('  Dropped (low variance) : %s' % (dropped if dropped else 'none'))
rep('  Observations/predictor : %.1f' % ratio)
rep('  VIF range              : %.2f to %.2f' % (vmin, vmax))
rep('  Train / test split     : %d / %d' % (int(N * .8), N - int(N * .8)))
rep('')
rep('REGRESSION - consumer trust')
for _, r in regt.iterrows():
    rep('  %-20s CV R2 %.3f (SD %.3f)  Test R2 %.3f  RMSE %.3f  MAE %.3f'
        % (r['Model'], r['CV R2'], r['CV SD'], r['Test R2'], r['RMSE'], r['MAE']))
rep('  BEST                   : %s, CV R2 = %.3f' % (best_reg['Model'], best_reg['CV R2']))
rep('')
rep('CLASSIFICATION - anti-consumption')
for _, r in clst.iterrows():
    rep('  %-20s CV AUC %.3f  Acc %.3f  Prec %.3f  Rec %.3f  Spec %.3f  F1 %.3f'
        % (r['Model'], r['CV AUC'], r['Accuracy'], r['Precision'],
           r['Recall'], r['Specificity'], r['F1']))
rep('  BEST                   : %s, CV AUC = %.3f' % (best_cls['Model'], best_cls['CV AUC']))
rep('')
rep('FEATURE IMPORTANCE')
for _, r in imp.iterrows():
    rep('  %-14s %.4f' % (r['Feature'], r['Importance']))
rep('  Top three              : %s' % top3)
rep('  CONTENT_TYPE           : %.4f' % ct_imp)
rep('')
rep('DECISIONS')
rep('  Keep H5 / Section IV-E : %s' % ('YES' if h5 else 'NO - delete both, N is under 180'))
rep('  Discussion version     : %s' % ('A' if p1 < .05 else 'B'))
rep('  Alpha problems         : %s' % (weak if weak else 'none'))
rep('')
rep('=============== END OF REPORT ===============')

print('\n' * 2)
for line in REPORT:
    print(line)

with open('%s/results.txt' % OUT, 'w') as f:
    f.write('\n'.join(LOG))
with open('%s/REPORT.txt' % OUT, 'w') as f:
    f.write('\n'.join(REPORT))
df.to_csv('%s/cleaned_data.csv' % OUT, index=False)

print('\nAlso saved: output/REPORT.txt, output/TABLES.txt,')
print('fig1_trust.png, fig2_roc.png, fig3_importance.png - send all of these.')
