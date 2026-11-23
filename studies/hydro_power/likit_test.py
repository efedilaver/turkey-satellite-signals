#!/usr/bin/env python3
"""
T-L1 / T-L2 (kural: ARASTIRMA_PLANI.md): çeyreğin hidro bolluğunu kusursuz bilmek,
elektrik tüketicisi (G1) ve termik üretici (G2) hisselerde para kazandırır mıydı?
Girdi: cikti/epias_gunluk.csv, cikti/hisse_gunluk.csv (hacim_tl sütunuyla)
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mevsimlik_test import anomali, veriler  # noqa: E402

CIKTI = Path("cikti")
GRUPLAR = {"G1_tuketici": (["IZMDC", "CEMTS"], +1),
           "G2_termik": (["ODAS", "CANTE", "AKSEN", "IZENR"], -1)}
MALIYET = 0.002
LIKIDITE_ESIK = 10e6  # TL, son 1 yıl günlük medyan


def likit_hisseler(hisseler):
    h = pd.read_csv(CIKTI / "hisse_gunluk.csv", parse_dates=["tarih"])
    son = h["tarih"].max()
    h = h[h["tarih"] > son - pd.Timedelta(days=365)]
    med = h.groupby("sembol")["hacim_tl"].median()
    print("  Son 1 yıl günlük medyan işlem hacmi (milyon TL): "
          + ", ".join(f"{s} {med.get(s, np.nan) / 1e6:.0f}" for s in hisseler))
    return [s for s in hisseler if med.get(s, 0) >= LIKIDITE_ESIK]


def grup_getirisi(p, hisseler, bas, son):
    once = p[p.index < bas].tail(1)
    sonra = p[p.index <= son].tail(1)
    if once.empty or sonra.empty:
        return np.nan, 0
    var = [s for s in hisseler if s in p.columns and pd.notna(once.iloc[0][s])]
    if not var:
        return np.nan, 0
    r = np.log(sonra.iloc[0][var] / once.iloc[0][var]) - np.log(sonra.iloc[0]["XU100"] / once.iloc[0]["XU100"])
    return float(r.mean()), len(var)


def strateji(fazla, sinyal):
    """sinyal True: grupta ol, False: BIST100 (fazla getiri 0). Değişim başına maliyet."""
    fazla, sinyal = np.asarray(fazla), np.asarray(sinyal, bool)
    degisim = np.abs(np.diff(np.r_[0, sinyal.astype(int)])).sum()
    return fazla[sinyal].sum() - MALIYET * degisim


def kaydirma(fazla, sinyal):
    deger = strateji(fazla, sinyal)
    kopya = [strateji(fazla, np.roll(sinyal, k)) for k in range(1, len(fazla))]
    return 100 * np.mean(np.array(kopya) < deger), deger


def main():
    g, p = veriler()
    son_tam = (g.index.max() + pd.Timedelta(days=1)).to_period("Q") - 1
    gq = g[g.index.to_period("Q") <= son_tam]
    hid = gq["dammedHydro_gwh"].groupby([gq.index.year, gq.index.quarter]).sum()
    ptf = gq["ptf_usd"].groupby([gq.index.year, gq.index.quarter]).mean()
    an = anomali(hid)
    sonuc = []
    for ad, (aday, yon) in GRUPLAR.items():
        print(f"\n{ad} (beklenen yön: {'+' if yon > 0 else '−'})")
        hisseler = likit_hisseler(aday)
        print(f"  Likit olanlar: {hisseler or 'YOK'}")
        if not hisseler:
            sonuc.append(dict(grup=ad, karar="likit hisse yok"))
            continue
        satir = []
        for (y, q) in hid.index:
            per = pd.Period(year=y, quarter=q, freq="Q")
            f, n = grup_getirisi(p, hisseler, per.start_time, per.end_time)
            satir.append(dict(ceyrek=f"{y}Ç{q}", anomali=an.get((y, q)), fazla=f, hisse=n,
                              ptf_yillik=np.log(ptf[(y, q)] / ptf[(y - 1, q)]) if (y - 1, q) in ptf.index else np.nan))
        d = pd.DataFrame(satir).dropna(subset=["anomali", "fazla"])
        r = np.corrcoef(d["anomali"], d["fazla"])[0, 1]
        sinyal = (d["anomali"] > 0) if yon > 0 else (d["anomali"] < 0)
        yuz, top = kaydirma(d["fazla"].values, sinyal.values)
        dp = d.dropna(subset=["ptf_yillik"])
        r_ptf = np.corrcoef(dp["ptf_yillik"], dp["fazla"])[0, 1]
        gec = (r * yon >= 0.30) and yuz >= 95
        print(f"  n = {len(d)} çeyrek (ilk: {d['ceyrek'].iloc[0]}), hisse sayısı {d['hisse'].min()}–{d['hisse'].max()}")
        print(f"  r(hidro anomalisi, fazla getiri) = {r:+.2f}   (kapı: beklenen yönde |r| ≥ 0,30)")
        print(f"  Strateji: toplam fazla getiri %{100 * (np.exp(top) - 1):+.0f}, kaydırılmış kopyaların %{yuz:.0f}'i "
              f"(kapı ≥ %95)")
        print(f"  Yalnız rapor: r(PTF yıllık değişim, fazla getiri) = {r_ptf:+.2f}")
        print(f"  KARAR: {'KAPIYI GEÇTİ' if gec else 'KALDI'}")
        sonuc.append(dict(grup=ad, n=len(d), r=r, yuzdelik=yuz, top=top, r_ptf=r_ptf, karar="GEÇTİ" if gec else "KALDI"))
        d.to_csv(CIKTI / f"likit_test_{ad}.csv", index=False)
    pd.DataFrame(sonuc).to_csv(CIKTI / "likit_test.csv", index=False)


if __name__ == "__main__":
    main()
