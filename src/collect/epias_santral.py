#!/usr/bin/env python3
"""
Santral bazında saatlik üretim (EPİAŞ gerçek zamanlı üretim), 2017'den bugüne.

Hangi santraller:
  - Fırat/Dicle büyük barajları: Keban, Karakaya, Atatürk, Birecik, Karkamış, Ilısu
  - hes/hes_santraller_borsa.csv içindeki borsa şirketlerine ait HES'ler

Çıktılar:
  cikti/epias_santral_listesi.csv   EPİAŞ'ın tüm santral listesi (ham)
  cikti/epias_santral_eslesme.csv   bizim adlarımız -> EPİAŞ kimliği (elle kontrol için)
  cikti/epias_santral_saatlik.csv   powerPlantId, date, total (MWh)

Kaldığı yerden devam eder. İlk sefer uzun sürer (yaklaşık 1–3 saat), sonra dakikalar.
  python epias_santral.py
  python epias_santral.py --baslangic 2020-01-01
"""
import argparse
import re
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path
from threading import Lock

import pandas as pd

from epias_dene import CIKTI, istek, tgt_al

FIRAT = ["KEBAN", "KARAKAYA", "ATATURK", "BIRECIK", "KARKAMIS", "ILISU"]
PARCA_GUN = 90
YOL = "/v1/generation/data/realtime-generation"

_kilit = Lock()
_tgt = {"t": None, "zaman": 0.0}


def tgt():
    """Bilet 2 saat geçerli; 90 dakikada bir yenilenir."""
    with _kilit:
        if not _tgt["t"] or time.time() - _tgt["zaman"] > 90 * 60:
            _tgt["t"], _tgt["zaman"] = tgt_al(), time.time()
        return _tgt["t"]


