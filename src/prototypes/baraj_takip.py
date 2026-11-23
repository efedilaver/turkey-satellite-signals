#!/usr/bin/env python3
"""
Baraj su yüzeyi takibi — Sentinel-2 (ücretsiz, hesap gerektirmez)

Fikir (videodaki tank yönteminin Türkiye uyarlaması):
  1. Sentinel-2 görüntülerinde suyu MNDWI indeksiyle ayır.
  2. Her baraj için su yüzey alanını (km²) zaman serisi olarak çıkar.
  3. Yöntemi, İSKİ'nin yayımladığı günlük doluluk oranlarıyla DOĞRULA
     (videodaki "önce kamuya açık veriyle test et" adımı).
  4. Doğrulanmış yöntemi, düzenli verisi olmayan büyük HES barajlarına uygula
     ve mevsim normaline göre anomali (kuraklık / bolluk sinyali) üret.

Komutlar:
  python baraj_takip.py uydu     --grup istanbul --baslangic 2017-01-01
  python baraj_takip.py dogrula  [--iski iski.xlsx]
  python baraj_takip.py uydu     --grup hes --baslangic 2018-01-01
  python baraj_takip.py anomali  --grup hes

Çıktılar ./cikti/ klasörüne yazılır.
"""
from __future__ import annotations

import argparse
import math
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import ndimage

CIKTI = Path("cikti")

STAC_URL = "https://earth-search.aws.element84.com/v1"
KOLEKSIYON = "sentinel-2-l2a"

# İBB Açık Veri Portalı: İstanbul Barajları Günlük Doluluk Oranları (İSKİ)
ISKI_URL = (
    "https://data.ibb.gov.tr/dataset/86658ecd-f3f7-4ca4-a313-ae6204f21959/"
    "resource/af0b3902-cfd9-4096-85f7-e2c3017e4f21/download/"
    "istanbul-dams-daily-occupancy-rates.xlsx"
)

# ---------------------------------------------------------------------------
# Baraj tanımları
#   bbox  : (batı boylam, güney enlem, doğu boylam, kuzey enlem) — gölü kapsayan kutu
#   tohum : (enlem, boylam) — gölün İÇİNDE bir nokta. Kutuda deniz/başka göl varsa
#           doğru su kütlesini seçmek için kullanılır.
#   cozunurluk : metre. Küçük göller 20 m, büyük HES gölleri 60 m (indirme hızı için).
#   iski  : İSKİ tablosundaki sütun adı (doğrulama için).
# Koordinatlar yaklaşıktır: ilk çalıştırmada cikti/onizleme_*.png dosyalarına bakıp
# seçilen su kütlesinin doğru göl olduğunu kontrol et, gerekirse burayı düzelt.
# ---------------------------------------------------------------------------
BARAJLAR = {
    "istanbul": {
        # Konumlar gerçek Sentinel-2 görüntülerinden doğrulandı (tohum = gölün en iç noktası,
        # kutu = ölçülen göl sınırı + en az 3 km pay). Ölçülen alanlar kurak dönemlere ait.
        # Elmalı çıkarıldı: 20 m çözünürlükte güvenilir ölçülemeyecek kadar küçük (~%1 kapasite).
        # Büyük göller 40 m'de okunur (göl yine 7000+ piksel; indirme ~4 kat azalır)
        "Omerli":       dict(bbox=(29.283, 40.976, 29.490, 41.111), tohum=(41.0569, 29.3738), cozunurluk=40, iski="Omerli"),        # 2024-08: 11,2 km²
        "Terkos":       dict(bbox=(28.473, 41.264, 28.721, 41.415), tohum=(41.3259, 28.5552), cozunurluk=40, iski="Terkos"),        # 2024-09: 19,6 km²
        "Buyukcekmece": dict(bbox=(28.476, 40.994, 28.633, 41.135), tohum=(41.0510, 28.5650), cozunurluk=40, iski="Buyukcekmece"),  # 2024-09: 21,9 km²
        "Sazlidere":    dict(bbox=(28.621, 41.080, 28.772, 41.185), tohum=(41.1110, 28.7165), cozunurluk=20, iski="Sazlidere"),     # 2023-05: 4,3 km²
        "Alibey":       dict(bbox=(28.845, 41.076, 28.965, 41.172), tohum=(41.1143, 28.9198), cozunurluk=20, iski="Alibey"),        # 2023-05: 1,9 km²
        "Darlik":       dict(bbox=(29.511, 41.059, 29.628, 41.141), tohum=(41.1003, 29.5739), cozunurluk=20, iski="Darlik"),        # 2024-09: 1,7 km²
    },
    # Büyük hidroelektrik barajları — İSKİ gibi günlük açık veri yok; anomali sinyali buradan.
    "hes": {
        "Ataturk":  dict(bbox=(38.20, 37.40, 39.10, 38.00), tohum=(37.560, 38.420), cozunurluk=60, arama_km=8),
        "Keban":    dict(bbox=(38.55, 38.65, 39.75, 39.15), tohum=(38.830, 38.800), cozunurluk=60, arama_km=8),
        "Karakaya": dict(bbox=(38.40, 38.20, 39.20, 38.60), tohum=(38.300, 39.050), cozunurluk=60, arama_km=8),
    },
}

