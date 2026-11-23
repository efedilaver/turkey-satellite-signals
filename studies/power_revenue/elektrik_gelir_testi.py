#!/usr/bin/env python3
"""T-E1 (kural: ARASTIRMA_PLANI.md): EPİAŞ santral üretimi × PTF -> elektrik şirketlerinin raporlanan satış geliri."""
import os, numpy as np, pandas as pd
R = os.path.join(os.environ.get('RESEARCH_DIR', '../Research'), 'data')
ANA, RAPOR = ['AYDEM', 'ENTRA', 'ENDAE', 'MOGAN'], ['AKFYE', 'ZOREN', 'ODAS']
e = pd.read_csv('cikti/epias_santral_eslesme.csv')
e = e[e.grup.isin(ANA + RAPOR)]
g = pd.read_csv('cikti/epias_santral_saatlik.csv', usecols=['powerPlantId', 'date', 'total'])
g = g[g.powerPlantId.isin(e.powerPlantId)]
g['saat'] = pd.to_datetime(g.date.str[:19])
p = pd.read_csv('cikti/epias_ptf_saatlik.csv', usecols=['date', 'price']); p['saat'] = pd.to_datetime(p.date.str[:19])
g = g.merge(p[['saat', 'price']], on='saat', how='left').merge(e[['powerPlantId', 'grup']], on='powerPlantId')
g['gelir'] = g.total * g.price
g['ceyrek'] = g.saat.dt.to_period('Q')
q = g.groupby(['grup', 'ceyrek']).agg(uretim=('total', 'sum'), gelir=('gelir', 'sum'), saat_n=('saat', 'nunique'),
                                       santral_n=('powerPlantId', 'nunique')).reset_index()
q.to_csv('cikti/elektrik_gelir_tahmini_ceyrek.csv', index=False)
rows = []
for s in ANA + RAPOR:
    f = pd.read_parquet(f'{R}/financials/{s}.parquet').set_index('itemCode')
    cols = [c for c in f.columns if '/' in str(c)]
    sal = pd.to_numeric(f.loc['3C', cols], errors='coerce').dropna()
    qs = q[q.grup == s].set_index('ceyrek')
    for c, v in sal.items():
        y, m = map(int, c.split('/')); k = m // 3
        if k == 4 and y >= 2022: continue
        onceki = f'{y-1}/{m}'
        if onceki not in sal.index or sal[onceki] <= 0 or v <= 0: continue
        pq = [pd.Period(f'{y}Q{i}', 'Q') for i in range(1, k + 1)]; pq0 = [x - 4 for x in pq]
        if not all(x in qs.index for x in pq + pq0): continue
        rows.append(dict(sirket=s, donem=c, d_rapor=np.log(v / sal[onceki]),
                         d_tahmin=np.log(qs.loc[pq, 'gelir'].sum() / qs.loc[pq0, 'gelir'].sum()),
                         d_uretim=np.log(qs.loc[pq, 'uretim'].sum() / qs.loc[pq0, 'uretim'].sum())))
d = pd.DataFrame(rows); d.to_csv('cikti/elektrik_gelir_kapi1.csv', index=False)
a = d[d.sirket.isin(ANA)]
r = a.d_tahmin.corr(a.d_rapor)
per = d.groupby('sirket').apply(lambda x: pd.Series({'n': len(x), 'r_gelir': x.d_tahmin.corr(x.d_rapor), 'r_uretim': x.d_uretim.corr(x.d_rapor)}))
print(per.round(2).to_string())
pos = (per.loc[[s for s in ANA if s in per.index], 'r_gelir'] > 0).sum()
print(f'\nKAPI 1: ana grup havuz r = {r:+.3f} (n={len(a)}, eşik +0,60); r>0 olan şirket {pos}/4 (eşik 3)')
print('Rapor: yalnız üretim, ana grup havuz r = %+.3f' % a.d_uretim.corr(a.d_rapor))
print('KAPI 1:', 'GEÇTİ' if (r >= 0.60 and pos >= 3) else 'KALDI')
print(d[d.sirket.isin(ANA)].round(2).to_string(index=False))
