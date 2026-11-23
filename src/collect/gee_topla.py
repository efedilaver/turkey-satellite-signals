#!/usr/bin/env python3
"""
Google Earth Engine'de SUNUCU TARAFINDA hesaplanan uydu serileri.
Görüntü indirilmez; yalnızca sayılar (CSV) iner. Her akış kaldığı yerden devam eder.

Akışlar (hepsi.py sırayla/paralel çağırır):
  kar    : ERA5-Land kar suyu eşdeğeri, kar erimesi, yağış + MODIS kar örtüsü
           -> cikti/gee_kar_aylik.csv          (havza x ay, 2000'den bugüne)
  firat  : Keban + Karakaya + Atatürk göl alanı (Sentinel-2 MNDWI, aylık)
           + JRC aylık su geçmişi (1984-2021)
           -> cikti/gee_firat_aylik.csv
  don    : Fındık kuşağında Mart-Nisan donlu derece-saat (ERA5-Land saatlik)
           -> cikti/gee_don_yillik.csv
  maden  : data/reference/tralt_sahalar.csv'deki sahalarda aylık çıplak toprak alanı (Sentinel-2)
           -> cikti/gee_maden_aylik.csv
  celik  : data/reference/celik_tesisler.csv'deki tesislerde sahne bazında sıcak piksel sayısı
           -> cikti/gee_celik_sahne.csv

Kullanım: python gee_topla.py [kar firat don maden celik] --proje <GEE proje kimliği>
"""
import argparse
import csv
import sys
import time
from datetime import date
from pathlib import Path

CIKTI = Path("cikti")
ARASTIRMA = Path("data/reference")

# Kaba havza kutuları (batı, güney, doğu, kuzey). Kar ova kesimlerinde zaten sıfır olduğu için
# kutu yaklaşımı anomali hesabı için yeterli; dağ kuşaklarını kapsayacak şekilde seçildi.
HAVZALAR = {
    "Firat_Karasu": (38.5, 39.3, 41.6, 40.6),
    "Firat_Murat": (39.0, 38.5, 43.6, 39.8),
    "Dicle_Ust": (40.0, 37.6, 43.6, 38.6),
    "Coruh": (40.0, 40.0, 42.6, 41.5),
    "Seyhan_Ceyhan": (34.8, 37.4, 37.6, 39.0),
}
# Fırat kaskadı (Keban + Karakaya + Atatürk). Hazar Gölü (doğal göl) dışarıda bırakılır.
FIRAT_KUTU = (37.9, 37.35, 39.85, 39.25)
HAZAR_KUTU = (39.25, 38.42, 39.55, 38.56)
KEBAN_KUTU = (38.75, 38.78, 39.85, 39.25)   # Keban gölünün kuzey kolları (Karakaya ile çakışmayan kısım)
FINDIK_KUTU = (36.5, 40.75, 40.2, 41.25)


def baslat(proje):
    import ee
    try:
        ee.Initialize(project=proje)
    except Exception:
        ee.Authenticate()
        ee.Initialize(project=proje)
    return ee


def _kutu(ee, b):
    return ee.Geometry.Rectangle(list(b))


def _mevcut(yol: Path, anahtar_sutunlar):
    if not yol.exists():
        return set()
    with open(yol, newline="", encoding="utf-8") as f:
        return {tuple(r[k] for k in anahtar_sutunlar) for r in csv.DictReader(f)}


def _ekle(yol: Path, satirlar, alanlar):
    yeni = not yol.exists()
    with open(yol, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=alanlar, extrasaction="ignore")
        if yeni:
            w.writeheader()
        w.writerows(satirlar)


def _getinfo(obj, deneme=4):
    for i in range(deneme):
        try:
            return obj.getInfo()
        except Exception as e:
            if i == deneme - 1:
                raise
            print(f"      GEE hatası ({str(e)[:90]}), {20 * (i + 1)} sn sonra tekrar", flush=True)
            time.sleep(20 * (i + 1))


def _tamam_aylar(bas_yil):
    bugun = date.today()
    for y in range(bas_yil, bugun.year + 1):
        for m in range(1, 13):
            if (y, m) < (bugun.year, bugun.month):
                yield y, m


