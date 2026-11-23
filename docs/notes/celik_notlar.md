# Entegre çelik tesisleri: uydu SWIR izleme için araştırma notları

Derleme tarihi: 21.10.2026. Bu klasördeki dosyalar:

| Dosya | İçerik |
|---|---|
| `celik_tesisler.csv` | Tesis merkezleri, birimler, tesis bbox'ları. Birim konumları **yaklaşık**: bkz. §1 |
| `celik_uretim.csv` | Çeyreklik sıvı çelik. Erdemir Grubu, İsdemir ayrı, Ereğli türetilmiş, Kardemir (kısmi). Toplam 164 satır |
| `celik_olaylar.csv` | Yüksek fırın (YF) duruşları, yenilemeler, deprem ve türetilmiş anomaliler. Toplam 17 olay |

## 1. Koordinatlar: ne doğrulandı, ne doğrulanamadı

- **Tesis düzeyi (doğrulandı).** GEM Global Iron & Steel Tracker sayfalarında tesis noktası "exact" olarak geçiyor:
  Erdemir 41.261469, 31.420106; İsdemir 36.735672, 36.204581; Kardemir 41.180307, 32.634343.
  Mapcarta üzerinden OSM poligon merkezleri de okundu: Erdemir way 133474356 → 41.26105, 31.41873; Kardemir way 169163741 → 41.18212, 32.62701.
  İsdemir'in tesis poligonu bulunamadı, yalnız İsdemir tren istasyonu düğümü var (36.72392, 36.21358).
- **Birim düzeyi (doğrulanamadı).** OSM'ye erişim kapalıydı: Overpass, Nominatim ve osm.org/api robots.txt veya proxy nedeniyle reddedildi.
  Wikimapia'da nesne kimliği çıkmadı. ÇED dosyalarında da koordinat bulunamadı.
  Bu yüzden her birim satırı tesis merkezine konuldu ve tüm tesisi kapsayan bir yarıçapla (Erdemir ve İsdemir 1500 m, Kardemir 1000 m) `YAKLASIK` olarak işaretlendi.
  Tek somut ipucu: KAP 2018 kararına göre yeni Ereğli YF-2 "eski YF-2'nin güneyindeki araziye" kuruldu.
- **Bbox'lar elle çizildi ve yaklaşık.** Dayanak olarak merkez noktalar, çevre referansları (liman, hastane, istasyon, Payas merkezi) ve İsdemir saha alanı (~6.8 km², Wikipedia) kullanıldı.
  İlk kullanımdan önce Sentinel-2 RGB üzerinde kontrol edin.
- **Birimleri bulmak için önerilen yol.**
  1. bbox içinde 2019–2026 arası tüm bulutsuz Sentinel-2 L2A sahnelerini alın.
  2. Her pikselde B12 > ~0.5 (veya B12/B8A > ~1.5 ve B12 > B11) olma sıklığını hesaplayın.
  3. Sıklığı en yüksek kümeler tipik olarak şunlardır: YF döküm holleri, BOF çelikhanesi (aralıklı), cüruf döküm sahaları (geniş, aralıklı) ve kok fırını itme tarafı.
  4. Kümeleri bir kez Google Earth veya OSM ile etiketleyip `celik_tesisler.csv`'ye yazın.

  OSM erişimi olan bir makinede çalıştırılacak Overpass sorgusu:
  ```
  [out:json];(nwr["man_made"~"works|kiln|chimney"](41.24,31.39,41.28,31.45);nwr["building"="industrial"]["name"](41.24,31.39,41.28,31.45);nwr["industrial"](41.24,31.39,41.28,31.45););out center tags;
  ```

## 2. Üretim verisi: yayın yapısı ve gecikme

