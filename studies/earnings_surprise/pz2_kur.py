#!/usr/bin/env python3
"""T-P2 — Kâr sürprizinin kur kaynaklı kısmı (kayıt: ARASTIRMA_PLANI.md, 2026-10-23 14:05).
Önce pz_testi.py çalışmış olmalı (cikti/pz/olaylar.csv).
Kullanım: python studies/earnings_surprise/pz2_kur.py  -> cikti/pz/{kur_olaylar,kur_ozet}.csv
"""
import os, numpy as np, pandas as pd

RS = os.path.join(os.environ.get('RESEARCH_DIR', '../Research'), 'data')
U = '.'
OUT = f'{U}/cikti/pz'
MIN_KOHORT = 30

ev = pd.read_csv(f'{OUT}/olaylar.csv', parse_dates=['yayin', 'ref', 'gun1'])
ev = ev[ev.ana].copy()

rd = pd.read_csv(f'{RS}/report_dates.csv').dropna(subset=['year', 'period'])
rd['year'] = rd.year.astype(int); rd['period'] = rd.period.astype(int)
rd['ts'] = pd.to_datetime(rd.publish_date)
rd = rd.sort_values('ts').drop_duplicates(['stock_code', 'year', 'period']).set_index(['stock_code', 'year', 'period']).ts

mk = pd.read_csv(f'{U}/cikti/faktor/gunluk_makro.csv', parse_dates=['date']).dropna(subset=['dd_deger']).sort_values('date')
FXD, FXV = mk.date.values, mk.dd_deger.values

def ceyrek_sonu(y, q):
    return pd.Timestamp(year=y, month=3 * q, day=1) + pd.offsets.MonthEnd(0)

def onceki(y, q, k):
    i = y * 4 + (q - 1) - k
    return i // 4, i % 4 + 1

def fx_at(t):
    i = np.searchsorted(FXD, np.datetime64(t), side='right') - 1
    return FXV[i] if i >= 0 else np.nan

