# Çok faktörlü BIST modeli: plan ve test kaydı (v2)

Amaç: hem **risk** (hisselerin birlikte hareketini açıklayan faktörler) hem **alfa** (gelecek
getiriyi öngören faktörler) için kullanılabilir değişkenleri bulmak; uydu, enerji ve makro
verisinden türetilen aday değişkenleri standart faktörlerin ve kur/faiz/enflasyon
duyarlılıklarının **ötesinde** katkıları için sınamak.

Kurallar `ARASTIRMA_PLANI.md` ile aynı: her test sonucu görülmeden kaydedilir, değişen kural
yeni numara alır, test sayısı tutulur.

- v1: 2026-10-22 sabah (yedek: `FAKTOR_PLANI_v1_2026-10-22.md`). Hiçbir v1 testi çalıştırılmadı.
- **v2: 2026-10-22 akşam.** `~/Desktop/Research` klasöründeki önceki çalışma ve verisi
  incelendi (bölüm 1). v2'deki değişiklikler yalnızca veri denetimine ve test tasarımına
  dayanır; Research'te iyi sonuç veren faktörler bu yüzden listeye **eklenmedi** (bölüm 5, F-A3).
  Bu revizyon sırasında 2024 ve sonrasına ait hiçbir getiri sonucu açılmadı
  (Research'ün yıllık regresyon dosyasının 2024–2026 satırlarına bakılmadı).

---

## 1. Önceki çalışma (Research) — ne yapılmış, ne bulunmuş

### 1.1 Kurulan altyapı (yeniden kullanılacak)

- İş Yatırım mali tablo istemcisi + önbellek; şirket **profilleri** (sanayi, holding, GYO, banka,
  katılım bankası, sigorta; leasing/faktoring desteklenmiyor). Her profil kendi kalem eşlemesiyle.
- YTD, çeyreklik ve son 12 ay (TTM) snapshot'ları; KAP'tan **gerçek yayın tarihleri**
  (`data/report_dates.csv`: 22.325 bildirim, 728 kod, 2016-06 → 2026-08).
- Fiyat: İş Yatırım HisseTekil; `close` = HGDG_KAPANIS (temettü/bölünme düzeltilmiş), ayrıca
  düzeltilmemiş kapanış, TL ve $ hacim, piyasa değeri (PD) ve halka açık PD, günlük BIST100 değeri.
- Sektör eşlemesi (BIST sektör / alt sektör Excel'i), metrik kaydı (formül, yön, profil
  uygunluğu, ekonomik geçerlilik kuralları), winsorize + kesitsel z/sıra puanı, sektör nötrleme.
- Faktör aileleri: değer (EBIT/EV, EBITDA/EV, FCF getirisi, E/P, B/P), kalite (ROIC, ROE, ROA,
  brüt kârlılık, CFO/NI, FCF/NI; banka ve sigortaya özel metrikler), kârlılık (marjlar), büyüme,
  yatırım (varlık, işletme sermayesi, capex büyümesi), kaldıraç, istikrar (8 çeyreklik std).
- **Hiç kurulmamış:** fiyat tabanlı faktörler (büyüklük, momentum, kısa dönem geri dönüş, düşük
  oynaklık, beta, likidite), makro duyarlılıklar, risk modeli, portföy kurulumu.

### 1.2 Verinin kapsamı (2026-10-22 denetimi)

| Konu | Durum |
|---|---|
| Evren | **Bugünkü Yıldız Pazar listesi**: 269 hissenin fiyatı, 289 şirketin mali tablosu. Borsadan çıkan **hiç** hisse yok; tüm fiyat serileri 2026-08-07'de bitiyor. Kesit büyüklüğü 2016'da ~130, 2026'da ~240. |
| Fiyat aralığı | 2015-08-10 → 2026-08-07 (indirme başlangıcı 2015-08 seçilmiş; 36 aylık beta için yetersiz). |
| Yayın tarihi | KAP, 2016-06'dan itibaren. Bankalarda 362 snapshot'ın 240'ında yayın tarihi eşleşmemiş → bankalar testlerin çoğundan fiilen düşmüş. |
| Yayın gecikmesi (KAP, gün) | Q1 medyan 39 / %95 81; Q2 41 / 88; Q3 36 / 43; **Q4 61 / 130**. Q4 raporlarının **%10'u 90 günden geç**. |

**Yeni bulgu — yıl sonu satırlarının üzerine yazılması (TMS 29).** Önbellekteki Q4 (yıl sonu)
değerleri o yılın orijinal raporundan değil, **sonraki raporlardaki yeniden düzenlenmiş
karşılaştırmalı rakamlardan** geliyor. 28 şirketlik snapshot önbelleğinde medyan
özkaynak(Q4)/özkaynak(Q3) oranı:

| Yıl | 2015–2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|
| Q4/Q3 | 1,03–1,06 | 1,16 | **2,43** | **2,38** | 1,39 | 1,17 |
| sonraki Q1/Q4 | ~1,02 | 1,10 | **0,51** | 0,83 | 0,84 | 0,97 |

Yani 2022Q4'ten itibaren Q4 satırındaki rakam, o tarihte piyasanın bilmediği (sonraki yılın
satın alma gücüne göre düzeltilmiş) bir rakam; ama Q4 raporunun KAP tarihine bağlanıyor.
Bu bir **ileriye bakma** hatası; B/P, E/P, büyüme ve istikrar metriklerini 2022Q4–2025Q4
yıl sonu kesitlerinde bozuyor. 2021 ve öncesinde etki küçük görünüyor.

