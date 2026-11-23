#!/usr/bin/env python3
"""
Mevsimlik "mükemmel bilgi" testi.

Haftalık testte hidro üretimi zayıf çıktı; olası neden, işletmecilerin suyu fiyata göre
haftadan haftaya kaydırması. Su stokunun etkisi ise aylar içinde görülmeli. Bu betik aynı
soruyu mevsim ölçeğinde sorar. Önceden sabitlenen tasarım:

TEST 1 – ÇEYREKLİK (2017Ç1 – son tam çeyrek)
  anomali_q = log( çeyrekteki barajlı hidro GWh / aynı çeyreğin DİĞER yıllardaki medyanı )
  Hedefler : (a) hidro sepetinin BIST100'e göre o çeyrekteki fazla getirisi
             (b) PTF ($) ortalamasının bir yıl önceki aynı çeyreğe göre log değişimi
  Mükemmel : aynı çeyreğin anomalisi   | Gerçekçi : bir önceki çeyreğin anomalisi
  Strateji : anomali > 0 olan çeyreklerde sepeti tut; kıyas = sinyalin zamanda kaydırılmış
             tüm kopyaları (aynı işlem sıklığı).

TEST 2 – SU YILI (her yıl bir gözlem)
  Bahar    : Mart–Mayıs anomalisi (Mayıs sonunda EPİAŞ'ta açık bilgi)
  Yaz-güz  : Haziran–Kasım anomalisi (mükemmel bilgi)
  Hedefler : Haziran–Kasım sepet fazla getirisi ve PTF ($) yıllık değişimi

Hidro sepeti: AYDEM, ENTRA, AKFYE, AKENR, AYEN, ENDAE'den o dönemde işlem görenlerin eşit
ağırlıklı ortalaması (2017–2021 arası yalnızca AKENR ve AYEN).

Girdi : cikti/epias_gunluk.csv, cikti/hisse_gunluk.csv
Çıktı : cikti/mevsimlik_test.csv, cikti/mevsimlik_test.png
"""
from pathlib import Path

import numpy as np
import pandas as pd

CIKTI = Path("cikti")
HISSELER = ["AYDEM", "ENTRA", "AKFYE", "AKENR", "AYEN", "ENDAE"]
rng = np.random.default_rng(11)


def veriler():
    g = pd.read_csv(CIKTI / "epias_gunluk.csv", parse_dates=["tarih"], index_col="tarih")
    h = pd.read_csv(CIKTI / "hisse_gunluk.csv", parse_dates=["tarih"])
    p = h.pivot_table(index="tarih", columns="sembol", values="kapanis").sort_index()
    # Altın/dolar gibi BIST dışı seriler BIST kapalıyken de işlem görür; yalnızca BIST günleri
    p = p[p["XU100"].notna()]
    return g, p


def donem_getirisi(p, bas, son):
    """[bas, son] dönemi: her hissenin BIST100'e göre log fazla getirisi, sonra eşit ağırlıklı ortalama."""
    once = p[p.index < bas].tail(1)          # dönem başından önceki son kapanış
    sonra = p[p.index <= son].tail(1)
    if once.empty or sonra.empty:
        return np.nan, 0
    r = np.log(sonra.iloc[0] / once.iloc[0])
    fazla = (r[HISSELER] - r["XU100"]).dropna()
    # dönem başında işlem görmeyen hisse sayılmaz
    fazla = fazla[[s for s in fazla.index if pd.notna(once.iloc[0][s])]]
    return (float(fazla.mean()) if len(fazla) else np.nan), len(fazla)


def anomali(seri_toplam: pd.Series) -> pd.Series:
    """Her dönem için: log(değer / aynı dönemin diğer yıllardaki medyanı)."""
    out = {}
    for k, v in seri_toplam.items():
        diger = seri_toplam[[x for x in seri_toplam.index if x[1] == k[1] and x[0] != k[0]]]
        out[k] = np.log(v / diger.median()) if len(diger) >= 3 else np.nan
    return pd.Series(out)


def kor_ve_aralik(x, y, n_boot=5000):
    x, y = np.asarray(x, float), np.asarray(y, float)
    m = np.isfinite(x) & np.isfinite(y)
    x, y = x[m], y[m]
    if len(x) < 5:
        return np.nan, (np.nan, np.nan), len(x)
    r = np.corrcoef(x, y)[0, 1]
    b = []
    for _ in range(n_boot):
        i = rng.integers(0, len(x), len(x))
        if np.std(x[i]) > 0 and np.std(y[i]) > 0:
            b.append(np.corrcoef(x[i], y[i])[0, 1])
    return r, tuple(np.percentile(b, [5, 95])), len(x)