def poz_seri(f, kod):
    if kod not in f.index: return {}
    r = f.loc[kod]; out = {}
    for c in r.index:
        if '/' in str(c) and pd.notna(r[c]):
            y, m = str(c).split('/'); out[(int(y), int(m) // 3)] = float(r[c])
    return out

def nfx_t0(s, poz, y, q):
    """t0 = çeyrek sonu (y,q); yayın tarihi <= t0 olan en son rapordaki pozisyon."""
    t0 = ceyrek_sonu(y, q)
    for k in range(1, 5):
        pp = onceki(y, q, k)
        ts = rd.get((s, pp[0], pp[1]))
        if ts is None or pd.isna(ts): return np.nan     # yayın tarihi bilinmiyor -> dışarı
        if ts <= t0:
            return poz.get(pp, np.nan)
    return np.nan

def kur_kazanc(s, poz, y, q):
    n = nfx_t0(s, poz, y, q)
    p1 = onceki(y, q, 1)
    d = fx_at(ceyrek_sonu(y, q)) / fx_at(ceyrek_sonu(*p1)) - 1
    return n * d, n, d

rows = []
for s, g in ev.groupby('symbol'):
    f = pd.read_parquet(f'{RS}/financials/{s}.parquet').drop_duplicates('itemCode').set_index('itemCode')
    pozA, pozB = poz_seri(f, '4BEA'), poz_seri(f, '4BEB')
    p = pd.read_parquet(f'{RS}/market/prices/{s}.parquet', columns=['date', 'close', 'end_deger', 'pd']).dropna(subset=['close'])
    p = p[p.close > 0].sort_values('date').reset_index(drop=True)
    D = p.date.values; C = np.log(p.close.values); I = np.log(p.end_deger.values)
    for _, r in g.iterrows():
        y, q = int(r.yil), int(r.ceyrek)
        qi = np.searchsorted(D, np.datetime64(ceyrek_sonu(y, q)), side='right') - 1
        ri = np.searchsorted(D, np.datetime64(r.ref), side='left')
        g1 = np.searchsorted(D, np.datetime64(r.gun1), side='left')
        if qi < 0 or g1 <= qi + 1: continue
        T = (C[g1] - C[qi + 1]) - (I[g1] - I[qi + 1])
        pd0 = p.pd.iloc[qi]
        out = dict(symbol=s, kohort=r.kohort, yil=y, ceyrek=q, S_KAR=r.S_KAR, A=r.A, P=r.P, T=T, pd_t0=pd0)
        for etk, poz in [('A', pozA), ('B', pozB)]:
            k1, n1, d1 = kur_kazanc(s, poz, y, q)
            k0, _, _ = kur_kazanc(s, poz, *onceki(y, q, 4))
            out[f'S_KUR_{etk}'] = (k1 - k0) / pd0 if pd0 and pd0 > 0 else np.nan
            out[f'NFX_PD_{etk}'] = n1 / pd0 if pd0 and pd0 > 0 else np.nan
            out['d_q'] = d1
        rows.append(out)

d = pd.DataFrame(rows)
for w in ['A', 'P', 'T']:
    lo, hi = np.nanpercentile(d[w], [1, 99]); d[w + '_k'] = d[w].clip(lo, hi)

def ozet(dd, x, y, etiket, q5=True):
    ics, qs = [], []
    for k, g in dd.groupby('kohort'):
        g = g[[x, y] + ([y + '_k'] if q5 and y + '_k' in g else [])].dropna()
        if len(g) < MIN_KOHORT: continue
        ics.append(g[x].rank().corr(g[y].rank()))
        if q5 and y + '_k' in g:
            qn = pd.qcut(g[x].rank(method='first'), 5, labels=False)
            qs.append(g[y + '_k'][qn == 4].mean() - g[y + '_k'][qn == 0].mean())
    ics = np.array(ics); n = len(ics)
    if n < 3: return dict(etiket=etiket, x=x, y=y, kohort=n)
    o = dict(etiket=etiket, x=x, y=y, kohort=n, IC_ort=ics.mean(), IC_t=ics.mean() / (ics.std(ddof=1) / np.sqrt(n)),
             IC_poz_oran=(ics > 0).mean())
    if qs:
        qs = np.array(qs); o.update(Q5_Q1_ort=qs.mean(), Q5_Q1_t=qs.mean() / (qs.std(ddof=1) / np.sqrt(n)))
    return o

# artık: kohort içinde rank(S_KAR) ~ rank(S_KUR_A)
def artik(g):
    g = g.copy(); m = g[['S_KAR', 'S_KUR_A']].notna().all(axis=1)
    a = g.loc[m, 'S_KAR'].rank(); b = g.loc[m, 'S_KUR_A'].rank()
    if m.sum() > 5:
        beta = np.cov(a, b)[0, 1] / np.var(b, ddof=1)
        g.loc[m, 'S_KAR_artik'] = a - a.mean() - beta * (b - b.mean())
    return g
d['S_KAR_artik'] = np.nan
d = d.groupby('kohort', group_keys=False).apply(artik)

res = [
    ozet(d, 'S_KUR_A', 'S_KAR', 'KAPI1', q5=False),
    ozet(d, 'S_KUR_A', 'T', 'KAPI2'),
    ozet(d, 'S_KUR_A', 'A', 'rapor'),
    ozet(d, 'S_KUR_A', 'P', 'rapor'),
    ozet(d, 'S_KUR_B', 'S_KAR', 'rapor_4BEB', q5=False),
    ozet(d, 'S_KUR_B', 'T', 'rapor_4BEB'),
    ozet(d, 'NFX_PD_A', 'T', 'plasebo_maruziyet'),
    ozet(d, 'NFX_PD_A', 'S_KAR', 'plasebo_maruziyet', q5=False),
    ozet(d[d.d_q > 0.05], 'S_KUR_A', 'S_KAR', 'TL_kaybi_>5%', q5=False),
    ozet(d[d.d_q > 0.05], 'S_KUR_A', 'T', 'TL_kaybi_>5%'),
    ozet(d, 'S_KAR', 'A', 'karsilastirma_T-P1_ayni_orneklem'),
    ozet(d, 'S_KAR_artik', 'A', 'kur_disi_kalan'),
]
oz = pd.DataFrame(res)
r1, r2 = oz.iloc[0], oz.iloc[1]
oz.loc[0, 'kapi'] = 'GECTI' if (r1.IC_ort >= 0.15 and r1.IC_t >= 3) else 'KALDI'
oz.loc[1, 'kapi'] = 'GECTI' if (r2.IC_ort >= 0.05 and r2.IC_t >= 3 and r2.Q5_Q1_ort >= 0.02) else 'KALDI'
d.to_csv(f'{OUT}/kur_olaylar.csv', index=False); oz.to_csv(f'{OUT}/kur_ozet.csv', index=False)
pd.set_option('display.width', 220)
print(f'olay {len(d)}; S_KUR_A dolu {d.S_KUR_A.notna().sum()}; S_KUR_B dolu {d.S_KUR_B.notna().sum()}; '
      f'kohort {d.kohort.nunique()}; d_q>5% kohort {d[d.d_q>0.05].kohort.nunique()}')
print(oz.round(4).to_string())
