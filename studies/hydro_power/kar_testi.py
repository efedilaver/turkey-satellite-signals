#!/usr/bin/env python3
"""
T-A1 / T-A2: kar verisi 1 Mart'ta bahar-yaz hidrosunu ve hidro hisselerini öngörüyor mu?
Kurallar ARASTIRMA_PLANI.md'de veri gelmeden kaydedildi.
Girdi: cikti/epias_gunluk.csv, cikti/hisse_gunluk.csv, cikti/gee_kar_aylik.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mevsimlik_test import donem_getirisi, veriler  # noqa: E402

CIKTI = Path("cikti")
YILLAR = range(2018, 2027)
HAVZA = ["Firat_Karasu", "Firat_Murat", "Dicle_Ust", "Coruh", "Seyhan_Ceyhan"]


def log_medyan_anomali(s: pd.Series) -> pd.Series:
    return pd.Series({y: np.log(v / s.drop(y).median()) for y, v in s.items()})


def kismi(x, y, z):
    rx = x - np.polyval(np.polyfit(z, x, 1), z)
    ry = y - np.polyval(np.polyfit(z, y, 1), z)
    return np.corrcoef(rx, ry)[0, 1], rx


def main():
    g, p = veriler()
    h = g["dammedHydro_gwh"]
    satir = []
    for y in YILLAR:
        kis = h[f"{y - 1}-12-01":f"{y}-02-28"].sum()
        by = h[f"{y}-03-01":f"{y}-07-31"]
        ptf = g.loc[f"{y}-03-01":f"{y}-07-31", "ptf_usd"].mean()
        ptf0 = g.loc[f"{y - 1}-03-01":f"{y - 1}-07-31", "ptf_usd"].mean()
        f, n = donem_getirisi(p, pd.Timestamp(f"{y}-03-01"), pd.Timestamp(f"{y}-07-31"))
        satir.append(dict(yil=y, kis_gwh=kis, by_gwh=by.sum() * 153 / len(by), by_gun=len(by),
                          ptf=np.log(ptf / ptf0), sepet=f, sepet_hisse=n))
    d = pd.DataFrame(satir).set_index("yil")
    d["kis"] = log_medyan_anomali(d["kis_gwh"])
    d["bahar_yaz"] = log_medyan_anomali(d["by_gwh"])

    # --- kar sinyali: 5 havzanın Şubat ortalama SWE'si, yalnızca geçmiş Şubatlara göre
    k = pd.read_csv(CIKTI / "gee_kar_aylik.csv")
    k = k[k["havza"].isin(HAVZA)]
    k["yil"] = k["ay"].str[:4].astype(int)
    k["ayno"] = k["ay"].str[5:7].astype(int)
    sub = k[k["ayno"] == 2].pivot_table(index="yil", columns="havza", values="swe_mm").mean(axis=1)
    d["kar"] = [np.log(sub[y] / sub[sub.index < y].median()) for y in d.index]
    # ikincil: MODIS kar örtüsü (Şubat) ve kış yağışı (Ara–Şub)
    ort = k[k["ayno"] == 2].pivot_table(index="yil", columns="havza", values="kar_ortu_yuzde").mean(axis=1)
    d["modis"] = [np.log(ort[y] / ort[ort.index < y].median()) for y in d.index]
    yag = k.assign(su_yili=np.where(k["ayno"] == 12, k["yil"] + 1, k["yil"]))
    yag = yag[yag["ayno"].isin([12, 1, 2])].groupby(["su_yili", "havza"])["yagis_mm"].sum().unstack().mean(axis=1)
    d["kis_yagis"] = [np.log(yag[y] / yag[(yag.index < y) & (yag.index >= 2002)].median()) for y in d.index]

    pd.set_option("display.width", 160)
    print(d[["kis", "bahar_yaz", "kar", "modis", "kis_yagis", "ptf", "sepet", "sepet_hisse"]].round(2).to_string())

    r2 = np.corrcoef(d["kis"], d["bahar_yaz"])[0, 1] ** 2
    art_by = d["bahar_yaz"] - np.polyval(np.polyfit(d["kis"], d["bahar_yaz"], 1), d["kis"])
    print(f"\nT-A1 kontrol: r²(kis→bahar_yaz)={r2:.2f}  artık~PTF r={np.corrcoef(art_by, d['ptf'])[0,1]:+.2f}  "
          f"artık~sepet r={np.corrcoef(art_by, d['sepet'])[0,1]:+.2f}")

    print("\nT-A2 (karar):")
    rk, kar_art = kismi(d["kar"], d["bahar_yaz"], d["kis"])
    rs = np.corrcoef(kar_art, d["sepet"])[0, 1]
    rp = np.corrcoef(kar_art, d["ptf"])[0, 1]
    print(f"  (i)  kısmi r(kar, bahar_yaz | kis) = {rk:+.2f}   eşik ≥ +0,50 -> {'GEÇTİ' if rk >= 0.5 else 'KALDI'}")
    print(f"  (ii) r(kar artığı, sepet)          = {rs:+.2f}   eşik ≥ +0,30 -> {'GEÇTİ' if rs >= 0.3 else 'KALDI'}")
    print(f"       r(kar artığı, PTF) (yalnız rapor) = {rp:+.2f}")
    print(f"  SONUÇ: {'GEÇTİ' if rk >= 0.5 and rs >= 0.3 else 'KALDI'}")
    print("\nİkincil (karar vermez):")
    for ad in ["modis", "kis_yagis"]:
        r, a = kismi(d[ad], d["bahar_yaz"], d["kis"])
        print(f"  {ad:10s} kısmi r(·, bahar_yaz | kis) = {r:+.2f};  artık~sepet r = {np.corrcoef(a, d['sepet'])[0,1]:+.2f}")
    print(f"  kar ham r(kar, bahar_yaz) = {np.corrcoef(d['kar'], d['bahar_yaz'])[0,1]:+.2f}")
    # Birini-dışarıda-bırak duyarlılığı
    print("\nDuyarlılık (her yıl dışarıda bırakılınca kısmi r):")
    print("  " + "  ".join(f"{y}:{kismi(d['kar'].drop(y), d['bahar_yaz'].drop(y), d['kis'].drop(y))[0]:+.2f}" for y in d.index))
    d.to_csv(CIKTI / "kar_testi.csv")


if __name__ == "__main__":
    main()
