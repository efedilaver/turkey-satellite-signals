#!/usr/bin/env python3
"""
"Mükemmel bilgi" testi (videodaki 8. dakika fikri):

  Gelecek haftanın barajlı hidro üretimini ÖNCEDEN kusursuz bilseydin, bununla
  (a) elektrik fiyatının yönünü, (b) hidro ağırlıklı hisselerin BIST100'e göre
  getirisini tahmin edebilir miydin?

  Cevap "hayır" ise, uydu ne kadar iyi olursa olsun bu kanal para kazandırmaz.

Önceden sabitlenen tasarım (sonuçlara bakarak değiştirilmez):
  - Hafta: Cumartesi–Cuma. Hisse getirisi: Cuma kapanışından Cuma kapanışına.
  - Hidro anomalisi: haftalık barajlı hidro üretimi / aynı yılın-haftasının DİĞER
    yıllardaki medyanı (log). >0 = normalden fazla su kullanılıyor.
  - Ana hipotez: anomali > 0 olan haftalarda hidro hisseleri BIST100'ü geçer.
  - Strateji: hafta t+1'in anomalisi > 0 ise o hafta hisseyi tut (BIST100'e karşı
    fazla getiri), değilse nakitte kal. Her pozisyon değişiminde %0,2 maliyet.
  - Kıyas: stratejinin kendi sinyalinin zamanda rastgele kaydırılmış 2.000 kopyası
    (aynı işlem sıklığı ve maliyet). Strateji bunların %95'inden iyiyse "anlamlı".
  - Gerçekçi sürüm: aynı kural, ama karar için BU haftanın anomalisi kullanılır
    (Cuma günü EPİAŞ'ta zaten açık olan bilgi).

Girdi : cikti/epias_gunluk.csv, cikti/hisse_gunluk.csv
Çıktı : cikti/mukemmel_bilgi.csv, cikti/mukemmel_bilgi.png
"""
from pathlib import Path

import numpy as np
import pandas as pd

CIKTI = Path("cikti")
HISSELER = ["AYDEM", "ENTRA", "AKFYE", "AKENR", "AYEN", "ENDAE"]
MALIYET = 0.002          # pozisyon değişimi başına (alım+satım komisyon/kayma)
RASTGELE = 2000
rng = np.random.default_rng(7)


def haftalik_epias():
    g = pd.read_csv(CIKTI / "epias_gunluk.csv", parse_dates=["tarih"], index_col="tarih")
    h = pd.DataFrame({
        "hidro_gwh": g["dammedHydro_gwh"].resample("W-FRI").sum(min_count=7),
        "ptf_usd": g["ptf_usd"].resample("W-FRI").mean(),
    }).dropna()
    h["yil"], h["hafta"] = h.index.year, h.index.isocalendar().week.astype(int).clip(upper=52)
    # Mevsim normali: aynı haftanın DİĞER yıllardaki medyanı (kendi yılını görmez)
    norm = []
    for t, r in h.iterrows():
        ayni = h[(h["hafta"] == r["hafta"]) & (h["yil"] != r["yil"])]["hidro_gwh"]
        norm.append(ayni.median() if len(ayni) >= 3 else np.nan)
    h["hidro_norm"] = norm
    h["anomali"] = np.log(h["hidro_gwh"] / h["hidro_norm"])
    h["ptf_degisim"] = np.log(h["ptf_usd"]).diff()   # bu hafta / geçen hafta
    return h


def haftalik_hisse():
    d = pd.read_csv(CIKTI / "hisse_gunluk.csv", parse_dates=["tarih"])
    p = d.pivot_table(index="tarih", columns="sembol", values="kapanis").sort_index()
    p = p.resample("W-FRI").last()
    return np.log(p).diff()   # haftalık log getiri


def strateji(fazla, sinyal):
    """sinyal: bool dizisi (True = o hafta hissede ol). Maliyetli/maliyetsiz toplam log getiri."""
    poz = sinyal.astype(float)
    brut = float((fazla * poz).sum())
    degisim = np.abs(np.diff(np.concatenate([[0.0], poz]))).sum()
    return brut, brut + degisim * np.log(1 - MALIYET)