# Sentinel-2 Sahne Sınıflandırma (SCL) katmanında geçersiz sayılan sınıflar:
# 0 veri yok, 1 doymuş/hatalı, 3 bulut gölgesi, 8-9 bulut, 10 ince sirrus, 11 kar/buz
SCL_GECERSIZ = (0, 1, 3, 8, 9, 10, 11)


# ===========================================================================
# Saf analiz fonksiyonları (ağ gerektirmez, demo_sentetik.py bunları test eder)
# ===========================================================================
def mndwi(green: np.ndarray, swir: np.ndarray) -> np.ndarray:
    """Modified NDWI = (Yeşil - SWIR) / (Yeşil + SWIR). Su > 0, kara < 0."""
    with np.errstate(divide="ignore", invalid="ignore"):
        return (green - swir) / (green + swir)


def gecerli_maske(scl: np.ndarray) -> np.ndarray:
    return ~np.isin(scl, SCL_GECERSIZ)


def su_kutlesi_sec(su: np.ndarray, tohum_rc: tuple[int, int], arama_px: int) -> np.ndarray:
    """
    Su maskesindeki bağlı bileşenlerden tohum noktasına en yakın olanı seç.
    Tohum suyun içindeyse o bileşen; değilse arama yarıçapı içindeki en yakın
    bileşen (eşitlikte büyük olan). Hiçbiri yoksa boş maske.
    Bu sayede aynı kutudaki deniz veya küçük göletler sayılmaz.
    """
    etiket, n = ndimage.label(su)
    if n == 0:
        return np.zeros_like(su, dtype=bool)
    r, c = tohum_rc
    h, w = su.shape
    if 0 <= r < h and 0 <= c < w and etiket[r, c] > 0:
        return etiket == etiket[r, c]
    # Tohumdan her piksele uzaklık; yalnızca yarıçap içindeki bileşenler aday
    r0, r1 = max(0, r - arama_px), min(h, r + arama_px + 1)
    c0, c1 = max(0, c - arama_px), min(w, c + arama_px + 1)
    pencere = etiket[r0:r1, c0:c1]
    if not pencere.any():
        return np.zeros_like(su, dtype=bool)
    rr, cc = np.nonzero(pencere)
    mesafe = np.hypot(rr + r0 - r, cc + c0 - c)
    ok = mesafe <= arama_px
    if not ok.any():
        return np.zeros_like(su, dtype=bool)
    adaylar = pencere[rr[ok], cc[ok]]
    mes = mesafe[ok]
    boyut = np.bincount(etiket.ravel())
    # en yakın; yakınlık eşitse büyük olan
    sira = np.lexsort((-boyut[adaylar], mes))
    return etiket == adaylar[sira[0]]


def sahne_analiz(green, swir, scl, tohum_rc, piksel_m, arama_px,
                 esik=0.0, min_gecerli=0.90):
    """
    Tek bir tarihin bantlarından gölün su alanını çıkar.
    Dönüş: dict(alan_km2, gecerli_oran, su_maske) — bulutluysa alan_km2 = NaN.

    Bulut kontrolü gölün çevresinde yapılır (su kütlesinin tamponlu kutusu):
    göl bulut altında kalırsa alan eksik ölçülür, bu yüzden o sahne atlanır.
    """
    gecerli = gecerli_maske(scl) & np.isfinite(green) & np.isfinite(swir)
    su = (mndwi(green, swir) > esik) & gecerli
    # SCL'de bulutlu ama gerçekte su olan pikselleri bilemeyiz; önce suyu seç,
    # sonra seçilen kütlenin çevresindeki geçerlilik oranına bak.
    kutle = su_kutlesi_sec(su, tohum_rc, arama_px)
    if kutle.any():
        rr, cc = np.nonzero(kutle)
        pad = max(5, int(0.1 * max(np.ptp(rr), np.ptp(cc))))
        r0, r1 = max(0, rr.min() - pad), min(su.shape[0], rr.max() + pad + 1)
        c0, c1 = max(0, cc.min() - pad), min(su.shape[1], cc.max() + pad + 1)
        oran = float(gecerli[r0:r1, c0:c1].mean())
        # Bulut göle değiyorsa (içinde delik açıyor ya da kıyısını örtüyorsa) alan eksik
        # ölçülür: göl kütlesine bitişik geçersiz piksel oranına da bak.
        komsu = ndimage.binary_dilation(kutle, iterations=2) & ~gecerli
        degen = komsu.sum() / kutle.sum()
    else:
        oran, degen = float(gecerli.mean()), 1.0
    alan = kutle.sum() * piksel_m**2 / 1e6
    if oran < min_gecerli or degen > 0.005 or not kutle.any():
        alan = float("nan")
    return dict(alan_km2=alan, gecerli_oran=oran, su_maske=kutle)