# ---------------------------------------------------------------- kar
def kar(ee):
    yol = CIKTI / "gee_kar_aylik.csv"
    alanlar = ["havza", "ay", "swe_mm", "erime_mm", "yagis_mm", "kar_ortu_yuzde"]
    var = _mevcut(yol, ["havza", "ay"])
    fc = ee.FeatureCollection([ee.Feature(_kutu(ee, b), {"havza": h}) for h, b in HAVZALAR.items()])
    era = ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR")
    modis = ee.ImageCollection("MODIS/061/MOD10A1").select("NDSI_Snow_Cover")
    for y in range(2001, date.today().year + 1):  # MODIS Şubat 2000'de başlıyor
        aylar = [m for (yy, m) in _tamam_aylar(y) if yy == y
                 and any((h, f"{y}-{m:02d}") not in var for h in HAVZALAR)]
        if not aylar:
            continue

        def ay_img(m):
            m = ee.Number(m)
            s = ee.Date.fromYMD(y, m, 1)
            e = s.advance(1, "month")
            c = era.filterDate(s, e)
            img = ee.Image.cat([
                c.select("snow_depth_water_equivalent").mean().multiply(1000).rename("swe_mm"),
                c.select("snowmelt_sum").sum().multiply(1000).rename("erime_mm"),
                c.select("total_precipitation_sum").sum().multiply(1000).rename("yagis_mm"),
                modis.filterDate(s, e).mean().rename("kar_ortu_yuzde"),
            ])
            return img.set("ay", s.format("YYYY-MM"))

        imgs = ee.ImageCollection.fromImages(ee.List(aylar).map(ay_img))
        sonuc = imgs.map(lambda im: im.reduceRegions(fc, ee.Reducer.mean(), 5000)
                         .map(lambda f: f.set("ay", im.get("ay")))).flatten()
        feats = _getinfo(sonuc)["features"]
        satir = [{k: f["properties"].get(k) for k in alanlar} for f in feats]
        satir = [s for s in satir if (s["havza"], s["ay"]) not in var]
        _ekle(yol, satir, alanlar)
        print(f"  kar: {y} ({len(satir)} satır)", flush=True)