def kaydirma_yuzdelik(fazla, sinyal):
    fazla, sinyal = np.asarray(fazla), np.asarray(sinyal, bool)
    deger = fazla[sinyal].sum()
    kopya = [fazla[np.roll(sinyal, k)].sum() for k in range(1, len(fazla))]
    return 100 * np.mean(np.array(kopya) < deger), deger


def test_ceyrek(g, p):
    son_tam = (g.index.max() + pd.Timedelta(days=1)).to_period("Q") - 1
    gq = g[g.index.to_period("Q") <= son_tam]
    hid = gq["dammedHydro_gwh"].groupby([gq.index.year, gq.index.quarter]).sum()
    ptf = gq["ptf_usd"].groupby([gq.index.year, gq.index.quarter]).mean()
    an = anomali(hid)
    satir = []
    for (y, q) in hid.index:
        bas = pd.Period(year=y, quarter=q, freq="Q").start_time
        son = pd.Period(year=y, quarter=q, freq="Q").end_time
        f, n = donem_getirisi(p, bas, son)
        onceki = (y, q - 1) if q > 1 else (y - 1, 4)
        satir.append(dict(ceyrek=f"{y}Ç{q}", anomali=an.get((y, q)), anomali_onceki=an.get(onceki),
                          sepet_fazla=f, sepet_hisse=n,
                          ptf_yillik=np.log(ptf[(y, q)] / ptf[(y - 1, q)]) if (y - 1, q) in ptf.index else np.nan))
    return pd.DataFrame(satir)


def test_suyili(g, p):
    satir = []
    for y in sorted(set(g.index.year)):
        bahar = g.loc[f"{y}-03-01":f"{y}-05-31", "dammedHydro_gwh"]
        yaz = g.loc[f"{y}-06-01":f"{y}-11-30"]
        if len(bahar) < 90 or len(yaz) < 60:
            continue
        ptf_once = g.loc[f"{y - 1}-06-01":f"{y - 1}-11-30", "ptf_usd"]
        f, n = donem_getirisi(p, pd.Timestamp(f"{y}-06-01"), pd.Timestamp(f"{y}-11-30"))
        satir.append(dict(yil=y, bahar_gwh=bahar.sum(), yaz_gwh=yaz["dammedHydro_gwh"].sum() * 183 / len(yaz),
                          yaz_gun=len(yaz), sepet_fazla=f, sepet_hisse=n,
                          ptf_yillik=np.log(yaz["ptf_usd"].mean() / ptf_once.mean()) if len(ptf_once) > 150 else np.nan))
    d = pd.DataFrame(satir).set_index("yil")
    for c in ["bahar", "yaz"]:
        d[f"{c}_anomali"] = [np.log(v / d[f"{c}_gwh"].drop(y).median()) for y, v in d[f"{c}_gwh"].items()]
    return d


def yaz_sonuc(ad, x, y, ek=""):
    r, (lo, hi), n = kor_ve_aralik(x, y)
    durum = "anlamlı" if (lo > 0 or hi < 0) else "belirsiz (aralık 0'ı içeriyor)"
    print(f"  {ad:58s} r = {r:+.2f}   %90 aralık [{lo:+.2f}, {hi:+.2f}]   n={n}   -> {durum}{ek}")
    return dict(test=ad, r=round(r, 3), alt=round(lo, 3), ust=round(hi, 3), n=n)


