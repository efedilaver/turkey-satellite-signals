#!/usr/bin/env python3
"""Research verisinden aylık panel kurar -> cikti/faktor/panel_aylik.parquet, makro_aylik.csv, gunluk_getiri.parquet"""
import glob, os, numpy as np, pandas as pd
R = os.environ.get('RESEARCH_DIR', '../Research'); U = '.'; O = f'{U}/cikti/faktor'
cols = ['symbol','date','close','hg_kapanis','hg_hacim','pd','dd_deger','end_deger','end_endeks_kodu']
fr = []
for fp in glob.glob(f'{R}/data/market/prices/*.parquet'):
    x = pd.read_parquet(fp)
    if 'close' in x.columns and len(x): fr.append(x[[c for c in cols if c in x.columns]])
print('fiyat dosyası:', len(fr))
d = pd.concat(fr); d['date'] = pd.to_datetime(d.date); d = d.sort_values(['symbol','date'])
d['ret'] = d.groupby('symbol').close.pct_change()
# günlük makro: USD/TL ve BIST100 (tüm dosyalarda aynı olmalı -> medyan)
g = d.groupby('date')[['dd_deger','end_deger']].median()
g.to_csv(f'{O}/gunluk_makro.csv')
d[['symbol','date','ret','hg_hacim']].to_parquet(f'{O}/gunluk_getiri.parquet')
d['ay'] = d.date.dt.to_period('M')
m = d.groupby(['symbol','ay']).agg(close=('close','last'), pd=('pd','last'), hacim_tl=('hg_hacim','mean'),
      gun=('ret','count'), oyn_g=('ret','std')).reset_index()
m['ret'] = m.groupby('symbol').close.pct_change()
mk = g.copy(); mk['ay'] = mk.index.to_period('M'); mk = mk.groupby('ay').last()
mk['piyasa_ret'] = mk.end_deger.pct_change(); mk['usd_deg'] = mk.dd_deger.pct_change()
e = pd.read_csv(f'{U}/cikti/epias_gunluk.csv', parse_dates=['tarih']); e['ay'] = e.tarih.dt.to_period('M')
ea = e.groupby('ay').agg(ptf_tl=('ptf_tl','mean'), ptf_usd=('ptf_usd','mean'), hidro_pay=('hidro_barajli_pay','mean'))
mk = mk.join(ea); mk['ptf_usd_deg'] = np.log(mk.ptf_usd).diff()
mk.to_csv(f'{O}/makro_aylik.csv')
# mali: Research raw_scored (KAP yayın tarihli). TMS29 düzeltmesi: >=2022-12 Q4 satırları atılır
f = pd.read_csv(f'{R}/data/reports/factor_validation/raw_scored.csv',
    usecols=['symbol','period','publish_date','equity','net_income','gross_profit','total_assets','selected_profile','sector','sub_sector'],
    parse_dates=['period','publish_date'])
f = f[~((f.period >= '2022-12-01') & (f.period.dt.month == 12))]
f['bilgi_ay'] = (f.publish_date + pd.Timedelta(days=1)).dt.to_period('M')  # yayınlandığı ayın sonunda bilinir
f = f.sort_values(['symbol','publish_date']).drop_duplicates(['symbol','bilgi_ay'], keep='last')
m = m.sort_values(['symbol','ay'])
out = []
for s, gm in m.groupby('symbol'):
    gf = f[f.symbol == s]
    if gf.empty: out.append(gm); continue
    x = pd.merge_asof(gm.assign(t=gm.ay.dt.to_timestamp('M')), gf.assign(t=gf.bilgi_ay.dt.to_timestamp('M')).drop(columns=['symbol']),
                      on='t', direction='backward')
    x['mali_yas_ay'] = (x.t - x.period).dt.days / 30.4
    out.append(x.drop(columns=['t']))
p = pd.concat(out, ignore_index=True)
p.loc[p.mali_yas_ay > 15, ['equity','net_income','gross_profit','total_assets']] = np.nan  # bayat tablo
p = p.merge(mk[['piyasa_ret','usd_deg']], left_on='ay', right_index=True, how='left')
p['ay'] = p.ay.astype(str)
p.to_parquet(f'{O}/panel_aylik.parquet')
print(p.shape, p.symbol.nunique(), p.ay.min(), p.ay.max())
print(p.groupby('ay').symbol.count().iloc[::12].to_string())
print('mali dolu oran:', p.equity.notna().mean().round(2)); print(mk[['piyasa_ret','usd_deg','ptf_usd_deg']].describe().round(3))
