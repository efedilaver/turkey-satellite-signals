#!/usr/bin/env python3
"""
T-I1 veri adımı: VIIRS aylık gece ışığı, il bazında toplam (kural: ARASTIRMA_PLANI.md).
  python gece_isik.py        # ~5-10 dk
Çıktı: cikti/gece_isik_il_aylik.csv
"""
import csv, sys, time
from pathlib import Path

KOK = Path(__file__).resolve().parents[2]  # depo kökü (src/collect/ -> kök)
CIKTI = KOK / "cikti" / "gece_isik_il_aylik.csv"
ESIK = 0.5


def proje_adi():
    for s in (KOK / ".env").read_text(encoding="utf-8").splitlines():
        if s.startswith("GEE_PROJECT="):
            return s.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit(".env içinde GEE_PROJECT yok")


def main():
    import ee
    try:
        ee.Initialize(project=proje_adi())
    except Exception:
        ee.Authenticate(); ee.Initialize(project=proje_adi())
    iller = ee.FeatureCollection("FAO/GAUL/2015/level1").filter(ee.Filter.eq("ADM0_NAME", "Turkey"))
    print("İl sayısı (GAUL):", iller.size().getInfo(), flush=True)
    col = ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG")
    satir = []
    for yil in range(2014, 2027):
        c = col.filterDate(f"{yil}-01-01", f"{yil + 1}-01-01")
        if c.size().getInfo() == 0:
            continue

        def olc(img):
            rad = img.select("avg_rad")
            cvg = img.select("cf_cvg")
            isik = rad.where(rad.lt(ESIK).Or(cvg.eq(0)), 0).rename("isik")
            kaps = cvg.gt(0).rename("kaps")
            bir = ee.Image.constant(1).rename("bir")
            st = isik.addBands(kaps).addBands(bir)
            fc = st.reduceRegions(iller, ee.Reducer.sum(), 463.83)
            ay = img.date().format("YYYY-MM")
            return fc.map(lambda f: ee.Feature(None, {"ay": ay, "il": f.get("ADM1_NAME"), "il_kod": f.get("ADM1_CODE"),
                                                       "isik": f.get("isik"), "kaps": f.get("kaps"), "bir": f.get("bir")}))

        t0 = time.time()
        feats = c.map(olc).flatten().getInfo()["features"]
        for f in feats:
            satir.append(f["properties"])
        print(f"{yil}: {len(feats)} satır ({time.time() - t0:.0f} sn)", flush=True)
    CIKTI.parent.mkdir(exist_ok=True)
    with open(CIKTI, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["ay", "il", "il_kod", "isik", "kaps", "bir"])
        w.writeheader(); w.writerows(satir)
    print(f"Yazıldı: {CIKTI} ({len(satir)} satır)")


if __name__ == "__main__":
    main()
