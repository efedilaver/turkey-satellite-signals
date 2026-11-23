#!/usr/bin/env python3
"""T-N2: EPİAŞ toplam üretim (aylık yıllık %) -> SÜE yıllık, no2_nowcast.ornek_disi_test ile."""
import numpy as np, pandas as pd


def ornek_disi_test(y, x, gecikme=2, min_egitim=24):
    """no2_nowcast.ornek_disi_test'in numpy kopyası (statsmodels yok)."""
    df = pd.concat([y.rename("y"), y.shift(gecikme).rename("y_gec"), x.rename("x")], axis=1).dropna()
    satir = []
    for t in df.index:
        e = df[df.index <= t - pd.DateOffset(months=gecikme)]
        if len(e) < min_egitim: continue
        b1 = np.linalg.lstsq(np.c_[np.ones(len(e)), e.y_gec], e.y, rcond=None)[0]
        b2 = np.linalg.lstsq(np.c_[np.ones(len(e)), e.y_gec, e.x], e.y, rcond=None)[0]
        r = df.loc[t]
        satir.append(dict(ay=t, gercek=r.y, m1=b1[0] + b1[1] * r.y_gec, m2=b2[0] + b2[1] * r.y_gec + b2[2] * r.x))
    return pd.DataFrame(satir).set_index("ay")
s = pd.read_csv('sue.csv'); s.index = pd.to_datetime(s.Tarih + '-01'); y = s.yillik_degisim_takvim
e = pd.read_csv('cikti/epias_gunluk.csv', parse_dates=['tarih'])
m = e.set_index('tarih').total_gwh.resample('MS').sum()
gun = e.set_index('tarih').total_gwh.resample('MS').count()
m = m[gun >= 28]
x = (np.log(m).diff(12) * 100).rename('elektrik_yoy')
oos = ornek_disi_test(y, x, gecikme=2)
oos = oos[oos.get('degerlendir', True) == True] if 'degerlendir' in oos else oos
for ad, d in [('2023-04→2026-08', oos.loc['2023-04-01':'2026-08-01']), ('tüm dönem', oos)]:
    r1 = np.sqrt(((d.gercek - d.m1) ** 2).mean()); r2 = np.sqrt(((d.gercek - d.m2) ** 2).mean())
    print(f'{ad:16s} n={len(d):3d}  RMSE M1={r1:.2f}  M3(elektrik)={r2:.2f}  iyileşme={100*(1-r2/r1):+.1f}%  '
          f'M3 daha iyi ay %{100*((d.gercek-d.m2).abs()<(d.gercek-d.m1).abs()).mean():.0f}')
print('eşzamanlı korelasyon r(elektrik_yoy, SÜE_yoy) =', round(pd.concat([x, y], axis=1).dropna().corr().iloc[0, 1], 2))