### 1.3 Test tasarımı (Research)

- Faktör her şirketin **kendi yayın tarihinde** ölçülüyor, getiri yayından sonraki ilk işlem
  gününden 1/3/6 ay ileri, **ham** (piyasa veya risksiz faize göre fazla değil).
- Kesitler mali çeyreğe göre gruplanıyor (43 kesit, 2016Q2–2026Q2): aynı kesitteki hisselerin
  giriş tarihleri haftalarca farklı; piyasa hareketi kesitsel IC'ye karışıyor.
- t = ortalama / (std/√n); Newey–West yok. 6 aylık vade çeyreklik örneklemle **örtüşüyor**
  (t yaklaşık √2 kat şişik).
- Yaklaşık **220 IC/regresyon istatistiği** üretilmiş (7 bileşik skor × 3 vade × ham/sektör-nötr,
  43 metrik × 3 vade, kalite bileşenleri, değer×kalite kovaları, regresyonlar).
- Çok değişkenli regresyonda büyüklük, momentum, beta kontrolü yok (fiyat faktörleri yok).
- Veri 2026-06'ya kadar kullanılmış → v1'deki saklı dönem (2024-01 → 2026-09) bu faktör
  aileleri için **zaten görülmüş**.

### 1.4 Sonuçlar (sektör-nötr, Spearman IC)

| Faktör | 1 ay IC (t) | 3 ay IC (t) | 6 ay IC (t, örtüşmeli) |
|---|---|---|---|
| Değer bileşik skoru | 0,060 (2,43) | 0,075 (**3,61**) | 0,079 (2,92) |
| B/P | 0,069 (2,96) | 0,073 (**3,17**) | 0,039 (1,65) |
| E/P | 0,027 (0,98) | 0,039 (1,52) | 0,066 (3,32) |
| EBIT/EV | 0,037 (1,23) | 0,047 (1,72) | 0,104 (3,79) |
| İstikrar bileşik | 0,000 (−0,02) | 0,029 (1,30) | 0,067 (3,72) |
| Kalite bileşik | 0,016 (0,69) | 0,021 (1,05) | 0,068 (2,34) |
| Kârlılık, büyüme, yatırım, kaldıraç | \|t\| < 1,5 (1 ve 3 ay) | | |

