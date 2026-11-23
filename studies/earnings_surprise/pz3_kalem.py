#!/usr/bin/env python3
"""T-P3 — Kur dışı sürprizi hangi kalem taşıyor? (kayıt: ARASTIRMA_PLANI.md, 2026-10-23 14:15)
Önce pz_testi.py ve pz2_kur.py çalışmış olmalı.
Kullanım: python studies/earnings_surprise/pz3_kalem.py -> cikti/pz/{kalem_olaylar,kalem_ozet}.csv
"""
import os, numpy as np, pandas as pd

RS = os.path.join(os.environ.get('RESEARCH_DIR', '../Research'), 'data')
OUT = 'cikti/pz'
MIN_KOHORT = 30

ev = pd.read_csv(f'{OUT}/olaylar.csv', parse_dates=['ref'])
ev = ev[ev.ana].copy()
kur = pd.read_csv(f'{OUT}/kur_olaylar.csv')[['symbol', 'kohort', 'S_KUR_A']]

def tek_ceyrek(f, kod):
    if kod not in f.index: return {}
    r = f.loc[kod]; ytd = {}
    for c in r.index:
        if '/' in str(c) and pd.notna(r[c]):
            y, m = str(c).split('/'); ytd[(int(y), int(m) // 3)] = float(r[c])
    out = {}
    for (y, q), v in ytd.items():
        if q == 1: out[(y, 1)] = v
        elif (y, q - 1) in ytd: out[(y, q)] = v - ytd[(y, q - 1)]
    return out

rows = []
for s, g in ev.groupby('symbol'):
    f = pd.read_parquet(f'{RS}/financials/{s}.parquet').drop_duplicates('itemCode').set_index('itemCode')
    K = {k: tek_ceyrek(f, k) for k in ['3C', '3D', '3DF', '3I', '3Z', '3L']}
    for k, v in K['3L'].items(): K['3Z'].setdefault(k, v)
    p = pd.read_parquet(f'{RS}/market/prices/{s}.parquet', columns=['date', 'pd']).set_index('date').pd
    for _, r in g.iterrows():
        y, q = int(r.yil), int(r.ceyrek); q4 = (y - 1, q)
        pdref = p.get(r.ref, np.nan)
        if not (pdref > 0): continue
        o = dict(symbol=s, kohort=r.kohort, A=r.A, hacim=r.hacim)
        for ad, kod in [('D_SATIS', '3C'), ('D_BRUT', '3D'), ('D_FAAL', '3DF'), ('D_VOK', '3I'), ('S_KAR', '3Z')]:
            a, b = K[kod].get((y, q)), K[kod].get(q4)
            o[ad] = (a - b) / pdref if a is not None and b is not None else np.nan
        sa, sb, ba, bb = K['3C'].get((y, q)), K['3C'].get(q4), K['3D'].get((y, q)), K['3D'].get(q4)
        o['D_MARJ'] = (ba / sa - bb / sb) if all(v is not None for v in [sa, sb, ba, bb]) and sa > 0 and sb > 0 else np.nan
        rows.append(o)

d = pd.DataFrame(rows).merge(kur, on=['symbol', 'kohort'], how='left')
d['B1'] = d.D_BRUT; d['B2'] = d.D_FAAL - d.D_BRUT; d['B3'] = d.D_VOK - d.D_FAAL; d['B4'] = d.S_KAR - d.D_VOK
B = ['B1', 'B2', 'B3', 'B4']
tam = d.dropna(subset=['A', 'D_SATIS', 'D_BRUT', 'D_FAAL', 'D_VOK', 'S_KAR']).copy()
lo, hi = np.nanpercentile(tam.A, [1, 99]); tam['A_k'] = tam.A.clip(lo, hi)
tam['likit'] = tam.groupby('kohort').hacim.transform(lambda x: x >= x.median())

def ic_ozet(dd, x, y='A', etiket='ANA'):
    ics = []
    for k, g in dd.groupby('kohort'):
        g = g[[x, y]].dropna()
        if len(g) < MIN_KOHORT: continue
        ics.append(g[x].rank().corr(g[y].rank()))
    ics = np.array(ics); n = len(ics)
    return dict(etiket=etiket, olcu=x, hedef=y, kohort=n, IC_ort=ics.mean(),
                IC_t=ics.mean() / (ics.std(ddof=1) / np.sqrt(n)), IC_poz_oran=(ics > 0).mean())

def fm(dd):
    cf = []
    for k, g in dd.groupby('kohort'):
        if len(g) < MIN_KOHORT: continue
        X = []
        for b in B:
            v = g[b].clip(*np.nanpercentile(g[b], [1, 99])); X.append((v - v.mean()) / v.std())
        X = np.c_[np.ones(len(g)), np.array(X).T]
        cf.append(np.linalg.lstsq(X, g.A_k.values, rcond=None)[0][1:])
    cf = np.array(cf); n = len(cf)
    return [dict(etiket='FM', olcu=b, hedef='A_k', kohort=n, katsayi=cf[:, i].mean(),
                 katsayi_t=cf[:, i].mean() / (cf[:, i].std(ddof=1) / np.sqrt(n))) for i, b in enumerate(B)]

res = [ic_ozet(tam, x) for x in ['D_SATIS', 'D_BRUT', 'D_FAAL', 'D_VOK', 'S_KAR']]
res += fm(tam)
res += [ic_ozet(tam, x, etiket='bilesen_tek') for x in B]
res.append(ic_ozet(tam, 'D_MARJ', etiket='rapor_marj'))
res += [ic_ozet(tam, 'S_KUR_A', y=b, etiket='rapor_kur_satiri') for b in B]
res += [ic_ozet(tam[tam.likit], x, etiket='rapor_likit') for x in ['D_SATIS', 'D_BRUT', 'D_FAAL', 'S_KAR']]
oz = pd.DataFrame(res)

ib = oz[(oz.etiket == 'ANA') & (oz.olcu == 'D_BRUT')].iloc[0]
ifa = oz[(oz.etiket == 'ANA') & (oz.olcu == 'D_FAAL')].iloc[0]
if ib.IC_ort >= 0.15 and ib.IC_t >= 3: karar = '1: hedef brüt kâr (hacim + fiyat makası)'
elif ifa.IC_ort >= 0.15 and ifa.IC_t >= 3: karar = '2: hedef faaliyet kârı (giderler de gerekir)'
else: karar = '3: tepki faaliyet altı kalemlerden'
d.to_csv(f'{OUT}/kalem_olaylar.csv', index=False); oz.to_csv(f'{OUT}/kalem_ozet.csv', index=False)
pd.set_option('display.width', 220)
print(f'olay (tam) {len(tam)}; kohort {tam.kohort.nunique()}; şirket {tam.symbol.nunique()}')
print(oz.round(4).to_string())
print('KARAR:', karar)
