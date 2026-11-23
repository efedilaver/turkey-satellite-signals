#!/usr/bin/env python3
"""
EPİAŞ Şeffaflık servislerini deneyen kısa betik.

Ne öğrenmek istiyoruz?
  1) Baraj servisleri (doluluk, hacim, kot) GEÇMİŞ veri veriyor mu, yoksa sadece bugünü mü?
  2) Elektrik fiyatı (PTF) ve kaynak bazında gerçek zamanlı üretim nasıl geliyor?

Kullanıcı adı / şifre:
  - Klasörde .env dosyası varsa oradan okunur:
        EPTR_USERNAME=eposta@adresin.com
        EPTR_PASSWORD=sifren
  - Yoksa çalışırken sorulur (şifre ekranda görünmez).
  Bu betik şifreyi hiçbir dosyaya ya da çıktıya yazmaz. (Not: hepsi.py ilk kurulumda
  girilen bilgileri git'e girmeyen .env dosyasına, yalnız kullanıcının okuyabileceği izinle yazar.)

Çıktı: cikti/epias_deneme.txt  (yalnızca veri özetleri)
"""
import getpass
import json
import os
import sys
from pathlib import Path

import requests

GIRIS = "https://giris.epias.com.tr/cas/v1/tickets"
TABAN = "https://seffaflik.epias.com.tr/electricity-service"
CIKTI = Path("cikti")
SAYFA = {"number": 1, "size": 1000}


def env_oku():
    d = {}
    p = Path(".env")
    if p.exists():
        for satir in p.read_text(encoding="utf-8").splitlines():
            if "=" in satir and not satir.strip().startswith("#"):
                k, v = satir.split("=", 1)
                d[k.strip()] = v.strip().strip('"').strip("'")
    return d


def tgt_al():
    env = env_oku()
    kullanici = env.get("EPTR_USERNAME") or os.environ.get("EPTR_USERNAME") or input("EPİAŞ kullanıcı adı (e-posta): ").strip()
    sifre = env.get("EPTR_PASSWORD") or os.environ.get("EPTR_PASSWORD") or getpass.getpass("EPİAŞ şifresi (görünmez): ")
    r = requests.post(GIRIS, data={"username": kullanici, "password": sifre},
                      headers={"Accept": "text/plain"}, timeout=30)
    if r.status_code != 201 or not r.text.startswith("TGT-"):
        sys.exit(f"Giriş başarısız (HTTP {r.status_code}). Kullanıcı adı/şifreyi kontrol et.")
    return r.text.strip()


def istek(tgt, yol, govde=None, yontem="POST", zaman_asimi=60):
    url = f"{TABAN}{yol}"
    h = {"TGT": tgt, "Accept": "application/json", "Content-Type": "application/json"}
    r = requests.request(yontem, url, headers=h, json=govde, timeout=zaman_asimi)
    try:
        veri = r.json()
    except ValueError:
        veri = r.text[:300]
    return r.status_code, veri


def ozet(ad, kod, veri, rapor, tarih_alani="date"):
    rapor.append(f"\n=== {ad}  (HTTP {kod}) ===")
    if kod != 200:
        rapor.append(f"  Hata: {str(veri)[:400]}")
        return []
    items = veri.get("items", veri) if isinstance(veri, dict) else veri
    if isinstance(veri, dict) and "damList" in veri:
        items = veri["damList"]
    if not isinstance(items, list):
        rapor.append(f"  Beklenmeyen yapı: {str(veri)[:400]}")
        return []
    rapor.append(f"  Kayıt sayısı: {len(items)}")
    if items and isinstance(items[0], dict):
        rapor.append(f"  Alanlar: {list(items[0].keys())}")
        tarihler = sorted({str(i.get(tarih_alani))[:10] for i in items if i.get(tarih_alani)})
        if tarihler:
            rapor.append(f"  Tarih aralığı: {tarihler[0]} – {tarihler[-1]}  ({len(tarihler)} farklı gün)")
        rapor.append(f"  İlk kayıt: {json.dumps(items[0], ensure_ascii=False)[:400]}")
    elif items:
        rapor.append(f"  İlk 15: {items[:15]}")
    if isinstance(veri, dict) and veri.get("page"):
        rapor.append(f"  Sayfa bilgisi: {veri['page']}")
    return items


def main():
    CIKTI.mkdir(exist_ok=True)
    tgt = tgt_al()
    print("Giriş başarılı, servisler deneniyor...")
    rapor = ["EPİAŞ Şeffaflık deneme sonuçları"]

    kod, v = istek(tgt, "/v1/dams/data/basin-list", yontem="GET")
    ozet("Havza listesi", kod, v, rapor)

    kod, v = istek(tgt, "/v1/dams/data/dam-list", {})
    barajlar = ozet("Baraj listesi", kod, v, rapor)

    kod, v = istek(tgt, "/v1/dams/data/active-fullness", {"page": SAYFA})
    doluluk = ozet("Aktif doluluk (tüm barajlar, parametresiz)", kod, v, rapor)
    if doluluk:
        adlar = sorted({str(i.get("dam")) for i in doluluk})
        rapor.append(f"  Barajlar ({len(adlar)}): {', '.join(adlar)}")
        hedef = [a for a in adlar if any(k in a.upper() for k in ["ATATÜRK", "ATATURK", "KEBAN", "KARAKAYA"])]
        rapor.append(f"  Atatürk/Keban/Karakaya listede mi? -> {hedef or 'HAYIR'}")

    # Servis baraj adıyla birlikte havza adını da istiyor; havzayı doluluk listesinden bul
    havzalar = {str(i.get("dam")).strip(): i.get("basin") for i in (doluluk or [])}
    for ornek in ["YAMULA", "KEMER", "MENZELET"]:
        havza = havzalar.get(ornek)
        if not havza:
            continue
        rapor.append(f"\n(Geçmiş veri testi: {ornek} / {havza})")
        for ad, yol in [("Günlük hacim", "/v1/dams/data/daily-volume"),
                        ("Günlük kot", "/v1/dams/data/daily-kot"),
                        ("Aktif hacim", "/v1/dams/data/active-volume")]:
            kod, v = istek(tgt, yol, {"basinName": havza, "damName": ornek, "page": SAYFA})
            ozet(f"{ad} – {ornek}", kod, v, rapor)
        if ornek != "YAMULA":
            continue
        # Havza bazında (baraj adı olmadan) da dene
        kod, v = istek(tgt, "/v1/dams/data/daily-volume", {"basinName": havza, "page": SAYFA})
        ozet(f"Günlük hacim – tüm {havza} havzası", kod, v, rapor)

    # Fiyat ve üretim geçmişinin 2017'ye gittiği ilk denemede doğrulandı; burada
    # tek istekte en fazla kaç gün alınabildiğini (indirme planı için) ölçüyoruz.
    g = {"startDate": "2026-01-01T00:00:00+03:00", "endDate": "2026-03-31T23:00:00+03:00"}
    kod, v = istek(tgt, "/v1/markets/dam/data/mcp", g)
    ozet("PTF – 3 aylık tek istek", kod, v, rapor)
    kod, v = istek(tgt, "/v1/generation/data/realtime-generation", g)
    ozet("Üretim – 3 aylık tek istek", kod, v, rapor)

    metin = "\n".join(rapor)
    (CIKTI / "epias_deneme.txt").write_text(metin, encoding="utf-8")
    print(metin)
    print(f"\n-> {CIKTI / 'epias_deneme.txt'}")


if __name__ == "__main__":
    main()