- **Erdemir (EREGL).** Çeyreklik yatırımcı sunumunda konsolide sıvı çelik veriliyor. Konsolide rakam Ereğli ile İsdemir'in toplamı.
  - Teyit: 2019'da 8787 − 5626 = 3161 kt. Bu, GEM'deki Ereğli 2019 BOF üretimiyle birebir aynı.
  - Sunum yayın tarihleri: 3A için ~27–29 Nisan, 6A için ~6–17 Ağustos, 9A için ~20–26 Ekim, 12A için ~10 Şubat–3 Mart. Yani çeyrek sonundan **~4–7 hafta** sonra.
  - 2026 9A sunumu 21.10.2026 itibarıyla bulunamadı. 2025 9A sunumu 20.10.2025'te yayımlanmıştı.
  - **Aylık hacim yayımlanmıyor.**
- **İsdemir (ISDMR).** Kendi yatırımcı sunumlarında çeyreklik sıvı çelik veriliyor. 2018Q1–2026Q2 serisi tam.
  - Ereğli tesisi bu yüzden **Grup − İsdemir** olarak türetilebiliyor. CSV'de `Erdemir_Eregli_tesisi_TURETILMIS` adıyla duruyor.
  - Böylece **iki ayrı tesis için uydu–üretim testi** yapılabiliyor.
- **Kardemir (KRDMD).** Çeyreklik faaliyet raporunda (KAP) yalnız **kümülatif** üretim tablosu var. Kalemler: kok, sinter, **sıvı ham demir** (YF çıktısı), sıvı çelik, ham çelik, net mamul.
  - Çeyrek değerleri farklardan türetilmeli. Ancak KAP ek PDF'lerine ancak tek tek ve kısmen erişilebildi.
  - Yatırımcı sunumları yıllık ve 6A/9A değer veriyor. Analist notları (Vakıf Yatırım) bazı çeyrekleri doğrudan veriyor.
  - Sonuç: Kardemir çeyrek serisi **eksik**. Yaklaşık değerler CSV'de `YAKLASIK` notuyla işaretli.
  - Önerilen tamamlama: KAP'tan 2018–2026 faaliyet raporlarının (3/6/9/12A) tablosunu toplayıp farkları almak.
  - Kardemir "ham çelik" terimini dökülmüş yarı mamul için kullanıyor. Bu yüzden ham çelik sıvı çelikten ~%3 düşük. SteelOrbis'in "crude steel" rakamları bu kalem.
  - Kardemir KAP'ta çeyreklik **planlanan satış hacmi** de açıklıyor (ör. Temmuz–Eylül 2026). Bu bir öncü gösterge olabilir; açılmadı, yalnız arama sonucunda görüldü.
- **Ulusal veri.**
  - worldsteel aylık ham çelik basın bülteni, ay sonundan **~22–26 gün** sonra çıkıyor (ör. Ağustos 2026 verisi 24.09.2026'da, Temmuz verisi 24.08.2026'da).
  - TÇÜD'ün tüketim ve dış ticareti de içeren aylık değerlendirmesi ~**1 ay** sonra çıkıyor (ör. Ağustos 2026 verisi haberde 01.10.2026).
  - TÇÜD sitesinde BOF/EAF ayrımı görülmedi.
  - TÜİK C241 sanayi üretim endeksi (proje kökündeki `celik.csv`) ise ~40 gün gecikmeli.
  - Ulusal toplamın ~%70'i EAF olduğu için BOF tesis sinyali ulusal veriyle ancak zayıf ilişkili olur. Doğru doğrulama hedefi şirket ve tesis serileridir.

## 3. Uydu testine en uygun olaylar (yer gerçeği)

