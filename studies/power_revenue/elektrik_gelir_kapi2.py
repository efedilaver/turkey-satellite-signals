#!/usr/bin/env python3
"""T-E1 Kapı 2 + Kapı 1 sağlamlık raporu."""
import os, numpy as np, pandas as pd
R = os.path.join(os.environ.get('RESEARCH_DIR', '../Research'), 'data')
ANA = ['AYDEM', 'ENTRA', 'ENDAE', 'MOGAN']
d = pd.read_csv('cikti/elektrik_gelir_kapi1.csv'); a = d[d.sirket.isin(ANA)]
x = a[~((a.sirket == 'AYDEM') & a.donem.str.startswith('2022'))]
print(f'Sağlamlık (rapor): AYDEM 2022 hariç ana grup r = {x.d_tahmin.corr(x.d_rapor):+.3f} (n={len(x)}); '
      f'Spearman (tümü) = {a.d_tahmin.rank().corr(a.d_rapor.rank()):+.3f}')
q = pd.read_csv('cikti/elektrik_gelir_tahmini_ceyrek.csv'); q['ceyrek'] = pd.PeriodIndex(q.ceyrek, freq='Q')
rd = pd.read_csv(f'{R}/report_dates.csv', parse_dates=['publish_date']).dropna(subset=['year', 'period'])
rd['ceyrek'] = [pd.Period(f'{int(y)}Q{int(p)}', 'Q') for y, p in zip(rd.year, rd.period)]
rd = rd.sort_values('publish_date').drop_duplicates(['stock_code', 'ceyrek'])
xu = pd.read_csv('cikti/hisse_gunluk.csv', parse_dates=['tarih']).query("sembol=='XU100'").set_index('tarih').kapanis
olay = []
for s in ANA:
    qs = q[q.grup == s].set_index('ceyrek').gelir
    g4 = np.log(qs / qs.shift(4).reindex(qs.index).values) if False else None
    yoy = pd.Series({c: np.log(qs[c] / qs[c - 4]) for c in qs.index if (c - 4) in qs.index and qs[c - 4] > 0 and qs[c] > 0})
    sur = (yoy - yoy.shift(1)).dropna()
    px = pd.read_parquet(f'{R}/market/prices/{s}.parquet')[['date', 'close']].set_index('date').close
    px = pd.concat([px, xu], axis=1, keys=['h', 'x']).dropna()
    for _, e in rd[rd.stock_code == s].iterrows():
        if e.ceyrek not in sur.index: continue
        gun = e.publish_date.normalize()
        once, sonra = px[px.index < gun].tail(1), px[px.index > gun].head(2)
        if once.empty or len(sonra) < 2: continue
        fg = np.log(sonra.h.iloc[-1] / once.h.iloc[0]) - np.log(sonra.x.iloc[-1] / once.x.iloc[0])
        olay.append(dict(hisse=s, ceyrek=str(e.ceyrek), yayin=e.publish_date, surpriz=sur[e.ceyrek], fazla_getiri=fg))
o = pd.DataFrame(olay); o.to_csv('cikti/elektrik_gelir_kapi2.csv', index=False)
print(o.groupby('hisse').size().to_dict(), 'toplam', len(o))
r = o.surpriz.rank().corr(o.fazla_getiri.rank())
print(f'KAPI 2: havuz Spearman = {r:+.3f} (eşik +0,25)  ->', 'GEÇTİ' if r >= 0.25 else 'KALDI')
print(o.groupby('hisse').apply(lambda z: z.surpriz.rank().corr(z.fazla_getiri.rank())).round(2).to_dict())
print(o.round(3).to_string(index=False))