Dikkat çeken tutarsızlıklar:
- Değer skorunun 5'li dilim uzun–kısa farkı küçük ve monoton değil: 1 ay +1,0 puan, 3 ay +1,0,
  **6 ay −1,1** (dönem başına).
- Tüm aileler aynı regresyona girince değerin katsayısı zayıflıyor: t = 1,84 (1 ay), 0,69 (3 ay),
  0,01 (6 ay). İstikrar 3 ve 6 ayda t ≈ 2,2–2,4.
- Değer, yüksek kaliteli yarıda daha iyi (3 ay t 3,67) ama düşük kaliteli yarıda da pozitif
  (2,06) — kalite filtresi kanıtı zayıf.
- Değer skoru ile log(PD) arasındaki kesitsel sıra korelasyonu medyan 0,13 (B/P −0,10):
  sonuç büyüklüğün kılık değiştirmiş hali gibi görünmüyor.

### 1.5 Okuma

1. Tek tutarlı aday **değer** (özellikle B/P, 1–3 ay). Ama (i) evren bugünkü Yıldız Pazar'dan
   seçildiği için "ucuzken sonradan büyüyen" hisseler örnekte; bu seçim değerin primini
   **olduğundan büyük** gösterebilir, (ii) dilim getirileri monoton değil, (iii) çok değişkenli
   modelde zayıflıyor, (iv) ~220 testin içinde \|t\| ≥ 3 eşiğini örtüşmesiz geçen yalnızca
   3 aylık değer skoru ve B/P var.
2. Kalite, kârlılık, büyüme, yatırım, kaldıraç: BIST'te bu tasarımla kanıt yok.
3. İstikrar ve EBIT/EV yalnız örtüşmeli 6 ay vadesinde öne çıkıyor → keşif sonrası hipotez.
4. Fiyat tabanlı faktörler ve makro risk hiç sınanmamış: v2'nin ağırlığı burada.

---

## 2. Saklı dönem ve faktör grupları

- **Grup G (görülmüş):** değer, kalite, kârlılık, büyüme, yatırım, kaldıraç, istikrar aileleri.
  2016-06 → 2026-06 sonuçları görüldü; 2024–2026 bunlar için temiz saklı dönem değil.
  Bunların **gerçek** doğrulaması ileriye dönük kayıttır: 2026-11'den itibaren her ay sonu
  sinyaller, sonraki ayın getirisi görülmeden `cikti/faktor/canli/` altına tarih damgasıyla
  yazılır. Ara değerlendirme 2027-10 (12 ay), karar 2028-10 (24 ay).
- **Grup Y (yeni):** fiyat tabanlı faktörler, makro duyarlılıklar, aday (enerji/uydu)
  faktörler, risk modeli. Bunlar için saklı dönem **2024-01 → 2026-09** temiz; en sonda,
  kayıtlı faktörler için bir kez açılır.
- Güç notu: 33 aylık saklı dönemde t ≥ 2 için yıllık Sharpe ≈ 1,2 gerekir; bu yüzden saklı
  dönem ölçütü "anlamlılık" değil, **işaretin korunması** ve tahminin keşif dönemi değerinin
  en az yarısı olmasıdır (raporlanır, geçme koşulu yalnız işaret).

---

## 3. Veri işleri (testlerden önce; hiçbiri getiri sonucu içermez)

**V1 — Evren.** Tüm BIST payları: KAP listesi (`faktor/veri_topla.py` evren adımı) +
borsadan çıkmış paylar. İş Yatırım HisseTekil'in çıkmış kodlara veri dönüp dönmediği
denenir; dönmüyorsa çıkmış pay sayısı ve son işlem tarihleri KAP'tan raporlanır ve sonuçlar
"hayatta kalan evren" etiketiyle yorumlanır. Yıldız Pazar'a özel evren yalnız karşılaştırma
(F-A0) için kullanılır.

