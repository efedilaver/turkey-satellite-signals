#!/usr/bin/env python3
"""T-P6 — Çeyrek sonu → bilanço sinyalleri momentum kontrolünden sonra kalıyor mu?
(kayıt: ARASTIRMA_PLANI.md, 2026-10-23 16:25). Önce pz_testi, pz2_kur, pz4_ufe çalışmış olmalı.
Kullanım: python studies/earnings_surprise/pz6_momentum.py -> cikti/pz/mom_ozet.csv
"""
import os, numpy as np, pandas as pd

U = '.'; RS = os.path.join(os.environ.get('RESEARCH_DIR', '../Research'), 'data'); OUT = f'{U}/cikti/pz'
MIN_KOHORT = 30

ev = pd.read_csv(f'{OUT}/olaylar.csv', parse_dates=['gun1'])[['symbol', 'kohort', 'gun1']]
kur = pd.read_csv(f'{OUT}/kur_olaylar.csv').merge(ev, on=['symbol', 'kohort'])
ufe = pd.read_csv(f'{OUT}/ufe_olaylar.csv', dtype={'nace2': str}, parse_dates=['gun1'])
alt = pd.read_parquet(f'{U}/cikti/faktor/panel_aylik.parquet', columns=['symbol', 'sub_sector']).dropna()
alt = alt.groupby('symbol').sub_sector.last()
kur['sektor'] = kur.symbol.map(alt).fillna('BILINMIYOR'); ufe['sektor'] = ufe.nace2
mk = pd.read_csv(f'{U}/cikti/faktor/gunluk_makro.csv', parse_dates=['date']).dropna(subset=['dd_deger']).sort_values('date')
FXD, FXV = mk.date.values, mk.dd_deger.values

def qe(y, q): return pd.Timestamp(year=int(y), month=3 * int(q), day=1) + pd.offsets.MonthEnd(0)

def ozellik(d, kayma):
    out = {}
    for s, g in d.groupby('symbol'):
        p = pd.read_parquet(f'{RS}/market/prices/{s}.parquet', columns=['date', 'close', 'end_deger']).dropna(subset=['close'])
        p = p[p.close > 0].sort_values('date'); D = p.date.values; C = np.log(p.close.values); I = np.log(p.end_deger.values)
        ar = lambda a, b: (C[b] - C[a]) - (I[b] - I[a]) if 0 <= a < b < len(D) else np.nan
        for i, r in g.iterrows():
            qi = np.searchsorted(D, np.datetime64(qe(r.yil, r.ceyrek)), side='right') - 1
            b = np.searchsorted(D, np.datetime64(r.gun1), side='left')
            a = qi + kayma
            fx0 = FXV[np.searchsorted(FXD, D[a], side='right') - 1] if a < len(D) else np.nan
            fx1 = FXV[np.searchsorted(FXD, np.datetime64(r.gun1), side='right') - 1]
            out[i] = dict(MOM_Q=ar(qi - 63, qi), MOM_12=ar(qi - 252, qi - 21), dFX_pencere=fx1 / fx0 - 1)
    return d.join(pd.DataFrame.from_dict(out, orient='index'))

kur = ozellik(kur, 1); ufe = ozellik(ufe, 5)
for d in (kur, ufe):
    t = d.groupby(['kohort', 'sektor']).MOM_Q.transform('sum'); n = d.groupby(['kohort', 'sektor']).MOM_Q.transform('count')
    d['SEKMOM'] = np.where(n > 1, (t - d.MOM_Q.fillna(0)) / (n - d.MOM_Q.notna().astype(int)).clip(lower=1), 0.0)
kur['MEK'] = kur.NFX_PD_A * kur.dFX_pencere

def fm(d, y, x, kontrol):
    cf = []
    for k, g in d.groupby('kohort'):
        g = g[[y, x] + kontrol].dropna()
        if len(g) < MIN_KOHORT: continue
        R = g.rank(); R = (R - R.mean()) / R.std()
        X = np.c_[np.ones(len(R)), R[[x] + kontrol].values]
        cf.append(np.linalg.lstsq(X, R[y].values, rcond=None)[0][1])
    cf = np.array(cf); n = len(cf)
    return dict(sinyal=x, hedef=y, kontroller='+'.join(kontrol) or '-', kohort=n,
                katsayi=cf.mean(), t=cf.mean() / (cf.std(ddof=1) / np.sqrt(n)))

K = ['MOM_Q', 'MOM_12', 'SEKMOM']
res = []
for d, x, y in [(kur, 'S_KUR_A', 'T'), (ufe, 'R', 'T5')]:
    res.append({**fm(d, y, x, K), 'etiket': 'KAPI'})
    res.append({**fm(d, y, x, []), 'etiket': 'rapor_kontrolsuz'})
    for c in K: res.append({**fm(d, y, x, [c]), 'etiket': 'rapor_tek_kontrol'})
res.append({**fm(kur, 'T', 'S_KUR_A', K + ['NFX_PD_A']), 'etiket': 'rapor_maruziyet'})
res.append({**fm(kur, 'T', 'S_KUR_A', K + ['MEK']), 'etiket': 'rapor_mekanik_kur(bilinmez)'})
oz = pd.DataFrame(res)
m = oz.etiket == 'KAPI'
oz.loc[m, 'kapi'] = np.where((oz.loc[m, 'katsayi'] >= 0.04) & (oz.loc[m, 't'] >= 2.5), 'GECTI', 'KALDI')
oz.to_csv(f'{OUT}/mom_ozet.csv', index=False)
pd.set_option('display.width', 200)
print(f'kur olay {len(kur)}, ufe olay {len(ufe)}')
print(kur[['S_KUR_A', 'MOM_Q', 'MOM_12', 'SEKMOM']].corr('spearman').round(2).iloc[0].to_dict())
print(ufe[['R', 'MOM_Q', 'MOM_12', 'SEKMOM']].corr('spearman').round(2).iloc[0].to_dict())
print(oz.round(4).to_string())
