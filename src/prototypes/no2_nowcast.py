#!/usr/bin/env python3
"""
Sanayi üretimi anlık tahmini (nowcasting) — Sentinel-5P NO2

Fikir:
  Fabrikalar, enerji santralleri ve ağır taşıma NO2 (azot dioksit) salar.
  Sentinel-5P uydusu her gün tüm Türkiye üzerindeki troposferik NO2 miktarını ölçer.
  Sanayi bölgelerindeki NO2'nin yıllık değişimi, TÜİK'in ~40 gün gecikmeyle
  açıkladığı Sanayi Üretim Endeksi'ni (SÜE) önceden tahmin etmeye yarayabilir.

Dürüst test (videodaki "mükemmel bilgiyle kazanır mıydım?" sorusunun karşılığı):
  Asıl soru "NO2 SÜE ile korele mi?" değil, "NO2, açıklama anında zaten bildiğimiz
  bilgiye (son açıklanan SÜE) bir şey ekliyor mu?". Bu yüzden iki modeli
  örneklem dışında karşılaştırıyoruz:
     M1 (kıyas): SÜE_yıllık(t) = a + b * SÜE_yıllık(t-2)
     M2 (uydu):  SÜE_yıllık(t) = a + b * SÜE_yıllık(t-2) + c * NO2_sinyali(t)
  M2'nin hatası M1'den belirgin küçük değilse, uydu sinyali para etmez.

Komutlar:
  python no2_nowcast.py indir  --proje BENIM-GEE-PROJEM
  python no2_nowcast.py model  --sue sue.csv [--covid-haric]

Gerekenler: ücretsiz Google Earth Engine hesabı (bir kez: earthengine authenticate)
            ve TÜİK Sanayi Üretim Endeksi (aylık, takvim etkisinden arındırılmış) CSV'si.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

CIKTI = Path("cikti")
GEE_KOLEKSIYON = "COPERNICUS/S5P/OFFL/L3_NO2"
GEE_BANT = "tropospheric_NO2_column_number_density"  # mol/m²
VERI_BASLANGIC = "2018-07-01"

# (batı boylam, güney enlem, doğu boylam, kuzey enlem) — yaklaşık sanayi kümeleri.
# Kutular ~1 km'lik NO2 ızgarasına göre bilerek geniş tutuldu.
BOLGELER = {
    "Kocaeli_Gebze_Dilovasi": (29.35, 40.70, 30.10, 40.87),
    "Bursa_OSB_Gemlik":       (28.85, 40.15, 29.20, 40.45),
    "Tekirdag_Corlu_Cerkezkoy": (27.70, 41.10, 28.05, 41.35),
    "Izmir_Aliaga":           (26.85, 38.70, 27.10, 38.90),
    "Manisa_OSB":             (27.30, 38.55, 27.50, 38.70),
    "Kayseri_OSB":            (35.30, 38.65, 35.60, 38.80),
    "Konya_OSB":              (32.40, 37.85, 32.65, 38.05),
    "Gaziantep_OSB":          (37.25, 37.00, 37.55, 37.20),
    "Iskenderun_Isdemir":     (36.05, 36.70, 36.30, 36.90),
    "Eregli_Erdemir":         (31.35, 41.20, 31.50, 41.32),
    "Karabuk_Kardemir":       (32.55, 41.15, 32.70, 41.25),
}
# Sanayisi olmayan kırsal alan: hava durumu ve mevsimsel kimya etkisini ayıklamak için
ARKA_PLAN = ("ArkaPlan_IcAnadolu", (32.30, 38.90, 32.90, 39.30))

# Demir-çelik hedefi için önceden (sonuçlara bakmadan) seçilen bölgeler:
# üç entegre tesis (yüksek fırın) + Aliağa'daki ark ocaklı çelik kümesi.
CELIK_BOLGELER = ["Iskenderun_Isdemir", "Eregli_Erdemir", "Karabuk_Kardemir", "Izmir_Aliaga"]

# Hava durumu: NOAA CFSv2 (6 saatlik, ~2 gün gecikme -> anlık tahminde de kullanılabilir)
HAVA_KOLEKSIYON = "NOAA/CFSV2/FOR6H_HARMONIZED"
HAVA_SUTUNLARI = ["ruzgar_ms", "sicaklik_c", "gunes_wm2"]


# ===========================================================================
# Veri indirme: Google Earth Engine
# ===========================================================================
def komut_indir(a):
    import ee

    try:
        ee.Initialize(project=a.proje)
    except Exception as e:
        metin = str(e)
        if "not been used" in metin or "SERVICE_DISABLED" in metin:
            sys.exit(f"Earth Engine API bu projede kapalı. Şu adresten 'Enable' de, 2-3 dk bekle:\n"
                     f"https://console.developers.google.com/apis/api/earthengine.googleapis.com/overview?project={a.proje}")
        if "not found" in metin:
            sys.exit(f"'{a.proje}' adlı proje bulunamadı. Proje ADI değil, proje KİMLİĞİ (ID) gerekli.")
        print("Earth Engine oturumu açılamadı, tarayıcıda yetkilendirme açılıyor...")
        ee.Authenticate()
        ee.Initialize(project=a.proje)

    CIKTI.mkdir(exist_ok=True)
    tum = dict(BOLGELER, **{ARKA_PLAN[0]: ARKA_PLAN[1]})
    fc = ee.FeatureCollection([
        ee.Feature(ee.Geometry.Rectangle(list(b)), {"bolge": ad}) for ad, b in tum.items()
    ])
    col = ee.ImageCollection(GEE_KOLEKSIYON).select([GEE_BANT], ["no2"])

    def hava_goruntusu(img):
        # Uydunun geçiş saatine (~10:30 UTC) yakın 06 ve 12 UTC analizleri kullanılır
        u = img.select("u-component_of_wind_height_above_ground")
        v = img.select("v-component_of_wind_height_above_ground")
        return ee.Image.cat([
            u.hypot(v).rename("ruzgar_ms"),
            img.select("Temperature_height_above_ground").subtract(273.15).rename("sicaklik_c"),
            img.select("Downward_Short-Wave_Radiation_Flux_surface_6_Hour_Average").rename("gunes_wm2"),
        ]).copyProperties(img, ["system:time_start"])

    def hava_ortalama(bas, son):
        # Tarih filtresi map'ten ÖNCE uygulanır (Image.cat zaman damgasını taşımaz)
        return (ee.ImageCollection(HAVA_KOLEKSIYON)
                .filterDate(bas, son)
                .filter(ee.Filter.calendarRange(6, 12, "hour"))
                .map(hava_goruntusu)
                .mean())

    son_tam_ay = (pd.Timestamp.today().normalize().replace(day=1) - pd.DateOffset(months=1))
    aylar = pd.date_range(a.baslangic, a.bitis or son_tam_ay, freq="MS")

    yol = CIKTI / "no2_aylik.csv"
    eski = pd.read_csv(yol, parse_dates=["ay"]) if yol.exists() else pd.DataFrame(columns=["ay", "bolge"])
    # Bir ay, tüm bölgeleri ve hava sütunları dolu olarak varsa tamam sayılır
    tamam = set()
    if not eski.empty and set(HAVA_SUTUNLARI) <= set(eski.columns):
        dolu = eski.dropna(subset=["no2_umol_m2"] + HAVA_SUTUNLARI)
        sayim = dolu.groupby("ay")["bolge"].nunique()
        tamam = set(sayim[sayim >= len(tum)].index)

    satirlar = []
    for i, ay in enumerate(aylar):
        if ay in tamam and ay < son_tam_ay:  # son ayı her zaman yeniden çek
            continue
        bas, son = ay.strftime("%Y-%m-%d"), (ay + pd.DateOffset(months=1)).strftime("%Y-%m-%d")
        img = col.filterDate(bas, son).mean().addBands(hava_ortalama(bas, son))
        sonuc = img.reduceRegions(collection=fc, reducer=ee.Reducer.mean(), scale=1113.2).getInfo()
        bu_ay = []
        for f in sonuc["features"]:
            p = f["properties"]
            bu_ay.append(dict(ay=ay, bolge=p["bolge"],
                              no2_umol_m2=None if p.get("no2") is None else p["no2"] * 1e6,
                              **{k: p.get(k) for k in HAVA_SUTUNLARI}))
        # Sessizce boş veri biriktirmemek için ilk ayda kontrol et
        if not satirlar and all(r[k] is None for r in bu_ay for k in HAVA_SUTUNLARI):
            sys.exit(f"{ay:%Y-%m} için hava verisi boş döndü. Dönen alanlar: {sorted(p)}\n"
                     "Bu çıktıyı Claude'a yapıştır.")
        satirlar += bu_ay
        ornek = next((r for r in bu_ay if r["ruzgar_ms"] is not None), None)
        ek = f"  rüzgâr {ornek['ruzgar_ms']:.1f} m/s, {ornek['sicaklik_c']:.0f}°C" if ornek else "  (hava yok)"
        print(f"  {ay:%Y-%m} tamam ({i + 1}/{len(aylar)}){ek}")

    yeni = pd.DataFrame(satirlar)
    df = pd.concat([eski, yeni]).drop_duplicates(["ay", "bolge"], keep="last").sort_values(["ay", "bolge"])
    df = df[[c for c in ["ay", "bolge", "no2_umol_m2", *HAVA_SUTUNLARI] if c in df.columns]]
    df.to_csv(yol, index=False)
    print(f"-> {yol}  ({df['ay'].nunique()} ay, {df['bolge'].nunique()} bölge)")


# ===========================================================================
# Saf analiz fonksiyonları (ağ gerektirmez)
# ===========================================================================
_AYLAR_TR = {a: i + 1 for i, a in enumerate(
    ["ocak", "şubat", "mart", "nisan", "mayıs", "haziran",
     "temmuz", "ağustos", "eylül", "ekim", "kasım", "aralık"])}


def _tarih_coz(s) -> pd.Timestamp | None:
    """'2024-01', '2024-1', '01/2024', '2024M01', 'Ocak 2024', '2024-01-01' gibi biçimleri çöz."""
    s = str(s).strip().lower()
    for ad, no in _AYLAR_TR.items():
        if ad in s:
            y = re.search(r"(19|20)\d{2}", s)
            return pd.Timestamp(int(y.group()), no, 1) if y else None
    m = re.search(r"((?:19|20)\d{2})\D{0,2}(\d{1,2})(?!\d)", s)
    if m and 1 <= int(m.group(2)) <= 12:
        return pd.Timestamp(int(m.group(1)), int(m.group(2)), 1)
    m = re.search(r"(\d{1,2})\D((?:19|20)\d{2})", s)
    if m and 1 <= int(m.group(1)) <= 12:
        return pd.Timestamp(int(m.group(2)), int(m.group(1)), 1)
    return None


def sue_oku(yol, sutun=None, tip="endeks") -> pd.Series:
    """
    TÜİK / EVDS'den indirilen SÜE dosyasını oku -> yıllık % değişim serisi.
    tip='endeks' : dosyadaki değer endeks seviyesi (yıllık değişimi biz hesaplarız)
    tip='yillik' : dosyadaki değer zaten yıllık % değişim
    """
    yol = str(yol)
    df = pd.read_excel(yol) if yol.lower().endswith((".xlsx", ".xls")) else pd.read_csv(yol, sep=None, engine="python")
    tarihler = df.iloc[:, 0].map(_tarih_coz)
    if sutun is None:
        sayisal = [c for c in df.columns[1:] if pd.to_numeric(df[c].astype(str).str.replace(",", "."), errors="coerce").notna().mean() > 0.5]
        if not sayisal:
            raise ValueError("Sayısal sütun bulunamadı; --sue-sutun ile belirt.")
        sutun = sayisal[0]
    deger = pd.to_numeric(df[sutun].astype(str).str.replace(",", "."), errors="coerce")
    s = pd.Series(deger.values, index=tarihler.values).dropna()
    s = s[s.index.notna()].sort_index()
    s = s[~s.index.duplicated(keep="last")].asfreq("MS")
    if tip == "endeks":
        s = 100 * (s / s.shift(12) - 1)
    return s.rename("sue_yillik").dropna()


def _pivot(no2, sutun):
    return no2.pivot_table(index="ay", columns="bolge", values=sutun).sort_index().asfreq("MS")


def hava_duzeltmeli_yillik(no2: pd.DataFrame, min_gozlem=60) -> pd.DataFrame:
    """
    Her bölgenin log(NO2) yıllık farkından hava durumunun açıkladığı kısmı çıkarır.

    Model (tüm bölgeler havuzlanmış, arka plan dahil):
        Δ12 log NO2 = a + b1·Δ12 log(rüzgâr) + b2·Δ12 sıcaklık + b3·Δ12 güneş + hata
    Düzeltilmiş sinyal = Δ12 log NO2 − (b1·… + b2·… + b3·…)

    Katsayılar her ay için YALNIZCA o aya kadarki verilerle tahmin edilir
    (genişleyen pencere); yani geriye dönük testte gelecekten bilgi sızmaz ve
    aynı hesap gerçek zamanlı anlık tahminde de birebir yapılabilir.
    """
    log = np.log(_pivot(no2, "no2_umol_m2").where(lambda t: t > 0))
    dy = log - log.shift(12)
    dw = np.log(_pivot(no2, "ruzgar_ms")).pipe(lambda t: t - t.shift(12))
    dt = _pivot(no2, "sicaklik_c").pipe(lambda t: t - t.shift(12))
    ds = _pivot(no2, "gunes_wm2").pipe(lambda t: (t - t.shift(12)) / 100)

    uzun = pd.concat({"y": dy.stack(), "w": dw.stack(), "t": dt.stack(), "s": ds.stack()}, axis=1).dropna()
    duz = pd.DataFrame(index=dy.index, columns=dy.columns, dtype=float)
    b = np.full(4, np.nan)
    for ay in dy.index:
        egitim = uzun[uzun.index.get_level_values("ay") <= ay]
        if len(egitim) < min_gozlem:
            continue
        X = np.column_stack([np.ones(len(egitim)), egitim[["w", "t", "s"]].to_numpy()])
        b = np.linalg.lstsq(X, egitim["y"].to_numpy(), rcond=None)[0]
        if ay not in uzun.index.get_level_values("ay"):
            continue
        bu = uzun.xs(ay, level="ay")
        duz.loc[ay, bu.index] = bu["y"] - bu[["w", "t", "s"]].to_numpy() @ b[1:]
    duz.attrs["son_katsayilar"] = dict(zip(["sabit", "log_ruzgar", "sicaklik", "gunes_100wm2"], b.round(3)))
    return duz


def no2_sinyali(no2: pd.DataFrame, bolgeler=None, hava=False) -> pd.DataFrame:
    """
    Her bölge için log(NO2)'nin yıllık farkı (12 ay öncesine göre; mevsimselliği yok eder).
      hava=False : eksi arka plan bölgesinin yıllık farkı (hava etkisini kabaca ayıklar)
      hava=True  : rüzgâr/sıcaklık/güneş etkisi regresyonla çıkarılmış hali
    Bileşik sinyal (BILESIK) = seçilen bölgelerin ortalaması. Birim: ~ % değişim / 100.
    """
    arka = ARKA_PLAN[0]
    if hava:
        if not set(HAVA_SUTUNLARI) <= set(no2.columns):
            raise ValueError("NO2 dosyasında hava sütunları yok; 'indir' komutunu yeniden çalıştır.")
        fark = hava_duzeltmeli_yillik(no2)
        fark = fark.drop(columns=[arka], errors="ignore")
    else:
        log = np.log(_pivot(no2, "no2_umol_m2").where(lambda t: t > 0))
        yillik = log - log.shift(12)
        bolg = [c for c in yillik.columns if c != arka]
        fark = yillik[bolg].sub(yillik[arka], axis=0) if arka in yillik.columns else yillik[bolg]
    secili = [b for b in (bolgeler or fark.columns) if b in fark.columns]
    if not secili:
        raise ValueError(f"Seçilen bölgeler veride yok: {bolgeler}")
    fark["BILESIK"] = fark[secili].mean(axis=1, skipna=True)
    return fark


def ornek_disi_test(y: pd.Series, x: pd.Series, gecikme=2, min_egitim=24, haric=None):
    """
    Genişleyen pencereyle örneklem dışı tahmin.
    Her ay t için yalnızca t'den önce bilinen verilerle model kurulur:
      - SÜE için t-gecikme'ye kadar (TÜİK yayın gecikmesi)
      - NO2 sinyali için t dahil (ay biter bitmez uydudan hesaplanabilir)
    """
    import statsmodels.api as sm

    df = pd.concat([y.rename("y"), y.shift(gecikme).rename("y_gec"), x.rename("x")], axis=1).dropna()
    maske = pd.Series(True, index=df.index)
    if haric is not None:
        maske &= ~df.index.isin(haric)

    satir = []
    for i, t in enumerate(df.index):
        # model t'yi tahmin ederken SÜE'nin t-gecikme'ye kadar olan değerlerini bilebilir
        egitim = df[(df.index <= t - pd.DateOffset(months=gecikme)) & maske]
        if len(egitim) < min_egitim:
            continue
        X1 = sm.add_constant(egitim[["y_gec"]])
        X2 = sm.add_constant(egitim[["y_gec", "x"]])
        m1 = sm.OLS(egitim["y"], X1).fit()
        m2 = sm.OLS(egitim["y"], X2).fit()
        r = df.loc[t]
        satir.append(dict(ay=t, gercek=r["y"],
                          m1=m1.params["const"] + m1.params["y_gec"] * r["y_gec"],
                          m2=m2.params["const"] + m2.params["y_gec"] * r["y_gec"] + m2.params["x"] * r["x"],
                          degerlendir=bool(maske.loc[t])))
    return pd.DataFrame(satir).set_index("ay")


def guncel_tahmin(y: pd.Series, x: pd.Series, gecikme=2, haric=None):
    """SÜE'si henüz açıklanmamış ama NO2'si hazır aylar için tahmin."""
    import statsmodels.api as sm

    df = pd.concat([y.rename("y"), y.shift(gecikme).rename("y_gec"), x.rename("x")], axis=1)
    egitim = df.dropna()
    if haric is not None:
        egitim = egitim[~egitim.index.isin(haric)]
    m2 = sm.OLS(egitim["y"], sm.add_constant(egitim[["y_gec", "x"]])).fit()
    # gelecek aylar: y bilinmiyor, x biliniyor, y_gec için y'nin gecikmeli değeri lazım
    y_gec = y.reindex(x.index).shift(gecikme)
    hedef = x.dropna().index[(x.dropna().index > y.index.max())]
    tahmin = []
    for t in hedef:
        if pd.isna(y_gec.get(t)):
            continue
        tahmin.append(dict(ay=t, tahmin=m2.params["const"] + m2.params["y_gec"] * y_gec[t] + m2.params["x"] * x[t]))
    return pd.DataFrame(tahmin), m2


def komut_model(a):
    import matplotlib.pyplot as plt

    no2 = pd.read_csv(a.no2, parse_dates=["ay"])
    sinyal = no2_sinyali(no2, a.bolgeler, a.hava)
    y = sue_oku(a.sue, a.sue_sutun, a.sue_tip)
    x = 100 * sinyal["BILESIK"]  # yaklaşık yüzde
    haric = pd.date_range("2020-03-01", "2021-06-01", freq="MS") if a.covid_haric else None

    print(f"SÜE: {y.index.min():%Y-%m} – {y.index.max():%Y-%m}  |  NO2 sinyali: "
          f"{x.dropna().index.min():%Y-%m} – {x.dropna().index.max():%Y-%m}")

    # 1) Basit ilişki: bölge bazında korelasyon
    ortak = pd.concat([y, 100 * sinyal], axis=1).dropna(subset=["sue_yillik"])
    if haric is not None:
        ortak = ortak[~ortak.index.isin(haric)]
    kor = ortak.drop(columns="sue_yillik").corrwith(ortak["sue_yillik"]).sort_values(ascending=False)
    print("\nSÜE yıllık değişimi ile NO2 sinyali korelasyonu (bölge bazında):")
    print(kor.round(2).to_string())

    # 2) Asıl test: örneklem dışı, yayın gecikmesine saygılı
    oos = ornek_disi_test(y, x, gecikme=a.gecikme, haric=haric)
    d = oos[oos["degerlendir"]]
    if len(d) < 6:
        sys.exit("Örneklem dışı değerlendirme için yeterli ay yok.")
    rmse1 = np.sqrt(((d["m1"] - d["gercek"]) ** 2).mean())
    rmse2 = np.sqrt(((d["m2"] - d["gercek"]) ** 2).mean())
    yon1 = (np.sign(d["m1"].diff()) == np.sign(d["gercek"].diff())).mean()
    yon2 = (np.sign(d["m2"].diff()) == np.sign(d["gercek"].diff())).mean()
    print(f"\nÖrneklem dışı ({len(d)} ay, {d.index.min():%Y-%m} – {d.index.max():%Y-%m}):")
    print(f"  M1 kıyas (sadece son açıklanan SÜE)  RMSE = {rmse1:.2f} puan   yön isabeti = {yon1:.0%}")
    print(f"  M2 uydu  (+ NO2 sinyali)             RMSE = {rmse2:.2f} puan   yön isabeti = {yon2:.0%}")
    iyilesme = 100 * (1 - rmse2 / rmse1)
    print(f"  -> Uydu sinyali hatayı %{iyilesme:.1f} {'azalttı' if iyilesme > 0 else 'ARTTIRDI'}")
    if iyilesme < 5:
        print("     Yorum: belirgin bir katkı yok — bu haliyle ticari değeri şüpheli.")

    tahmin, m2 = guncel_tahmin(y, x, gecikme=a.gecikme, haric=haric)
    print(f"\nTam örneklem M2 katsayısı (NO2): {m2.params['x']:.3f}  (p = {m2.pvalues['x']:.3f})")
    if not tahmin.empty:
        print("\nHenüz açıklanmamış aylar için SÜE yıllık değişim tahmini:")
        for _, r in tahmin.iterrows():
            print(f"  {r['ay']:%Y-%m}: %{r['tahmin']:+.1f}")

    CIKTI.mkdir(exist_ok=True)
    oos.to_csv(CIKTI / "no2_ornek_disi.csv")
    fig, ax = plt.subplots(2, 1, figsize=(11, 8))
    ax[0].plot(y.index, y, color="k", lw=1.5, label="TÜİK SÜE (yıllık %)")
    ax[0].plot(oos.index, oos["m1"], lw=1, ls="--", label="M1 kıyas (örneklem dışı)")
    ax[0].plot(oos.index, oos["m2"], lw=1.2, label="M2 + NO2 (örneklem dışı)")
    if not tahmin.empty:
        ax[0].scatter(tahmin["ay"], tahmin["tahmin"], color="red", zorder=5, label="Anlık tahmin")
    if haric is not None:
        ax[0].axvspan(haric.min(), haric.max(), color="grey", alpha=0.15, label="Dışarıda bırakılan dönem")
    ax[0].axhline(0, color="grey", lw=0.6)
    ax[0].legend(fontsize=8)
    ax[0].set_title("Sanayi üretimi yıllık değişimi: gerçek vs tahmin")
    sc = ortak[["sue_yillik", "BILESIK"]].dropna()
    ax[1].scatter(sc["BILESIK"], sc["sue_yillik"], s=14, alpha=0.7)
    ax[1].set_xlabel("NO2 sinyali (sanayi bölgeleri − arka plan, yıllık %)")
    ax[1].set_ylabel("SÜE yıllık %")
    ax[1].set_title(f"Aynı ay ilişkisi (korelasyon {sc.corr().iloc[0, 1]:.2f})")
    fig.tight_layout()
    fig.savefig(CIKTI / "no2_nowcast.png", dpi=120)
    print(f"\nGrafik: {CIKTI / 'no2_nowcast.png'}")


def komut_karsilastir(a):
    """
    Önceden belirlenmiş 2x2 deney: hedef (toplam sanayi / demir-çelik) x hava düzeltmesi (yok / var).
    Aynı hedef içindeki iki model, AYNI aylarda değerlendirilir ki karşılaştırma adil olsun.
    """
    import matplotlib.pyplot as plt

    no2 = pd.read_csv(a.no2, parse_dates=["ay"])
    hava_var = set(HAVA_SUTUNLARI) <= set(no2.columns) and no2[HAVA_SUTUNLARI].notna().any().all()
    if not hava_var:
        sys.exit("NO2 dosyasında hava verisi yok. Önce: python no2_nowcast.py indir --proje <ID>")
    haric = pd.date_range("2020-03-01", "2021-06-01", freq="MS")

    hedefler = [("Toplam sanayi", a.sue, None)]
    if a.celik:
        hedefler.append(("Demir-çelik (C241)", a.celik, CELIK_BOLGELER))

    tablo, grafik = [], []
    for ad, dosya, bolgeler in hedefler:
        y = sue_oku(dosya)
        sonuclar, tahminler = {}, {}
        for hava in (False, True):
            x = 100 * no2_sinyali(no2, bolgeler, hava)["BILESIK"]
            oos = ornek_disi_test(y, x, gecikme=a.gecikme, haric=haric)
            sonuclar[hava] = oos[oos["degerlendir"]]
            t, _ = guncel_tahmin(y, x, gecikme=a.gecikme, haric=haric)
            tahminler[hava] = t
        ortak = sonuclar[False].index.intersection(sonuclar[True].index)
        for hava in (False, True):
            d = sonuclar[hava].loc[ortak]
            r1 = np.sqrt(((d.m1 - d.gercek) ** 2).mean())
            r2 = np.sqrt(((d.m2 - d.gercek) ** 2).mean())
            kazanilan = ((d.m2 - d.gercek).abs() < (d.m1 - d.gercek).abs()).mean()
            son = tahminler[hava]
            tablo.append({
                "hedef": ad, "hava_duzeltmesi": "var" if hava else "yok", "ay": len(d),
                "donem": f"{d.index.min():%Y-%m}–{d.index.max():%Y-%m}",
                "RMSE_M1": round(r1, 2), "RMSE_M2": round(r2, 2),
                "iyilesme_%": round(100 * (1 - r2 / r1), 1),
                "M2_daha_iyi_ay_%": round(100 * kazanilan),
                "son_tahmin": "; ".join(f"{r.ay:%Y-%m}: {r.tahmin:+.1f}" for r in son.itertuples()) or "-",
            })
        grafik.append((ad, y, sonuclar[False].loc[ortak], sonuclar[True].loc[ortak], tahminler[True]))

    df = pd.DataFrame(tablo)
    CIKTI.mkdir(exist_ok=True)
    df.to_csv(CIKTI / "no2_karsilastirma.csv", index=False)
    pd.set_option("display.width", 200)
    print("\nÖrneklem dışı karşılaştırma (Covid dönemi hariç, TÜİK yayın gecikmesine saygılı):\n")
    print(df.to_string(index=False))
    print("\nOkuma:\n"
          "  iyilesme_%        : uydu modelinin (M2) hatayı, son TÜİK verisine dayanan kıyasa (M1) göre ne kadar azalttığı\n"
          "  M2_daha_iyi_ay_%  : uydu modelinin kıyastan daha isabetli olduğu ayların oranı (50 = yazı-tura)\n"
          "  Kabaca: iyileşme %10'un ve isabetli ay oranı %60'ın altındaysa ciddi bir avantaj yok.")

    fig, axs = plt.subplots(len(grafik), 1, figsize=(11, 4 * len(grafik)))
    for ax, (ad, y, d0, d1, t) in zip(np.atleast_1d(axs), grafik):
        aralik = y[y.index >= d0.index.min() - pd.DateOffset(months=6)]
        ax.plot(aralik.index, aralik, color="k", lw=1.6, label="TÜİK (yıllık %)")
        ax.plot(d0.index, d0["m1"], ls="--", lw=1, label="M1 kıyas")
        ax.plot(d0.index, d0["m2"], lw=1, alpha=0.7, label="M2 + NO2 (hava düzeltmesiz)")
        ax.plot(d1.index, d1["m2"], lw=1.4, label="M2 + NO2 (hava düzeltmeli)")
        if not t.empty:
            ax.scatter(t["ay"], t["tahmin"], color="red", zorder=5, label="Anlık tahmin")
        ax.axhline(0, color="grey", lw=0.6)
        ax.set_title(ad)
        ax.legend(fontsize=8, ncol=3)
    fig.tight_layout()
    fig.savefig(CIKTI / "no2_karsilastirma.png", dpi=120)
    print(f"\nGrafik: {CIKTI / 'no2_karsilastirma.png'}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    alt = p.add_subparsers(dest="komut", required=True)

    i = alt.add_parser("indir", help="Earth Engine'den aylık bölgesel NO2 çek")
    i.add_argument("--proje", required=True, help="Google Cloud proje kimliği (Earth Engine kayıtlı)")
    i.add_argument("--baslangic", default=VERI_BASLANGIC)
    i.add_argument("--bitis", default=None)
    i.set_defaults(f=komut_indir)

    m = alt.add_parser("model", help="SÜE ile örneklem dışı test ve anlık tahmin")
    m.add_argument("--sue", required=True, help="TÜİK/EVDS SÜE dosyası (csv/xlsx): 1. sütun tarih")
    m.add_argument("--sue-sutun", default=None, help="Değer sütununun adı (varsayılan: ilk sayısal sütun)")
    m.add_argument("--sue-tip", choices=["endeks", "yillik"], default="endeks")
    m.add_argument("--no2", default=str(CIKTI / "no2_aylik.csv"))
    m.add_argument("--gecikme", type=int, default=2, help="TÜİK yayın gecikmesi (ay)")
    m.add_argument("--covid-haric", action="store_true",
                   help="2020-03..2021-06'yı eğitim ve değerlendirmeden çıkar (tek bir şokun sonucu domine etmesini önler)")
    m.add_argument("--bolgeler", nargs="*", default=None, help="Sadece bu bölgeler (ör. Eregli_Erdemir Karabuk_Kardemir)")
    m.add_argument("--hava", action="store_true", help="Rüzgâr/sıcaklık/güneş etkisini çıkar")
    m.set_defaults(f=komut_model)

    k = alt.add_parser("karsilastir", help="2x2 deney: toplam sanayi / demir-çelik x hava düzeltmesi yok / var")
    k.add_argument("--sue", required=True, help="Toplam sanayi endeksi dosyası (sue.csv)")
    k.add_argument("--celik", default=None, help="Demir-çelik (C241) endeksi dosyası (celik.csv)")
    k.add_argument("--no2", default=str(CIKTI / "no2_aylik.csv"))
    k.add_argument("--gecikme", type=int, default=2)
    k.set_defaults(f=komut_karsilastir)

    a = p.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
