# Uydu altimetrisi ve rezervuar veri setleri: Atatürk, Keban, Karakaya

Tarih: 21.10.2026. Sayfalar WebFetch ile açıldı. dahiti.dgfi.tum.de, hydroweb ve zenodo'ya bu oturumdan doğrudan erişim (curl) vekil tarafından engellendi. Bu yüzden API denenemedi, veri indirilemedi.

## 1. DAHITI (DGFI-TUM)

### Hedefler (sayfalar açılıp doğrulandı)

| Rezervuar | DAHITI ID | Ürün | Dönem | Nokta sayısı |
|---|---|---|---|---|
| Atatürk ("Atatürk, Lake", tip: Reservoir) | **112** | Su seviyesi (altimetri) | 2002-06-23 → 2026-09-23 | **539** |
| | | Yüzey alanı, hacim değişimi, hipsometrik seviye | — | veri yok |
| Keban ("Keban, Reservoir") | **38595** | Su seviyesi (altimetri) | 2016-10-17 → 2026-10-10 | **294** |
| | | **Hacim değişimi** (altimetri + optik) | 2016-10-17 → 2026-10-10 | **294** |
| Karakaya ("Karakaya Baraji, Reservoir") | **221** | Su seviyesi (altimetri) | 1993-03-29 → 2026-08-09 | **677** |
| | | Yüzey alanı, hacim, hipsometri | — | veri yok |

- Atatürk sayfasındaki ek bilgi: seviye en düşük 526,859 m, en yüksek 538,665 m, ortalama 533,248 m (11,8 m genlik).
- Karakaya'da kullanılan uydular: Topex/Poseidon, Jason-1/2/3 ve Sentinel-6A (hepsi pass 220), ayrıca Envisat (pass 0627, 0786).
- Yakındaki diğer Türk hedefleri (Asya sanal istasyon listesi):
  - Hirfanlı 41400 (2016–2026, 224 nokta)
  - Çatalan 41750 (seviye ve hacim, 124 nokta)
  - Almus 39925, Aslantaş 39676, Demirköprü 39368, Çamlıca 39985
  - Fırat nehri istasyonları 14880, 24459, 20010–20012, 24460, 24462
  - Dicle 20002
- **Seyreklik uyarısı.** Örnekleme aralığı ayda yaklaşık 1–3 ölçüm. Sebebi: Jason/Sentinel-6 uydularının ~10 günlük, Sentinel-3'ün ~27 günlük tekrar döngüsü. Keban serisi ancak 2016'dan itibaren var (Sentinel-3 dönemi). Bu yüzden günlük EPİAŞ kot/hacim verisinin yerine geçmez. Ancak EPİAŞ geçmiş baraj verisi vermediği için **2016 öncesi ve sonrası için bağımsız bir geçmiş seri** olarak değerli. Karakaya seviyesi 1993'ten, Atatürk seviyesi 2002'den başlıyor.

### Erişim, API ve lisans

