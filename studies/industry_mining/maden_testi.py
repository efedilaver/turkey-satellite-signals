#!/usr/bin/env python3
"""
T-M1: TRALT yığın liçi / açık ocak sahalarında uydudan ölçülen çıplak alan değişimi,
sahanın bir sonraki çeyrekteki üretim değişimini öngörüyor mu? Kural: ARASTIRMA_PLANI.md
Girdi: cikti/gee_maden_aylik.csv, data/reference/tralt_uretim.csv
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

CIKTI, AR = Path("cikti"), Path("data/reference")
SAHA = {"Himmetdede": "himmetdede_lic_oz", "Kaymaz": "kaymaz_tesis_oz"}


def main():
    m = pd.read_csv(CIKTI / "gee_maden_aylik.csv")
    m = m[m["kapsama"] >= 0.6].copy()
    m["donem"] = pd.PeriodIndex(pd.to_datetime(m["ay"] + "-01"), freq="Q")
    u = pd.read_csv(AR / "tralt_uretim.csv")
    u = u[u["donem_tipi"] == "ceyrek"].copy()
    u["donem"] = pd.PeriodIndex(u["donem"], freq="Q")
    u = u.set_index("donem")
    tum = []
    for saha, sut in SAHA.items():
        a = m[m["saha"].str.startswith(saha)].groupby("donem")["ciplak_km2"].mean()
        p = u[sut]
        d = pd.DataFrame({"alan": a, "uretim": p})
        d["d_alan"] = d["alan"].diff()
        d["d_uretim_sonraki"] = d["uretim"].shift(-1) - d["uretim"]
        d["sonraki_q"] = [q + 1 for q in d.index]
        # 4. çeyrek içeren üretim farkları hariç (kayıtta belirtildiği gibi)
        d = d[[(q.quarter != 4) and ((q + 1).quarter != 4) for q in d.index]]
        d = d[(d.index >= pd.Period("2021Q1", "Q")) & (d.index <= pd.Period("2026Q1", "Q"))]
        d = d.dropna(subset=["d_alan", "d_uretim_sonraki"]).assign(saha=saha)
        rho = spearmanr(d["d_alan"], d["d_uretim_sonraki"]).correlation if len(d) > 3 else np.nan
        print(f"  {saha:11s} n={len(d):2d}  Spearman = {rho:+.2f}")
        tum.append(d)
    t = pd.concat(tum)
    rho = spearmanr(t["d_alan"], t["d_uretim_sonraki"]).correlation
    print(f"\nT-M1 (iki saha birlikte) n={len(t)}  Spearman = {rho:+.2f}   eşik ≥ +0,40 -> "
          f"{'GEÇTİ' if rho >= 0.40 else 'KALDI'}")

    # Kontrol: Mastra 2024-04-30'da kapandı
    ms = m[m["saha"].str.startswith("Mastra")].set_index("donem")["ciplak_km2"].groupby(level=0).mean()
    once, sonra = ms[ms.index < pd.Period("2024Q2", "Q")].tail(8).mean(), ms[ms.index > pd.Period("2024Q2", "Q")].mean()
    print(f"Kontrol – Mastra çıplak alan: kapanış öncesi 2 yıl {once:.3f} km², kapanış sonrası {sonra:.3f} km²")

    # Mollakara (ileriye dönük izleme)
    mk = m[m["saha"].str.startswith("Mollakara")].set_index("ay")["ciplak_km2"]
    print("\nMollakara çıplak alan (km², son 12 ay):")
    print("  " + "  ".join(f"{k}:{v:.2f}" for k, v in mk.tail(12).items()))
    t.to_csv(CIKTI / "maden_testi.csv")


if __name__ == "__main__":
    main()