def iski_oku(kaynak) -> pd.DataFrame:
    """İSKİ günlük doluluk tablosunu oku; değerleri yüzdeye (0-100) çevir."""
    kaynak = str(kaynak)
    df = pd.read_excel(kaynak) if kaynak.lower().endswith((".xlsx", ".xls")) else pd.read_csv(kaynak)
    tarih_sut = next(c for c in df.columns if str(c).strip().lower() in ("tarih", "date"))
    df["tarih"] = pd.to_datetime(df[tarih_sut], dayfirst=True, errors="coerce")
    df = df.drop(columns=[tarih_sut]).dropna(subset=["tarih"]).set_index("tarih").sort_index()
    df = df.apply(pd.to_numeric, errors="coerce")
    if df.max().max() <= 1.5:  # oran olarak verilmişse
        df = df * 100
    return df


def alan_dolulugu_esle(alan: pd.Series, doluluk: pd.Series, tolerans_gun=1) -> pd.DataFrame:
    """Uydu tarihlerini en yakın İSKİ gününe eşle (± tolerans)."""
    a = alan.dropna().rename("alan_km2").to_frame().sort_index()
    d = doluluk.dropna().rename("doluluk").to_frame().sort_index()
    return pd.merge_asof(a, d, left_index=True, right_index=True,
                         tolerance=pd.Timedelta(days=tolerans_gun),
                         direction="nearest").dropna()


def yil_disli_dogrulama(eslesme: pd.DataFrame) -> pd.DataFrame:
    """
    Alan -> doluluk ilişkisini monoton (izotonik) regresyonla kur ve
    'bir yılı dışarıda bırak' çapraz doğrulamasıyla örneklem dışı tahmin üret.
    Böylece model test ettiği yılı hiç görmeden tahmin yapar.
    """
    from sklearn.isotonic import IsotonicRegression

    sonuc = eslesme.copy()
    sonuc["tahmin"] = np.nan
    yillar = sonuc.index.year
    for y in np.unique(yillar):
        egitim = sonuc[yillar != y]
        if len(egitim) < 8:
            continue
        x, hedef = egitim["alan_km2"].to_numpy(), egitim["doluluk"].to_numpy()
        m = IsotonicRegression(increasing=True, out_of_bounds="clip").fit(x, hedef)
        xt = sonuc.loc[yillar == y, "alan_km2"].to_numpy()
        tahmin = m.predict(xt)
        # Eğitimde hiç görülmemiş (ör. rekor kuraklık) seviyeler: izotonik model kenarda
        # sabitlenir; bunun yerine uçtaki %25'lik dilime doğru çizgisiyle dışa uzat.
        for kenar, sec in (("alt", xt < x.min()), ("ust", xt > x.max())):
            if not sec.any():
                continue
            q = np.quantile(x, 0.25 if kenar == "alt" else 0.75)
            dilim = (x <= q) if kenar == "alt" else (x >= q)
            egim, kesisim = np.polyfit(x[dilim], hedef[dilim], 1)
            tahmin[sec] = np.clip(egim * xt[sec] + kesisim, 0, 100)
        sonuc.loc[yillar == y, "tahmin"] = tahmin
    return sonuc


def mevsimsel_anomali(alan: pd.Series) -> pd.DataFrame:
    """
    Aylık medyan alanı, aynı ayın tüm yıllardaki medyanıyla kıyasla.
    anomali_yuzde > 0  -> mevsim normalinden fazla su (bol yıl)
    anomali_yuzde < 0  -> kurak
    """
    aylik = alan.dropna().resample("MS").median().dropna().to_frame("alan_km2")
    norm = aylik.groupby(aylik.index.month)["alan_km2"].median()
    aylik["normal_km2"] = norm.reindex(aylik.index.month).to_numpy()
    aylik["anomali_yuzde"] = 100 * (aylik["alan_km2"] / aylik["normal_km2"] - 1)
    return aylik


