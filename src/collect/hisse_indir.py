#!/usr/bin/env python3
"""
Hidro ağırlıklı hisselerin ve BIST100'ün günlük kapanışlarını indirir (Yahoo Finance).

  python hisse_indir.py   ->  cikti/hisse_gunluk.csv  (tarih, sembol, kapanis)

Kapanışlar temettü/bölünmeye göre düzeltilmiş (adjusted) fiyatlardır.
Önce doğrudan Yahoo grafik servisi denenir; olmazsa yfinance paketi kullanılır.
"""
import sys
import time
from pathlib import Path

import pandas as pd
import requests

SEMBOLLER = ["AYDEM", "ENTRA", "AKFYE", "AKENR", "AYEN", "ENDAE", "XU100",
             "TRALT", "KOZAA", "EREGL", "KRDMD", "BALSU", "ALTIN_USD", "USDTRY",
             "IZMDC", "CEMTS", "ODAS", "CANTE", "AKSEN", "IZENR"]
# Yahoo'daki karşılıkları (varsayılan: <sembol>.IS). Birden fazla aday sırayla denenir.
YAHOO = {"TRALT": ["TRALT.IS", "KOZAL.IS"], "KOZAA": ["TRMET.IS", "KOZAA.IS"], "ALTIN_USD": ["GC=F"], "USDTRY": ["USDTRY=X"]}
CIKTI = Path("cikti")
BASLANGIC = "2017-01-01"


def _adaylar(sembol):
    return YAHOO.get(sembol, [f"{sembol}.IS"])


def yahoo_dogrudan(sembol: str) -> pd.Series:
    bas = int(pd.Timestamp(BASLANGIC).timestamp())
    son = int(time.time())
    for kod in _adaylar(sembol):
        url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{kod}"
               f"?period1={bas}&period2={son}&interval=1d&events=div%2Csplits")
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
        if r.status_code != 200:
            continue
        res = (r.json().get("chart") or {}).get("result")
        if not res:
            continue
        res = res[0]
        tarih = pd.to_datetime(res["timestamp"], unit="s").normalize()
        kapanis = (res["indicators"].get("adjclose") or [{}])[0].get("adjclose") \
            or res["indicators"]["quote"][0]["close"]
        q = res["indicators"]["quote"][0]
        tl_hacim = [(v or 0) * (c or 0) for v, c in zip(q.get("volume") or [], q.get("close") or [])]
        if len(tl_hacim) != len(tarih):
            tl_hacim = None
        return pd.DataFrame({"kapanis": kapanis, "hacim_tl": tl_hacim}, index=tarih).dropna(subset=["kapanis"])
    raise ValueError("bulunamadı")


def yahoo_yfinance(sembol: str) -> pd.Series:
    import yfinance as yf
    for kod in _adaylar(sembol):
        df = yf.download(kod, start=BASLANGIC, auto_adjust=True, progress=False)
        if len(df):
            s = df["Close"].squeeze()
            v = df["Volume"].squeeze() * s
            out = pd.DataFrame({"kapanis": s, "hacim_tl": v})
            out.index = pd.to_datetime(out.index).normalize()
            return out.dropna(subset=["kapanis"])
    raise ValueError("bulunamadı")


def main():
    CIKTI.mkdir(exist_ok=True)
    parcalar = []
    for s in SEMBOLLER:
        seri = None
        for yontem in (yahoo_dogrudan, yahoo_yfinance):
            try:
                seri = yontem(s)
                break
            except Exception as e:
                print(f"  {s}: {yontem.__name__} başarısız ({e.__class__.__name__})")
        if seri is None or seri.empty:
            print(f"  {s}: İNDİRİLEMEDİ. 'pip install yfinance' ile tekrar dene.")
            continue
        print(f"  {s}: {len(seri)} gün, {seri.index.min():%Y-%m-%d} – {seri.index.max():%Y-%m-%d}")
        parcalar.append(seri.assign(sembol=s))
        time.sleep(1)
    if not parcalar:
        sys.exit("Hiç veri indirilemedi.")
    df = pd.concat(parcalar).rename_axis("tarih").reset_index()[["tarih", "sembol", "kapanis", "hacim_tl"]]
    df.to_csv(CIKTI / "hisse_gunluk.csv", index=False)
    print(f"-> {CIKTI / 'hisse_gunluk.csv'} ({len(df)} satır)")


if __name__ == "__main__":
    main()
