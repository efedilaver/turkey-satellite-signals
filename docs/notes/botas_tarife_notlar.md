# BOTAŞ elektrik üretim amaçlı doğal gaz toptan satış tarifesi (2016-01 – 2026-09): notlar

Veri dosyası: `botas_elektrik_tarife.csv` (129 ay, her ay bir satır). Değer, o ayın 15'inde geçerli tarifedir. Derleme tarihi 2026-10-23.

## 1. Özet

| Durum | Ay sayısı |
|---|---|
| Toplam ay | 129 |
| Dolu | 118 |
| — doğrudan o ay için kaynaktan okunan | 82 |
| — önceki değer taşınan (değişiklik yok varsayımı, dayanağı aşağıda) | 33 |
| — yüzde değişimden hesaplanan | 3 (2018-09, 2018-10, 2022-09) |
| İki bağımsız kaynakla teyitli | 27 |
| Boş (bulunamadı) | 11: 2016-01 … 2016-09, 2019-04, 2019-05 |

## 2. Hangi tarife/sütun alındı

* **Sütun:** BOTAŞ tarife tablolarındaki **"Elektrik Üretimi Amaçlı Kullanım"** sütunu alındı. 2019–2024 tablolarında bu sütun Serbest Tüketici Kademe‑1, Kademe‑2, (Kademe‑1 Konaklama), Serbest Bölge, OSB Kademe‑1/2 satırlarında yer alır. Bakılan her PDF'de bu satırların hepsi **aynı değerdeydi**. 1 Mart 2025'ten itibaren tablo yapısı değişti: "Dağıtım Şirketleri / Konut", "OSB ve Serbest Tüketiciler" ve "Serbest Bölgeler" bloklarının her birinde ayrı bir "Elektrik Üretimi Amaçlı Kullanım" satırı var. Bunlar da birbirinin aynısı.
* **Alınmayanlar:**
  * "Elektrik Üretimi Amacı Dışındaki Kullanım", yani sanayi Kademe‑1/2.
  * Konut (evsel) tarifesi.
  * CNG ve LNG fiyatları.
  * **"Kompozit Kullanım"** (kojenerasyon/otoprodüktör) sütunu. Bu sütun 2018-08 ile 2019-08 arasında ayrı bir fiyattı: 2019-06'da 1,503 TL/Sm3, 2019-08'de 1,626 TL/Sm3. Dünya'ya göre 2018-11'de kojenerasyon fiyatı 1.503 TL/1000 m3 idi.
* **BOSB kaynakları:** Bursa OSB duyurularındaki "Elektrik üretim amaçlı kullanım, tüm kademeler" satırı, BOTAŞ tarifesinin OSB'ye birebir yansıtılmış hâlidir. Bu duyurularda fiyatın ÖTV, SKB ve OSB dağıtım bedeli hariç olduğu yazıyor.
* Tüm fiyatlar **KDV ve ÖTV hariç**tir.
* **`gecerlilik_baslangici`** sütunu, o fiyat seviyesinin ilk yürürlüğe girdiği tarihi gösterir; o ayın belgesinin yayım tarihini değil. Örnek: 2025-07 satırındaki 15,00 TL/Sm3'ün kaynağı "2 Temmuz 2025" tarifesidir, ama elektrik fiyatı 5 Nisan 2025'ten beri aynıdır. Bu yüzden satırda 2025-04-05 yazar.
* **Ay içi yürürlük:** 2025-04 (5 Nisan) ve 2026-04 (4 Nisan) tarifeleri ay ortasından önce yürürlüğe girdi. O ayın 15'inde geçerli olan yeni değerdir.

## 3. Birimler ve dönüşüm

CSV'de `tarife` sütunu kaynağın kendi birimiyle yazıldı, bu yüzden **iki farklı ölçek** var:

