#!/usr/bin/env python3
"""T-G2 (kural: ARASTIRMA_PLANI.md): bahar donu endeksi -> yıllık meyve üretimi anomalisi.
Üretim: TÜİK veri portalı, Taş/Yumuşak çekirdekli meyveler tabloları (1988-2025) -> cikti/gida/tuik_meyve_uretim.csv"""
import json, numpy as np, pandas as pd
G='cikti/gida'
u=pd.read_csv(f'{G}/tuik_meyve_uretim.csv').set_index('yil')
don=pd.DataFrame(json.load(open(f'{G}/don_era5land.json'))); don.index=don.index.astype(int)
D=np.log1p(don.mean(axis=1)).rename('don'); Dmal=np.log1p(don.Malatya).rename('don_malatya')
L=np.log(u[['kayisi','elma','kiraz']])
A=(L-L.shift(1).rolling(3).mean()).loc[2004:2025]
A['ort']=A[['kayisi','elma','kiraz']].mean(axis=1)
df=A.join(D).join(Dmal)
def loo_max(x,y): return max(np.corrcoef(x.drop(i),y.drop(i))[0,1] for i in x.index)
print(pd.concat([don.mean(axis=1).round(1).rename('don_ham'),A.round(2)],axis=1).loc[2004:2025].to_string())
r=df.ort.corr(df.don); m=loo_max(df.don,df.ort)
print(f'\nANA TEST n={len(df)}: r = {r:+.3f} (eşik ≤ −0,45); bir-yıl-çıkar en yüksek r = {m:+.3f} (eşik ≤ −0,25)')
print('KARAR:','GEÇTİ' if (r<=-0.45 and m<=-0.25) else 'KALDI')
for c in ['kayisi','elma','kiraz']: print(f'Rapor {c}: r = {df[c].corr(df.don):+.3f}')
print(f'Rapor kayısı ~ yalnız Malatya: r = {df.kayisi.corr(df.don_malatya):+.3f}')
df.to_csv(f'{G}/t_g2_yillik.csv')