def main():
    g, p = veriler()
    sonuc = []

    q = test_ceyrek(g, p)
    print(f"\nTEST 1 – ÇEYREKLİK ({q['ceyrek'].iloc[0]} – {q['ceyrek'].iloc[-1]}, {len(q)} çeyrek)")
    sonuc.append(yaz_sonuc("Mükemmel: çeyreğin hidrosu -> sepetin fazla getirisi", q["anomali"], q["sepet_fazla"]))
    sonuc.append(yaz_sonuc("Gerçekçi: önceki çeyreğin hidrosu -> sepetin fazla getirisi", q["anomali_onceki"], q["sepet_fazla"]))
    sonuc.append(yaz_sonuc("Mükemmel: çeyreğin hidrosu -> PTF yıllık değişim", q["anomali"], q["ptf_yillik"]))
    sonuc.append(yaz_sonuc("Gerçekçi: önceki çeyreğin hidrosu -> PTF yıllık değişim", q["anomali_onceki"], q["ptf_yillik"]))
    qq = q.dropna(subset=["anomali", "sepet_fazla"])
    for ad, s in [("mükemmel", qq["anomali"] > 0), ("gerçekçi", qq["anomali_onceki"].fillna(0) > 0)]:
        yuz, top = kaydirma_yuzdelik(qq["sepet_fazla"], s)
        print(f"  Strateji ({ad}): sulu çeyreklerde sepeti tut -> toplam fazla getiri %{100 * (np.exp(top) - 1):+.0f}, "
              f"kaydırılmış kopyaların %{yuz:.0f}'ini geçti ({int(s.sum())}/{len(s)} çeyrek)")
        sonuc.append(dict(test=f"Çeyreklik strateji ({ad})", r=np.nan, alt=np.nan, ust=np.nan, n=len(s),
                          yuzdelik=round(yuz), toplam_fazla_yuzde=round(100 * (np.exp(top) - 1), 1)))

    d = test_suyili(g, p)
    print(f"\nTEST 2 – SU YILI ({d.index.min()}–{d.index.max()}, her yıl 1 gözlem)")
    print(d[["bahar_anomali", "yaz_anomali", "sepet_fazla", "sepet_hisse", "ptf_yillik"]].round(2).to_string())
    sonuc.append(yaz_sonuc("Bahar suyu -> Haz–Kas hidrosu (bahar yazı haber veriyor mu?)", d["bahar_anomali"], d["yaz_anomali"]))
    sonuc.append(yaz_sonuc("Mükemmel: Haz–Kas hidrosu -> Haz–Kas sepet fazla getirisi", d["yaz_anomali"], d["sepet_fazla"]))
    sonuc.append(yaz_sonuc("Gerçekçi: bahar suyu -> Haz–Kas sepet fazla getirisi", d["bahar_anomali"], d["sepet_fazla"]))
    sonuc.append(yaz_sonuc("Mükemmel: Haz–Kas hidrosu -> Haz–Kas PTF yıllık değişim", d["yaz_anomali"], d["ptf_yillik"]))
    sonuc.append(yaz_sonuc("Gerçekçi: bahar suyu -> Haz–Kas PTF yıllık değişim", d["bahar_anomali"], d["ptf_yillik"]))
    if d.index.max() == pd.Timestamp.today().year:
        print(f"  Not: {d.index.max()} yılı Haz–Kas dönemi henüz tamamlanmadı ({int(d['yaz_gun'].iloc[-1])} gün).")

    pd.DataFrame(sonuc).to_csv(CIKTI / "mevsimlik_test.csv", index=False)
    q.to_csv(CIKTI / "mevsimlik_ceyrek_veri.csv", index=False)
    d.to_csv(CIKTI / "mevsimlik_suyili_veri.csv")
    print("\nOkuma: %90 aralığı 0'ı içeriyorsa veri 'etki yok' ihtimalini dışlayamıyor."
          "\nSu yılı testinde yalnızca ~10 gözlem var; tek bir yıl sonucu tersine çevirebilir.")
    try:
        ciz(q, d)
    except Exception as e:
        print(f"(grafik çizilemedi: {e})")


def ciz(q, d):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axs = plt.subplots(2, 2, figsize=(12, 9))
    for ax, (x, y, xl, yl, veri, etiket) in zip(axs.ravel(), [
        ("anomali", "sepet_fazla", "Çeyreğin hidro anomalisi (log)", "Sepetin BIST100'e göre fazla getirisi (log)", q, "ceyrek"),
        ("anomali", "ptf_yillik", "Çeyreğin hidro anomalisi (log)", "PTF ($) yıllık değişim (log)", q, "ceyrek"),
        ("yaz_anomali", "sepet_fazla", "Haz–Kas hidro anomalisi (log)", "Haz–Kas sepet fazla getirisi (log)", d.reset_index(), "yil"),
        ("bahar_anomali", "ptf_yillik", "Mar–May (bahar) hidro anomalisi (log)", "Haz–Kas PTF ($) yıllık değişim (log)", d.reset_index(), "yil"),
    ]):
        v = veri[[x, y, etiket]].dropna()
        ax.scatter(v[x], v[y], s=28)
        for _, rr in v.iterrows():
            ax.annotate(str(rr[etiket]), (rr[x], rr[y]), fontsize=7, alpha=0.7, xytext=(3, 3), textcoords="offset points")
        if len(v) >= 3:
            k = np.polyfit(v[x], v[y], 1)
            xs = np.linspace(v[x].min(), v[x].max(), 10)
            ax.plot(xs, np.polyval(k, xs), color="tab:red", lw=1)
        ax.axhline(0, color="grey", lw=0.6); ax.axvline(0, color="grey", lw=0.6)
        ax.set_xlabel(xl); ax.set_ylabel(yl)
        ax.set_title(f"r = {np.corrcoef(v[x], v[y])[0, 1]:+.2f}  (n={len(v)})", fontsize=10)
    fig.suptitle("Mevsimlik test: su bolluğu fiyatı ve hidro hisselerini açıklıyor mu?")
    fig.tight_layout()
    fig.savefig(CIKTI / "mevsimlik_test.png", dpi=120)
    print(f"Grafik: {CIKTI / 'mevsimlik_test.png'}")


if __name__ == "__main__":
    main()