- **Kayıt zorunlu.** Ürün sayfasında "To download data, please log in or register first" yazıyor. Kayıt ücretsiz (https://dahiti.dgfi.tum.de/register/).
- **API v2 (Beta)** bilgileri:
  - Dokümantasyon: https://dahiti.dgfi.tum.de/en/api/doc/v2/
  - Su seviyesi uç noktası: `https://dahiti.dgfi.tum.de/api/v2/download-water-level/`. POST (JSON) ya da GET (sorgu dizesi) kabul ediyor. Parametreler: `api_key`, `dahiti_id`, `format` (`json` varsayılan; `ascii`, `netcdf`, `csv` de var). JSON yanıtında `data[]` içinde `date`, `wse` (su yüzeyi yüksekliği), `wse_u` (belirsizlik) ve `data` (görev/döngü) alanları dönüyor.
  - Hacim uç noktası: `https://dahiti.dgfi.tum.de/api/v2/download-volume-variation/`
  - Hedef listesi: `https://dahiti.dgfi.tum.de/api/v2/list-targets/`. Filtreler: `basin`, `country`, `continent`, `min_lon/max_lon/min_lat/max_lat`.
  - Diğer uç noktalar: `get-target-info`, `get-nearest-target`.
  - **API anahtarı:** Kayıt sonrası profil sayfasından (https://dahiti.dgfi.tum.de/en/profile/) ücretsiz oluşturuluyor. `~/.netrc` dosyasına ya da `api_key` parametresine konuyor (dahiti-api.readthedocs.io). Python istemcisi: `dahitiapi.DAHITI` sınıfı (`download_water_level()`, `download_volume_variation()`).
  - Erişim düzeyleri "User" ve "Premium" olarak ayrılıyor. Bazı uç noktalar kullanıcı statüsüne bağlı olabilir.
- **Lisans (kayıt sayfasındaki şartlar):**
  - Ücretsiz kullanım yalnızca "private persons, educational institutions and non-profit organizations" için.
  - Açık ifade: "It is **not** allowed to use DAHITI products for commercial purposes."
  - Metin "CC BY 4.0" diyor, ama rozet **CC BY-NC 4.0**'a bağlanıyor.
  - Atıf zorunlu: Schwatke vd. (2015), HESS 19, 4345–4364, doi:10.5194/hess-19-4345-2015.
  - **Yorum:** Kişisel araştırma kullanımı uygun görünüyor. Sinyal ticari bir ürün veya hizmette kullanılacaksa izin gerekir.

## 2. Hydroweb.next (Theia / CNES)

- Ürün: **HYDROWEB_LAKES_OPE**. 399 göl için altimetri su seviyesi, bazılarında yüzey alanı ve hacim, belirsizlikler dahil. Operasyonel göller yaklaşık 3 gün gecikmeyle güncelleniyor.
- Göl listesi bir KML dosyasında. Ürün sayfasında Atatürk, Keban ya da Karakaya adı **geçmiyor**. STAC araması (`/api/v1/rs-catalog/stac/search`) robots engeli nedeniyle denenemedi. Bu yüzden bu üç baraj için kapsam **doğrulanamadı**. Güven düşük; 399 gölde olmamaları muhtemel.
- Erişim: THEIA hesabı ile giriş zorunlu. İndirme için `py-hydroweb` istemcisi var (sürüm ≥1.3.3 önerilmiş). Eski hydroweb.theia-land.fr adresi 31.03.2024'te kapatılacağı duyurulmuştu.
- Lisans veren kurumlar: C3S, CLMS, CNES, ESA (Lakes-CCI), Theia. Atıf DOI'si: 10.24400/329360/HYDROWEB_WATER_LEVEL. Lisans türü sayfada adlandırılmamış.

## 3. Küresel rezervuar veri setleri ve Google Earth Engine (GEE)

| Veri seti | İçerik | Dönem / çözünürlük | Erişim | GEE'de var mı? |
|---|---|---|---|---|
| **GRSAD** (Zhao & Gao 2018) | 6.817 rezervuarın yüzey alanı (Pekel/JRC tabanlı, bulut düzeltmeli) | 1984–2015, aylık | Texas Data Repository doi:10.18738/T8/DF80WG | Hayır (asset bulunamadı) |
| **GRS – Global Reservoir Storage** (Li vd. 2023, Nat. Commun.) | 7.245 rezervuarın alan, depolama ve normalize depolama değerleri | 1999–2018, aylık | Zenodo doi:10.5281/zenodo.7855477 | Yalnızca görüntüleme uygulaması (yao.users.earthengine.app/view/grs, ee-zhang-tamu…/view/grs); asset olarak yayınlanmamış |
| **GloLakes** (Hou vd. 2024, ESSD 16, 201) | 170.000+ gölün mutlak hacmi; yaklaşık 27.000 gölde yakın-gerçek-zamanlı izleme | Tarihsel 1984–2020 aylık; NRT 2020–bugün, günlük güncelleme | NCI THREDDS doi:10.25914/K8ZF-6G46 (OPeNDAP/HTTP); globalwater.online görüntüleyici; kullanım kısıtı "None" | Hayır (makale GEE'yi yalnızca gelecek seçeneği olarak anıyor) |
| **ReaLSAT** (Khandelwal vd. 2022) | 681.137 göl ve rezervuar alanı | 1984–2015 | Zenodo; CC BY 4.0 | Yalnızca statik poligonlar: `projects/sat-io/open-datasets/ReaLSAT/ReaLSAT-1_4` (zaman serisi yüklenmemiş) |
| **Global Dam Watch v1.0** | 41.145 bariyer ve 35.295 rezervuar poligonu (statik) | — | CC BY 4.0 | `projects/sat-io/open-datasets/GDW/GDW_RESERVOIRS_V1_0`, `…/GDW_BARRIERS_V1_0` |
| **GRanD v1.01** | Baraj ve rezervuar poligonları (statik) | — | SEDAC / data.gov | GDW, GRanD'ı büyük ölçüde içeriyor; ayrı resmi GEE asset'i bulunamadı |

- Bu üç baraj (Atatürk, Keban, Karakaya) GRanD, GRSAD ve GRS gibi büyük rezervuar listelerinde olmalı. Hepsi Türkiye'nin en büyük rezervuarları arasında. Ancak dosyalar indirilemediği için ID düzeyinde **doğrulanamadı**.
- **GEE'de zaman serisi için pratik yol:**
  - JRC Global Surface Water aylık su maskesi (`JRC/GSW1_4/MonthlyHistory`, 1984–2021) ile GDW rezervuar poligonu kesiştirilerek aylık alan çıkarılabilir.
  - Daha güncel dönem için Sentinel-2 MNDWI kullanılabilir. Proje bunu `baraj_takip.py` ile STAC üzerinden, GEE gerektirmeden zaten yapıyor.

## 4. Proje için öneri

1. DAHITI'ye kayıt olup API anahtarı alınmalı. Çekilecek seriler: 112 (Atatürk seviye), 221 (Karakaya seviye), 38595 (Keban seviye ve hacim). Bunlar Sentinel-2 alan ölçümünün kalibrasyonu ve alan→hacim dönüşümü için kullanılabilir.
2. EPİAŞ geçmiş veri vermediği için uzun dönem doğrulamada GRS (1999–2018 aylık depolama) ve GloLakes (1984–bugün) kullanılmalı. Zenodo ve NCI'dan elle indirilip rezervuar adı ya da GRanD ID'si ile filtrelenmeli.
3. Lisans: DAHITI ticari kullanıma kapalı (NC). GloLakes'te kısıt yok. ReaLSAT ve GDW CC BY.

## Açılan URL'ler

- https://dahiti.dgfi.tum.de/en/
- https://dahiti.dgfi.tum.de/en/112/
- https://dahiti.dgfi.tum.de/38595/
- https://dahiti.dgfi.tum.de/en/221/
- https://dahiti.dgfi.tum.de/en/221/water-level-altimetry/
- https://dahiti.dgfi.tum.de/en/41400/
- https://dahiti.dgfi.tum.de/en/41750/
- https://dahiti.dgfi.tum.de/en/virtual-stations/asia/
- https://dahiti.dgfi.tum.de/en/api/doc/
- https://dahiti.dgfi.tum.de/en/api/doc/v2/
- https://dahiti.dgfi.tum.de/en/api/doc/v2/download-water-level/
- https://dahiti.dgfi.tum.de/en/api/doc/v2/list-targets/
- https://dahiti.dgfi.tum.de/en/products/water-level-altimetry
- https://dahiti.dgfi.tum.de/en/register/
- https://dahiti-api.readthedocs.io/en/latest/
- https://dahiti-api.readthedocs.io/en/latest/authentication.html
- https://hydroweb.next.theia-land.fr/catalog/details/HYDROWEB_LAKES_OPE
- https://www.theia-land.fr/en/blog/new-dissemination-portal-for-theia-river-and-lake-water-level-products-hydroweb/
- https://hgao.engr.tamu.edu/research/
- https://hgao.engr.tamu.edu/research/research-ii-test/
- https://www.nature.com/articles/s41467-023-38843-5
- https://essd.copernicus.org/articles/16/201/2024/
- https://climatedataguide.ucar.edu/climate-data/lake-water-storage-glolakes
- https://gee-community-catalog.org/projects/realsat/
- https://gee-community-catalog.org/projects/gdw/
- https://zenodo.org/records/10599732 (GLRSED, ODbL; ilgili ama hedef dışı)
- Açılamayanlar: https://dahiti.dgfi.tum.de/en/faq/ (hata), hydroweb STAC araması (robots engeli)
