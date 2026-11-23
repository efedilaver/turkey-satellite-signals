#!/usr/bin/env python3
"""
Tek komutla bütün veri toplama. Kaldığı yerden devam eder; tekrar çalıştırmak güvenlidir.

  python hepsi.py              # her şeyi topla (ilk sefer saatler sürebilir, sonra dakikalar)
  python hepsi.py --zamanla    # günlük/haftalık otomatik çalıştırmayı kur (Mac, bir kez)
  python hepsi.py --sadece gee # yalnızca bir grubu çalıştır (gee / epias / hisse)

Ne yapar (paralel):
  1) Earth Engine (sunucuda hesaplanır, yalnızca sayılar iner):
       kar, Fırat barajları, fındık don endeksi, TRALT maden sahaları, çelik tesisleri
  2) EPİAŞ: PTF ve kaynak bazında üretim (güncelleme) + barajların bugünkü durumu (arşiv)
     + santral bazında üretim (Fırat barajları ve borsa şirketlerinin HES'leri)
  3) Hisse ve altın fiyatları

İlk çalıştırmada eksik ayarları (Earth Engine proje kimliği, EPİAŞ kullanıcı bilgisi) bir kez
sorar ve klasördeki .env dosyasına yazar. .env yalnızca bu bilgisayarda kalır.
Günlükler: cikti/log_*.txt   Özet: cikti/hepsi_durum.txt
"""
import argparse
import getpass
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

KLASOR = Path(__file__).resolve().parents[2]  # depo kökü (src/collect/ -> kök)
BETIK = "src/collect/"
CIKTI = KLASOR / "cikti"
ENV = KLASOR / ".env"


def env_oku():
    d = {}
    if ENV.exists():
        for s in ENV.read_text(encoding="utf-8").splitlines():
            if "=" in s and not s.strip().startswith("#"):
                k, v = s.split("=", 1)
                d[k.strip()] = v.strip().strip('"').strip("'")
    return d


def env_hazirla(etkilesimli=True):
    d = env_oku()
    eksik = [k for k in ("GEE_PROJECT", "EPTR_USERNAME", "EPTR_PASSWORD") if not d.get(k)]
    if not eksik:
        return d
    if not etkilesimli:
        sys.exit(f".env eksik: {eksik}. Bir kez elle 'python src/collect/hepsi.py' çalıştır.")
    print("Bir kerelik ayar (cevaplar yalnızca bu bilgisayardaki .env dosyasına yazılır):")
    if "GEE_PROJECT" in eksik:
        d["GEE_PROJECT"] = input("  Earth Engine proje kimliği (ID): ").strip()
    if "EPTR_USERNAME" in eksik:
        d["EPTR_USERNAME"] = input("  EPİAŞ kullanıcı adı (e-posta): ").strip()
    if "EPTR_PASSWORD" in eksik:
        d["EPTR_PASSWORD"] = getpass.getpass("  EPİAŞ şifresi (görünmez): ")
    ENV.write_text("".join(f"{k}={v}\n" for k, v in d.items()), encoding="utf-8")
    os.chmod(ENV, 0o600)
    print("  -> .env kaydedildi (yalnızca senin kullanıcın okuyabilir)\n")
    return d


def calistir(ad, komut):
    """Bir adımı alt süreç olarak çalıştırır; çıktısını cikti/log_<ad>.txt'ye yazar."""
    log = CIKTI / f"log_{ad}.txt"
    t0 = time.time()
    with open(log, "a", encoding="utf-8") as f:
        f.write(f"\n===== {datetime.now():%Y-%m-%d %H:%M} {' '.join(komut)}\n")
        f.flush()
        r = subprocess.run([sys.executable, *komut], cwd=KLASOR, stdout=f, stderr=subprocess.STDOUT,
                           stdin=subprocess.DEVNULL)
    sure = (time.time() - t0) / 60
    durum = "TAMAM" if r.returncode == 0 else f"HATA (kod {r.returncode})"
    print(f"  [{ad}] {durum}  ({sure:.0f} dk)  -> {log.name}", flush=True)
    return ad, durum, sure