def sade(s):
    s = str(s).upper().replace("İ", "I").replace("I", "I")
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^A-Z0-9 ]", " ", s)
    s = re.sub(r"\b(HES|HIDROELEKTRIK|SANTRALI|SANTRAL|BARAJI|BARAJ|REGULATORU|VE|DB|BENDI|BENT)\b", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def santral_listesi():
    kod, v = istek(tgt(), "/v1/generation/data/powerplant-list", yontem="GET")
    if kod != 200:
        raise SystemExit(f"Santral listesi alınamadı (HTTP {kod})")
    df = pd.DataFrame(v.get("items", []))
    df.to_csv(CIKTI / "epias_santral_listesi.csv", index=False)
    print(f"  santral listesi: {len(df)} kayıt, alanlar: {list(df.columns)}")
    return df


def eslestir(liste):
    ad_sut = next((c for c in ("name", "shortName", "powerPlantName") if c in liste.columns), None)
    id_sut = next((c for c in ("id", "powerPlantId") if c in liste.columns), None)
    if not ad_sut or not id_sut:
        raise SystemExit(f"Beklenmeyen alanlar: {list(liste.columns)}")
    liste = liste.assign(_sade=liste[ad_sut].map(sade))
    hedef = [("FIRAT", k, k) for k in FIRAT]
    borsa = Path("hes/hes_santraller_borsa.csv")
    if borsa.exists():
        b = pd.read_csv(borsa)
        hedef += [(r["hisse"], r["santral"], sade(r["santral"])) for _, r in b.iterrows()]
    satir = []
    for grup, bizim, anahtar in hedef:
        if not anahtar:
            continue
        # Önce birebir, olmazsa EPİAŞ adı bizim anahtarla başlıyorsa
        aday = liste[liste["_sade"] == anahtar]
        if aday.empty:
            aday = liste[liste["_sade"].str.startswith(anahtar + " ") | (liste["_sade"] == anahtar)]
        if aday.empty and len(anahtar.split()) > 1:
            ilk = anahtar.split()[0]
            if len(ilk) >= 5:
                aday = liste[liste["_sade"].str.split().str[0] == ilk]
        # yalnızca HES kayıtları (biyogaz/RES/JES/ticari unvan benzerlerini ele) ve bilinen yanlış eşleşmeler
        aday = aday[aday[ad_sut].str.upper().str.contains("HES") & ~aday["_sade"].str.match(r"^(KEBAN DERESI|KARAKAYA TRABZON)")]
        for _, a in aday.iterrows():
            satir.append(dict(grup=grup, bizim_ad=bizim, epias_ad=a[ad_sut], powerPlantId=a[id_sut]))
        if aday.empty:
            satir.append(dict(grup=grup, bizim_ad=bizim, epias_ad="", powerPlantId=""))
    e = pd.DataFrame(satir)
    e.to_csv(CIKTI / "epias_santral_eslesme.csv", index=False)
    bulunan = e[e["powerPlantId"] != ""]
    print(f"  eşleşme: {bulunan['bizim_ad'].nunique()}/{e['bizim_ad'].nunique()} santral bulundu "
          f"({len(bulunan)} EPİAŞ kaydı) -> cikti/epias_santral_eslesme.csv")
    return sorted(bulunan["powerPlantId"].astype(int).unique())


def _tarih(d, son=False):
    return f"{d:%Y-%m-%d}T{'23' if son else '00'}:00:00+03:00"


def santral_indir(pid, bas, bitis, yol_csv, var):
    """Parça başarısız olursa (ör. HTTP 400) parçayı küçültür: 90 -> 30 -> 10 -> 3 -> 1 gün.
    Tek gün bile alınamıyorsa o gün atlanır ve cikti/epias_santral_atlanan.csv'ye yazılır."""
    d = max(bas, var.get(pid, bas - timedelta(days=1)) + timedelta(days=1))
    n, boy, ilk_hata = 0, PARCA_GUN, True
    while d <= bitis:
        s = min(d + timedelta(days=boy - 1), bitis)
        kod, v = None, None
        for deneme in range(4):
            try:
                kod, v = istek(tgt(), YOL, {"startDate": _tarih(d), "endDate": _tarih(s, True),
                                           "powerPlantId": int(pid)}, zaman_asimi=180)
                if kod in (200, 400):
                    break
                if kod == 401:
                    _tgt["zaman"] = 0  # bileti yenile
            except Exception as e:
                kod, v = None, e.__class__.__name__
            time.sleep(10 * (deneme + 1))
        if kod != 200:
            if ilk_hata:
                print(f"  santral {pid}: {d}–{s} HTTP {kod}: {str(v)[:300]}", flush=True)
                ilk_hata = False
            if boy > 1:
                boy = max(1, boy // 3)
                continue
            with _kilit:
                pd.DataFrame([dict(powerPlantId=int(pid), gun=str(d), kod=kod, mesaj=str(v)[:200])]).to_csv(
                    CIKTI / "epias_santral_atlanan.csv", mode="a",
                    header=not (CIKTI / "epias_santral_atlanan.csv").exists(), index=False)
            d += timedelta(days=1)
            continue
        p = pd.DataFrame(v.get("items", []))
        if len(p):
            p = p[["date", "total"]].assign(powerPlantId=int(pid))[["powerPlantId", "date", "total"]]
            with _kilit:
                p.to_csv(yol_csv, mode="a", header=not yol_csv.exists(), index=False)
        n += 1
        d = s + timedelta(days=1)
        boy = min(PARCA_GUN, boy * 3)  # başarılıysa yeniden büyüt
        time.sleep(0.3)
    print(f"  santral {pid}: tamam ({n} parça)", flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--baslangic", default="2017-01-01")
    p.add_argument("--paralel", type=int, default=3)
    a = p.parse_args()
    CIKTI.mkdir(exist_ok=True)
    ids = eslestir(santral_listesi())
    yol_csv = CIKTI / "epias_santral_saatlik.csv"
    var = {}
    if yol_csv.exists():
        eski = pd.read_csv(yol_csv)
        eski["gun"] = pd.to_datetime(eski["date"], utc=True).dt.tz_convert("Europe/Istanbul").dt.date
        var = eski.groupby("powerPlantId")["gun"].max().to_dict()
    bas = date.fromisoformat(a.baslangic)
    dun = date.today() - timedelta(days=1)
    print(f"  {len(ids)} santral indiriliyor ({a.paralel} paralel)...", flush=True)
    with ThreadPoolExecutor(a.paralel) as h:
        list(h.map(lambda pid: santral_indir(pid, bas, dun, yol_csv, var), ids))
    df = pd.read_csv(yol_csv).drop_duplicates(["powerPlantId", "date"], keep="last")
    df.to_csv(yol_csv, index=False)
    print(f"  -> {yol_csv} ({len(df)} satır, {df['powerPlantId'].nunique()} santral)")


if __name__ == "__main__":
    main()
