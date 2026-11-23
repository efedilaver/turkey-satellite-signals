#!/usr/bin/env python3
"""
İnternet gerektirmeyen sağlama testi: iki prototipin analiz mantığını,
cevabını önceden bildiğimiz yapay verilerle çalıştırır.

  python demo_sentetik.py

Gerçek veriyle sonuç vermez; yalnızca kodun doğru çalıştığını ve yöntemin
bilinen bir sinyali geri bulabildiğini gösterir. Çıktılar: cikti/demo_*.png
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import baraj_takip as bt
import no2_nowcast as nn

rng = np.random.default_rng(42)
bt.CIKTI.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# 1) Baraj: elips şeklinde göl + yanında deniz + rastgele bulutlar
# ---------------------------------------------------------------------------
def sahne_uret(doluluk, bulut=0.0, h=200, w=260):
    yy, xx = np.mgrid[0:h, 0:w]
    # göl kıyıları eğimli: doluluk arttıkça yarıçap büyür (alan ~ doluluk^0.7)
    olcek = 0.35 + 0.65 * (doluluk / 100) ** 0.7
    gol = ((yy - 100) / (60 * olcek)) ** 2 + ((xx - 110) / (85 * olcek)) ** 2 <= 1
    deniz = xx > 235                                     # kutunun kenarında deniz şeridi
    gölet = (yy - 30) ** 2 + (xx - 30) ** 2 <= 36        # küçük ayrı gölet
    su = gol | deniz | gölet
    green = np.where(su, 0.06, 0.09) + rng.normal(0, 0.008, (h, w))
    swir = np.where(su, 0.02, 0.22) + rng.normal(0, 0.012, (h, w))
    scl = np.where(su, 6, 4).astype("uint8")
    if bulut > 0:  # bulut lekeleri
        for _ in range(int(bulut * 30)):
            cy, cx, r = rng.integers(0, h), rng.integers(0, w), rng.integers(8, 25)
            scl[(yy - cy) ** 2 + (xx - cx) ** 2 <= r * r] = 9
    gercek_alan = gol.sum() * 20**2 / 1e6
    return green, swir, scl, gercek_alan


tarih = pd.date_range("2018-01-01", "2023-12-31", freq="5D")
gun = np.arange(len(tarih))
# mevsimsel dolum + 2021 kuraklığı
doluluk = 60 + 25 * np.sin(2 * np.pi * (gun * 5 / 365.25 - 0.1)) - 25 * np.exp(-((tarih.year + tarih.dayofyear / 365 - 2021.0) ** 2) / 0.1)
doluluk = np.clip(doluluk + rng.normal(0, 2, len(tarih)), 5, 100)
bulutluluk = rng.choice([0, 0, 0, 0.3, 1.0], len(tarih))

satir = []
for t, d, b in zip(tarih, doluluk, bulutluluk):
    g, s, c, gercek = sahne_uret(d, b)
    r = bt.sahne_analiz(g, s, c, tohum_rc=(100, 110), piksel_m=20, arama_px=100)
    satir.append(dict(tarih=t, alan_km2=r["alan_km2"], gercek_km2=gercek, gecerli=r["gecerli_oran"]))
sonuc = pd.DataFrame(satir).set_index("tarih")
iyi = sonuc.dropna()
hata = (iyi["alan_km2"] / iyi["gercek_km2"] - 1).abs()
print(f"[Baraj] {len(sonuc)} sahne, {len(iyi)} bulutsuz kabul edildi, "
      f"{len(sonuc) - len(iyi)} bulutlu sahne atlandı")
print(f"[Baraj] Alan ölçüm hatası: ortalama %{100 * hata.mean():.2f}, en kötü %{100 * hata.max():.2f}"
      "  (deniz ve gölet doğru şekilde hariç tutuldu mu? -> hata küçükse evet)")

iski = pd.Series(doluluk, index=tarih, name="Demo")
es = bt.alan_dolulugu_esle(sonuc["alan_km2"], iski)
cv = bt.yil_disli_dogrulama(es).dropna()
mae = (cv["tahmin"] - cv["doluluk"]).abs().mean()
print(f"[Baraj] Yıl dışarıda bırakılarak doluluk tahmini: ortalama mutlak hata {mae:.1f} puan "
      f"(doluluğun std'si {es['doluluk'].std():.1f} puan)")
an = bt.mevsimsel_anomali(sonuc["alan_km2"])
kurak = an.loc["2021-01":"2021-03", "anomali_yuzde"].mean()
print(f"[Baraj] 2021 başı kuraklık anomalisi: %{kurak:.0f}  (negatif olması bekleniyor)")

g, s, c, _ = sahne_uret(70, 0.3)
r = bt.sahne_analiz(g, s, c, (100, 110), 20, 100)
fig, ax = plt.subplots(2, 2, figsize=(12, 8))
ax[0, 0].imshow(np.clip(bt.mndwi(g, s), -0.6, 0.6), cmap="RdBu"); ax[0, 0].set_title("Sentetik sahne MNDWI (göl + deniz + gölet)")
ax[0, 1].imshow(r["su_maske"], cmap="Blues"); ax[0, 1].set_title("Seçilen su kütlesi (yalnızca göl)")
ax[0, 1].plot(110, 100, "r+", ms=14, mew=2)
ax[1, 0].plot(iski.index, iski, lw=1, label="'İSKİ' doluluk (gerçek)")
ax[1, 0].scatter(cv.index, cv["tahmin"], s=8, color="tab:orange", label="Uydudan tahmin (örneklem dışı)")
ax[1, 0].legend(fontsize=8); ax[1, 0].set_title(f"Doğrulama — MAE {mae:.1f} puan")
ax[1, 1].bar(an.index, an["anomali_yuzde"], width=25,
             color=np.where(an["anomali_yuzde"] < 0, "tab:red", "tab:blue"))
ax[1, 1].set_title("Mevsimsel anomali (2021 kuraklığı)")
for a in ax[0]: a.set_xticks([]); a.set_yticks([])
fig.tight_layout(); fig.savefig(bt.CIKTI / "demo_baraj.png", dpi=110); plt.close(fig)


# ---------------------------------------------------------------------------
# 2) NO2: bilinen bir ilişki + mevsimsellik + hava durumu gürültüsü
# ---------------------------------------------------------------------------
aylar = pd.date_range("2018-07-01", "2026-09-01", freq="MS")
n = len(aylar)
# "Gerçek" sanayi aktivitesi: yavaş döngü + 2020 Covid çöküşü
dongu = 3 * np.sin(np.arange(n) / 9) + rng.normal(0, 1.5, n).cumsum() * 0.3
covid = np.where((aylar >= "2020-04-01") & (aylar <= "2020-06-01"), -25, 0)
aktivite = 100 * np.exp((dongu + covid) / 100)
sue_endeks = pd.Series(aktivite * (1 + 0.05 * np.sin(2 * np.pi * aylar.month / 12)), index=aylar)
sue_endeks = sue_endeks.iloc[:-2]  # son 2 ay henüz açıklanmadı (TÜİK gecikmesi)

mevsim = 1 + 0.45 * np.cos(2 * np.pi * (aylar.month - 1) / 12)       # kışın NO2 yüksek
hava = np.exp(rng.normal(0, 0.12, n))                                   # tüm ülkeyi etkileyen hava etkisi
satir = []
for b in list(nn.BOLGELER) + [nn.ARKA_PLAN[0]]:
    if b == nn.ARKA_PLAN[0]:
        deger = 15 * mevsim * hava * np.exp(rng.normal(0, 0.05, n))
    else:
        duyarlilik = rng.uniform(0.6, 1.2)
        deger = 60 * mevsim * hava * (aktivite / 100) ** duyarlilik * np.exp(rng.normal(0, 0.10, n))
    satir += [dict(ay=a, bolge=b, no2_umol_m2=v, piksel=500) for a, v in zip(aylar, deger)]
no2 = pd.DataFrame(satir)
no2.to_csv(nn.CIKTI / "demo_no2_aylik.csv", index=False)
sue_csv = nn.CIKTI / "demo_sue.csv"
pd.DataFrame({"Tarih": sue_endeks.index.strftime("%Y-%m"),
              "TP.SANAYI.ENDEKS": sue_endeks.round(2).astype(str).str.replace(".", ",")}).to_csv(sue_csv, index=False)

# Dosya okuyucuyu da test et (EVDS tarzı '2024-01' tarih ve virgüllü ondalık)
y = nn.sue_oku(sue_csv)
x = 100 * nn.no2_sinyali(no2)["BILESIK"]
print(f"\n[NO2] SÜE serisi okundu: {len(y)} ay; NO2 sinyali: {x.notna().sum()} ay")
print(f"[NO2] Ham korelasyon (aynı ay): {pd.concat([x, y], axis=1).dropna().corr().iloc[0, 1]:.2f}")
for etiket, haric in [("Covid dahil", None), ("Covid hariç", pd.date_range("2020-03-01", "2021-06-01", freq="MS"))]:
    oos = nn.ornek_disi_test(y, x, gecikme=2, haric=haric)
    d = oos[oos["degerlendir"]]
    r1 = np.sqrt(((d.m1 - d.gercek) ** 2).mean()); r2 = np.sqrt(((d.m2 - d.gercek) ** 2).mean())
    print(f"[NO2] {etiket}: M1 RMSE {r1:.2f} | M2 (+uydu) RMSE {r2:.2f} -> iyileşme %{100 * (1 - r2 / r1):.0f}")
tahmin, m2 = nn.guncel_tahmin(y, x, gecikme=2)
gercek_son = 100 * (aktivite[-2:] * (1 + 0.05 * np.sin(2 * np.pi * aylar[-2:].month / 12))
                    / (aktivite[-14:-12] * (1 + 0.05 * np.sin(2 * np.pi * aylar[-14:-12].month / 12))) - 1)
for (_, r), g_ in zip(tahmin.iterrows(), gercek_son):
    print(f"[NO2] Açıklanmamış ay {r['ay']:%Y-%m}: tahmin %{r['tahmin']:+.1f}  (sentetik gerçek %{g_:+.1f})")

# Komut satırı yolunu da uçtan uca çalıştır
import argparse
nn.komut_model(argparse.Namespace(no2=str(nn.CIKTI / "demo_no2_aylik.csv"), sue=str(sue_csv),
                                  sue_sutun=None, sue_tip="endeks", gecikme=2, covid_haric=True,
                                  bolgeler=None, hava=False))
import shutil
shutil.move(nn.CIKTI / "no2_nowcast.png", nn.CIKTI / "demo_no2.png")
print("\nGrafikler: cikti/demo_baraj.png, cikti/demo_no2.png")