# ---------------------------------------------------------------- firat
def firat(ee):
    yol = CIKTI / "gee_firat_aylik.csv"
    alanlar = ["bolge", "ay", "kaynak", "su_km2", "kapsama", "gecerli_gozlem"]
    var = _mevcut(yol, ["bolge", "ay", "kaynak"])
    jrc_max = ee.Image("JRC/GSW1_4/GlobalSurfaceWater").select("max_extent").eq(1)
    hazar = ee.Image.constant(1).clip(_kutu(ee, HAZAR_KUTU)).unmask(0, False).Not()  # False: kutu dışı da 0 olsun
    bolgeler = {"Firat_kaskad": _kutu(ee, FIRAT_KUTU), "Keban_kuzey": _kutu(ee, KEBAN_KUTU)}
    maske = jrc_max.And(hazar)
    alan = ee.Image.pixelArea().divide(1e6)

    s2 = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")

    def s2_ay(y, m, geo):
        s = ee.Date.fromYMD(y, m, 1)
        c = s2.filterBounds(geo).filterDate(s, s.advance(1, "month"))

        def hazirla(img):
            scl = img.select("SCL")
            temiz = scl.neq(3).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10)).And(scl.neq(0)).And(scl.neq(1))
            mndwi = img.normalizedDifference(["B3", "B11"]).rename("mndwi")
            return mndwi.updateMask(temiz)

        c2 = c.map(hazirla)
        medyan = c2.median()
        sayi = c2.count()
        img = ee.Image.cat([
            medyan.gt(0).And(maske).multiply(alan).rename("su_km2"),
            sayi.gt(0).And(maske).multiply(alan).rename("gozlenen_km2"),
            maske.multiply(alan).rename("maske_km2"),
            sayi.updateMask(maske).rename("gecerli_gozlem"),
        ])
        return img.reduceRegion(ee.Reducer.sum(), geo, 60, maxPixels=1e10, tileScale=4)

    for bolge, geo in bolgeler.items():
        for y, m in _tamam_aylar(2017):
            ay = f"{y}-{m:02d}"
            if (bolge, ay, "S2") in var:
                continue
            r = _getinfo(ee.Dictionary(s2_ay(y, m, geo)))
            if not r or r.get("maske_km2") in (None, 0):
                print(f"  firat: {bolge} {ay} S2 boş sonuç {r}", flush=True)
                continue
            kap = (r.get("gozlenen_km2") or 0) / r["maske_km2"]
            _ekle(yol, [dict(bolge=bolge, ay=ay, kaynak="S2", su_km2=round(r.get("su_km2") or 0, 2),
                             kapsama=round(kap, 3), gecerli_gozlem=r.get("gecerli_gozlem"))], alanlar)
            print(f"  firat: {bolge} {ay} S2 su={r.get('su_km2') or 0:.0f} km², kapsama={kap:.2f}", flush=True)

        # JRC aylık su geçmişi (1984-2021): uzun geçmiş için
        jrc = ee.ImageCollection("JRC/GSW1_4/MonthlyHistory").filterBounds(geo)
        for y in range(1990, 2022):
            if all((bolge, f"{y}-{m:02d}", "JRC") in var for m in range(1, 13)):
                continue
            yil = jrc.filter(ee.Filter.calendarRange(y, y, "year"))

            def jrc_ay(img):
                w = img.select("water")
                st = ee.Image.cat([w.eq(2).And(maske).multiply(alan).rename("su_km2"),
                                   w.gt(0).And(maske).multiply(alan).rename("gozlenen_km2"),
                                   maske.multiply(alan).rename("maske_km2")])
                return ee.Feature(None, st.reduceRegion(ee.Reducer.sum(), geo, 60, maxPixels=1e10, tileScale=4)) \
                    .set("ay", img.date().format("YYYY-MM"))

            feats = _getinfo(ee.FeatureCollection(yil.map(jrc_ay)))["features"]
            satir = []
            for f in feats:
                p = f["properties"]
                if (bolge, p["ay"], "JRC") in var or not p.get("maske_km2"):
                    continue
                satir.append(dict(bolge=bolge, ay=p["ay"], kaynak="JRC", su_km2=round(p.get("su_km2") or 0, 2),
                                  kapsama=round((p.get("gozlenen_km2") or 0) / p["maske_km2"], 3)))
            _ekle(yol, satir, alanlar)
            print(f"  firat: {bolge} {y} JRC ({len(satir)} ay)", flush=True)


# ---------------------------------------------------------------- don
def don(ee):
    yol = CIKTI / "gee_don_yillik.csv"
    alanlar = ["yil", "don_derece_saat", "en_dusuk_c", "don_saati"]
    var = {k[0] for k in _mevcut(yol, ["yil"])}
    geo = _kutu(ee, FINDIK_KUTU)
    alcak = ee.Image("USGS/SRTMGL1_003").lt(800)   # fındık bahçeleri ağırlıkla 0-750 m
    saatlik = ee.ImageCollection("ECMWF/ERA5_LAND/HOURLY").select("temperature_2m")
    for y in range(2000, date.today().year + 1):
        if str(y) in var or (y == date.today().year and date.today() < date(y, 5, 1)):
            continue
        c = saatlik.filterDate(f"{y}-03-01", f"{y}-05-01")
        dh = c.map(lambda i: i.multiply(-1).add(273.15).max(0)).sum().rename("dh")
        saat = c.map(lambda i: i.lt(273.15)).sum().rename("saat")
        mn = c.min().subtract(273.15).rename("mn")
        r = _getinfo(ee.Image.cat([dh, saat, mn]).updateMask(alcak)
                     .reduceRegion(ee.Reducer.mean(), geo, 11132, maxPixels=1e9))
        _ekle(yol, [dict(yil=y, don_derece_saat=round(r.get("dh") or 0, 2), en_dusuk_c=round(r.get("mn") or 0, 2),
                         don_saati=round(r.get("saat") or 0, 1))], alanlar)
        print(f"  don: {y} derece-saat={r.get('dh') or 0:.1f}", flush=True)