def adimlar(env, sadece=None):
    proje = env["GEE_PROJECT"]
    g = {
        "gee_kar": [BETIK + "gee_topla.py", "kar", "--proje", proje],
        "gee_firat": [BETIK + "gee_topla.py", "firat", "--proje", proje],
        "gee_don": [BETIK + "gee_topla.py", "don", "--proje", proje],
        "gee_maden": [BETIK + "gee_topla.py", "maden", "--proje", proje],
        "gee_celik": [BETIK + "gee_topla.py", "celik", "--proje", proje],
        "epias": [BETIK + "epias_indir.py"],
        "epias_santral": [BETIK + "epias_santral.py"],
        "hisse": [BETIK + "hisse_indir.py"],
    }
    if sadece:
        g = {k: v for k, v in g.items() if k.startswith(sadece)}
    return g


def zamanla():
    """macOS launchd: her gün 18:30'da EPİAŞ güncellemesi + baraj arşivi, her Cuma 19:00'da tam toplama."""
    if sys.platform != "darwin":
        sys.exit("Otomatik zamanlama şimdilik yalnızca macOS için.")
    la = Path.home() / "Library/LaunchAgents"
    la.mkdir(parents=True, exist_ok=True)
    isler = {
        "com.uydusinyal.gunluk": ([BETIK + "epias_indir.py"], "<dict><key>Hour</key><integer>18</integer><key>Minute</key><integer>30</integer></dict>"),
        "com.uydusinyal.haftalik": ([BETIK + "hepsi.py", "--otomatik"],
                                    "<dict><key>Weekday</key><integer>5</integer><key>Hour</key><integer>19</integer><key>Minute</key><integer>0</integer></dict>"),
    }
    for etiket, (komut, takvim) in isler.items():
        arg = "".join(f"<string>{x}</string>" for x in [sys.executable, *komut])
        plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>Label</key><string>{etiket}</string>
<key>ProgramArguments</key><array>{arg}</array>
<key>WorkingDirectory</key><string>{KLASOR}</string>
<key>StartCalendarInterval</key>{takvim}
<key>StandardOutPath</key><string>{CIKTI / (etiket + '.log')}</string>
<key>StandardErrorPath</key><string>{CIKTI / (etiket + '.log')}</string>
</dict></plist>
"""
        yol = la / f"{etiket}.plist"
        yol.write_text(plist, encoding="utf-8")
        subprocess.run(["launchctl", "unload", str(yol)], capture_output=True)
        subprocess.run(["launchctl", "load", str(yol)], check=False)
        print(f"  kuruldu: {etiket}")
    print("Bilgisayar o saatte uykudaysa iş, uyandığında çalışır. Kaldırmak için:"
          "\n  launchctl unload ~/Library/LaunchAgents/com.uydusinyal.*.plist")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--zamanla", action="store_true")
    p.add_argument("--sadece", choices=["gee", "epias", "hisse"])
    p.add_argument("--paralel", type=int, default=4)
    p.add_argument("--otomatik", action="store_true", help=argparse.SUPPRESS)
    a = p.parse_args()
    CIKTI.mkdir(exist_ok=True)
    env = env_hazirla(etkilesimli=not a.otomatik)
    if a.zamanla:
        zamanla()
        return
    g = adimlar(env, a.sadece)
    print(f"{len(g)} adım, en fazla {a.paralel} paralel. Ayrıntılar cikti/log_*.txt dosyalarında.\n", flush=True)
    with ThreadPoolExecutor(a.paralel) as h:
        sonuc = list(h.map(lambda kv: calistir(*kv), g.items()))
    ozet = [f"{datetime.now():%Y-%m-%d %H:%M}"] + [f"{ad}: {d} ({s:.0f} dk)" for ad, d, s in sonuc]
    (CIKTI / "hepsi_durum.txt").write_text("\n".join(ozet) + "\n", encoding="utf-8")
    print("\nÖzet: cikti/hepsi_durum.txt")


if __name__ == "__main__":
    main()
