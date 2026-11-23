#!/usr/bin/env python3
"""T-G1 (kural: ARASTIRMA_PLANI.md): bahar donu -> meyvenin genel TÜFE'ye göre göreli fiyatı.
Girdi: cikti/gida/tufe_aylik.csv (EVDS TP.TUKFIY2025.*), don_era5land.json (Open-Meteo ERA5-Land,
15 Mar-10 May sum max(0,-Tmin)), yagis_era5.json (Eki-May yağış; rapor b)."""
import json, os, numpy as np, pandas as pd
G = 'cikti/gida'
t = pd.read_csv(f'{G}/tufe_aylik.csv'); t['tarih'] = pd.PeriodIndex(t.tarih, freq='M'); t = t.set_index('tarih')
don = pd.DataFrame(json.load(open(f'{G}/don_era5land.json'))); don.index = don.index.astype(int)
D = np.log1p(don.mean(axis=1)).rename('don')

def goreli(seri, y):  # Mayıs y -> Mayıs y+1, genel TÜFE'ye göre
    a, b = pd.Period(f'{y}-05', 'M'), pd.Period(f'{y+1}-05', 'M')
    if b not in t.index: return np.nan
    return np.log(t.loc[b, seri] / t.loc[a, seri]) - np.log(t.loc[b, 'genel'] / t.loc[a, 'genel'])

yil = range(2005, 2026)
R = pd.DataFrame({s: [goreli(s, y) for y in yil] for s in ['meyve', 'meyve_taze_cekirdekli', 'sebze', 'tahil']}, index=list(yil))
df = R.join(D)
def loo(x, y):
    return min(np.corrcoef(x.drop(i), y.drop(i))[0, 1] for i in x.index)
print('Don endeksi (ham, 9 nokta ort.) ve meyvenin göreli değişimi:')
print(pd.concat([don.mean(axis=1).round(1).rename('don_ham'), df[['meyve', 'meyve_taze_cekirdekli', 'sebze']].round(3)], axis=1).loc[2005:2025].to_string())
r = df.meyve.corr(df.don); m = loo(df.don, df.meyve)
print(f'\nANA TEST n={df.meyve.notna().sum()}: r = {r:+.3f} (eşik +0,45); bir-yıl-çıkar en düşük r = {m:+.3f} (eşik +0,25)')
print('KARAR:', 'GEÇTİ' if (r >= 0.45 and m >= 0.25) else 'KALDI')
print('\nRapor (c) sebze: r = %+.3f' % df.sebze.corr(df.don))
print('Rapor (ek) taze çekirdekli meyve (01163): r = %+.3f, LOO min %+.3f' % (df.meyve_taze_cekirdekli.corr(df.don), loo(df.don, df.meyve_taze_cekirdekli)))
# (a) aylık gecikme profili: don endeksi en yüksek 4 yıl vs diğerleri
gm = (np.log(t.meyve).diff() - np.log(t.genel).diff())
ust = df.don.sort_values(ascending=False).index[:4].tolist()
prof = {}
for y in yil:
    s = gm[(gm.index >= pd.Period(f'{y}-04', 'M')) & (gm.index <= pd.Period(f'{y+1}-05', 'M'))]
    if len(s) == 14: prof[y] = s.values
P = pd.DataFrame(prof, index=['Nis','May','Haz','Tem','Ağu','Eyl','Eki','Kas','Ara','Oca','Şub','Mar','Nis+1','May+1']).T
print(f'\nRapor (a) en donlu 4 yıl {ust}: aylık göreli meyve değişimi, fark (donlu − diğer), puan:')
print(((P.loc[[y for y in ust if y in P.index]].mean() - P.drop([y for y in ust if y in P.index]).mean()) * 100).round(1).to_string())
# (b) kuraklık
f = f'{G}/yagis_era5.json'
if os.path.exists(f):
    yg = pd.DataFrame({k: {int(a): b for a, b in v.items() if a != 'nulls'} for k, v in json.load(open(f)).items()})
    an = ((yg - yg.mean()) / yg.std()).mean(axis=1).rename('yagis_z')
    d2 = R[['tahil']].join(an)
    print('\nRapor (b) kuraklık: r(yağış z, tahıl göreli) = %+.3f (beklenen < 0), n=%d' % (d2.tahil.corr(d2.yagis_z), d2.dropna().shape[0]))
df.to_csv(f'{G}/t_g1_yillik.csv')
