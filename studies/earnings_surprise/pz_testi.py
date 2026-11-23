#!/usr/bin/env python3
"""T-P1 — Mükemmel bilgi kapısı: çeyrek sonucunu önceden bilmek bilanço günü getirisi sağlar mı?
Kayıt: ARASTIRMA_PLANI.md, 2026-10-23 13:45. Tanımlar oradakiyle birebir aynıdır.
Kullanım:  python studies/earnings_surprise/pz_testi.py      -> cikti/pz/{olaylar,kohort,ozet}.csv
"""
import os, glob, json, numpy as np, pandas as pd

RS = os.path.join(os.environ.get('RESEARCH_DIR', '../Research'), 'data')
OUT = 'cikti/pz'; os.makedirs(OUT, exist_ok=True)
ANA = [(y, q) for y in range(2016, 2023) for q in range(1, 5)
       if (y, q) >= (2016, 2) and (y, q) <= (2022, 3)]
RAPOR_2023 = [(2023, 1), (2023, 2), (2023, 3)]
KESIM = pd.Timedelta(hours=18, minutes=10)
MIN_KOHORT = 30

# ---------------- evren ----------------
ps = {os.path.basename(x)[:-8] for x in glob.glob(f'{RS}/market/prices/*.parquet')}
fs = {os.path.basename(x)[:-8] for x in glob.glob(f'{RS}/financials/*.parquet')}
sek = pd.read_csv(f'{RS}/sector_mapping_raw.csv').drop_duplicates('ticker').set_index('ticker').sector
evren, dislanan = [], {}
for s in sorted(ps & fs):
    try:
        prof = json.load(open(f'{RS}/financials/{s}.json')).get('isyatirim_profile')
    except Exception:
        prof = None
    if prof == 'bank':
        dislanan[s] = 'banka'; continue
    if str(sek.get(s, '')).strip().upper().startswith('MALİ KURULUŞLAR'):
        dislanan[s] = 'mali'; continue
    evren.append(s)
print(f'evren {len(evren)}; dışlanan {len(dislanan)} (banka {sum(v=="banka" for v in dislanan.values())}, '
      f'mali {sum(v=="mali" for v in dislanan.values())})')

# ---------------- yayın tarihleri ----------------
rd = pd.read_csv(f'{RS}/report_dates.csv')
rd = rd.dropna(subset=['year', 'period'])
rd['year'] = rd.year.astype(int); rd['period'] = rd.period.astype(int)
rd['ts'] = pd.to_datetime(rd.publish_date)
rd = rd.sort_values('ts').drop_duplicates(['stock_code', 'year', 'period'], keep='first')
rd = rd.set_index(['stock_code', 'year', 'period']).ts