1. **İsdemir depremi: 06.02.2023 – 24.04.2023 tam duruş.** 2023Q1 sıvı çelik 431 kt (normal ~1400 kt). En temiz "kapalı" kontrol dönemi.
2. **İsdemir YF-2 bakımı: 24.11.2020'den itibaren 44 gün.** YF-4 Nisan 2020'de duruşa girdi; 2020Q2 1026 kt.
3. **Ereğli 2024Q4–2025Q2 düşüşü (türetilmiş).** Çeyrek üretimi 692 / 531 / 449 kt'ye indi, normali ~900 kt. Hangi birimin durduğu açıklanmamış.
   Kok bataryası geçişi (1–2 kapandı, 4. batarya ~Mayıs 2025'te devreye girdi) veya talep kaynaklı kısıntı olabilir. **Uydunun gerçekten bilgi katabileceği vaka.**
4. **Ereğli 2023Q3 düşüşü.** Üretim ~464 kt'ye indi. Ardından 29.10.2023'te yeni YF-2 devreye girdi.
5. **Kardemir YF-1 (Kasım 2021–Mart 2022) ve YF-4 (Nisan–Kasım 2022) yenilemeleri.** 2022 yıllık üretim 2297 kt'ye düştü.

## 4. Bulutluluk (MGM uzun dönem ortalaması, günlük güneşlenme saati)

| Ay | Zonguldak (Erdemir) | Karabük (Kardemir) | Hatay (İsdemir) |
|---|---|---|---|
| Oca | 2.3 | 0.0* | 3.4 |
| Şub | 2.8 | 0.2* | 4.6 |
| Mar | 3.8 | 4.6 | 6.0 |
| Nis | 5.2 | 7.9 | 7.3 |
| May | 6.9 | 7.5 | 9.1 |
| Haz | 9.1 | 8.1 | 10.8 |
| Tem | 9.9 | 10.6 | 11.2 |
| Ağu | 9.2 | 10.7 | 10.3 |
| Eyl | 7.2 | 8.5 | 9.3 |
| Eki | 4.9 | 7.4 | 7.1 |
| Kas | 3.4 | 4.9 | 5.1 |
| Ara | 2.4 | 0.0* | 3.4 |
| Yağışlı gün, Ara–Şub | ~17/ay | ~9/ay | ~14/ay |
| Yağışlı gün, Haz–Ağu | 6–9/ay | 4–7/ay | 0.5–2/ay |

\*Karabük kış değerleri (0.0) büyük olasılıkla eksik ölçümden kaynaklanıyor. Ancak vadi sisi ve inversiyon kışın gerçek bir sorun.

Sonuç:
- **En bulutlu tesis Erdemir Ereğli** (Karadeniz kıyısı). Ekim–Mart arasında bulutsuz Sentinel-2 sahnesi seyrek olacak.
- Kardemir'de kışın sis, inversiyon ve tesis dumanı var.
- İsdemir yazın neredeyse her geçişte açık.
- Çeyreklik Ereğli ve Kardemir tahminleri için Landsat 8/9 (B6/B7) ile Sentinel-2'yi birleştirin. Gece VIIRS (VNF/Nightfire, M10/M11) bulut sorunundan bağımsız değil ama zaman çözünürlüğünü artırır.
- Hepsinde geçiş saati ~10:30–11:00 yerel saat. Aralıklı süreçler (BOF üfleme, cüruf dökümü) örnekleme gürültüsü yaratır; çeyreklik ortalama alın.

## 5. Güven düzeyi

| Veri | Güven | Not |
|---|---|---|
| Erdemir Grubu ve İsdemir çeyrekleri | **Yüksek** | Her yıl için çeyrek toplamı yıllık rakamla ±1 kt tutuyor. Grafik etiketleri karışık gelen sunumlarda kümülatif farklar ve %YoY/QoQ ifadeleriyle eşleştirildi |
| Kardemir yıllık, 9A ve 6A | Yüksek | |
| Kardemir çeyrek değerleri | Düşük–orta | Çoğu türetilmiş veya yaklaşık |
| Tesis noktaları ve OSM merkezleri | Yüksek | |
| bbox | Orta | |
| Birim koordinatları | **Düşük** | Doğrulanamadı |

`yayin_tarihi` sütunu, rakamın alındığı **açılan belgenin** tarihidir. Rakam ilk kez genelde daha önce, ilgili çeyreğin kendi sunumunda yayımlanmıştır. Tarihsiz Erdemir sunumlarında yükleme ayı yazıldı.

## 6. Açılan URL'ler

### Tesis ve koordinat
- https://www.gem.wiki/Erdemir_Eregli_steel_plant
- https://gem.wiki/Isdemir_steel_plant
- https://www.gem.wiki/Kardemir_Merkez_steel_plant
- https://inzonex.co.uk/industryatlas/plant/erdemir-eregli-steel-plant.html
- https://en.wikipedia.org/wiki/Port_of_Erdemir
- https://en.wikipedia.org/wiki/%C4%B0sdemir
- https://en.wikipedia.org/wiki/Kardemir
- https://mapcarta.com/Erdemir
- https://mapcarta.com/W133474356
- https://mapcarta.com/Kardemir
- https://mapcarta.com/%C4%B0sdemir
- https://wikimapia.org/search/?q=Erdemir (sonuç yok)
- https://webdosya.csb.gov.tr/db/ippc/duyurular/proje-tanitimi-prof.-dr.-mustafa-yasar-20190307131323.pdf

Açılamayanlar:
- https://www.gem.wiki/Isdemir_Payas_steel_plant (sunucu hatası)
- Overpass, Nominatim ve osm.org/api (robots/proxy)
- Overpass aynaları (kumi, private.coffee, mail.ru)
- api.wikimapia.org

### Erdemir yatırımcı sunumları (erdemir.com.tr/storage/uploads/…)
- 2023/09/66fdd938f01354e2730329f9fd6cce8d.pdf (6A18)
- 2023/09/3ae129acc78ad3369ae5e3707ca46206.pdf (9A18)
- 2023/09/476b3b4a09d9603e91a76dc47b10c012.pdf (6A19)
- 2023/09/aef8d2d9bf781e9c656e05ebe0cf2cd6.pdf (12A19)
- 2023/09/2d53b7bdfc3c6f91a4b59fdce0e703fd.pdf (3A20)
- 2023/09/c7e09ce1776bf9cde465bfb4b9b83586.pdf (6A20)
- 2023/09/30a5e3f38f4c219bab770445df795719.pdf (9A20)
- 2023/09/f65cfec3c07db42a0536dbdac27062c3.pdf (12A20)
- 2023/09/6a0a008f675246cd9b4f081be3030d00.pdf (3A21)
- 2023/09/ee50de783ce8ee6b0dce8814defbd007.pdf (6A21)
- 2023/09/ead0fbbaad67018d0d8153c7f5f27fc9.pdf (9A21)
- 2023/09/f792a7fc9a7b0da8bcba07ba34e7ba01.pdf (12A21)
- 2023/09/8597931e19aabc5ef647ad79eeba077d.pdf (3A22)
- 2023/09/def75a4a53c9b411a91103d7924ea888.pdf (6A22)
- 2023/10/12efa51ac001236ab8761bf49e6eaa15.pdf (9A23)
- 2024/05/0aa6704e4db1d22859d7462a811216b2.pdf (3A24)
- 2025/02/0b3a63d15f4e08a6c49f639560836d4e.pdf (12A24)
- 2025/08/e8a3e1d0b37e5a4195aada003abbbd94.pdf (6A25)
- 2025/10/ba71f3258b18cb3b02abaae5f997a428.pdf (9A25)
- 2026/02/a78b69bab603a60cecc24de19e0eb6fa.pdf (12A25)
- 2026/04/b970b7704b83acadc002b72500fa0844.pdf (3A26)
- 2026/08/1caf0becd3bab3772f7b92093765e5db.pdf (6A26)
- 2026/08/e6c966a281bedb6453b1af19273a2647.pdf (OYAK tesis bazlı mamul üretimi)
- 2023/08/d239e74dad4a3c029dadace2345a6f10.pdf (büyük kaza bildirimi)
- https://kap.org.tr/en/api/file/download/4028328d9cc9d32c019d1a42640c1f44 (2025 entegre rapor)

### İsdemir yatırımcı sunumları (isdemir.com.tr/storage/uploads/…)
- 2024/03/37e536f955e80a440df9aa473320492d.pdf (6A19)
- 2024/03/665e871ced13f0fa34434f03b86ba197.pdf (9A19)
- 2024/03/05d87e07300f60a430801b8093054976.pdf (12A19)
- 2024/03/8ff8d7bd467482ddce6d8b26fdedc590.pdf (6A20)
- 2024/03/b7937423d58d8e6655a0ca649ef50392.pdf (9A20)
- 2024/03/71d302d1310f51edfd67e2f16408f65c.pdf (12A20)
- 2024/03/3f9f6bbcdde55e2af4581321b54436e5.pdf (6A21)
- 2024/03/6a92abceaf22bf98969f25a06701ce6c.pdf (9A21)
- 2024/03/318483ab6a60b719d2df53858c1ad983.pdf (12A21)
- 2024/03/16f9a91b7d6e08bf4808d4fc147f1848.pdf (3A22)
- 2024/03/d82ec45e1076f898b47fecca7569a975.pdf (6A22)
- 2024/03/f54cee94b02e5b19d4f497ca7c7ef321.pdf (9A22)
- 2024/03/0605d6d1ad0e7172423b9dbecfdc3e31.pdf (12A22)
- 2024/03/3e83461c078db8d74b7d2d2c9b9b5022.pdf (3A23)
- 2024/03/0c21df7ff2bc701e13308c11b3645683.pdf (6A23)
- 2024/03/b7e1d41217db5ea2af8c77cc98186a0a.pdf (9A23)
- 2024/03/6482ef4640b9c6db9b683244c2e6c224.pdf (12A23)
- 2024/05/427212a87c1ed9a68b7fdb973f928541.pdf (3A24)
- 2024/08/5b9abacd8d3235b8d5ce70564d9049f5.pdf (6A24)
- 2024/10/51fbd890f351fb4a48224321d0ae8419.pdf (9A24)
- 2025/10/cc4d5e3f5c8fb3da8b660a16407fc8b3.pdf (9A25)
- 2026/02/eef2141b936b13152b5e54a8fac457b8.pdf (12A25)
- 2026/04/01c791de897e7e5039accfc8ac0f04af.pdf (3A26)
- 2026/08/064eb13d6bfbee7ba75796507c1a000b.pdf (6A26)
- https://isdemir.com.tr/en/investor-relations/reports-and-presentations (2018–2026 ara dönem rapor bağlantıları listelendi)

### Kardemir
- https://www.kardemir.com/dosyalar/yatirimci/1/11112019/2019111111232564_yatirimci_1_11112019.pdf
- https://www.kardemir.com/dosyalar/yatirimci/1/22052024/2024052216442441_yatirimci_1_22052024.pdf
- https://www.kardemir.com/dosyalar/yatirimci/1/06092024/2024090609331553_yatirimci_1_06092024.pdf
- https://www.kardemir.com/dosyalar/yatirimci/1/12112024/2024111215391479_yatirimci_1_12112024.pdf
- https://www.kardemir.com/dosyalar/yatirimci/1/03122025/2025120314495355_yatirimci_1_03122025.pdf
- https://kap.org.tr/en/api/file/download/4028328c998ee9d7019a59ad2ab53684 (KAP 9A25 faaliyet raporu, üretim tablosu)
- https://kap.org.tr/tr/api/BildirimPdf/1512431 (KAP 9A25 bildirimi, 06.11.2025)
- https://kap.org.tr/tr/api/BildirimPdf/1653180
- https://kap.org.tr/en/Bildirim/1342168 (04.10.2024)
- https://vkyanaliz.com/Files/docs/4c24-finansal-sonuclari-kardemir-1741587346.pdf
- https://www.vkyanaliz.com/Files/docs/1c25-finansal-sonuclari-kardemir-1747058889.pdf
- https://www.vkyanaliz.com/Files/docs/4c25-finansal-sonuclari-kardemir-1773227773.pdf
- https://www.vkyanaliz.com/Files/docs/1c26-finansal-sonuclari-kardemir-1778496490.pdf
- https://www.vkyanaliz.com/Files/docs/2c22-finansal-sonuclari-kardemir-1659678083.pdf
- https://quartr.com/events/kardemir-karab-k-demir-elik-sanayi-ve-ticaret-a-s-krdmd-q2-2026_FROBQ79I
- https://gmk.center/en/news/kardemir-increased-steel-production-by-2-7-y-y-in-q1/amp/
- https://www.steelorbis.com/steel-news/latest-news/turkeys-kardemir-posts-net-loss-for-h1-2025-1404756.htm
- https://www.steelorbis.com/steel-news/latest-news/kardemir-posts-net-profit-in-h1-2026-accelerates-efforts-to-increase-international-market-share-1471225.htm
- https://www.ekonomist.com.tr/sirketler/kardemir-2026-yili-ilk-yari-finansal-sonuclarini-acikladi-77809
- https://yatirim.akbank.com/_layouts/15/AkbankYatirimciPortali/Rapor/Download.aspx?ID=11239
- https://denizyatirim.com/Uploads/Deniz_Yat_r_m_Strateji_ve_Ara_t_rma_KRDMD_1_24_Bilan_o_De_erlendirme_6833.pdf
- https://www.denizyatirim.com/Uploads/Deniz_Yat_r_m_Strateji_ve_Ara_t_rma_KRDMD_1_23_Bilan_o_De_erlendirme_3441.pdf
- https://www.denizyatirim.com/Uploads/Deniz_Yat_r_m_Strateji_ve_Ara_t_rma_KRDMD_2_23_Bilan_o_De_erlendirme_4241.pdf
- https://fintables.com/borsa-haber-akisi/c614e615-fc5c-4ee1-b9f1-9664ab7e4b33/krdma-faaliyet-raporu-konsolide

Yanlış şirket çıkan KAP dosyaları (Kardemir **Çelik** Sanayi; Karabük'le ilgisi yok):
- https://kap.org.tr/tr/api/file/download/4028328d9f52dddd01a01b3ed2a0331c
- https://kap.org.tr/tr/api/file/download/4028328d9f52dddd01a01b3bff5d32c5
- https://kap.org.tr/tr/api/file/download/4028328c9f52dc3f019f851ec5655c6c

### Olaylar ve haberler
- https://www.kap.org.tr/tr/BildirimPdf/704371
- https://uzmanpara.milliyet.com.tr/kap-haberi/ozel-durum-aciklamasi-genel/682f3f3d321e0c4a62dce6d0
- https://borsacoo.com/bildirim/24853
- https://www.bloomberght.com/erdemir-in-2nci-yuksek-firini-devreye-alindi-2341016
- https://www.steelorbis.com/steel-news/latest-news/turkeys-erdemir-to-commission-bf-no-2-on-october-29-1311933.htm
- https://erdemir.com.tr/en/corporate/media/press-release/erdemir-and-isdemir-launch-strategic-investments
- https://www.dunya.com/gundem/erdemir039de-korkutan-patlama-3-isci-yaralandi-haberi-279200
- https://www.dunya.com/sektorler/isdemir-kademeli-ve-kontrollu-sekilde-uretime-yeniden-baslanacak-haberi-686010
- https://www.capital.com.tr/haberler/tum-haberler/isdemirden-uretim-aciklamasi-geldi
- https://www.steelradar.com/en/haber/isdemir-announced-the-restart-of-production
- https://eurometal.net/isdemirs-new-blast-furnace-nears-completion-to-be-turkeys-largest/
- https://eurometal.net/turkeys-kardemir-to-reduce-output-on-adverse-market-conditions/
- https://kallanish.com/en/news/steel/market-reports/article-details/kardemir-to-decrease-production-amid-covid-19-0420
- https://kallanish.com/en/news/steel/market-reports/article-details/isdemir-to-halt-production-in-one-furnace-due-to-maintenance-0320
- https://kallanish.com/en/news/steel/market-reports/article-details/turkeys-isdemir-starts-repair-work-at-2nd-blast-furnace-1120
- https://fastmarkets.com/insights/turkeys-isdemir-starts-planned-maintenance-on-blast-furnace
- https://production.kallanish.com/en/news/steel/market-reports/article-details/erdemir-groups-output-and-revenue-notch-down-in-h1-0820/ (2020 H1: İsdemir YF-4 bakımı)
- https://www.capital.com.tr/haberler/tum-haberler/turkiyenin-ilk-yuksek-firini-yenilendi-1939da-acilmisti
- https://www.steelorbis.com/steel-news/latest-news/kardemir-reignites-upgraded-blast-furnace-1113395.htm
- https://www.steelorbis.com/steel-news/latest-news/turkeys-kardemir-commissions-modernized-blast-furnace-no-4-1269230.htm
- https://kallanish.com/en/news/steel/market-reports/article-details/kardemir-recommissions-revamped-no4-blast-furnace-1122
- https://gmk.center/en/news/turkeys-isdemir-prepares-to-launch-the-countrys-largest-blast-furnace/
- https://www.bloomberght.com/eregli-den-beklentilerin-altinda-net-zarar-3769411
- https://www.piapiri.com/analizler/arastirma-raporlari/erdemir-eregl-1-ceyrek-2025-sonuclari
- https://kuveytturkyatirim.com.tr/media/abxhp5eg/eregl-2ç25-finansal-sonuç-değerlendirmesi.pdf
- https://kuveytturkyatirim.com.tr/media/u0figitz/eregl-4ç24-finansal-sonuç-değerlendirmesi1.pdf
- https://yatirim.akbank.com/_layouts/15/AkbankYatirimciPortali/Rapor/Download.aspx?ID=10457
- https://www.vkyanaliz.com/Files/docs/1c26-finansal-sonuclari-erdemir-1777463035.pdf
- https://www.vkyanaliz.com/Files/docs/2c26-finansal-sonuclari-erdemir-1786094187.pdf
- https://ziraatyatirim.com.tr/documents/features/ZFG_YATIRIM_eregl-2023_05_03-1c23-2--pdf_260.pdf

Açılamayanlar:
- uzmanpara (Kardemir planlı bakım haberi)
- steelradar'daki Kardemir YF haberleri
- gmk.center'ın bazı sayfaları
- eurometal "Isdemir restarts BF" (içerik okunamadı)
- qnbinvest blog

### Ulusal veri ve iklim
- https://worldsteel.org/media/press-releases/
- https://www.hellenicshippingnews.com/world-steel-association-may-2026-crude-steel-production-slightly-lower/
- https://www.celik.org.tr/
- https://uzmanpara.milliyet.com.tr/uzmanpara/turkiyenin-ham-celik-uretimi-azaldi-7670840
- https://www.steelradar.com/en/haber/turkiyes-crude-steel-production-up-138-year-on-year-in-9-months/
- https://www.mgm.gov.tr/veridegerlendirme/il-ve-ilceler-istatistik.aspx?m=ZONGULDAK
- https://www.mgm.gov.tr/veridegerlendirme/il-ve-ilceler-istatistik.aspx?m=HATAY
- https://www.mgm.gov.tr/veridegerlendirme/il-ve-ilceler-istatistik.aspx?m=KARABUK
