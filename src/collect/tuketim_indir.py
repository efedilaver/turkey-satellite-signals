#!/usr/bin/env python3
"""EPİAŞ gerçek zamanlı tüketim (saatlik, MWh), 2017-01-01'den düne -> cikti/epias_tuketim_saatlik.csv
   python tuketim_indir.py      (kullanıcı adı/şifre .env'den; epias_indir.py ile aynı giriş)"""
from datetime import date, timedelta
from epias_dene import CIKTI, tgt_al
from epias_indir import seri_indir

if __name__ == "__main__":
    tgt = tgt_al()
    seri_indir(tgt, "/v1/consumption/data/realtime-consumption", "Tüketim", date(2017, 1, 1),
               date.today() - timedelta(days=1), CIKTI / "epias_tuketim_saatlik.csv")
