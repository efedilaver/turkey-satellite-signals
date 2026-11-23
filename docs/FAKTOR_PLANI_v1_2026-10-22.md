# Çok faktörlü BIST modeli: plan ve test kaydı

Amaç: hem **risk** (hisselerin birlikte hareketini açıklayan faktörler) hem **alfa** (gelecek
getiriyi öngören faktörler) için kullanılabilir değişkenleri bulmak; uydu, enerji ve makro
verisinden türetilen aday değişkenleri standart faktörlerin **ötesinde** katkıları için sınamak.

Kurallar `ARASTIRMA_PLANI.md` ile aynı: her test sonucu görülmeden kaydedilir, değişen kural
yeni numara alır, test sayısı tutulur. Kayıt: 2026-10-22, veri henüz inmedi.

## Veri

- Evren: KAP'taki tüm BIST şirketleri (bugün işlem görenler; borsadan çıkanlar yok → hayatta
  kalan yanlılığı; özellikle düşük kalite/küçük hisse sonuçlarını iyimser gösterebilir).
- Fiyat, hacim, piyasa değeri: İş Yatırım (günlük, 2014–). Mali tablolar: İş Yatırım (çeyreklik,
  2013–; sanayi XI_29, finansallar UFRS).
- Makro: TCMB EVDS (TÜFE, politika faizi, fonlama maliyeti, dolar/TL, euro/TL).
- Enerji/uydu: EPİAŞ PTF ve barajlı hidro (2017–), kar (ERA5-Land, 2001–).

## Ortak kurallar (her test için)

- Frekans aylık. Getiri: ay sonu düzeltilmiş kapanışlardan log getiri; BIST100'e göre fazla getiri.
- Ay başı evren: en az 12 ay fiyat geçmişi olan ve önceki 3 ayın medyan günlük TL hacmine göre
  **en likit 250** hisse (enflasyon yüzünden sabit TL eşiği kullanılmaz).
- **Bilgi gecikmesi:** bir çeyreğin mali tablosu çeyrek sonundan **3 ay sonra** kullanılabilir
  sayılır (SPK süreleri bundan kısa; temkinli). Akım kalemler son 12 ay toplamı (kümülatif
  raporlardan türetilir).
- Karakteristikler her ay %1–%99 kırpılır ve kesitsel z-puanına çevrilir.
- Finansal şirketler (banka, sigorta, aracı kurum, GYO) değer/kalite faktörlerinden çıkarılır;
  risk modelinde ayrı sektör olarak kalır.
- **Örneklem bölünmesi:** keşif 2016-01 → 2023-12; **saklı dönem 2024-01 → 2026-09**, yalnızca en
  sonda, kayıtlı faktörler için **bir kez** bakılır.
- İşlem maliyeti: alfa portföylerinde tek yön %0,2.

## Standart faktörler (tanımlar sabit)

| Kod | Tanım |
|---|---|
| BUYUKLUK | log(piyasa değeri) |
| DEGER_EP | son 12 ay net kâr / piyasa değeri |
| DEGER_BP | özkaynak / piyasa değeri |
| MOMENTUM | t−12 → t−1 ay getirisi (son ay hariç) |
| GERI_DONUS | son 1 ay getirisi |
| DUSUK_OYN | son 12 ay günlük getiri oynaklığı |
| BETA | son 36 ay aylık getirilerin BIST100 betası |
| KALITE_ROE | son 12 ay net kâr / ortalama özkaynak |
| KARLILIK | son 12 ay brüt kâr / toplam varlık |
| YATIRIM | toplam varlıkların yıllık büyümesi |
| LIKIDITE | son 3 ay ortalama günlük TL hacim / piyasa değeri |

## F-A: Alfa testleri

**F-A1 — Standart faktörlerin BIST'te prim üretip üretmediği (keşif dönemi).**
Her ay kesitsel regresyon: sonraki ayın fazla getirisi ~ tüm standart faktör z-puanları
(Fama–MacBeth); katsayıların zaman ortalaması, Newey–West (6 gecikme) t-istatistiği. Ayrıca her
faktör için 5'li dilim uzun-kısa getirisi. Bu literatürde bilinen faktörlerin doğrulamasıdır;
"çalışıyor" eşiği |t| ≥ 2,0.

**F-A2 — Aday (yeni) faktörler.** Aynı regresyona standart faktörler kontrol olarak girer; aday
ancak **|t| ≥ 3,0** (çoklu test düzeltmesi; Harvey–Liu–Zhu önerisi) ve uzun-kısa portföyü
maliyet sonrası pozitifse geçer; ardından saklı dönemde işareti korumalı. İlk adaylar:
- ELEKTRIK_DUYARLILIK: hissenin son 36 ayda PTF ($) aylık değişimine betası, × PTF'nin
  önceki ay değişimi (fiyat şoku elektrik-duyarlı hisselere gecikmeli yansıyor mu?).
- HIDRO_DUYARLILIK: hidro anomalisi betası × önceki ayın hidro anomalisi.
- KUR_DUYARLILIK: dolar/TL betası × önceki ayın dolar/TL değişimi.
- Her aday için tanım, veri görülmeden bu dosyaya eklenmiş olmalı.

## F-R: Risk testleri

**F-R1 — Temel risk modeli.** Her hisse için 36 aylık pencerede zaman serisi regresyonu:
fazla getiri ~ piyasa + Δ dolar/TL + Δ politika faizi + enflasyon sürprizi
(enflasyon sürprizi = aylık TÜFE değişimi − önceki 3 ayın ortalaması). Raporlanan: ortalama
açıklanan varyans (R²), her makro faktörün anlamlı (|t| > 2) çıktığı hisse oranı.

**F-R2 — Aday risk faktörü katkısı.** F-R1 modeline aday eklenir (ΔPTF, hidro anomalisi).
Aday geçer, eğer: (i) hisselerin ≥ %15'inde |t| > 2 (rastgelede ~%5 beklenir), **ve**
(ii) betalar istikrarlı: keşif döneminin iki yarısında hesaplanan betaların kesitsel
korelasyonu ≥ 0,30, **ve** (iii) saklı dönemde, adayla tahmin edilen kovaryans matrisiyle
kurulan minimum varyans portföyünün gerçekleşen oynaklığı, adaysız modele göre düşük.

## Test sayacı

Bu dosyada kayıtlı: F-A1 (11 standart faktör, doğrulama), F-A2 (3 aday), F-R1 (rapor),
F-R2 (2 aday). Uydu projesinden devreden ~32 test ayrıca sayılır.
