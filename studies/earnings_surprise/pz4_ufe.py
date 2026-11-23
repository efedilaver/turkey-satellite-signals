#!/usr/bin/env python3
"""T-P4 — Sektör üretici fiyatları brüt marjı ve bilanço günü tepkisini öngörüyor mu?
(kayıt: ARASTIRMA_PLANI.md, 2026-10-23 14:40). Önce pz_testi.py, pz3_kalem.py çalışmış olmalı.
Veri: cikti/pz/yiufe_nace_aylik.csv (EVDS bie_tufe1yi, 2003=100), nace_eslesme.csv
Kullanım: python studies/earnings_surprise/pz4_ufe.py -> cikti/pz/{ufe_olaylar,ufe_ozet}.csv
"""
import os, numpy as np, pandas as pd

U = '.'; RS = os.path.join(os.environ.get('RESEARCH_DIR', '../Research'), 'data')
OUT = f'{U}/cikti/pz'; MIN_KOHORT = 30
# NACE 2 hane -> EVDS Yİ-ÜFE serisi (bie_tufe1yi)
SERI = {'06': 'T6', '07': 'T9', '10': 'T16', '11': 'T26', '13': 'T30', '16': 'T41', '17': 'T44', '19': 'T49',
        '20': 'T52', '21': 'T59', '22': 'T61', '23': 'T64', '24': 'T73', '27': 'T93', '28': 'T99', '29': 'T105',
        '31': 'T112', '35': 'T119'}

u = pd.read_csv(f'{OUT}/yiufe_nace_aylik.csv')
y, m = u.tarih.str.split('-', expand=True).astype(int).T.values
u['ck'] = [f'{a}Q{(b - 1) // 3 + 1}' for a, b in zip(y, m)]
u = u.drop(columns='tarih').groupby('ck').mean()              # çeyrek ortalaması
u.columns = [c.replace('TP_TUFE1YI_', '') for c in u.columns]
L = np.log(u)
def d4(col, k):
    yy, qq = int(k[:4]), int(k[-1]); k4 = f'{yy - 1}Q{qq}'
    return L.at[k, col] - L.at[k4, col] if k in L.index and k4 in L.index else np.nan

es = pd.read_csv('studies/earnings_surprise/nace_eslesme.csv', dtype={'nace2': str})
es['nace2'] = es.nace2.str.zfill(2); es['seri'] = es.nace2.map(SERI)
kal = pd.read_csv(f'{OUT}/kalem_olaylar.csv')[['symbol', 'kohort', 'A', 'D_MARJ', 'D_BRUT', 'S_KAR']]
ev = pd.read_csv(f'{OUT}/olaylar.csv', parse_dates=['gun1'])
ev = ev[ev.ana][['symbol', 'kohort', 'yil', 'ceyrek', 'gun1']]
d = kal.merge(ev, on=['symbol', 'kohort']).merge(es[['symbol', 'nace2', 'seri']], on='symbol')
d = d[d.seri.notna()].copy()
d['UFE_S'] = [d4(s, k) for s, k in zip(d.seri, d.kohort)]
d['UFE_G'] = [d4('T1', k) for k in d.kohort]
d['R'] = d.UFE_S - d.UFE_G

# T5: çeyrek sonundan sonraki 5. işlem günü kapanışı -> gün 1 kapanışı
T5 = []
for s, g in d.groupby('symbol'):
    p = pd.read_parquet(f'{RS}/market/prices/{s}.parquet', columns=['date', 'close', 'end_deger']).dropna(subset=['close'])
    p = p[p.close > 0].sort_values('date'); D = p.date.values; C = np.log(p.close.values); I = np.log(p.end_deger.values)
    for i, r in g.iterrows():
        qe = pd.Timestamp(year=int(r.yil), month=3 * int(r.ceyrek), day=1) + pd.offsets.MonthEnd(0)
        a = np.searchsorted(D, np.datetime64(qe), side='right') + 4
        b = np.searchsorted(D, np.datetime64(r.gun1), side='left')
        T5.append((i, (C[b] - C[a]) - (I[b] - I[a]) if a < b < len(D) else np.nan))
d['T5'] = pd.Series(dict(T5))

def ic(dd, x, yv, et):
    ics = []
    for k, g in dd.groupby('kohort'):
        g = g[[x, yv]].dropna()
        if len(g) < MIN_KOHORT or g[x].nunique() < 3: continue
        ics.append(g[x].rank().corr(g[yv].rank()))
    ics = np.array(ics); n = len(ics)
    return dict(etiket=et, x=x, y=yv, kohort=n, IC_ort=ics.mean(), IC_t=ics.mean() / (ics.std(ddof=1) / np.sqrt(n)),
                IC_poz_oran=(ics > 0).mean())

res = [ic(d, 'R', 'D_MARJ', 'KAPI1'), ic(d, 'R', 'A', 'KAPI2'),
       ic(d, 'R', 'D_BRUT', 'rapor'), ic(d, 'R', 'S_KAR', 'rapor'), ic(d, 'R', 'T5', 'rapor'),
       ic(d, 'UFE_S', 'D_MARJ', 'rapor_cikti_fiyati'), ic(d, 'UFE_S', 'A', 'rapor_cikti_fiyati')]
oz = pd.DataFrame(res)
oz.loc[0, 'kapi'] = 'GECTI' if oz.loc[0, 'IC_ort'] >= 0.10 and oz.loc[0, 'IC_t'] >= 3 else 'KALDI'
oz.loc[1, 'kapi'] = 'GECTI' if oz.loc[1, 'IC_ort'] >= 0.05 and oz.loc[1, 'IC_t'] >= 3 else 'KALDI'
d.to_csv(f'{OUT}/ufe_olaylar.csv', index=False); oz.to_csv(f'{OUT}/ufe_ozet.csv', index=False)
pd.set_option('display.width', 200)
print(f'olay {len(d)}; R dolu {d.R.notna().sum()}; şirket {d.symbol.nunique()}; kohort {d.kohort.nunique()}; '
      f'ort. kohort olayı {d.groupby("kohort").size().mean():.0f}')
print(d.groupby('nace2').size().to_string())
print(oz.round(4).to_string())
