# EPİAŞ Şeffaflık: santral bazlı üretim ve baraj uç noktaları

Tarih: 21.10.2026.

**Kaynak durumu.** Resmi teknik doküman (https://seffaflik.epias.com.tr/electricity-service/technical/en/index.html) WebFetch ile açıldı, ama tek sayfalık dev bir HTML olduğu için yalnızca ilk ~100 bin karakter okunabildi. Bu kısım içindekiler tablosunu ve §5.31'e kadarki bölümü kapsıyor. Bölüm numaraları ve DTO adları oradan alındı. Uç nokta yolları, metotlar ve gövde alanları ise iki bağımsız açık kaynak istemciden çıkarıldı. İkisi de PyPI'dan indirilip kaynak kodu okundu:
- **eptr2 1.3.9** (Tideseed, Apache-2.0)
- **theohe-epias 0.0.13**

İki kaynak birbiriyle tutarlı. Bu oturumda seffaflik.epias.com.tr'ye doğrudan erişim (curl) vekil tarafından engellendi. Swagger dosyası (`swagger.json`) bağlantısı dokümanda var ama hedefi okunamadı.

## 0. Ortak kurallar

- **Kimlik doğrulama.** `POST https://giris.epias.com.tr/cas/v1/tickets`
  - Başlıklar: `Content-Type: application/x-www-form-urlencoded`, `Accept: text/plain`
  - Gövde: `username=...&password=...`
  - Başarılı yanıt: 201 ve gövdesi `TGT-...` ile başlayan bir bilet.
  - Bilet 2 saat geçerli. Her istekte `TGT: <bilet>` başlığıyla gönderilir. (Kaynak: dokümanın §2 bölümü, doğrudan okundu.)
- **Taban adres:** `https://seffaflik.epias.com.tr/electricity-service`
- **İstek gövdesi:** JSON, `Content-Type: application/json`.
- **Tarih biçimi:** `YYYY-MM-DDT00:00:00+03:00`. eptr2 `format_date_epias_hour` her tarihi bu biçime çeviriyor.
- **Yanıt biçimi:** Liste servisleri `{"items": [...]}` döndürüyor (eptr2 `postprocess_items_to_df`). Projede sayfalama için `"page": {"number": 1, "size": 1000}` kullanılıyor.
- **Dışa aktarım:** Her `/data/` uç noktasının bir `/export/` eşi var (ör. `/v1/dams/export/water-energy-provision`). Bunlar XLSX/CSV/PDF döndürüyor.

## 1. Üretim (santral bazlı)

| Amaç | Metot ve yol | Gövde (zorunlu / isteğe bağlı) | eptr2 anahtarı | Dok. § |
|---|---|---|---|---|
| Gerçek zamanlı üretim için santral listesi | **GET** `/v1/generation/data/powerplant-list` | gövde yok | `pp-list` | 5.78 |
| Tarih aralığına göre santral listesi | **POST** `/v1/generation/data/powerplant-list-for-date-range` | `startDate`, `endDate` (zorunlu) | `pp-list-for-date-range` | 5.79 |
| Gerçek zamanlı üretim (saatlik) | **POST** `/v1/generation/data/realtime-generation` | `startDate`, `endDate` (zorunlu); `powerPlantId` (isteğe bağlı; verilmezse Türkiye toplamı gelir) | `rt-gen` | 5.80 |
| Toplu gerçek zamanlı üretim (çok santral, tek gün) | **POST** `/v1/generation/data/realtime-generation-bulk` | `date` (zorunlu), `powerPlantIds` (zorunlu; string listesi, en fazla 1000) | `rt-gen-bulk` | 5.81 |
| UEVM santral listesi | **GET** `/v1/generation/data/injection-quantity-powerplant-list` | gövde yok | `uevm-pp-list` | 5.75 |
| UEVM (uzlaştırmaya esas veriş miktarı, saatlik) | **POST** `/v1/generation/data/injection-quantity` | `startDate`, `endDate` (zorunlu); **`powerplantId`** (isteğe bağlı) | `uevm` | 5.74 |
| Üretici organizasyon listesi | POST `/v1/generation/data/organization-list` | `startDate`, `endDate` | `gen-org` | — |
| UEVÇB listesi | POST `/v1/generation/data/uevcb-list` | `organizationId`, `startDate` | `gen-uevcb` | 5.84 |

**Dikkat.** UEVM servisinde alan adı **`powerplantId`** (küçük p ile) yazılıyor. Diğer servislerde `powerPlantId`. Hem eptr2 hem theohe-epias bu farkı ayrıca düzeltiyor.

eptr2 yorumu: "Only non-standard naming in powerPlantId."

**ID'ler birbirinden farklı.** `pp-list`'teki ID (gerçek zamanlı üretim) ile `uevm-pp-list`'teki ID (UEVM) aynı santral için **farklı sayılar**. KGÜP/plan verisinde ise UEVÇB ID'si kullanılıyor.

**Yanıt alanları** (eptr2 belgeleri ve projedeki `epias_indir.py`'den):
- `realtime-generation` → `items[]`: `date`, `hour`, `total`, `naturalGas`, `importCoal`, `dammedHydro`, `river`, `wind`, `sun`, `geothermal`, `biomass`, `lignite` vb.
  - eptr2 uyarısı: `total` zaten toplamdır, yakıt sütunlarıyla tekrar toplanmamalı.
  - Santral filtresi verilince de aynı sütun yapısı döner. Santral kendi kaynak sütununda dolu, diğerleri 0 gelir.
- `injection-quantity` → `items[]`: `date`, `hour`, `total` ve kaynak bazlı sütunlar.
- `injection-quantity-powerplant-list` → `items[]` içinde `id` alanı var (theohe-epias `k["id"]` ile okuyor). Ad alanı büyük olasılıkla `name`. Resmi sayfada **doğrulanamadı**.
- `powerplant-list` → dokümandaki DTO adları `PowerPlantDto`, `PowerPlantResponseDto` (§6.360–6.362). Alanlar (`id`, `name`, `eic`, `shortName` olduğu tahmin ediliyor) **doğrulanamadı**. Script çalışınca anahtarlar yazdırılmalı.

## 2. Barajlar

Tüm baraj servisleri **POST** ile çağrılıyor (yalnızca `basin-list` GET). Gövdede yalnızca `basinName` ve `damName` var, ikisi de isteğe bağlı. **Tarih parametresi yok.**

| Amaç | Yol | eptr2 anahtarı | Dok. § | DTO |
|---|---|---|---|---|
| Debi ve kurulu güç | `/v1/dams/data/flow-rate-and-installed-power` | `dams-info` | 5.52 | `FlowRateAndInstalledPowerResponse(Dto)` (§6.165–6.166) |
| Suyun enerji karşılığı (MWh) | `/v1/dams/data/water-energy-provision` | `dams-water-energy-provision` | 5.53 | `WaterEnergyProvisionDataDto`, `…RequestDto`, `…ResponseDto`, `…ExportRequestDto` (§6.551–6.554) |
| Aktif doluluk % | `/v1/dams/data/active-fullness` | `dams-active-fullness` | 5.44 | — |
| Aktif hacim | `/v1/dams/data/active-volume` | `dams-active-volume` | 5.45 | — |
| Havza listesi | GET `/v1/dams/data/basin-list` | `basin-list` | 5.46 | — |
| Günlük kot | `/v1/dams/data/daily-kot` | `dams-daily-level` | 5.47 | — |
| Günlük hacim | `/v1/dams/data/daily-volume` | `dams-daily-volume` | 5.48 | — |
| Min-maks kot | `/v1/dams/data/dam-kot` | `dams-level-minmax` | 5.49 | — |
| Baraj listesi (havzaya göre) | `/v1/dams/data/dam-list` (gövde: `basinName`) | `dam-list` | 5.50 | — |
| Min-maks hacim | `/v1/dams/data/dam-volume` | `dams-volume-minmax` | 5.51 | — |

**Geçmiş veri alınabiliyor mu? Hayır.**
- İstek gövdesinde `startDate`/`endDate` yok.
- theohe-epias, açıklamaları resmi dokümandan kopyalamış. Suyun enerji karşılığı, günlük kot, günlük hacim, aktif doluluk ve aktif hacim için şöyle yazıyor: *"Veriler saat 17:00 itibariyle nihai halini almaktadır. Baraj verileri günlük olarak verilmektedir. Geriye dönük veri bulunmamaktadır / verilmemektedir."*
- Debi ve kurulu güç servisi sabit (statik) bilgi veriyor. Açıklaması: "İlgili barajda üniteden geçen suyun miktarını ve barajın kurulu gücünü gösterir."
- Sonuç: Seri oluşturmak için her gün 17:00'den sonra **anlık görüntü alıp arşive eklemek** gerekiyor. `epias_indir.py` içindeki `baraj_arsivle` bunu doluluk, hacim ve kot için zaten yapıyor. `water-energy-provision` buna eklenmeli.
- Değerlendirme: Barajdaki suyun MWh karşılığı, HES gelir beklentisi için doğrudan bir öncü gösterge olabilir.

**Yanıt alanları:**
- Projede kullanılanlar:
  - `active-fullness` → `items[]`: `date`, `basin`, `dam`, `damId`, `activeFullnessAmount`
  - `daily-volume` → `items[]`: `damName`, `volume`
  - `daily-kot` → `items[]`: `dam`, `dailyKot`
- `water-energy-provision` ve `flow-rate-and-installed-power` için alan adları dokümanın okunabilen kısmında yoktu, **doğrulanamadı**. Beklenen alanlar:
  - water-energy-provision: baraj adı, havza, tarih, MWh değeri
  - flow-rate-and-installed-power: baraj adı, debi (m³/s), kurulu güç (MW)
- Öneri: Script'te ilk çağrıdan sonra `print(v["items"][0].keys())` ile alan adları yazdırılsın.

## 3. Santral ID'leri

| Santral | Gerçek zamanlı üretim `powerPlantId` | UEVM `powerplantId` | Kaynak |
|---|---|---|---|
| ATATÜRK HES | **641** | **142** | eptr2 `composite/production.py` belgesi: `rt_pp_id=641, ## ATATÜRK HES`, `uevm_pp_id=142, ## ATATÜRK HES` |
| (ilişkili) EÜAŞ organizasyonu | `organizationId` = 195 | — | eptr2 skill örneği (openskillindex.com) |
| (ilişkili) ATATÜRK HES DB | UEVÇB ID = 733 | — | aynı kaynak |

Aşağıdaki santraller için açık bir sayfada ID **bulunamadı**:
- KEBAN, KARAKAYA, BİRECİK, KARKAMIŞ, ILISU
- Aydem: Göktaş, Adıgüzel, Kemer, Akıncı
- Ayen: Yamula
- Akenerji: Uluabat, Feke-2

Web aramaları ve iki istemci paketinin kaynak kodu tarandı. Bu ID'ler script ile şöyle çıkarılmalı:

```python
# 1) Gerçek zamanlı üretim ID'leri
pp = GET /v1/generation/data/powerplant-list               # items[] -> id, name ...
# 2) UEVM ID'leri
up = GET /v1/generation/data/injection-quantity-powerplant-list
# Ad eşleme: büyük harf + Türkçe karakterleri sadeleştir, "HES" / "BARAJ" / "DB" eklerini at,
# sonra 'KEBAN', 'KARAKAYA', 'BIRECIK', 'KARKAMIS', 'ILISU', 'GOKTAS', 'ADIGUZEL',
# 'KEMER', 'AKINCI', 'YAMULA', 'ULUABAT', 'FEKE' içerenleri listele.
```

EPİAŞ adlandırması büyük harf kullanıyor ("ATATÜRK HES"). UEVÇB tarafında "… HES DB" gibi ekler görülüyor. Bazı santraller birden çok kayıtla gelebilir (ör. GÖKTAŞ 1/2, FEKE 1/2). Bu yüzden eşleme sonuçları elle kontrol edilmeli.

## 4. Kaynaklar

Açılan ve okunan URL'ler:
- https://seffaflik.epias.com.tr/electricity-service/technical/en/index.html (ilk ~100 bin karakter: içindekiler, §1–§5.31, TGT kuralları)
- https://seffaflik.epias.com.tr/electricity-service/technical/tr/index.html (içindekiler: §5.52/5.53/5.78/5.80/5.81 ve DTO adları)
- https://github.com/Tideseed/eptr2 (lisans Apache-2.0, kimlik doğrulama, örnek ID'ler)
- https://openskillindex.com/skills/majiayu000-claude-skill-registry-eptr2-generation-tracking (641 / 142 / org 195 / uevcb 733)
- PyPI'dan indirilip okunan paketler:
  - eptr2 1.3.9: `mapping/path.py`, `mapping/parameters.py`, `processing/preprocess/params.py`, `main.py`, `composite/production.py`, `assets/eptr2_api_schema.json`
  - theohe-epias 0.0.13: `transparency/data/dams.py`, `transparency/data/production.py`
  - seffaflik 0.0.22: eski v1 API, yalnızca karşılaştırma için
- Açılamayanlar:
  - https://seffaflik.epias.com.tr/electricity-service/v3/api-docs (hata)
  - GitHub tests klasörü (robots engeli)