**V2 — Fiyat.** Tüm evren için 2012-01'den bugüne günlük düzeltilmiş kapanış (`close`),
düzeltilmemiş kapanış, TL hacim, PD, halka açık PD. BIST100 seviyesi aynı dosyalardan
(`end_deger`). 2012 başlangıcı, 2016-07'de 36 aylık beta ve 12 aylık momentum için ısınma payı.

**V3 — Yayın tarihi.** Kullanılabilirlik = KAP'taki ilk bildirim tarihi + 1 işlem günü.
KAP tarihi yoksa yedek gecikme: Q1–Q3 için çeyrek sonu + 3 ay, **Q4 için çeyrek sonu + 5 ay**
(KAP dağılımında yaklaşık %95–97'yi kapsar; v1'deki tek tip 3 ay Q4'ün %10'unda ileriye
bakıyordu). Bankaların KAP eşlemesi düzeltilene kadar yedek gecikme kullanılır.

**V4 — Yıl sonu üzerine yazma.** Öncelik: ilk yayımlanan yıllık tabloları KAP'tan almak
(KAP API anahtarları: [yerel dosya yolu çıkarıldı]). Bu yapılamazsa kural: **2022Q4 ve sonrası
Q4 satırları kullanılmaz**; Q3 değerleri bir sonraki Q1 raporu yayımlanana kadar taşınır.
Kontrol: düzeltme sonrası medyan Q4/Q3 özkaynak oranı tüm yıllarda 0,9–1,3 aralığında olmalı.

**V5 — Enflasyon muhasebesi.** 2023Q4'ten itibaren tablolar TMS 29'a göre.
- Oran faktörleri (B/P, E/P, GP/A) her ay kesitsel z-puanına çevrildiği için seviye kırılması
  nötrlenir; değişiklik yapılmaz.
- Yıllık büyüme/değişim metrikleri (varlık büyümesi, kâr büyümesi, istikrar) karışık bazlı
  dönemde (paydanın tarihsel, payın TMS 29 olduğu 2023Q4–2024Q3 raporları) **hesaplanmaz**.
- TTM akım kalemleri dört çeyreğin toplamı; karışık satın alma gücü kabul edilir, not edilir.

**V6 — Makro (EVDS, aylık).** TÜFE, politika faizi, TL mevduat faizi (1 aya kadar vadeli;
risksiz getiri olarak), dolar/TL, euro/TL. EVDS anahtarı `.env`'de.

**V7 — Enerji/uydu.** EPİAŞ PTF ve barajlı hidro (2017–), kar (ERA5-Land) — uydu projesinin
`cikti/` klasöründen.

**F-V0 — Veri kabul raporu (sonuç içermez).** Her ay: evren büyüklüğü, çıkmış pay sayısı,
fiyat faktörü doluluğu, mali faktör doluluğu (profile göre), yedek gecikme kullanılan oran,
V4 kontrol tablosu. Testlere geçiş koşulu: keşif döneminde evren-ay gözlemlerinin ≥ %90'ında
fiyat faktörleri, sanayi profilinde ≥ %80'inde değer/kalite faktörleri dolu.

---

## 4. Ortak kurallar (her test için)

- **Frekans aylık, takvim bazlı.** Ay sonunda yalnızca o tarihe kadar yayımlanmış bilgi kullanılır
  (Research'ün yayın-tarihi bazlı kesitleri yerine; böylece tüm hisseler aynı getiri penceresini
  paylaşır).
- Getiri: ay sonu düzeltilmiş kapanışlardan basit getiri; **risksiz faize göre fazla getiri**
  (risk modeli ve Fama–MacBeth). Piyasa faktörü = BIST100 getirisi − risksiz.