# ---------------- yardımcılar ----------------
def tek_ceyrek(f, kod):
    if kod not in f.index: return {}
    r = f.loc[kod]
    if isinstance(r, pd.DataFrame): r = r.iloc[0]
    ytd = {}
    for c in r.index:
        if '/' in str(c):
            y, m = str(c).split('/')
            v = r[c]
            if pd.notna(v): ytd[(int(y), int(m) // 3)] = float(v)
    out = {}
    for (y, q), v in ytd.items():
        if q == 1: out[(y, 1)] = v
        elif (y, q - 1) in ytd: out[(y, q)] = v - ytd[(y, q - 1)]
    return out

def onceki(y, q, k):
    i = y * 4 + (q - 1) - k
    return i // 4, i % 4 + 1

def ceyrek_sonu(y, q):
    return pd.Timestamp(year=y, month=3 * q, day=1) + pd.offsets.MonthEnd(0)

# ---------------- olaylar ----------------
satirlar = []
for s in evren:
    f = pd.read_parquet(f'{RS}/financials/{s}.parquet').set_index('itemCode')
    sat = tek_ceyrek(f, '3C')
    nk = tek_ceyrek(f, '3Z')
    nk3l = tek_ceyrek(f, '3L')
    for k, v in nk3l.items(): nk.setdefault(k, v)
    p = pd.read_parquet(f'{RS}/market/prices/{s}.parquet',
                        columns=['date', 'close', 'end_deger', 'pd', 'volume']).dropna(subset=['close'])
    p = p[p.close > 0].sort_values('date').reset_index(drop=True)
    if len(p) < 100: continue
    D = p.date.values; C = np.log(p.close.values); I = np.log(p.end_deger.values)
    for (y, q) in ANA + RAPOR_2023:
        ts = rd.get((s, y, q))
        if ts is None or pd.isna(ts): continue
        gun = ts.normalize()
        if ts - gun < KESIM:
            ri = np.searchsorted(D, np.datetime64(gun), side='left') - 1    # son işlem günü < yayın günü
        else:
            ri = np.searchsorted(D, np.datetime64(gun), side='right') - 1   # son işlem günü <= yayın günü
        if ri < 0 or ri + 2 >= len(D): continue
        ar = lambda a, b: (C[b] - C[a]) - (I[b] - I[a])
        A = ar(ri, ri + 2)
        B = ar(ri + 2, ri + 62) if ri + 62 < len(D) else np.nan
        qi = np.searchsorted(D, np.datetime64(ceyrek_sonu(y, q)), side='right') - 1
        P = ar(qi, ri) if 0 <= qi < ri else np.nan
        pdref = p.pd.iloc[ri]
        hacim = np.nanmedian(p.volume.values[max(0, ri - 59): ri + 1])
        # sürprizler
        q1, q4, q5 = onceki(y, q, 1), onceki(y, q, 4), onceki(y, q, 5)
        S_SAT = np.nan
        vals = [sat.get(k) for k in [(y, q), q4, q1, q5]]
        if all(v is not None and v > 0 for v in vals):
            S_SAT = np.log(vals[0] / vals[1]) - np.log(vals[2] / vals[3])
        S_KAR = np.nan
        if (y, q) in nk and q4 in nk and pd.notna(pdref) and pdref > 0:
            S_KAR = (nk[(y, q)] - nk[q4]) / pdref
        satirlar.append(dict(symbol=s, yil=y, ceyrek=q, yayin=ts, ref=pd.Timestamp(D[ri]),
                             gun1=pd.Timestamp(D[ri + 2]), bosluk_gun=(D[ri + 2] - D[ri]) / np.timedelta64(1, 'D'),
                             S_SATIS=S_SAT, S_KAR=S_KAR, A=A, B=B, P=P, hacim=hacim,
                             gecikme_gun=(gun - ceyrek_sonu(y, q)).days))

ev = pd.DataFrame(satirlar)
ev['kohort'] = ev.yil.astype(str) + 'Q' + ev.ceyrek.astype(str)
ev['ana'] = [(y, q) in ANA for y, q in zip(ev.yil, ev.ceyrek)]
ev.to_csv(f'{OUT}/olaylar.csv', index=False)

# ---------------- istatistik ----------------
def kirp(x):
    lo, hi = np.nanpercentile(x, [1, 99]); return x.clip(lo, hi)

for w in ['A', 'B', 'P']:
    ev[w + '_k'] = np.nan
    m = ev.ana
    ev.loc[m, w + '_k'] = kirp(ev.loc[m, w])
    m2 = ~ev.ana
    if ev.loc[m2, w].notna().sum() > 10: ev.loc[m2, w + '_k'] = kirp(ev.loc[m2, w])

def kohort_tablo(d, sur, w):
    rows = []
    for k, g in d.groupby('kohort'):
        g = g[[sur, w, w + '_k']].dropna()
        if len(g) < MIN_KOHORT: continue
        ic = g[sur].rank().corr(g[w].rank())
        qn = pd.qcut(g[sur].rank(method='first'), 5, labels=False)
        q5q1 = g[w + '_k'][qn == 4].mean() - g[w + '_k'][qn == 0].mean()
        rows.append(dict(kohort=k, n=len(g), IC=ic, Q5_Q1=q5q1))
    return pd.DataFrame(rows)

def ozet(d, sur, w, etiket):
    t = kohort_tablo(d, sur, w)
    if len(t) < 3:
        return dict(etiket=etiket, olcu=sur, pencere=w, kohort=len(t))
    n = len(t)
    return dict(etiket=etiket, olcu=sur, pencere=w, kohort=n, olay=int(t.n.sum()),
                IC_ort=t.IC.mean(), IC_t=t.IC.mean() / (t.IC.std(ddof=1) / np.sqrt(n)),
                IC_poz_oran=(t.IC > 0).mean(), Q5_Q1_ort=t.Q5_Q1.mean(),
                Q5_Q1_t=t.Q5_Q1.mean() / (t.Q5_Q1.std(ddof=1) / np.sqrt(n)))

ana = ev[ev.ana].copy()
ana['likit'] = ana.groupby('kohort').hacim.transform(lambda x: x >= x.median())
alt1 = ana[ana.yil <= 2019]; alt2 = ana[ana.yil >= 2020]
res, kohortlar = [], []
for sur in ['S_SATIS', 'S_KAR']:
    for w in ['A', 'B', 'P']:
        res.append(ozet(ana, sur, w, 'ANA'))
        kt = kohort_tablo(ana, sur, w); kt['olcu'] = sur; kt['pencere'] = w; kohortlar.append(kt)
    res.append(ozet(alt1, sur, 'A', '2016Q2-2019Q4'))
    res.append(ozet(alt2, sur, 'A', '2020Q1-2022Q3'))
    res.append(ozet(ana[ana.ceyrek == 4], sur, 'A', 'yalniz_Q4'))
    res.append(ozet(ana[ana.ceyrek != 4], sur, 'A', 'Q1-Q3'))
    res.append(ozet(ana[ana.likit], sur, 'A', 'likit_ust_yari'))
    res.append(ozet(ev[~ev.ana], sur, 'A', '2023Q1-Q3_rapor'))
oz = pd.DataFrame(res)
for sur in ['S_SATIS', 'S_KAR']:
    r = oz[(oz.etiket == 'ANA') & (oz.olcu == sur) & (oz.pencere == 'A')].iloc[0]
    gec = (r.IC_ort >= 0.10) and (r.IC_t >= 3.0) and (r.Q5_Q1_ort >= 0.02)
    oz.loc[(oz.etiket == 'ANA') & (oz.olcu == sur) & (oz.pencere == 'A'), 'kapi'] = 'GECTI' if gec else 'KALDI'
oz.to_csv(f'{OUT}/ozet.csv', index=False)
pd.concat(kohortlar).to_csv(f'{OUT}/kohort.csv', index=False)

pd.set_option('display.width', 200)
print(f'olay (ana): {len(ana)}; S_SATIS dolu {ana.S_SATIS.notna().sum()}, S_KAR dolu {ana.S_KAR.notna().sum()}, '
      f'A dolu {ana.A.notna().sum()}; şirket {ana.symbol.nunique()}')
print('ref→gün1 boşluğu > 10 gün:', int((ana.bosluk_gun > 10).sum()))
print('yayın gecikmesi (gün) medyan:', ana.gecikme_gun.median())
print(oz.round(4).to_string())
