#!/usr/bin/env python3
"""T-P5 — Şirkete özgü ihracat verisi (GTİP/HS6) satış sürprizini ve bilanço günü tepkisini öngörüyor mu?
(kayıt: ARASTIRMA_PLANI.md, 2026-10-23 15:05). Önce pz_testi.py ve pz3_kalem.py çalışmış olmalı.
Veri: cikti/pz/comtrade_aylik.csv (UN Comtrade, Türkiye ihracatı, aylık HS6; ay,kod,deger_usd,kg)
Kullanım: python studies/earnings_surprise/pz5_gtip.py -> cikti/pz/gtip_olaylar.csv, gtip_ozet.csv
"""
import os, numpy as np, pandas as pd

U = '.'; OUT = f'{U}/cikti/pz'
KOD = {'KORDS': ['590210', '590220'], 'SASA': ['550320', '550120'],
       'PETKM': ['390110', '390120', '390410'], 'TTRAK': ['870191', '870192', '870193', '870194', '870195']}

ct = pd.read_csv(f'{OUT}/comtrade_aylik.csv', dtype={'kod': str, 'ay': str})
mk = pd.read_csv(f'{U}/cikti/faktor/gunluk_makro.csv', parse_dates=['date']).dropna(subset=['dd_deger'])
fx = mk.groupby(mk.date.dt.strftime('%Y%m')).dd_deger.mean()
ev = pd.read_csv(f'{OUT}/olaylar.csv', parse_dates=['ref'])
ev = ev[ev.ana & ev.symbol.isin(KOD)].copy()
kal = pd.read_csv(f'{OUT}/kalem_olaylar.csv')[['symbol', 'kohort', 'D_MARJ']]
ev = ev.merge(kal, on=['symbol', 'kohort'], how='left')

def ay_ekle(a, k):
    y, m = int(a[:4]), int(a[4:]); i = y * 12 + m - 1 + k
    return f'{i // 12}{i % 12 + 1:02d}'
def bilinir(a, ref):  # ay a, (a+1) ayının son gününden sonra bilinir
    son = pd.Timestamp(year=int(ay_ekle(a, 1)[:4]), month=int(ay_ekle(a, 1)[4:]), day=1) + pd.offsets.MonthEnd(0)
    return son < ref

rows = []
for s, kods in KOD.items():
    c = ct[ct.kod.isin(kods)].groupby('ay')[['deger_usd', 'kg']].sum()
    X = (c.deger_usd * fx.reindex(c.index)).to_dict(); USD = c.deger_usd.to_dict(); KG = c.kg.to_dict()
    def g(aylar, src):
        a0 = [ay_ekle(a, -12) for a in aylar]
        if any(a not in src or a2 not in src for a, a2 in zip(aylar, a0)): return np.nan
        num, den = sum(src[a] for a in aylar), sum(src[a] for a in a0)
        return np.log(num / den) if num > 0 and den > 0 else np.nan
    for _, r in ev[ev.symbol == s].iterrows():
        y, q = int(r.yil), int(r.ceyrek)
        aylar = [f'{y}{3 * (q - 1) + k:02d}' for k in (1, 2, 3)]
        bil = [a for a in aylar if bilinir(a, r.ref)]
        ony = [ay_ekle(a, -3) for a in aylar]
        gq = g(bil, X) if len(bil) >= 2 else np.nan
        gp = g(ony, X) if all(bilinir(a, r.ref) for a in ony) else np.nan
        uv = lambda al: (sum(USD[a] for a in al) / sum(KG[a] for a in al)) if all(a in USD and KG.get(a, 0) > 0 for a in al) else np.nan
        uv_q = uv(bil) if len(bil) >= 2 else np.nan; uv_4 = uv([ay_ekle(a, -12) for a in bil]) if len(bil) >= 2 else np.nan
        rows.append(dict(symbol=s, kohort=r.kohort, ref=r.ref, bilinen_ay=len(bil), P_SATIS=gq - gp,
                         UV_D4=np.log(uv_q / uv_4) if uv_q > 0 and uv_4 > 0 else np.nan,
                         S_SATIS=r.S_SATIS, S_KAR=r.S_KAR, D_MARJ=r.D_MARJ, A=r.A))
d = pd.DataFrame(rows)

def kor(dd, x, yv, yontem):
    g = dd[[x, yv]].dropna()
    return (g[x].corr(g[yv], method=yontem), len(g)) if len(g) > 3 else (np.nan, len(g))
res = []
for x, yv, yon, et in [('P_SATIS', 'S_SATIS', 'pearson', 'KAPI1'), ('P_SATIS', 'A', 'spearman', 'KAPI2'),
                       ('P_SATIS', 'S_KAR', 'spearman', 'rapor'), ('P_SATIS', 'D_MARJ', 'spearman', 'rapor'),
                       ('UV_D4', 'D_MARJ', 'spearman', 'rapor'), ('UV_D4', 'A', 'spearman', 'rapor')]:
    r0, n0 = kor(d, x, yv, yon); o = dict(etiket=et, x=x, y=yv, yontem=yon, havuz_r=r0, n=n0)
    for s in KOD:
        rs, ns = kor(d[d.symbol == s], x, yv, yon); o[f'{s}_r'] = rs; o[f'{s}_n'] = ns
    o['pozitif_sirket'] = sum((o[f'{s}_r'] > 0) for s in KOD); res.append(o)
oz = pd.DataFrame(res)
oz.loc[0, 'kapi'] = 'GECTI' if oz.loc[0, 'havuz_r'] >= 0.30 and oz.loc[0, 'pozitif_sirket'] >= 3 else 'KALDI'
oz.loc[1, 'kapi'] = 'GECTI' if oz.loc[1, 'havuz_r'] >= 0.20 and oz.loc[1, 'pozitif_sirket'] >= 3 else 'KALDI'
d.to_csv(f'{OUT}/gtip_olaylar.csv', index=False); oz.to_csv(f'{OUT}/gtip_ozet.csv', index=False)
pd.set_option('display.width', 250)
print(f'olay {len(d)}; P_SATIS dolu {d.P_SATIS.notna().sum()}; bilinen ay dağılımı {d.bilinen_ay.value_counts().to_dict()}')
print(oz.round(3).to_string())
