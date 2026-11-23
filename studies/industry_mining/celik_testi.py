#!/usr/bin/env python3
"""
T-C1: Sentinel-2 sıcak piksel ölçüsü çelik üretimini izliyor mu? (kural: ARASTIRMA_PLANI.md)
Girdi: cikti/gee_celik_sahne_v2.csv, data/reference/celik_uretim.csv
Çıktı: cikti/celik_testi.csv, cikti/celik_testi.png
"""
from pathlib import Path

import numpy as np
import pandas as pd

CIKTI, AR = Path("cikti"), Path("data/reference")
ESLE = {"Isdemir_Payas": "Isdemir", "Erdemir_Eregli": "Erdemir_Eregli_tesisi_TURETILMIS"}


def ceyreklik_olcu(c):
    c = c[c["bulut_orani"] < 0.10].copy()
    c["donem"] = pd.PeriodIndex(pd.to_datetime(c["tarih"]), freq="Q").astype(str)
    g = c.groupby(["tesis", "donem"]).agg(olcu=("sicak_yogunluk", "mean"), sahne=("sicak_yogunluk", "size"))
    return g[g["sahne"] >= 3].reset_index()


def main():
    c = pd.read_csv(CIKTI / "gee_celik_sahne_v2.csv")
    u = pd.read_csv(AR / "celik_uretim.csv")
    u = u[u["donem"].str.contains("Q") & (u["tur"] == "sivi_celik")].copy()
    u["donem"] = u["donem"].str.replace("Q", "Q")
    q = ceyreklik_olcu(c)
    satir, tablo = [], []
    for tesis, sirket in ESLE.items():
        a = q[q["tesis"] == tesis].merge(u[u["sirket"] == sirket][["donem", "uretim_ton"]], on="donem")
        a = a[(a["donem"] >= "2018Q1") & (a["donem"] <= "2026Q2")]
        r = np.corrcoef(a["olcu"], a["uretim_ton"])[0, 1]
        rd = np.corrcoef(a["olcu"].diff().dropna(), a["uretim_ton"].diff().dropna())[0, 1]
        satir.append(dict(tesis=tesis, n=len(a), r=r, r_degisim=rd))
        tablo.append(a.assign(tesis=tesis))
        print(f"{tesis:16s} n={len(a):2d}  r(düzey)={r:+.2f}  r(çeyrekten çeyreğe değişim, rapor)={rd:+.2f}")
    t = pd.concat(tablo)

    # Deprem duruşu kontrolü (İsdemir, 2023-02-06 → 2023-04-24)
    ci = c[(c["tesis"] == "Isdemir_Payas") & (c["bulut_orani"] < 0.10)].copy()
    ci["tarih"] = pd.to_datetime(ci["tarih"])
    dur = ci[(ci["tarih"] >= "2023-02-06") & (ci["tarih"] <= "2023-04-24")]["sicak_yogunluk"]
    ref = ci[ci["tarih"].dt.year == 2022]["sicak_yogunluk"].mean()
    oran = dur.mean() / ref
    print(f"\nİsdemir deprem duruşu: {len(dur)} temiz sahne, ortalama = 2022'nin %{100 * oran:.0f}'i (eşik < %20)")

    gec = all(s["r"] >= 0.5 for s in satir) and oran < 0.2
    print(f"\nT-C1 SONUÇ: {'GEÇTİ' if gec else 'KALDI'}")
    print("\nÇeyreklik tablo:")
    print(t.pivot_table(index="donem", columns="tesis", values=["olcu", "uretim_ton"]).round(0).to_string())
    t.to_csv(CIKTI / "celik_testi.csv", index=False)

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(2, 1, figsize=(10, 7), sharex=False)
        for i, tesis in enumerate(ESLE):
            a = t[t["tesis"] == tesis]
            x = pd.PeriodIndex(a["donem"], freq="Q").to_timestamp()
            ax[i].plot(x, a["uretim_ton"] / 1000, color="#1f4e79", label="Açıklanan üretim (bin ton)")
            ax2 = ax[i].twinx()
            ax2.plot(x, a["olcu"], color="#c55a11", label="Uydu sıcak piksel ölçüsü")
            ax[i].set_title(f"{tesis}: r = {next(s['r'] for s in satir if s['tesis'] == tesis):+.2f}")
            ax[i].legend(loc="lower left"); ax2.legend(loc="lower right")
        fig.tight_layout()
        fig.savefig(CIKTI / "celik_testi.png", dpi=120)
    except Exception as e:
        print("grafik çizilemedi:", e)


if __name__ == "__main__":
    main()