def rastgele_yuzdelik(fazla, sinyal, deger, maliyetli):
    """
    Kıyas portföyleri: stratejinin KENDİ sinyal dizisi zamanda rastgele kaydırılır (dairesel).
    Böylece kıyaslar aynı sayıda haftada hissede kalır, aynı sıklıkta işlem yapar (aynı maliyet)
    ve 'su bolluğu dönemleri' gibi aylarca süren yapıyı korur; yalnızca getirilerle zamanlaması
    bozulur. (Her hafta yazı-tura atmak, haftalık işlem maliyeti yüzünden stratejiyi haksız
    yere iyi gösterirdi.)
    """
    n = len(fazla)
    kaymalar = rng.integers(8, n - 8, RASTGELE)   # en az 8 hafta kaydır
    sonuc = np.empty(RASTGELE)
    for i, k in enumerate(kaymalar):
        b, m = strateji(fazla, np.roll(sinyal, k))
        sonuc[i] = m if maliyetli else b
    return 100 * (sonuc < deger).mean(), sonuc


def main():
    h = haftalik_epias()
    r = haftalik_hisse()
    bist = r["XU100"]

    satirlar, cizim = [], {}
    # (a) Elektrik fiyatı: gelecek haftanın hidrosu fiyatı düşürüyor mu?
    ptf = h[["anomali", "ptf_degisim"]].copy()
    ptf["anomali_degisim"] = ptf["anomali"].diff()
    ptf = ptf.dropna()
    kor = ptf["anomali_degisim"].corr(ptf["ptf_degisim"])
    yon = (np.sign(ptf["anomali_degisim"]) == -np.sign(ptf["ptf_degisim"])).mean()
    print(f"\n(a) ELEKTRİK FİYATI ({len(ptf)} hafta, {ptf.index.min():%Y-%m} – {ptf.index.max():%Y-%m})")
    print(f"    Hidro anomalisindeki haftalık değişim ile PTF ($) haftalık değişimi korelasyonu: {kor:+.2f}")
    print(f"    'Hidro artarsa fiyat düşer' kuralının isabeti: %{100 * yon:.0f}  (yazı-tura %50)")

    # (b) Hisseler
    print(f"\n(b) HİSSELER – BIST100'e göre fazla getiri, hafta hafta")
    for s in HISSELER:
        if s not in r.columns:
            continue
        fazla = (r[s] - bist).rename("fazla")
        df = pd.concat([fazla, h["anomali"]], axis=1).dropna()
        df["anomali_onceki"] = h["anomali"].shift(1).reindex(df.index)  # gerçekçi: bir önceki haftanın verisi
        df = df.dropna()
        if len(df) < 40:
            print(f"    {s}: yalnızca {len(df)} hafta, atlandı")
            continue
        fz = df["fazla"].to_numpy()
        for ad, sinyal in [("mükemmel bilgi (gelecek hafta)", df["anomali"].to_numpy() > 0),
                           ("gerçekçi (önceki hafta, kamuya açık)", df["anomali_onceki"].to_numpy() > 0)]:
            brut, net = strateji(fz, sinyal)
            yb, _ = rastgele_yuzdelik(fz, sinyal, brut, maliyetli=False)
            yn, dag = rastgele_yuzdelik(fz, sinyal, net, maliyetli=True)
            # Ters yön de raporlanır (önceden belirlenmemiş; yalnızca bilgi için)
            tb, _ = strateji(fz, ~sinyal)
            yt, _ = rastgele_yuzdelik(fz, ~sinyal, tb, maliyetli=False)
            satirlar.append(dict(
                hisse=s, surum=ad, hafta=len(df),
                donem=f"{df.index.min():%Y-%m}–{df.index.max():%Y-%m}",
                hissede_hafta_yuzde=round(100 * sinyal.mean()),
                fazla_getiri_brut_yuzde=round(100 * (np.exp(brut) - 1), 1),
                fazla_getiri_net_yuzde=round(100 * (np.exp(net) - 1), 1),
                rastgeleyi_gecme_brut=round(yb), rastgeleyi_gecme_net=round(yn),
                ters_yon_rastgeleyi_gecme=round(yt),
                korelasyon=round(float(np.corrcoef(df["anomali"] if "mükemmel" in ad else df["anomali_onceki"], fz)[0, 1]), 3),
            ))
            if "mükemmel" in ad:
                cizim[s] = (df.index, fz, sinyal, dag, net)

    t = pd.DataFrame(satirlar)
    t.to_csv(CIKTI / "mukemmel_bilgi.csv", index=False)
    pd.set_option("display.width", 250)
    print(t.drop(columns=["ters_yon_rastgeleyi_gecme"]).to_string(index=False))
    m = t[t["surum"].str.startswith("mükemmel")]
    print(f"\n    Mükemmel bilgiyle, maliyet sonrası rastgelenin %95'ini geçen hisse: "
          f"{(m['rastgeleyi_gecme_net'] >= 95).sum()} / {len(m)}")
    print(f"    Ters yön (hidro AZKEN hissede ol) %95'i geçen: {(m['ters_yon_rastgeleyi_gecme'] >= 95).sum()} / {len(m)}"
          "   (önceden belirlenmemiş hipotez; yalnızca bilgi için)")
    print("\nOkuma: 'rastgeleyi_gecme' videodaki ölçüt. 95+ = rastgele seçimlerin %95'inden iyi."
          "\n6 hisse x 2 sürüm test edildiği için 1 tanesinin tesadüfen 95'i geçmesi şaşırtıcı olmaz.")

    try:
        ciz(cizim, t, ptf)
    except Exception as e:
        print(f"(grafik çizilemedi: {e})")


