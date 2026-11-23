#!/usr/bin/env python3
"""
T-C2 veri adımı (kural: ARASTIRMA_PLANI.md): Landsat 8+9 yüzey sıcaklığıyla çelik tesisi faaliyeti.
Her sahne için: tesis kutusunda açık piksellerin p90 sıcaklığı − çevre halkası (2–5 km) medyanı.

  python celik_landsat.py            # tüm tesisler, ~5-15 dk
Çıktı: cikti/celik_landsat_sahne.csv
Earth Engine: .env'deki GEE_PROJECT; ilk seferde tarayıcıda giriş isteyebilir.
"""
import csv, sys, time
from pathlib import Path

KOK = Path(__file__).resolve().parents[2]  # depo kökü (src/collect/ -> kök)
CIKTI = KOK / "cikti" / "celik_landsat_sahne.csv"
TESISLER = {  # (min_lon, min_lat, max_lon, max_lat)
    "IZMDC_Aliaga": (26.9263, 38.7384, 26.9321, 38.7419),
    "Isdemir_Payas": (36.180, 36.712, 36.225, 36.752),
    "Erdemir_Eregli": (31.398, 41.240, 31.445, 41.272),
    "Kardemir_Karabuk": (32.612, 41.170, 32.648, 41.195),
}
BAS, SON = "2013-04-01", "2026-10-01"


def proje_adi():
    p = KOK / ".env"
    for s in p.read_text(encoding="utf-8").splitlines():
        if s.startswith("GEE_PROJECT="):
            return s.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit(".env içinde GEE_PROJECT yok")


def main():
    import ee
    proje = proje_adi()
    try:
        ee.Initialize(project=proje)
    except Exception:
        ee.Authenticate()
        ee.Initialize(project=proje)

    col = (ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
           .merge(ee.ImageCollection("LANDSAT/LC09/C02/T1_L2"))
           .filterDate(BAS, SON))
    BULUT = (1 << 1) | (1 << 2) | (1 << 3) | (1 << 4) | (1 << 5)  # genişletilmiş bulut, sirrus, bulut, gölge, kar

    satirlar = []
    for ad, b in TESISLER.items():
        kutu = ee.Geometry.Rectangle(list(b))
        halka = kutu.buffer(5000).difference(kutu.buffer(2000), 10)

        def olc(img):
            st = img.select("ST_B10").multiply(0.00341802).add(149.0)
            qa = img.select("QA_PIXEL")
            acik = qa.bitwiseAnd(BULUT).eq(0).And(qa.bitwiseAnd(1).eq(0))
            su = qa.bitwiseAnd(1 << 7).neq(0)
            t = st.updateMask(acik).reduceRegion(
                ee.Reducer.percentile([50, 90]).combine(ee.Reducer.count(), sharedInputs=True),
                kutu, 30, maxPixels=1e9)
            toplam = ee.Image.constant(1).clip(kutu).reduceRegion(ee.Reducer.count(), kutu, 30, maxPixels=1e9)
            h = st.updateMask(acik.And(su.Not())).reduceRegion(
                ee.Reducer.median().combine(ee.Reducer.count(), sharedInputs=True), halka, 30, maxPixels=1e9)
            return ee.Feature(None, {
                "tarih": img.date().format("YYYY-MM-dd"),
                "uydu": img.get("SPACECRAFT_ID"),
                "tesis_p50": t.get("ST_B10_p50"), "tesis_p90": t.get("ST_B10_p90"),
                "tesis_acik_n": t.get("ST_B10_count"), "tesis_toplam_n": toplam.get("constant"),
                "halka_med": h.get("ST_B10_median"), "halka_n": h.get("ST_B10_count"),
                "bulut_sahne": img.get("CLOUD_COVER"),
            })

        fc = col.filterBounds(kutu).map(olc)
        n = fc.size().getInfo()
        print(f"{ad}: {n} sahne, indiriliyor...", flush=True)
        t0 = time.time()
        feats = fc.getInfo()["features"]
        for f in feats:
            p = f["properties"]; p["tesis"] = ad; satirlar.append(p)
        print(f"  tamam ({time.time() - t0:.0f} sn)", flush=True)

    CIKTI.parent.mkdir(exist_ok=True)
    alan = ["tesis", "tarih", "uydu", "tesis_p50", "tesis_p90", "tesis_acik_n", "tesis_toplam_n",
            "halka_med", "halka_n", "bulut_sahne"]
    with open(CIKTI, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=alan, extrasaction="ignore")
        w.writeheader(); w.writerows(satirlar)
    print(f"Yazıldı: {CIKTI} ({len(satirlar)} satır)")


if __name__ == "__main__":
    main()