* `TL/1000 m3`: haber kaynakları ("1000 metreküp doğal gazın fiyatı …"). Haberler "m3" yazar, BOTAŞ'ın baz birimi Sm3'tür. Haberlerdeki m3 değerlerinin BOTAŞ Sm3 değerinin 1000 katı olduğu, PDF'li aylarla tutarlılıktan doğrulandı. Örnekler:
  * 2022-05: NTV 10.750 ↔ PDF 10,75
  * 2023-04: Birgün 10.000 ↔ PDF 10,00
  * 2020-10: AA 1.400 ↔ PDF 1,40
  * 2025-03: AA 12.000 ↔ PDF 12,00
* `TL/Sm3`: BOTAŞ tarife PDF'leri, BOSB duyuruları, Petroturk ve Anka.

**Normalize etmek için:** `TL/Sm3` değerini 1000 ile çarpın; böylece TL/1000 Sm3 elde edilir. Yıllık değişim hesabından önce bu yapılmalıdır, aksi hâlde seri 1.000 kat sıçrar.

**Enerji birimi (TL/kWh, TL/MWh) dönüşümü:**
* BOTAŞ PDF'leri her TL/Sm3 fiyatın yanına bir TL/kWh karşılığı yazar. Oran sabittir: **1 Sm3 = 10,64 kWh**, yani **1000 Sm3 = 10,64 MWh** (üst ısıl değer bazında).
* Teyit edilen örnekler:
  * 6,300000 / 0,59210526 = 10,640 (Şubat 2022)
  * 1,550000 / 0,14567669 = 10,640 (Haziran 2019)
  * 18,000000 / 1,69172932 = 10,640 (Nisan 2026)
  * 1,312200 / 0,12332707 = 10,640 (Ağustos 2018, Petroturk'ün aktardığı BOTAŞ yazısı)
* BOTAŞ Aralık 2021 serbest tüketici fiyat detayında referans koşullar şöyle verilmiş: 15 °C, 1,01325 bar, **9155 kcal/Sm3 üst ısıl değer**. 9155 × 4,1868 / 3600 = 10,647 kWh/Sm3 eder, bu da BOTAŞ'ın 10,64 katsayısıyla uyumludur.
* Buna göre: TL/MWh = TL/Sm3 × 1000 / 10,64 ≈ TL/Sm3 × 93,98.
* Dosyada TL/MWh birimiyle verilmiş bir kaynak yok; bu birime dönüştürme yapılmadı.

**Dolar bazlı dönem (2018-08 – 2018-10):**
* BOTAŞ, 1 Ağustos 2018'den itibaren elektrik üretim amaçlı gazı **270 USD/1000 Sm3** olarak belirledi ve "güncel kur üzerinden TL olarak faturalandırılacağını" duyurdu. Kaynaklar: Hürriyet, Dünya, Kojentürk, MMO.
* Santrallere gönderilen yazıda dönüşüm kuru 4,86 TL/USD idi; bu kurla fiyat 1.312,2 TL/1000 m3 = 1,3122 TL/Sm3 eder (Petroturk, Bloomberg HT).
* CSV'ye TL değeri yazıldı. 2018-08 … 2018-10 döneminde fiili faturanın kurla dalgalanmış olabileceği bir belirsizliktir (bkz. §5).

## 4. Fiyat değişim noktaları (normalize TL/1000 Sm3, CSV'deki değerlerden)

| Yürürlük | TL/1000 Sm3 | Not |
|---|---|---|
| 2016-01 … 2016-09 | (boş) | Dolaylı tahmin ≈782, bkz. §5-1 |
| 2016-10 (yaklaşık) | 704 | Başlangıç tarihi çıkarım |
| 2017-12-01 | 763 | +%8,4. Ayrıca hacim kademeli ek ücret, bkz. §5-3 |
| 2018-01-01 | 800 | +%4,8 |
| 2018-04-01 | 877,6 | +%9,7 |
| 2018-08-01 | 1.312,2 | +%49,5; 270 USD/1000 Sm3 |
| 2018-09-01 | 1.700,6 | Hesaplanmış: +%29,6 (MMO) |
| 2018-11-01 | 1.550 | −%8,8 |
| 2019-01-01 | 1.485 | F1. Ayrıca F2 = 1.700, bkz. §5-5 |
| 2019-04/05 | (boş) | |
| 2019-06 | 1.550 | |
| 2019-07-01 | 1.650 | |
| 2019-09-01 | 1.600 | |
| 2020-07-01 | 1.400 | −%12,5 |
| 2021-01-01 | 1.414 | |
| 2021-02-01 | 1.428 | |
| 2021-03-01 | 1.442 | |
| 2021-04-01 | 1.456 | |
| 2021-05-01 | 1.631,667 | +%12 |
| 2021-06-01 | 1.713,25 | +%5 |
| 2021-07-01 | 2.060 | +%20,2 |
| 2021-09-01 | 2.369 | +%14,99 |
| 2021-10-01 | 2.724,35 | +%15 |
| 2021-11-01 | 4.000 | +%46,8 |
| 2021-12-01 | 4.800 | +%20 |
| 2022-01-01 | 5.520 | +%15 |
| 2022-02-01 | 6.300 | +%14 |
| 2022-03-01 | 7.450 | +%18,25 |
| 2022-04-01 | 10.750 | |
| 2022-06-01 | 12.500 | |
| 2022-08-01 | 13.750 | +%10 |
| 2022-09-01 | 20.625 | +%50, hesaplanmış. BOTAŞ "ortalama %49,5" dedi |
| 2023-01-01 | 18.000 | −%12,73 |
| 2023-02-01 | 15.000 | |
| 2023-03-01 | 12.000 | |
| 2023-04-01 | 10.000 | −%16,67 |
| 2023-10-01 | 12.000 | +%20 |
| 2025-04-05 | 15.000 | |
| 2026-04-04 | 18.000 | +%20 |

## 5. Belirsizlikler ve tutarsızlıklar

1. **2016-01 … 2016-09 boş.** Bu dönemin tarifesini doğrudan gösteren bir belge bulunamadı. Eski BOTAŞ sitesi kapanmış; EPDK yıllık sektör raporları WebFetch ile okunamadı (ikili dosya); Wayback erişimi engelli.
   * **Dolaylı tahmin:** yaklaşık 782 TL/1000 m3. CSV'ye **yazılmadı**.
   * Dayanaklar:
     * İbrahim Kahveci (Karar, 05.09.2019) "2015-16 ortalama elektrik santrallerine satış fiyatı 0,782 liradan 0,763 liraya" der. Bu ifade 2015 ortalaması 0,782 ve 2016 ortalaması 0,763 olarak okunabilir.
     * 9 ay × 782 + 3 ay × 704 = 2016 ortalaması 762,7 eder ve Kahveci'nin 0,763'üyle örtüşür.
     * Ekim 2016'daki "yaklaşık %10 indirim" (Kojentürk) ile de uyumludur: 704 / 0,9 = 782,2.
   * Aynı yazıda sanayi rakamları elektrikle birebir aynı verilmiş; olası bir kopyalama hatası olabilir.
   * Bu tahmin **teyitsizdir**; 2016 tabanı olarak kullanılacaksa dikkat edilmeli.

2. **704 TL/1000 m3'ün başlangıç tarihi (2016-10) çıkarımdır.**
   * Doğrudan bilinen: 1 Aralık 2017 zammından önceki fiyat 704'tü (AA, Hürriyet, Petroturk).
   * "Ekim 2016'da yaklaşık %10 indirim" bilgisi Kojentürk'te geçiyor. Petroturk aynı ifadeyi **konut** için kullanıyor ve bir sektör kaynağının "2016 Ekim'inden beri sübvansiyon var" dediğini aktarıyor.
   * Destekleyici hesap: Kahveci'nin "2017 ortalamasına göre %132,7 zam" ifadesiyle 1,65 TL fiyatından geriye gidildiğinde 2017 ortalaması 0,709 bulunur. Bu, 11 ay × 704 + 1 ay × 763 = 708,9 ile uyumludur ve 704'ün Ocak–Kasım 2017 boyunca geçerli olduğunu destekler.
   * 2016-10 … 2017-10 ayları taşınmış değerdir.

3. **Aralık 2017 – Mart 2018 kademeli fiyat.**
   * AA/Hürriyet (05.12.2017): BOTAŞ, özel santrallerin çekişini tüketimlerinin yarısıyla sınırladı.
   * Önerilen ek ücretler: tüketimin %50–70'i için %20, %70–100'ü için %25.
   * CSV'deki 763 ve 800 **baz fiyattır**. Kota üstü fiili ortalama maliyet daha yüksek olabilir.
   * 800 değeri yalnız Petroturk'te var ("özel sektör santralleri"). Ancak 877,6 / 1,097 = 800 ile tutarlıdır.

4. **2018-09 ve 2018-10 = 1.700,6 hesaplanmıştır.**
   * MMO (04.09.2018) Tablo 3'e göre "Serbest Tüketici Elektrik" satırında 1 Eylül 2018'de %29,6 artış var. 1.312,2 × 1,296 = 1.700,6.
   * Bu artış, 270 USD sabit kalırken kurun 4,86'dan yaklaşık 6,30'a çıkmasının TL'ye yansıması olarak da okunabilir: 270 × 6,30 ≈ 1.700.
   * Ekim 2018: Dünya, Kasım 2018'deki 1.550'yi "%8,8 indirim" olarak verdi. Geriye hesapla önceki değer ≈1.699,6 çıkar; bu da Ekim'de değişiklik olmadığını destekliyor. Ekim için doğrudan kaynak yok.

5. **2019 Ocak–Mart: F1/F2 iki fiyatlı rejim** (Petroturk, 13.12.2018).
   * F1 = 1,485 TL/Sm3: sözleşme miktarına ya da BOTAŞ'tan alınan miktarın %70'ine kadar.
   * F2 = 1,700 TL/Sm3: bunun üstündeki çekişler.
   * CSV'ye **F1** yazıldı.
   * Petroturk, 70/30 dağılımla ağırlıklı ortalamanın Aralık 2018'e (1,55) eşit olduğunu söylüyor.
   * ELDER Ocak 2019 bülteni "santrallere %4 indirim" diyor; bu F1'deki −%4,2 ile uyumlu.

6. **2019-04 ve 2019-05 boş.**
   * Bu aylarda F1/F2 rejiminin sürüp sürmediği ya da tek fiyata (1,55) geçilip geçilmediği bulunamadı.
   * BOTAŞ'ın aylık PDF arşivi Haziran 2019'dan başlıyor.
   * Haziran 2019 = 1,55 (PDF).

7. **Çeyreklik fiyatlama ve taşınan aylar (2019–2020).**
   * 2019–2020'de santral fiyatı çeyreklik belirleniyordu. TSKB Aralık 2019 bülteni: "2020 yılı ilk çeyreğinde … 1,6 TL/Sm3 olarak devam".
   * 2019-10/11: Eylül 2019 = 1,60 (PDF) ile Aralık 2019 "değiştirmedi" (TSKB) arasından taşındı.
   * 2020-04/05: Q1 2020 = 1,60 ve Haziran 2020 = 1,60 (Enerji Günlüğü; ayrıca Temmuz'daki %12,5 indirimin geriye hesabı) arasından taşındı.
   * 2020-11: Ekim ve Aralık PDF'leri 1,40.

8. **Aralık 2021 çelişkisi.**
   * Petroturk (03.12.2021): "%20 artışla 4,200000 TL/Sm3". Bu tutarsız.
   * Kasım 2021 = 4.000 (AA; Enerji Günlüğü %46,8; 2,72435 × 1,4682 = 4,000).
   * 4.000 × 1,2 = **4.800**. Bunu NTV (03.12.2021) açıkça veriyor; Sondakika %20'yi teyit ediyor.
   * Ocak 2022'nin 5.520 (= 4.800 × 1,15) olması da 4.800'ü doğruluyor. CSV'de 4.800 kullanıldı.
   * Ayrıca Aralık 2021'de dağıtım şirketi ve OSB bazında kota üstü tüketime +%50 uygulaması vardı. Bu, elektrik dışı Kademe‑2 fiyatına bağlıydı (BOTAŞ fiyat detayı); CSV'ye yansıtılmadı.

9. **Eylül 2022 = 20,625 hesaplanmıştır.**
   * 13,75 × 1,5 = 20,625. BOTAŞ "ortalama %49,5" dedi; Euronews "Eylül 2022'de 20,63 lira" diye yuvarlıyor.
   * Ekim 2022 PDF'i 20,625000'i doğrudan gösteriyor. Eylül için BOTAŞ PDF'i veya BOSB sayfası açılamadı (BOSB'deki tahmini sayfa numarası 404 döndü).

10. **Nisan 2026 artış oranı tutarsızlığı.**
    * T24 (03.04.2026) santraller için "%19,42 artış" yazdı.
    * BOSB (07.04.2026) "%20 artış (18,000000 TL/Sm3)" diyor; 15 → 18 = +%20.
    * BOTAŞ'ın 4 Nisan 2026 tarife sayfası 18,000000 TL/Sm3 gösteriyor. CSV'de 18 kullanıldı.

11. **2026 Haziran–Eylül tarife referansları.**
    * BOSB duyuruları bu aylarda "1 Haziran 2026 / 1 Ağustos 2026 / 1 Eylül 2026 tarihinden itibaren geçerli BOTAŞ tarifesi"ne atıf yapıyor.
    * BOTAŞ'ın "Satış Fiyat Tarifesi" sayfası ise 23.10.2026 itibarıyla yalnız 4 Nisan 2026 tarifesini listeliyor.
    * Her iki durumda da elektrik üretim fiyatı 18,000000 TL/Sm3 ("artış yapılmamıştır"); değere etkisi yok.

12. **Temmuz 2025 tarifesi** (2 Temmuz 2025) elektrik üretim fiyatını değiştirmedi; 5 Nisan 2025'ten beri 15,00. Bu, 2026-02'ye kadarki BOSB duyurularında açıkça yazıyor.

13. **Diğer taşınan aylar ve dayanakları:**

| Ay(lar) | Taşınan değer | Dayanak |
|---|---|---|
| 2018-02/03 | 800 | 1 Ocak'tan 1 Nisan'a kadar başka değişiklik yok (Petroturk kronolojisi) |
| 2018-05/06 | 877,6 | Petroturk: 1 Temmuz 2018'de değişiklik yok; Ağustos'taki zammın baz fiyatı 877,6 (Bloomberg HT) |
| 2021-08 | 2.060 | Eylül'deki +%14,99'un geriye hesabı = 2,060 |
| 2023-05 | 10.000 | Nisan PDF'i 10,00; Haziran (Takvim) 10.000, "değişiklik yok" |
| 2024-02/03 | 12.000 | Ocak 12.000 ve Nisan 12.000 "değişmedi" |
| 2025-05 | 15,00 | BOSB Haziran 2025: "herhangi bir değişiklik yapılmamıştır" |
| 2025-08 | 15,00 | BOSB Eylül 2025 hâlâ 2 Temmuz 2025 tarifesine atıf yapıyor |
| 2025-10/11/12 | 15,00 | BOSB Ocak 2026 hâlâ 2 Temmuz 2025 tarifesine atıf yapıyor |
| 2026-03 | 15,00 | BOSB Nisan 2026: %20 artışla 18'e (yani önceki 15) |
| 2026-05 | 18,00 | BOSB Haziran 2026: "artış yapılmamıştır" |

## 6. İki bağımsız kaynakla teyit edilen aylar (27)

| Ay | Kaynaklar |
|---|---|
| 2017-11 | 704 — AA + Hürriyet + Petroturk (Aralık 2017 zammından önceki fiyat olarak) |
| 2017-12 | 763 — AA + Hürriyet + Petroturk |
| 2018-04 | 877,6 — Petroturk (1 Nisan'da belirlendi) + Bloomberg HT/Bigpara (Ağustos öncesi fiyat) |
| 2018-07 | 877,6 — Bloomberg HT + Petroturk |
| 2018-08 | 1.312,2 — Bloomberg HT + Bigpara + Petroturk; 270 USD: Hürriyet + Dünya + Kojentürk + MMO |
| 2018-11 | 1.550 — Dünya + Petroturk |
| 2019-07 | 1,65 — BOTAŞ PDF + sol.org.tr (+%6,5) |
| 2019-08 | 1,65 — BOTAŞ PDF + Karar/Kahveci |
| 2020-01 | 1,60 — BOTAŞ PDF + TSKB |
| 2020-07 | 1,40 — BOTAŞ PDF + Hürriyet + Sözcü |
| 2020-10 | 1,40 — BOTAŞ PDF + AA |
| 2021-03 | 1.442 — Enerji Günlüğü + Euronews ("1,44") |
| 2021-09 | 2,369 — Anka + Euronews ("2,37") |
| 2021-10 | 2,72435 — Yatırımlar + Enerji Günlüğü ("2.724") |
| 2021-11 | 4.000 — AA + Enerji Günlüğü (+ Sondakika %46,82) |
| 2021-12 | 4.800 — NTV + Sondakika (%20) |
| 2022-02 | 6,30 — BOTAŞ PDF + Turkishtime ("6 bin 300") |
| 2022-03 | 7,45 — BOTAŞ PDF + Cumhuriyet |
| 2022-05 | 10,75 — BOTAŞ PDF + NTV |
| 2022-08 | 13,75 — BOSB + T24 + Cumhuriyet |
| 2022-09 | 20,625 — Euronews (20,63) + Petroturk (BOTAŞ %49,5) |
| 2022-10 | 20,625 — BOTAŞ PDF + TSKB bülteni |
| 2023-04 | 10,00 — BOTAŞ PDF + Birgün |
| 2024-06 | 12.000 — AA + Enerji Günlüğü |
| 2025-02 | 12.000 — AA + Lider Gazete |
| 2025-03 | 12,00 — BOTAŞ PDF + AA |
| 2026-04 | 18,00 — BOTAŞ tarife sayfası + BOSB |

Ayrıca yüzde zincirleri bütün dönemde iç tutarlılık sağlıyor:
* 2021-05 × 1,05 = 2021-06
* 2021-06 × 1,202 ≈ 2021-07
* 2023-01 = 20.625 × (1 − 0,1273)
* 2023-03 → 2023-04: −%16,67

## 7. Kaynak türleri

* **BOTAŞ aylık tarife PDF'leri** (`botas.gov.tr/uploads/dosyaYoneticisi/...`). Okunanlar: 2019 Haziran, Temmuz, Ağustos, Eylül; 2020 Ocak, Temmuz, Ağustos, Ekim, Aralık; 2022 Şubat, Mart, Nisan, Mayıs, Temmuz, Ekim, Kasım, Aralık; 2023 Şubat, Mart, Nisan; 2024 Mayıs; 2025 1 Mart, 5 Nisan, 2 Temmuz; 2026 4 Nisan (HTML sayfası).
  * 2019-08 PDF'inin bir kopyası (423192) boş tablo döndü; 823001 kopyası okundu.
  * BOTAŞ'ın güncel sitesinde 2019 öncesine ait tarife PDF'i bulunamadı.
* **BOSB** (Bursa OSB) aylık "doğal gaz tüketimleri için fiyat tarife uygulaması" duyuruları, 2022–2026.
* **Haberler:** AA (ve AA Enerji Terminali), Bloomberg HT, Dünya, Hürriyet/Bigpara, NTV, Cumhuriyet, T24, Petroturk, Enerji Günlüğü, Anka, Euronews, Yatırımlar, Capital, Takvim, Turkishtime, Sondakika.
* **Raporlar ve kurum yayınları:** MMO Enerji Çalışma Grubu (2018), Kojentürk (2018), ELDER bülteni (Ocak 2019), TSKB Enerji Bülteni (Aralık 2019, Eylül 2022), Karar/İbrahim Kahveci (05.09.2019).
* **Okunamayanlar:**
  * EPDK Doğal Gaz Piyasası yıllık sektör raporları (2016, 2017): ikili dosya, WebFetch metin çıkaramadı.
  * BOTAŞ sektör ve faaliyet raporları (2016, 2017, 2018): fiyat tablosu içermiyor.
  * Eski TSKB bültenleri (2019 Mart–Mayıs): görüntü PDF.
  * Wayback Machine: erişim engelli.
