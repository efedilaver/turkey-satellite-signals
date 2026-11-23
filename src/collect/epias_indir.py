#!/usr/bin/env python3
"""
EPİAŞ Şeffaflık verilerini indirir.

  1) Saatlik PTF (piyasa takas fiyatı)            -> cikti/epias_ptf_saatlik.csv
  2) Saatlik kaynak bazında gerçek zamanlı üretim -> cikti/epias_uretim_saatlik.csv
     (barajlı hidro = dammedHydro, akarsu = river, doğalgaz, rüzgâr, ...)
  3) Günlük özet (2 dosyanın gün bazında birleşimi) -> cikti/epias_gunluk.csv
  4) Barajların BUGÜNKÜ durumu -> cikti/epias_baraj_arsiv.csv dosyasına EKLENİR.
     EPİAŞ baraj verisinin geçmişini vermiyor (denendi); her gün çalıştırılırsa
     kendi arşivimiz oluşur.

Kaldığı yerden devam eder: dosyalar varsa yalnızca eksik günleri indirir.

Kullanıcı adı / şifre: .env (EPTR_USERNAME, EPTR_PASSWORD) veya çalışırken sorulur.

  python epias_indir.py                      # 2017'den düne kadar
  python epias_indir.py --baslangic 2020-01-01
  python epias_indir.py --sadece-baraj       # yalnızca bugünkü baraj durumunu arşive ekle
"""
import argparse
import time
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from epias_dene import CIKTI, istek, tgt_al

PARCA_GUN = 90  # tek istekte alınabilen gün sayısı (denendi: 90 gün sorunsuz)


def _tarih(d: date, son=False) -> str:
    return f"{d:%Y-%m-%d}T{'23' if son else '00'}:00:00+03:00"


def seri_indir(tgt, yol, ad, baslangic: date, bitis: date, yol_csv: Path, parca_gun=PARCA_GUN):
    """
    Parça parça indirir ve HER PARÇADAN SONRA dosyaya ekler; yarıda kesilirse aynı komut
    kaldığı yerden devam eder. Zaman aşımı/bağlantı hatalarında 4 kez, giderek uzayan
    aralıklarla yeniden dener.
    """
    if yol_csv.exists():
        tarih = pd.read_csv(yol_csv, usecols=["date"])["date"]
        son_gun = pd.to_datetime(tarih, utc=True).dt.tz_convert("Europe/Istanbul").max().date()
        baslangic = max(baslangic, son_gun + timedelta(days=1))
    if baslangic > bitis:
        print(f"  {ad}: güncel")
        return
    d, i = baslangic, 0
    toplam = (bitis - baslangic).days // parca_gun + 1
    while d <= bitis:
        s = min(d + timedelta(days=parca_gun - 1), bitis)
        kod, v = None, None
        for deneme in range(4):
            try:
                kod, v = istek(tgt, yol, {"startDate": _tarih(d), "endDate": _tarih(s, son=True)},
                               zaman_asimi=180)
                if kod == 200:
                    break
            except Exception as e:  # zaman aşımı, bağlantı kopması
                kod, v = None, f"{e.__class__.__name__}"
            bekle = 15 * (deneme + 1)
            print(f"    {d}–{s}: {kod or v}, {bekle} sn sonra tekrar denenecek", flush=True)
            time.sleep(bekle)
        if kod != 200:
            raise SystemExit(f"{ad}: {d}–{s} 4 denemede indirilemedi ({kod or v}). "
                             f"İndirilen kısım kaydedildi; aynı komutla devam edebilirsin.")
        parca = pd.DataFrame(v.get("items", []))
        parca.to_csv(yol_csv, mode="a", header=not yol_csv.exists(), index=False)
        i += 1
        print(f"  {ad}: {d} – {s}  ({i}/{toplam})", flush=True)
        d = s + timedelta(days=1)
        time.sleep(0.5)  # servise nazik ol
    # Olası tekrarları temizle
    df = pd.read_csv(yol_csv)
    df = df.drop_duplicates(subset=["date", "hour"] if "hour" in df.columns else ["date"], keep="last")
    df.to_csv(yol_csv, index=False)
    print(f"  -> {yol_csv} ({len(df)} satır)")


def gunluk_ozet():
    ptf = pd.read_csv(CIKTI / "epias_ptf_saatlik.csv")
    ure = pd.read_csv(CIKTI / "epias_uretim_saatlik.csv")
    for d in (ptf, ure):
        d["gun"] = pd.to_datetime(d["date"], utc=True).dt.tz_convert("Europe/Istanbul").dt.date
    p = ptf.groupby("gun").agg(ptf_tl=("price", "mean"), ptf_usd=("priceUsd", "mean"))
    kaynak = [c for c in ure.columns if c not in ("date", "hour", "gun")]
    u = ure.groupby("gun")[kaynak].sum() / 1000  # MWh -> GWh
    u.columns = [f"{c}_gwh" for c in u.columns]
    g = p.join(u, how="outer")
    g["hidro_barajli_pay"] = g["dammedHydro_gwh"] / g["total_gwh"]
    g.index.name = "tarih"
    g.to_csv(CIKTI / "epias_gunluk.csv")
    print(f"  -> {CIKTI / 'epias_gunluk.csv'} ({len(g)} gün, {g.index.min()} – {g.index.max()})")