# ===========================================================================
# Veri indirme (internet gerektirir)
# ===========================================================================
def _utm_epsg(lon, lat):
    zon = int((lon + 180) // 6) + 1
    return (32600 if lat >= 0 else 32700) + zon


def _bant_anahtari(item, adaylar):
    for k in adaylar:
        if k in item.assets:
            return k
    raise KeyError(f"{adaylar} bantlarından hiçbiri yok: {list(item.assets)}")


def dn_ofset_tespit(swir_dn: np.ndarray, scl: np.ndarray) -> int:
    """
    Sentinel-2'nin yeni işleme sürümlerinde piksel değerlerine (DN) +1000 eklenir. Oran
    indekslerinde (MNDWI) bu ofset çıkarılmazsa sonuç tamamen bozulur.

    Earth Search metadatası buna güvenilir şekilde karar vermeye yetmiyor. Gerçek pikseller
    kontrol edildi (Ömerli, su pikselleri, SWIR): 2022 ve 2024 sahnelerinde ~75-185 (ofset yok),
    yeniden işlenmiş 2018 sahnesinde ~1040 (ofset var). Oysa üçünde de metadata aynı şeyi söylüyor.

    Bu yüzden ofset her sahnede piksellerden tespit edilir: kutuda göl olduğu için en karanlık
    SWIR pikselleri (temiz su, yansıma < %1) ofset yoksa ~0-150, ofset varsa ~1000-1150 olur.
    """
    # 1) SCL'nin "su" dediği pikseller yeterliyse en güvenilir ölçüt onların medyanı
    su = (scl == 6) & (swir_dn > 0)
    if su.sum() >= 200:
        return 1000 if np.median(swir_dn[su]) >= 700 else 0
    # 2) Yoksa en karanlık %0,5'lik dilim (su, gölge). Ofsetliyken DN 1000'in altına inemez.
    gecerli = (swir_dn > 0) & gecerli_maske(scl)
    if gecerli.sum() < 50:
        gecerli = swir_dn > 0
    if not gecerli.any():
        return 0
    return 1000 if np.nanpercentile(swir_dn[gecerli], 0.5) >= 900 else 0


def dn_ofset_karar(item, swir_dn: np.ndarray, scl: np.ndarray) -> int:
    """
    Ofsete önce sahnenin kimliğine bakarak karar ver, piksellere yalnızca güçlü çelişki varsa uy.

    Gerçek piksellerle doğrulanan kural (Ömerli su pikselleri, SWIR):
      - işleme sürümü < 04.00                 -> ofset yok
      - '_0_' kopyaları (2022, 2024, 2026)    -> ofset yok (~75-185)
      - '_1_' kopyaları (2018, 2026)          -> ofset var (~1040-1330)
    Yalnızca piksellere bakmak yetmedi: güneş parlaması (glint) olan yaz günlerinde göl SWIR'da
    parlaklaşıp ofsetsiz sahneyi ofsetli gösterdi (2026-05-16, 2026-06-05 -> alan ~0).
    """
    p = item.properties
    try:
        surum = float(p.get("s2:processing_baseline", "0"))
    except ValueError:
        surum = 0.0
    if surum < 4.0:
        kural = 0
    elif _surum_eki(item) != "0":
        kural = 1000
    else:
        kural = 0 if p.get("earthsearch:boa_offset_applied") is not False else 1000
    gecerli = (swir_dn > 0) & gecerli_maske(scl)
    if gecerli.sum() >= 1000:
        p1 = np.percentile(swir_dn[gecerli], 1)
        if kural == 0 and p1 >= 1000:   # ofsetsiz veride en karanlık %1 bile %10 yansıma olamaz
            return 1000
        if kural == 1000 and p1 < 700:  # ofsetli veride DN 1000'in altına inemez
            return 0
    return kural


def aykiri_temizle(alan: pd.Series, pencere="45D", esik=0.15) -> pd.Series:
    """
    Göl alanı günler içinde sıçramaz. Çevresindeki 45 günün medyanından %15'ten fazla sapan
    ölçümler (kısmi bulut, gölge, parlama) atılır.
    """
    a = alan.dropna().sort_index()
    if len(a) < 5:
        return a
    med = a.rolling(pencere, center=True, min_periods=3).median()
    return a[~((a / med - 1).abs() > esik)]


def _surum_eki(item) -> str:
    """'S2B_35TPF_20260607_0_L2A' -> '0'. Aynı sahnenin farklı işlenmiş kopyalarını ayırır."""
    parca = item.id.split("_")
    return parca[-2] if len(parca) >= 2 else ""


def gun_itemlerini_sec(its: list) -> list:
    """
    Earth Search'te aynı gün ve pafta için birden fazla kopya olabiliyor (ör. ..._0_L2A ve
    ..._1_L2A). Kontrol edilen örneklerde _1_ kopyalarında +1000 ofset vardı, _0_'da yoktu.
    Birleştirince ofsetli ve ofsetsiz pikseller karışıp sonucu bozuyor. Bu yüzden bir günde
    _0_ kopyası varsa yalnızca onlar, yoksa en küçük sürüm ekine sahip olanlar kullanılır;
    her paftadan da tek kopya tutulur.
    """
    ekler = sorted({_surum_eki(i) for i in its})
    secili = [i for i in its if _surum_eki(i) == ekler[0]]
    pafta = {}
    for i in secili:
        pafta.setdefault(i.properties.get("grid:code", i.id), i)
    return list(pafta.values())


GDAL_AYARLARI = dict(
    AWS_NO_SIGN_REQUEST="YES",
    GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
    CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif",
    GDAL_HTTP_MULTIRANGE="YES",
    GDAL_HTTP_MERGE_CONSECUTIVE_RANGES="YES",
    VSI_CACHE="TRUE",
    # Ağ takılmalarına karşı: bağlantı 30 sn, okuma 120 sn'de kesilsin, GDAL kendisi 3 kez denesin
    GDAL_HTTP_CONNECTTIMEOUT="30",
    GDAL_HTTP_TIMEOUT="120",
    GDAL_HTTP_MAX_RETRY="3",
    GDAL_HTTP_RETRY_DELAY="5",
)


def _item_epsg(item):
    p = item.properties
    kod = p.get("proj:epsg") or p.get("proj:code")
    if isinstance(kod, str):
        kod = kod.split(":")[-1]
    try:
        return int(kod)
    except (TypeError, ValueError):
        return None


def gun_paftalarini_sec(its: list, epsg: int, bbox_poligon) -> list:
    """
    Bir gün için okunacak sahneleri seç:
      1) Aynı sahnenin farklı işlenmiş kopyalarından tek sürümü tut (gun_itemlerini_sec).
      2) Yalnızca hedef UTM dilimindeki paftalar (piksel ızgarası birebir hizalı okunabilsin).
      3) Kutuyu TEK BAŞINA tamamen kapsayan bir pafta varsa sadece onu oku (veri yarıya iner);
         yoksa kapsayanları birleştir.
    """
    from shapely.geometry import shape

    its = [i for i in gun_itemlerini_sec(its) if _item_epsg(i) == epsg]
    if not its:
        return []
    for i in sorted(its, key=lambda x: x.properties.get("eo:cloud_cover", 100)):
        try:
            if shape(i.geometry).contains(bbox_poligon):
                return [i]
        except Exception:
            pass
    return its


def bant_oku(href: str, sinirlar, sekil, resampling) -> np.ndarray:
    """
    COG'den kutuyu hedef ızgarada okur. İstenen çözünürlük dosyanınkinden kabaysa GDAL
    otomatik olarak sunucudaki hazır düşük çözünürlüklü kopyayı (overview) okur; yani
    10 m'lik yeşil bant 20 m'de okunurken ~4 kat daha az veri iner.
    """
    import rasterio
    from rasterio.windows import from_bounds

    with rasterio.open(href) as src:
        pencere = from_bounds(*sinirlar, transform=src.transform)
        return src.read(1, window=pencere, out_shape=sekil, boundless=True,
                        fill_value=0, resampling=resampling)


def ayda_en_iyi_gunler(gruplar: dict, ayda_en_fazla: int | None) -> dict:
    """Her ayın en az bulutlu N gününü tut (doğrulama/anomali için ayda birkaç ölçüm yeterli)."""
    if not ayda_en_fazla:
        return gruplar
    aylik = defaultdict(list)
    for gun, its in gruplar.items():
        bulut = min(i.properties.get("eo:cloud_cover", 100) for i in its)
        aylik[(gun.year, gun.month)].append((bulut, gun))
    secili = {gun for liste in aylik.values() for _, gun in sorted(liste)[:ayda_en_fazla]}
    return {g: its for g, its in gruplar.items() if g in secili}


def uydu_seri_cikar(ad, tanim, baslangic, bitis, max_bulut=30, onizleme=True, paralel=8,
                    ayda_en_fazla=4, atla=frozenset(), kaydet=None):
    import pystac_client
    import rasterio
    from rasterio.enums import Resampling
    from pyproj import Transformer
    from shapely.geometry import box

    katalog = pystac_client.Client.open(STAC_URL)
    bbox = tanim["bbox"]
    arama = katalog.search(collections=[KOLEKSIYON], bbox=bbox,
                           datetime=f"{baslangic}/{bitis}",
                           query={"eo:cloud_cover": {"lt": max_bulut}})
    itemler = list(arama.items())
    gruplar = defaultdict(list)
    for it in itemler:
        gruplar[it.datetime.date()].append(it)
    tum_gun = len(gruplar)
    gruplar = ayda_en_iyi_gunler(gruplar, ayda_en_fazla)
    gruplar = {g: its for g, its in gruplar.items() if pd.Timestamp(g) not in atla}
    print(f"  {ad}: {len(itemler)} sahne, {tum_gun} gün; ayda en fazla {ayda_en_fazla} gün seçildi"
          f" -> {len(gruplar)} gün indirilecek" + (f" ({len(atla)} gün zaten vardı)" if atla else ""))
    if not gruplar:
        return pd.DataFrame()

    res = tanim["cozunurluk"]
    lon_c, lat_c = (bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2
    epsg = _utm_epsg(lon_c, lat_c)
    arama_px = int(tanim.get("arama_km", 2) * 1000 / res)
    tr = Transformer.from_crs(4326, epsg, always_xy=True)
    # hedef ızgara: kutunun UTM karşılığı, res'e hizalı
    xs_, ys_ = tr.transform([bbox[0], bbox[2], bbox[0], bbox[2]], [bbox[1], bbox[1], bbox[3], bbox[3]])
    x0, x1 = math.floor(min(xs_) / res) * res, math.ceil(max(xs_) / res) * res
    y0, y1 = math.floor(min(ys_) / res) * res, math.ceil(max(ys_) / res) * res
    sinirlar, sekil = (x0, y0, x1, y1), (int((y1 - y0) / res), int((x1 - x0) / res))
    tx, ty = tr.transform(tanim["tohum"][1], tanim["tohum"][0])
    tohum_rc = (int((y1 - ty) / res), int((tx - x0) / res))
    bbox_poligon = box(*bbox)

    def oku(its, anahtar_adaylari, resampling):
        """Seçili paftalardan bandı oku; birden fazlaysa boş (0) yerleri sıradakiyle doldur."""
        sonuc = None
        for it in its:
            k = _bant_anahtari(it, anahtar_adaylari)
            arr = bant_oku(it.assets[k].href, sinirlar, sekil, resampling)
            sonuc = arr if sonuc is None else np.where(sonuc == 0, arr, sonuc)
        return sonuc

    def tekrarla(f, *a):
        hata = None
        for deneme in range(3):  # geçici ağ hatalarında 3 kez dene
            try:
                return f(*a)
            except Exception as e:
                hata = e
                time.sleep(10 * (deneme + 1))
        raise RuntimeError(f"{hata.__class__.__name__}: {str(hata)[:80]}")

    def gun_isle(gun, its):
        """Önce yalnızca küçük SCL (bulut) katmanını indirir; kutunun yarısından fazlası
        bulutluysa asıl bantları hiç indirmeden geçer."""
        with rasterio.Env(**GDAL_AYARLARI):
            its = gun_paftalarini_sec(its, epsg, bbox_poligon)
            if not its:
                return dict(tarih=pd.Timestamp(gun), alan_km2=np.nan, gecerli_oran=0.0, dn_ofset=np.nan), None
            c = tekrarla(oku, its, ["scl", "SCL"], Resampling.nearest)
            on_oran = float(gecerli_maske(c).mean())
            if on_oran < 0.5:
                return dict(tarih=pd.Timestamp(gun), alan_km2=np.nan, gecerli_oran=round(on_oran, 3),
                            dn_ofset=np.nan), None
            g = tekrarla(oku, its, ["green", "B03"], Resampling.average).astype("float32")
            s = tekrarla(oku, its, ["swir16", "B11"], Resampling.average).astype("float32")
        ofset = dn_ofset_karar(its[0], s, c)
        g[g == 0] = np.nan
        s[s == 0] = np.nan
        g, s = (g - ofset) * 1e-4, (s - ofset) * 1e-4
        r = sahne_analiz(g, s, c, tohum_rc, res, arama_px)
        satir = dict(tarih=pd.Timestamp(gun), alan_km2=r["alan_km2"],
                     gecerli_oran=round(r["gecerli_oran"], 3), dn_ofset=ofset)
        ek = (r["gecerli_oran"], gun, g, s, r["su_maske"], tohum_rc) if np.isfinite(r["alan_km2"]) else None
        return satir, ek

    from concurrent.futures import ThreadPoolExecutor, as_completed

    satirlar, en_iyi, atlanan = [], None, []
    gunler = sorted(gruplar.items())
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=paralel) as havuz:
        isler = {havuz.submit(gun_isle, gun, its): gun for gun, its in gunler}
        for i, is_ in enumerate(as_completed(isler)):
            gun = isler[is_]
            try:
                satir, ek = is_.result()
                satirlar.append(satir)
                # önizleme için en bulutsuz günü tut (bellek için yalnızca birini)
                if ek is not None and (en_iyi is None or ek[0] >= en_iyi[0]):
                    en_iyi = ek
            except Exception as e:
                print(f"    {gun}: 3 denemede okunamadı ({e}), atlandı")
                atlanan.append(str(gun))
            if kaydet is not None and satirlar and (i + 1) % 20 == 0:
                kaydet(pd.DataFrame(satirlar).set_index("tarih"))
            if (i + 1) % 10 == 0 or i + 1 == len(gunler):
                gecen = time.time() - t0
                kalan = gecen / (i + 1) * (len(gunler) - i - 1)
                print(f"    {i + 1}/{len(gunler)} gün işlendi  (geçen {gecen / 60:.0f} dk, kalan ~{kalan / 60:.0f} dk)",
                      flush=True)

    if onizleme and en_iyi:
        onizleme_ciz(ad, *en_iyi[1:])
    if atlanan:
        print(f"  Uyarı: {len(atlanan)} gün ağ hatası yüzünden atlandı: {', '.join(sorted(atlanan)[:10])}"
              f"{' …' if len(atlanan) > 10 else ''}")
    if not satirlar:
        return pd.DataFrame()
    return pd.DataFrame(satirlar).set_index("tarih").sort_index()


def onizleme_ciz(ad, gun, g, s, maske, tohum_rc):
    """Seçilen su kütlesini göster — doğru gölün seçildiğini gözle kontrol etmek için."""
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(1, 2, figsize=(11, 5))
    ax[0].imshow(np.clip(mndwi(g, s), -0.6, 0.6), cmap="RdBu")
    ax[0].set_title(f"{ad} MNDWI ({gun})")
    ax[1].imshow(maske, cmap="Blues")
    ax[1].set_title(f"Seçilen su kütlesi: {maske.sum()} piksel")
    for a in ax:
        a.plot(tohum_rc[1], tohum_rc[0], "r+", ms=14, mew=2)
        a.set_xticks([]); a.set_yticks([])
    fig.tight_layout()
    fig.savefig(CIKTI / f"onizleme_{ad}.png", dpi=110)
    plt.close(fig)


# ===========================================================================
# Komutlar
# ===========================================================================
def komut_uydu(a):
    CIKTI.mkdir(exist_ok=True)
    barajlar = BARAJLAR[a.grup]
    if a.baraj:
        barajlar = {k: v for k, v in barajlar.items() if k in a.baraj}
    for ad, tanim in barajlar.items():
        yol = CIKTI / f"alan_{ad}.csv"
        eski = pd.DataFrame()
        if yol.exists() and not a.uzerine_yaz:
            eski = pd.read_csv(yol, parse_dates=["tarih"], index_col="tarih")
            if "dn_ofset" not in eski.columns:  # eski (hatalı ofsetli) sürümün çıktısı: kullanma
                eski = pd.DataFrame()

        def kaydet(yeni, eski=eski, yol=yol):
            # Ara kayıt: yarıda kesilirse aynı komut kaldığı yerden devam eder
            df = pd.concat([eski, yeni]) if not eski.empty else yeni
            df = df[~df.index.duplicated(keep="last")].sort_index()
            df.to_csv(yol)
            return df

        atla = frozenset(eski.index) if not eski.empty else frozenset()
        df = uydu_seri_cikar(ad, tanim, a.baslangic, a.bitis, a.max_bulut, paralel=a.paralel,
                             ayda_en_fazla=a.ayda_en_fazla or None, atla=atla, kaydet=kaydet)
        if df.empty and eski.empty:
            continue
        df = kaydet(df) if not df.empty else eski
        n = df["alan_km2"].notna().sum()
        print(f"  -> {yol} ({n} bulutsuz gözlem)")


def komut_dogrula(a):
    import matplotlib.pyplot as plt

    kaynak = a.iski or ISKI_URL
    print(f"İSKİ verisi okunuyor: {kaynak}")
    iski = iski_oku(kaynak)
    print(f"  {iski.index.min():%Y-%m-%d} – {iski.index.max():%Y-%m-%d}, sütunlar: {list(iski.columns)}")

    ozet, paneller = [], []
    for ad, tanim in BARAJLAR["istanbul"].items():
        yol = CIKTI / f"alan_{ad}.csv"
        if not yol.exists() or tanim["iski"] not in iski.columns:
            continue
        alan = aykiri_temizle(pd.read_csv(yol, parse_dates=["tarih"], index_col="tarih")["alan_km2"])
        es = alan_dolulugu_esle(alan, iski[tanim["iski"]])
        if len(es) < 15:
            print(f"  {ad}: yalnızca {len(es)} eşleşen gün, atlandı")
            continue
        cv = yil_disli_dogrulama(es).dropna()
        hata = (cv["tahmin"] - cv["doluluk"]).abs()
        ozet.append(dict(baraj=ad, eslesen_gun=len(es),
                         korelasyon=round(es["alan_km2"].corr(es["doluluk"], method="spearman"), 3),
                         ort_mutlak_hata_puan=round(hata.mean(), 1),
                         doluluk_std_puan=round(es["doluluk"].std(), 1)))
        paneller.append((ad, iski[tanim["iski"]], cv))

    if not ozet:
        sys.exit("Doğrulanacak veri yok. Önce: python baraj_takip.py uydu --grup istanbul")
    tablo = pd.DataFrame(ozet).set_index("baraj")
    tablo.to_csv(CIKTI / "dogrulama_ozet.csv")
    print("\nDoğrulama (yıl dışarıda bırakılarak, örneklem dışı):")
    print(tablo.to_string())
    print("\nOkuma: 'ort_mutlak_hata_puan', doluluğun kendi oynaklığından (std) belirgin küçükse"
          "\nuydu yöntemi gerçekten bilgi taşıyor demektir.")

    fig, axs = plt.subplots(len(paneller), 1, figsize=(11, 2.6 * len(paneller)), sharex=True)
    axs = np.atleast_1d(axs)
    for ax, (ad, gercek, cv) in zip(axs, paneller):
        gercek = gercek[gercek.index >= cv.index.min() - pd.Timedelta(days=30)]
        ax.plot(gercek.index, gercek.values, lw=1.2, label="İSKİ doluluk (%)")
        ax.scatter(cv.index, cv["tahmin"], s=10, color="tab:orange", label="Uydu tahmini (örneklem dışı)")
        ax.set_ylabel(ad)
        ax.set_ylim(0, 105)
    axs[0].legend(loc="lower left", fontsize=8)
    fig.suptitle("Sentinel-2 su alanından tahmin edilen doluluk vs İSKİ")
    fig.tight_layout()
    fig.savefig(CIKTI / "dogrulama.png", dpi=120)
    print(f"\nGrafik: {CIKTI / 'dogrulama.png'}")


def komut_anomali(a):
    import matplotlib.pyplot as plt

    satirlar = []
    fig, ax = plt.subplots(figsize=(11, 4))
    for ad in BARAJLAR[a.grup]:
        yol = CIKTI / f"alan_{ad}.csv"
        if not yol.exists():
            continue
        alan = aykiri_temizle(pd.read_csv(yol, parse_dates=["tarih"], index_col="tarih")["alan_km2"])
        an = mevsimsel_anomali(alan)
        an.to_csv(CIKTI / f"anomali_{ad}.csv")
        ax.plot(an.index, an["anomali_yuzde"], marker=".", lw=1, label=ad)
        son = an.dropna().iloc[-1]
        satirlar.append(dict(baraj=ad, son_ay=f"{an.dropna().index[-1]:%Y-%m}",
                             alan_km2=round(son["alan_km2"], 1),
                             normal_km2=round(son["normal_km2"], 1),
                             anomali_yuzde=round(son["anomali_yuzde"], 1)))
    if not satirlar:
        sys.exit(f"Veri yok. Önce: python baraj_takip.py uydu --grup {a.grup}")
    ax.axhline(0, color="k", lw=0.8)
    ax.set_ylabel("Mevsim normaline göre su alanı (%)")
    ax.legend()
    ax.set_title("Baraj gölü su alanı anomalisi (negatif = kurak)")
    fig.tight_layout()
    fig.savefig(CIKTI / f"anomali_{a.grup}.png", dpi=120)
    print(pd.DataFrame(satirlar).set_index("baraj").to_string())
    print(f"\nGrafik: {CIKTI / f'anomali_{a.grup}.png'}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    alt = p.add_subparsers(dest="komut", required=True)

    u = alt.add_parser("uydu", help="Sentinel-2'den su alanı serisi çıkar")
    u.add_argument("--grup", choices=list(BARAJLAR), default="istanbul")
    u.add_argument("--baraj", nargs="*", help="Sadece bu barajlar (ör. Omerli Terkos)")
    u.add_argument("--baslangic", default="2017-01-01")
    u.add_argument("--bitis", default=pd.Timestamp.today().strftime("%Y-%m-%d"))
    u.add_argument("--max-bulut", type=int, default=30, help="Sahne geneli bulut %% üst sınırı")
    u.add_argument("--paralel", type=int, default=8, help="Aynı anda işlenen gün sayısı (internet yavaşsa düşür)")
    u.add_argument("--ayda-en-fazla", type=int, default=4,
                   help="Her aydan en az bulutlu kaç gün indirilsin (0 = hepsi)")
    u.add_argument("--uzerine-yaz", action="store_true", help="Eski CSV ile birleştirme")
    u.set_defaults(f=komut_uydu)

    d = alt.add_parser("dogrula", help="İSKİ doluluk verisiyle karşılaştır")
    d.add_argument("--iski", help="Yerel İSKİ xlsx/csv dosyası (yoksa İBB portalından indirilir)")
    d.set_defaults(f=komut_dogrula)

    n = alt.add_parser("anomali", help="Mevsim normaline göre su alanı anomalisi")
    n.add_argument("--grup", choices=list(BARAJLAR), default="hes")
    n.set_defaults(f=komut_anomali)

    a = p.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
