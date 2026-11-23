#!/usr/bin/env python3
"""T-C2 analizi (kural: ARASTIRMA_PLANI.md). Girdi: cikti/celik_landsat_sahne.csv (celik_landsat.py)."""
import os, numpy as np, pandas as pd
K = os.environ.get('RESEARCH_DIR', '../Research')
s = pd.read_csv('cikti/celik_landsat_sahne.csv', parse_dates=['tarih'])
s['tam_acik_n'] = s.groupby('tesis').tesis_acik_n.transform('max')  # düzeltme: sabit-görüntü paydası kenar piksellerini fazla sayıyordu
s = s[(s.tesis_acik_n / s.tam_acik_n >= 0.9) & (s.halka_n >= 50)].dropna(subset=['tesis_p90', 'halka_med'])
s['dT'] = s.tesis_p90 - s.halka_med
s = s.groupby(['tesis', 'tarih'], as_index=False).dT.mean()  # komşu karelerdeki aynı geçiş tek sayılır
s['ceyrek'] = s.tarih.dt.to_period('Q')
print('Geçerli sahne:', s.groupby('tesis').size().to_dict())
print('Ortalama ΔT (K):', s.groupby('tesis').dT.mean().round(2).to_dict())
q = s.groupby(['tesis', 'ceyrek']).agg(dT=('dT', 'mean'), n=('dT', 'size')).reset_index()
q = q[q.n >= 2]
q['onceki'] = q.ceyrek - 4
q = q.merge(q[['tesis', 'ceyrek', 'dT']].rename(columns={'ceyrek': 'onceki', 'dT': 'dT_gy'}), on=['tesis', 'onceki'], how='left')
q['surpriz'] = q.dT - q.dT_gy

# ---- Kapı 1: ölçüm ~ üretim
u = pd.read_csv('data/reference/celik_uretim.csv')
u = u[u.donem.str.contains('Q') & (u.tur == 'sivi_celik')].copy()
u['ceyrek'] = pd.PeriodIndex(u.donem, freq='Q')
es = {'Isdemir': 'Isdemir_Payas', 'Erdemir_Eregli_tesisi_TURETILMIS': 'Erdemir_Eregli', 'Kardemir': 'Kardemir_Karabuk'}
u = u[u.sirket.isin(es)].assign(tesis=lambda d: d.sirket.map(es))
u = u.groupby(['tesis', 'ceyrek']).uretim_ton.first().reset_index()
u['onceki'] = u.ceyrek - 4
u = u.merge(u[['tesis', 'ceyrek', 'uretim_ton']].rename(columns={'ceyrek': 'onceki', 'uretim_ton': 'u_gy'}), on=['tesis', 'onceki'], how='left')
u['du'] = np.log(u.uretim_ton / u.u_gy)
k1 = q.merge(u[['tesis', 'ceyrek', 'du']], on=['tesis', 'ceyrek']).dropna(subset=['surpriz', 'du'])
k1a = k1[k1.tesis.isin(['Isdemir_Payas', 'Erdemir_Eregli'])]
r1 = k1a.surpriz.corr(k1a.du)
print(f'\nKAPI 1: r(ΔT yıllık değişim, üretim yıllık log değişim), İsdemir+Ereğli n={len(k1a)}: {r1:+.3f} (eşik +0,40)')
for t, d in k1.groupby('tesis'): print(f'  {t}: n={len(d)} r={d.surpriz.corr(d.du):+.3f}')
dep = s[(s.tesis == 'Isdemir_Payas') & (s.tarih >= '2023-02-07') & (s.tarih <= '2023-04-23')]
diger = s[(s.tesis == 'Isdemir_Payas') & ~s.index.isin(dep.index)]
dk = (len(dep) > 0) and (dep.dT.median() < diger.dT.quantile(0.10))
print(f'  Deprem kontrolü: duruş sahnesi n={len(dep)}, medyan ΔT={dep.dT.median():.2f} K; diğerlerinin 10. yüzdeliği={diger.dT.quantile(0.10):.2f} K -> {"GEÇTİ" if dk else "KALDI"}')
kapi1 = (r1 >= 0.40) and dk
print('KAPI 1:', 'GEÇTİ' if kapi1 else 'KALDI')

# ---- Kapı 2: bilanço günü tepkisi
rd = pd.read_csv(f'{K}/data/report_dates.csv', parse_dates=['publish_date']).dropna(subset=['year', 'period'])
rd['ceyrek'] = [pd.Period(f'{int(y)}Q{int(p)}', 'Q') for y, p in zip(rd.year, rd.period)]
rd = rd.sort_values('publish_date').drop_duplicates(['stock_code', 'ceyrek'])
h = pd.read_csv('cikti/hisse_gunluk.csv', parse_dates=['tarih']).pivot(index='tarih', columns='sembol', values='kapanis')
isd = pd.read_parquet(f'{K}/data/market/prices/ISDMR.parquet')[['date', 'close']].set_index('date').close.rename('ISDMR')
h = h.join(isd, how='left')
eslesme = {'IZMDC': ('IZMDC', ['IZMDC_Aliaga']), 'ISDMR': ('ISDMR', ['Isdemir_Payas']),
           'EREGL': ('EREGL', ['Isdemir_Payas', 'Erdemir_Eregli']), 'KRDMD': ('KRDMA', ['Kardemir_Karabuk'])}
olay = []
for hisse, (kod, tesisler) in eslesme.items():
    sig = q[q.tesis.isin(tesisler)].groupby('ceyrek').surpriz.mean()
    for _, e in rd[rd.stock_code == kod].iterrows():
        if e.ceyrek not in sig.index or pd.isna(sig[e.ceyrek]) or hisse not in h: continue
        px = h[[hisse, 'XU100']].dropna()
        once = px[px.index < e.publish_date.normalize()].tail(1)
        sonra = px[px.index > e.publish_date.normalize()].head(2).tail(1)
        if once.empty or len(px[px.index > e.publish_date.normalize()].head(2)) < 2: continue
        fg = np.log(sonra[hisse].iloc[0] / once[hisse].iloc[0]) - np.log(sonra.XU100.iloc[0] / once.XU100.iloc[0])
        olay.append(dict(hisse=hisse, ceyrek=str(e.ceyrek), surpriz=sig[e.ceyrek], fazla_getiri=fg))
o = pd.DataFrame(olay)
if o.empty:
    print('Olay yok'); raise SystemExit
r2 = o.surpriz.rank().corr(o.fazla_getiri.rank())
isaret = o.groupby('hisse').apply(lambda d: d.surpriz.rank().corr(d.fazla_getiri.rank()))
print(f'\nKAPI 2: havuz Spearman n={len(o)}: {r2:+.3f} (eşik +0,25); hisse bazında:', isaret.round(3).to_dict(), o.groupby('hisse').size().to_dict())
k2 = (r2 >= 0.25) and ((isaret > 0).sum() >= 3)
print('KAPI 2:', ('GEÇTİ' if k2 else 'KALDI') + ('' if kapi1 else ' (Kapı 1 kaldığı için yalnız rapor)'))
o.to_csv('cikti/celik_landsat_olaylar.csv', index=False); q.to_csv('cikti/celik_landsat_ceyrek.csv', index=False)