def baraj_arsivle(tgt):
    """Bugünkü aktif doluluk + günlük hacim + kot, tüm barajlar için. Arşive eklenir."""
    kod, v = istek(tgt, "/v1/dams/data/active-fullness", {"page": {"number": 1, "size": 1000}})
    if kod != 200:
        print(f"  Baraj doluluğu alınamadı (HTTP {kod})")
        return
    dol = pd.DataFrame(v["items"]).rename(columns={"dam": "baraj", "basin": "havza",
                                                   "activeFullnessAmount": "aktif_doluluk_yuzde"})
    dol["baraj"] = dol["baraj"].str.strip()
    hacim, kot, enerji = [], [], []
    for havza in sorted(dol["havza"].dropna().unique()):
        govde = {"basinName": havza, "page": {"number": 1, "size": 1000}}
        k1, v1 = istek(tgt, "/v1/dams/data/daily-volume", govde)
        if k1 == 200:
            hacim += [{"baraj": str(i["damName"]).strip(), "hacim_hm3": i.get("volume")} for i in v1.get("items", [])]
        k2, v2 = istek(tgt, "/v1/dams/data/daily-kot", govde)
        if k2 == 200:
            kot += [{"baraj": str(i["dam"]).strip(), "kot_m": i.get("dailyKot")} for i in v2.get("items", [])]
        try:  # suyun enerji karşılığı (MWh); alan adları belgelenmemiş, ham saklanır
            k3, v3 = istek(tgt, "/v1/dams/data/water-energy-provision", {"basinName": havza})
            if k3 == 200:
                enerji += [dict(i, havza_sorgu=havza) for i in v3.get("items", [])]
        except Exception:
            pass
    if enerji:
        e = pd.DataFrame(enerji).assign(arsiv_tarihi=str(date.today()))
        ey = CIKTI / "epias_baraj_enerji_arsiv.csv"
        if ey.exists():
            e = pd.concat([pd.read_csv(ey), e]).drop_duplicates(keep="last")
        e.to_csv(ey, index=False)
        print(f"  -> {ey}: alanlar {[c for c in e.columns]}")
    df = dol[["date", "havza", "baraj", "damId", "aktif_doluluk_yuzde"]]
    if hacim:
        df = df.merge(pd.DataFrame(hacim).drop_duplicates("baraj"), on="baraj", how="left")
    if kot:
        df = df.merge(pd.DataFrame(kot).drop_duplicates("baraj"), on="baraj", how="left")
    df["tarih"] = pd.to_datetime(df["date"]).dt.date
    df = df.drop(columns=["date"])
    yol = CIKTI / "epias_baraj_arsiv.csv"
    if yol.exists():
        eski = pd.read_csv(yol)
        eski["tarih"] = pd.to_datetime(eski["tarih"]).dt.date
        df = pd.concat([eski, df]).drop_duplicates(["tarih", "baraj"], keep="last")
    df.sort_values(["tarih", "havza", "baraj"]).to_csv(yol, index=False)
    print(f"  -> {yol}: {df['tarih'].nunique()} gün arşivde, son gün {len(dol)} baraj")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--baslangic", default="2017-01-01")
    p.add_argument("--sadece-baraj", action="store_true")
    a = p.parse_args()
    CIKTI.mkdir(exist_ok=True)
    tgt = tgt_al()
    print("Giriş başarılı.")
    print("Barajların bugünkü durumu arşivleniyor...")
    try:
        baraj_arsivle(tgt)
    except Exception as e:  # arşiv başarısız olsa da fiyat/üretim indirmesi sürsün
        print(f"  Baraj arşivi alınamadı ({e.__class__.__name__}), devam ediliyor")
    if a.sadece_baraj:
        return
    bas = date.fromisoformat(a.baslangic)
    dun = date.today() - timedelta(days=1)
    print("PTF indiriliyor...")
    seri_indir(tgt, "/v1/markets/dam/data/mcp", "PTF", bas, dun, CIKTI / "epias_ptf_saatlik.csv")
    print("Kaynak bazında üretim indiriliyor...")
    # Üretim servisi daha yavaş (90 günlük istek zaman aşımına uğradı): 30 günlük parçalar
    seri_indir(tgt, "/v1/generation/data/realtime-generation", "Üretim", bas, dun,
               CIKTI / "epias_uretim_saatlik.csv", parca_gun=30)
    print("Günlük özet hazırlanıyor...")
    gunluk_ozet()


if __name__ == "__main__":
    main()
