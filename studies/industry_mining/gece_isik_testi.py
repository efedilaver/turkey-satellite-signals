#!/usr/bin/env python3
"""T-I1 (kural: ARASTIRMA_PLANI.md): VIIRS gece ışığı -> il bazında reel GSYH büyümesi."""
import unicodedata, re, numpy as np, pandas as pd
def norm(s):
    s = str(s).replace('İ', 'i').replace('ı', 'i').lower()
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z]', '', s)
ALIAS = {'afyon': 'afyonkarahisar', 'kmaras': 'kahramanmaras', 'zinguldak': 'zonguldak', 'icel': 'mersin',
         'kinkkale': 'kirikkale', 'kirikale': 'kirikkale'}
m = pd.read_csv('cikti/gece_isik_il_aylik.csv')
m['anahtar'] = m.il.map(norm).replace(ALIAS)
m = m[m.kaps / m.bir >= 0.9]
m['yil'] = m.ay.str[:4].astype(int)
y = m.groupby(['anahtar', 'yil']).agg(isik=('isik', 'mean'), ay_n=('isik', 'size')).reset_index()
y = y[y.ay_n >= 9]
g = pd.read_csv('cikti/isik/tuik_il_gsyh_reel.csv', sep=';'); g = g[g.kod != 'TR']
g['anahtar'] = g.il.map(norm)
gl = g.melt(id_vars=['kod', 'il', 'anahtar'], var_name='yil', value_name='gsyh'); gl['yil'] = gl.yil.astype(int)
eksik = sorted(set(g.anahtar) - set(y.anahtar)); fazla = sorted(set(y.anahtar) - set(g.anahtar))
print('Eşleşmeyen TÜİK illeri:', eksik, '| eşleşmeyen GAUL:', fazla)
d = gl.merge(y, on=['anahtar', 'yil']).sort_values(['anahtar', 'yil'])
d['dg'] = d.groupby('anahtar').gsyh.transform(lambda s: np.log(s).diff())
d['di'] = d.groupby('anahtar').isik.transform(lambda s: np.log(s).diff())
d = d.dropna(subset=['dg', 'di'])
d = d[np.isfinite(d.di)]
d['dg_s'] = d.dg - d.groupby('yil').dg.transform('mean'); d['di_s'] = d.di - d.groupby('yil').di.transform('mean')
r = d.dg_s.corr(d.di_s); yr = d.groupby('yil').apply(lambda x: x.dg_s.corr(x.di_s))
print(f'İl sayısı {d.anahtar.nunique()}, il-yıl {len(d)}, yıllar {d.yil.min()}–{d.yil.max()}')
print(f'ANA: havuz r(ışık sapması, reel büyüme sapması) = {r:+.3f} (eşik +0,20)')
print('Yıllara göre r:', yr.round(2).to_dict())
print('KAPI:', 'GEÇTİ' if (r >= 0.20 and (yr > 0).mean() >= 2 / 3) else 'KALDI')
# (a) uzun fark
ilk, son = d.yil.min() - 1, d.yil.max()
w = gl.merge(y, on=['anahtar', 'yil'])
a = w[w.yil == ilk].set_index('anahtar')[['gsyh', 'isik']].join(w[w.yil == son].set_index('anahtar')[['gsyh', 'isik']], rsuffix='_s')
print(f'(a) Uzun fark {ilk}→{son}: r = {np.log(a.gsyh_s / a.gsyh).corr(np.log(a.isik_s / a.isik)):+.3f} (n={len(a)})')
# (b) örneklem dışı
rows = []
for t in sorted(d.yil.unique())[2:]:
    e, s = d[d.yil < t], d[d.yil == t]
    b = np.polyfit(e.di_s, e.dg_s, 1)
    onceki = d[d.yil == t - 1].set_index('anahtar').dg_s
    rows.append(dict(yil=t, rmse_isik=np.sqrt(((s.dg_s - np.polyval(b, s.di_s)) ** 2).mean()),
                     rmse_sifir=np.sqrt((s.dg_s ** 2).mean()),
                     rmse_gecenyil=np.sqrt(((s.dg_s - s.anahtar.map(onceki).fillna(0)) ** 2).mean())))
o = pd.DataFrame(rows).set_index('yil'); print('(b) Örneklem dışı RMSE (puan ×100):'); print((o * 100).round(2).to_string())
print('   ortalama:', (o.mean() * 100).round(2).to_dict())
# (c) deprem bölgesi
dep = ['kahramanmaras', 'hatay', 'adiyaman', 'malatya', 'gaziantep', 'osmaniye', 'adana', 'diyarbakir', 'kilis', 'sanliurfa', 'elazig']
c = d[(d.yil == 2023) & d.anahtar.isin(dep)][['il', 'dg_s', 'di_s']]
print('(c) Deprem bölgesi 2023 (ulusal ortalamaya göre, %):'); print((c.set_index('il') * 100).round(1).to_string())
print(f'    11 il ortalaması: GSYH {c.dg_s.mean()*100:+.1f}, ışık {c.di_s.mean()*100:+.1f}; il içi r = {c.dg_s.corr(c.di_s):+.2f}')
d.to_csv('cikti/isik/t_i1_il_yil.csv', index=False)
