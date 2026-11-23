#!/usr/bin/env python3
"""
T-F1: Fırat kaskadının (Keban+Karakaya+Atatürk) uydudan ölçülen su alanı değişimi,
sonraki 3 ayın barajlı hidro üretimini, o ayın hidrosunun ötesinde öngörüyor mu?
Kural: ARASTIRMA_PLANI.md. Girdi: cikti/gee_firat_aylik.csv, cikti/epias_gunluk.csv,
cikti/santral_gunluk.csv (varsa; Fırat santralleri için ek rapor)
"""
from pathlib import Path

import numpy as np
import pandas as pd

CIKTI = Path("cikti")
FIRAT_ID = {641: "Atatürk", 979: "Keban", 986: "Karakaya"}


def ay_anomali(s: pd.Series) -> pd.Series:
    """log(değer / aynı takvim ayının diğer yıllardaki medyanı)"""
    out = {}
    for t, v in s.items():
        diger = s[(s.index.month == t.month) & (s.index.year != t.year)]
        out[t] = np.log(v / diger.median()) if len(diger) >= 3 and v > 0 else np.nan
    return pd.Series(out)


def ileri3_anomali(s: pd.Series) -> pd.Series:
    """m+1..m+3 toplamı, aynı pencerenin diğer yıllardaki medyanına göre log."""
    ileri = s.shift(-1) + s.shift(-2) + s.shift(-3)
    return ay_anomali(ileri.dropna())


def kismi(x, y, z):
    rx = x - np.polyval(np.polyfit(z, x, 1), z)
    ry = y - np.polyval(np.polyfit(z, y, 1), z)
    return np.corrcoef(rx, ry)[0, 1]


def analiz(ad, hidro, alan):
    d = pd.DataFrame({"alan": alan, "hid_an": ay_anomali(hidro), "ileri": ileri3_anomali(hidro)})
    d["d_alan"] = np.log(d["alan"]).diff()
    d = d.dropna()
    r = kismi(d["d_alan"], d["ileri"], d["hid_an"])
    r_ham = np.corrcoef(d["d_alan"], d["ileri"])[0, 1]
    print(f"  {ad:34s} n={len(d):3d}  kısmi r = {r:+.2f}   (ham r = {r_ham:+.2f})")
    return r, d


def main():
    f = pd.read_csv(CIKTI / "gee_firat_aylik.csv")
    f = f[(f["kaynak"] == "S2") & (f["bolge"] == "Firat_kaskad")].copy()
    f["t"] = pd.to_datetime(f["ay"] + "-01")
    f = f.set_index("t")
    alan = f.loc[f["kapsama"] >= 0.8, "su_km2"]
    # kapsama düşük ay çıkarılınca bir sonraki ayın değişimi iki aylık olur; bunu önlemek için
    # alanı tam aylık dizine yerleştir (eksik ay NaN kalır, değişimi de NaN olur)
    alan = alan.reindex(pd.date_range(f.index.min(), f.index.max(), freq="MS"))

    g = pd.read_csv(CIKTI / "epias_gunluk.csv", parse_dates=["tarih"], index_col="tarih")
    hid = g["dammedHydro_gwh"].resample("MS").sum()
    hid = hid[hid.index <= "2026-09-01"]

    print("T-F1 (karar: Türkiye barajlı hidro, kısmi r ≥ +0,30):")
    r, d = analiz("Türkiye barajlı hidro", hid, alan)
    print(f"  SONUÇ: {'GEÇTİ' if r >= 0.30 else 'KALDI'}")

    s_yol = next((y for y in (CIKTI / "santral_gunluk.csv", CIKTI / "ara" / "santral_gunluk.csv") if y.exists()), None)
    if s_yol:
        s = pd.read_csv(s_yol, parse_dates=["gun"])
        s = s[s["powerPlantId"].isin(FIRAT_ID)]
        fh = s.set_index("gun")["mwh"].resample("MS").sum() / 1000
        son = s.groupby("powerPlantId")["gun"].max().min()
        fh = fh[fh.index < son.replace(day=1)]
        print("\nEk rapor (karar vermez): yalnız Keban+Karakaya+Atatürk üretimi")
        analiz("Fırat 3 santral üretimi", fh, alan)

    d.to_csv(CIKTI / "firat_testi.csv")


if __name__ == "__main__":
    main()