# ---------------------------------------------------------------- maden
def _csv_oku(yol):
    if not yol.exists():
        return []
    with open(yol, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def maden(ee):
    sahalar = [s for s in _csv_oku(ARASTIRMA / "tralt_sahalar.csv") if s.get("lat") and s.get("lon")]
    if not sahalar:
        print("  maden: data/reference/tralt_sahalar.csv yok, atlandı")
        return
    yol = CIKTI / "gee_maden_aylik.csv"
    alanlar = ["saha", "tur", "ay", "ciplak_km2", "bsi_ort", "ndvi_ort", "kapsama"]
    var = _mevcut(yol, ["saha", "tur", "ay"])
    s2 = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
    alan = ee.Image.pixelArea().divide(1e6)
    for s in sahalar:
        geo = ee.Geometry.Point([float(s["lon"]), float(s["lat"])]).buffer(float(s.get("yaricap_m") or 1500))
        for y, m in _tamam_aylar(2017):
            ay = f"{y}-{m:02d}"
            if (s["saha"], s.get("tur", ""), ay) in var:
                continue
            st = ee.Date.fromYMD(y, m, 1)
            c = s2.filterBounds(geo).filterDate(st, st.advance(1, "month"))

            def hazirla(img):
                scl = img.select("SCL")
                temiz = scl.eq(4).Or(scl.eq(5)).Or(scl.eq(6)).Or(scl.eq(7)).Or(scl.eq(11))
                b = img.select(["B2", "B4", "B8", "B11"]).divide(10000)
                bsi = b.expression("((s+r)-(n+bl))/((s+r)+(n+bl))",
                                   {"s": b.select("B11"), "r": b.select("B4"), "n": b.select("B8"), "bl": b.select("B2")})
                ndvi = img.normalizedDifference(["B8", "B4"])
                return ee.Image.cat([bsi.rename("bsi"), ndvi.rename("ndvi")]).updateMask(temiz)

            bos = ee.Image.constant([0, 0]).rename(["bsi", "ndvi"]).updateMask(0)
            med = ee.Image(ee.Algorithms.If(c.size().gt(0), c.map(hazirla).median(), bos))
            ciplak = med.select("bsi").gt(0.05).And(med.select("ndvi").lt(0.2))
            img = ee.Image.cat([ciplak.multiply(alan).rename("ciplak_km2"), med.select("bsi").mask().multiply(alan).rename("gozlenen"),
                                ee.Image.constant(1).multiply(alan).rename("toplam")])
            r1 = img.reduceRegion(ee.Reducer.sum(), geo, 10, maxPixels=1e9)
            r2 = med.reduceRegion(ee.Reducer.mean(), geo, 10, maxPixels=1e9)
            r = _getinfo(ee.Dictionary(r1).combine(r2))
            if not r or not r.get("toplam"):
                continue
            _ekle(yol, [dict(saha=s["saha"], tur=s.get("tur", ""), ay=ay, ciplak_km2=round(r.get("ciplak_km2") or 0, 4),
                             bsi_ort=r.get("bsi"), ndvi_ort=r.get("ndvi"),
                             kapsama=round((r.get("gozlenen") or 0) / r["toplam"], 3))], alanlar)
        print(f"  maden: {s['saha']} tamam", flush=True)


# ---------------------------------------------------------------- celik
def celik(ee):
    satirlar = [t for t in _csv_oku(ARASTIRMA / "celik_tesisler.csv") if t.get("lat") and t.get("lon")]
    # Birimlerin gerçek konumu bilinmiyor (hepsi tesis merkezinde); ölçüm tesis düzeyinde yapılır:
    # tesisin bbox satırı varsa o dikdörtgen, yoksa tek bir merkez+yarıçap.
    tesisler, gorulen = [], set()
    for t in sorted(satirlar, key=lambda r: 0 if r.get("bbox_min_lat") else 1):
        if t["tesis"] in gorulen:
            continue
        gorulen.add(t["tesis"])
        tesisler.append(dict(t, birim="tesis"))
    if not tesisler:
        print("  celik: data/reference/celik_tesisler.csv yok, atlandı")
        return
    # v2: bulut oranı Cloud Score+ ile (QA60 2022-02 – 2024-01 arasında boş geliyor)
    yol = CIKTI / "gee_celik_sahne_v2.csv"
    alanlar = ["tesis", "birim", "tarih", "sicak_piksel", "sicak_yogunluk", "bulut_orani", "bulut_qa60"]
    var = _mevcut(yol, ["tesis", "birim", "tarih"])
    # Sıcak metal SWIR'da parlar: B12 (2,2 µm) belirgin şekilde B11'den (1,6 µm) yüksek.
    # Ham TOA (L1C) kullanılır; L2A atmosfer düzeltmesi sıcak pikselleri bozabilir.
    csp = ee.ImageCollection("GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED")
    s2 = ee.ImageCollection("COPERNICUS/S2_HARMONIZED").linkCollection(csp, ["cs"])
    for t in tesisler:
        if t.get("bbox_min_lat"):
            geo = ee.Geometry.Rectangle([float(t["bbox_min_lon"]), float(t["bbox_min_lat"]),
                                         float(t["bbox_max_lon"]), float(t["bbox_max_lat"])])
        else:
            geo = ee.Geometry.Point([float(t["lon"]), float(t["lat"])]).buffer(float(t.get("yaricap_m") or 1500))
        yillar_var = {k[2][:4] for k in var if k[0] == t["tesis"] and k[1] == t.get("birim", "")}
        for y in range(2017, date.today().year + 1):
            if str(y) in yillar_var and y < date.today().year:
                continue  # geçmiş yıl zaten indirilmiş
            c = s2.filterBounds(geo).filterDate(f"{y}-01-01", f"{y + 1}-01-01")

            def olc(img):
                b11 = img.select("B11").divide(10000)
                b12 = img.select("B12").divide(10000)
                nhi = b12.subtract(b11).divide(b12.add(b11))
                sicak = nhi.gt(0.1).And(b12.gt(0.25))
                bulut = img.select("cs").lt(0.6)
                qa60 = img.select("QA60").gt(0)
                toplam = ee.Image.cat([sicak.rename("sicak"), sicak.multiply(b12).rename("yog")]) \
                    .reduceRegion(ee.Reducer.sum(), geo, 20, maxPixels=1e8)
                ort = ee.Image.cat([bulut.rename("bulut"), qa60.rename("qa60")]) \
                    .reduceRegion(ee.Reducer.mean(), geo, 60, maxPixels=1e8)
                return ee.Feature(None, {"tarih": img.date().format("YYYY-MM-dd"),
                                         "sicak": toplam.get("sicak"), "yog": toplam.get("yog"),
                                         "bulut": ort.get("bulut"), "qa60": ort.get("qa60")})

            feats = _getinfo(ee.FeatureCollection(c.map(olc)))["features"]
            satir = []
            for f in feats:
                p = f["properties"]
                if (t["tesis"], t.get("birim", ""), p["tarih"]) in var:
                    continue
                satir.append(dict(tesis=t["tesis"], birim=t.get("birim", ""), tarih=p["tarih"],
                                  sicak_piksel=p.get("sicak"), sicak_yogunluk=p.get("yog"), bulut_orani=p.get("bulut"),
                                  bulut_qa60=p.get("qa60")))
            _ekle(yol, satir, alanlar)
        print(f"  celik: {t['tesis']} / {t.get('birim', '')} tamam", flush=True)


AKISLAR = {"kar": kar, "firat": firat, "don": don, "maden": maden, "celik": celik}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("akislar", nargs="*", default=list(AKISLAR))
    p.add_argument("--proje", required=True)
    a = p.parse_args()
    CIKTI.mkdir(exist_ok=True)
    ee = baslat(a.proje)
    hata = 0
    for ad in a.akislar:
        print(f"[GEE] {ad} başlıyor", flush=True)
        try:
            AKISLAR[ad](ee)
            print(f"[GEE] {ad} bitti", flush=True)
        except Exception as e:
            print(f"[GEE] {ad} HATA: {e}", flush=True)
            hata += 1
    return 1 if hata else 0


if __name__ == "__main__":
    sys.exit(main())