- Ay başı evren: o ay işlem gören, en az 12 ay fiyat geçmişi olan, önceki 3 ayın medyan günlük TL
  hacmine göre **en likit 200** pay (v1: 250; 2016'da ~400 paylık piyasada 250, %0,2 maliyet
  varsayımının geçersiz olduğu sığ hisseleri içeriyordu).
- Karakteristikler her ay %1–%99 kırpılır, kesitsel z-puanına çevrilir.
- Profil kuralı (Research'teki gibi): EV tabanlı ve nakit akışı metrikleri yalnız sanayi/holding/
  GYO; B/P ve E/P bankalar ve sigorta dahil; kalite metrikleri profile özel. Değer ve kalite
  z-puanları sektör içinde hesaplanır (sektörde < 10 pay varsa tüm evrende).
- **Örneklem:** keşif 2016-07 → 2023-12 (90 ay); saklı 2024-01 → 2026-09 (yalnız Grup Y);
  ileriye dönük kayıt 2026-11 → (Grup G ve tüm nihai model).
- Çıkarım: Fama–MacBeth katsayılarının zaman ortalaması, Newey–West (6 gecikme) t. Dilim
  portföyleri: 5'li, eşit ağırlıklı (değer ağırlıklı ikincil rapor).
- İşlem maliyeti: tek yön %0,2; alfa portföylerinde ciro raporlanır.

---

## 5. Faktör tanımları (sabit)

Liste literatürden gelir; Research sonuçlarına göre seçilmemiştir.

| Kod | Grup | Tanım |
|---|---|---|
| BUYUKLUK | Y | log(PD), ay sonu |
| MOMENTUM | Y | t−12 → t−1 ay getirisi (son ay hariç) |
| GERI_DONUS | Y | son 1 ay getirisi |
| DUSUK_OYN | Y | son 12 ay günlük getiri oynaklığı (en az 200 gün) |
| BETA | Y | son 36 ay (en az 24) aylık fazla getirinin piyasa betası |
| LIKIDITE | Y | son 3 ay ortalama günlük TL hacim / PD |
| DEGER_BP | G | özkaynak / PD (son yayımlanmış bilanço) |
| DEGER_EP | G | TTM net kâr / PD |
| KALITE_ROE | G | TTM net kâr / ortalama özkaynak |
| KARLILIK | G | TTM brüt kâr / toplam varlık (yalnız sanayi/holding/GYO) |
| YATIRIM | G | toplam varlıkların yıllık büyümesi (V5 kuralıyla) |

Makro duyarlılıklar (Grup Y, F-R1'den gelir; F-A2'de kontrol değişkeni): BETA_USD, BETA_FAIZ,
BETA_ENF — her hissenin 36 aylık zaman serisi regresyonundaki katsayıları.

---

## 6. Testler

### F-A: Alfa

**F-A0 — Research replikasyonu ve evren yanlılığı (rapor, geçme ölçütü yok).** Research'ün
değer bileşik skoru ve B/P'si, bölüm 4 kurallarıyla (aylık takvim, fazla getiri, NW t), keşif
döneminde iki evrende hesaplanır: (a) bugünkü Yıldız Pazar, (b) V1 evreni. Raporlanan: 1 aylık
IC ve uzun–kısa getirisi. (a) − (b) farkı, Research sonuçlarındaki seçim yanlılığının ölçüsüdür.

**F-A1 — Standart faktörler (keşif dönemi).** Her ay kesitsel regresyon: sonraki ayın fazla
getirisi ~ 11 standart faktör + sektör kuklaları. "Çalışıyor" eşiği \|t\| ≥ 2,0 ve işaret
literatürle aynı (BUYUKLUK −, MOMENTUM +, GERI_DONUS −, DUSUK_OYN −, BETA −, LIKIDITE −,
DEGER +, KALITE +, KARLILIK +, YATIRIM −). Grup G için bu, görülmüş dönemin yeniden ölçümüdür;
geçse bile nihai kanıt ileriye dönük kayıttır. Grup Y için geçenler saklı dönemde işaretini
korumalıdır. Her faktör için tek değişkenli 5'li dilim uzun–kısa ayrıca raporlanır.

**F-A2 — Aday (yeni) faktörler.** F-A1 regresyonuna aday eklenir; kontroller: 11 standart faktör,
sektör kuklaları ve **BETA_USD, BETA_FAIZ, BETA_ENF** (adayın kur/faiz/enflasyon duyarlılığının
kılık değiştirmiş hali olmadığını göstermek için). Aday geçer, eğer: keşifte \|t\| ≥ 3,0 **ve**
uzun–kısa portföyü maliyet sonrası pozitif **ve** saklı dönemde işaret korunuyor. Adaylar:
- ELEKTRIK_DUYARLILIK: hissenin son 36 ayda PTF ($) aylık değişimine betası × PTF'nin önceki ay
  değişimi.
- HIDRO_DUYARLILIK: hidro anomalisi betası × önceki ayın hidro anomalisi.
- KUR_DUYARLILIK: dolar/TL betası × önceki ayın dolar/TL değişimi.
- Her yeni aday, veri görülmeden bu dosyaya eklenmiş olmalı.

**F-A3 — Research'ten gelen keşif sonrası hipotezler (yalnız ileriye dönük).** EBIT/EV, istikrar
bileşik skoru, değer×kalite (değer skoru, kalite skoru üst yarısında). Geçmiş veride yeniden
test edilmez (sonuç zaten görüldü). 2026-11'den itibaren aylık kayıt; 24 ay sonunda NW t ≥ 2,0 ve
uzun–kısa maliyet sonrası pozitifse kabul.

**F-A4 — Birleşik alfa skoru.** F-A1 ve F-A2'den geçen faktörlerin **eşit ağırlıklı** z-puanı
ortalaması; işaretler bölüm F-A1'deki literatür işaretleri (ağırlık tahmin edilmez). Grup Y
bileşenleri için saklı dönemde, tüm skor için ileriye dönük kayıtta değerlendirilir: 5'li dilim
uzun–kısa maliyet sonrası pozitif ve aylık IC ortalaması pozitif.

### F-R: Risk

**F-R1 — Makro zaman serisi modeli.** Her hisse için 36 aylık pencerede: fazla getiri ~ piyasa +
Δ dolar/TL + Δ politika faizi + enflasyon sürprizi (aylık TÜFE değişimi − önceki 3 ayın
ortalaması). Raporlanan: ortalama R², her makro faktörün \|t\| > 2 çıktığı hisse oranı.
Çıktı olarak BETA_USD, BETA_FAIZ, BETA_ENF üretilir (yalnız t'ye kadar veri; ileriye bakmasız).

**F-R2 — Aday risk faktörü katkısı.** F-R1'e aday eklenir (ΔPTF, hidro anomalisi). Aday geçer,
eğer: (i) hisselerin ≥ %15'inde \|t\| > 2 (rastgelede ~%5), **ve** (ii) keşif döneminin iki
yarısında hesaplanan betaların kesitsel korelasyonu ≥ 0,30, **ve** (iii) saklı dönemde, adayla
tahmin edilen kovaryansla kurulan minimum varyans portföyünün gerçekleşen oynaklığı adaysız
modelinkinden düşük.

**F-R3 — Kesitsel (Barra tipi) risk modeli.** Her ay: fazla getiri ~ sektör kuklaları + BUYUKLUK,
BETA, MOMENTUM, DUSUK_OYN, LIKIDITE, DEGER_BP, BETA_USD (z-puanları), PD karekökü ağırlıklı
EKK. Faktör kovaryansı 36 ay üstel ağırlıklı (yarı ömür 12 ay), özgül risk 24 ay. Raporlanan:
keşifte ortalama kesitsel R². Geçme ölçütü (saklı dönem): 100 rastgele ve 20 sektör-nötr uzun–kısa
portföyün **yanlılık istatistiği** (gerçekleşen / öngörülen oynaklık) ortalaması 0,8–1,2 arasında,
ve aynı portföylerde yalnız piyasa + sektör modelinden daha yakın 1'e.

---

## 7. Hedef model mimarisi (testler geçerse)

Risk: F-R3 (+ F-R2'den geçen aday). Alfa: F-A4 skoru. Portföy: risk modeliyle sektör ve
piyasa nötr, ciro sınırlı optimizasyon. Her ay sinyal ve portföy, getiri görülmeden kayda yazılır.

---

## 8. Test sayacı

| Kayıt | Sayı |
|---|---|
| Research (önceki, sonuçlar görüldü) | ~220 istatistik; bağımsız faktör sayısı ~45 |
| F-A1 | 11 faktör |
| F-A2 | 3 aday |
| F-A3 | 3 hipotez (yalnız ileriye dönük) |
| F-A4, F-R1, F-R3 | 1'er model testi |
| F-R2 | 2 aday |
| F-A0, F-V0 | rapor (sayılmaz) |
| Uydu projesinden devreden | ~32 |

Eşikler (\|t\| ≥ 3 adaylar için) bu toplam sayı göz önünde tutularak seçildi.

## 9. Sıradaki adım

1. V1–V2 indirmesi (kullanıcının bilgisayarında; bulut İş Yatırım'a erişemiyor):
   `faktor/veri_topla.py`'ye çıkmış paylar ve 2012 başlangıcı eklenecek; Research'ün fiyat
   istemcisi (`src/data/market`) yeniden kullanılabilir.
2. V3–V5 düzeltmeleri, ardından F-V0 raporu. Getiri sonucu ancak F-V0 geçince hesaplanır.

---

## Ek (2026-10-23): F-A5 — Kur farkı sürprizi (ileriye dönük aday)

Kaynak: `ARASTIRMA_PLANI.md` T-P2 ve T-P6 (keşif 2017Ç3–2022Ç3: çeyrek sonu → bilanço getirisi IC +0,081, t 3,8;
momentum kontrolünden etkilenmiyor; kâr sürprizini IC +0,25 ile öngörüyor; bilanço günü tepkisi yok).
- Sinyal: Ŝ_KUR = (NFX × d_q − NFX' × d_(q−4)) / PD; NFX = çeyrek sonuna kadar KAP'ta yayımlanmış son rapordaki parasal
  net yabancı para pozisyonu (İş Yatırım kalem 4BEA), d = çeyrekte USD/TRY değişimi, PD = çeyrek sonu piyasa değeri.
- Kayıt: her çeyrek sonundan sonraki ilk işlem günü (ilk: 2027-01-04, 2026Ç4) sinyaller, getiri görülmeden
  `cikti/faktor/canli/kur_surpriz_<tarih>.csv` dosyasına yazılır. Pozisyon: kohort içi 5'li dilim, Q5 al / Q1 sat,
  çeyrek sonu + 1 işlem günü → her şirketin bilanço sonrası 2. işlem günü.
- Değerlendirme: 8 çeyrek sonra (2028Ç4 bilançoları). Kabul: ortalama IC > 0 ve t ≥ 2 (8 kohortla zor; ikincil ölçüt
  işaret kohortların ≥ 6/8'inde pozitif) ve Q5 − Q1 maliyet (%0,4) sonrası pozitif.
- Açık risk: sinyal çoğu çeyrekte şirketin kur maruziyetiyle neredeyse aynı (|r| 0,6–1,0); getiri, pencere içinde süren
  kur hareketine maruziyet olabilir. İleriye dönük raporda pencere içi USD/TRY değişimi ve NFX/PD ile birlikte raporlanır.
- TMS 29 notu: 2024 sonrası raporlarda NFX hâlâ dönem sonu TL tutarı; PD ile oranlandığı için seviye kırılması yok.