def ciz(cizim, t, ptf):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    n = len(cizim)
    fig, axs = plt.subplots(2, 1, figsize=(11, 9), gridspec_kw={"height_ratios": [1.2, 1]})
    m = t[t["surum"].str.startswith("mükemmel")].set_index("hisse")
    g = t[t["surum"].str.startswith("gerçekçi")].set_index("hisse")
    x = np.arange(len(m))
    axs[0].bar(x - 0.2, m["rastgeleyi_gecme_net"], 0.4, label="Mükemmel bilgi (gelecek haftanın hidrosu)")
    axs[0].bar(x + 0.2, g.reindex(m.index)["rastgeleyi_gecme_net"], 0.4, label="Gerçekçi (geçen haftanın hidrosu)")
    axs[0].axhline(95, color="red", ls="--", lw=1, label="%95 eşiği")
    axs[0].axhline(50, color="grey", lw=0.8)
    axs[0].set_xticks(x, m.index)
    axs[0].set_ylim(0, 100)
    axs[0].set_ylabel("Rastgele portföylerin yüzde kaçını geçti")
    axs[0].set_title("Hidro bilgisiyle hisse seçimi – maliyet sonrası (videodaki test)")
    axs[0].legend(fontsize=8, loc="lower right")

    s = max(cizim, key=lambda k: len(cizim[k][0]))  # en uzun geçmişi olan hisse
    tarih, fz, sinyal, dag, net = cizim[s]
    eg = np.cumsum(fz * sinyal)
    axs[1].plot(tarih, 100 * (np.exp(eg) - 1), lw=1.8, label=f"{s}: mükemmel bilgi stratejisi")
    axs[1].plot(tarih, 100 * (np.exp(np.cumsum(fz)) - 1), lw=1, color="grey", label=f"{s}: sürekli tut")
    axs[1].axhline(0, color="k", lw=0.6)
    axs[1].set_ylabel("BIST100'e göre birikimli fazla getiri (%)")
    axs[1].legend(fontsize=8)
    axs[1].set_title(f"{s} – rastgele portföylerin %{m.loc[s, 'rastgeleyi_gecme_net']:.0f}'ini geçti")
    fig.tight_layout()
    fig.savefig(CIKTI / "mukemmel_bilgi.png", dpi=120)
    print(f"Grafik: {CIKTI / 'mukemmel_bilgi.png'}")


if __name__ == "__main__":
    main()
