# Araştırma planı ve test kaydı

Bu dosya her testi **sonucu görmeden önce** kaydeder. Kurallar sonradan değiştirilmez;
değişirse yeni test numarası alır. Böylece kaç deneme yaptığımızı sayabilir ve tesadüfi
"başarıları" ayıklayabiliriz.

Son güncelleme: 2026-10-21

## İş bölümü

| Kim | Ne yapar |
|---|---|
| Kullanıcı | Tek komut: `python hepsi.py` (veri toplama; günlük işleri otomatiğe bağlar) |
| Google Earth Engine | Uydu hesapları sunucuda (kar, göl alanı, maden alanı, sıcak piksel); bilgisayara yalnızca sayılar iner |
| Araştırma ajanları | Koordinatlar, geçmiş üretim tabloları, piyasa/veri erişimi (`arastirma/` klasörü) |
| Claude | Analizler (önceden kayıtlı testler), rapor |

## İş akışları (öncelik sırasıyla)

1. **Kar → bahar hidrosu → PTF ve hidro sepeti** (ERA5-Land kar suyu eşdeğeri, MODIS kar örtüsü)
2. **TRALT maden sahaları** (Sentinel-2 çıplak toprak / liç alanı değişimi)
3. **Fırat barajlarının su stoku** (Keban, Karakaya, Atatürk; Sentinel-2 göl alanı, uygunsa altimetri)
4. **Çelik tesislerinin sıcak piksel endeksi** (Sentinel-2 B11/B12; İsdemir, Erdemir, Kardemir)
5. **Fındık bölgesi don endeksi** (ERA5-Land saatlik sıcaklık; düşük öncelik)
6. **Altyapı**: EPİAŞ baraj durumunun günlük arşivi; her hafta sinyallerin fiyat görülmeden kaydı

## Genel kurallar

- Her fikir önce **mükemmel bilgi** testinden geçer; geçemezse uydu verisi toplanmaz.
- Kıyas her zaman "zaten kamuya açık olan bilgi"dir (son açıklanan veri, EPİAŞ'ın mevcut verisi).
- Anlamlılık eşiği, yapılan toplam test sayısına göre sıkılaştırılır (aşağıdaki sayaç).
- İşlem maliyeti pozisyon değişimi başına %0,2.
- Bugünden sonraki sinyaller fiyat görülmeden kaydedilir; gerçek değerlendirme ileriye dönük yapılır.

## Test sayacı

Önceki testler (rapordaki): NO₂ 4 (+1 ilk deneme), haftalık hidro 12, mevsimlik 9 → **~26 test**.
Bu kadar testten sonra tek bir %95 sonucu tesadüf olabilir; yeni bulgular için hedef p < 0,005
(ya da ileriye dönük doğrulama).

## Kayıtlı testler

### T-A1 — Kar fikri için mükemmel bilgi kapısı (kayıt: 2026-10-21, sonuç görülmeden)

Soru: 1 Mart'ta Mart–Temmuz barajlı hidro anomalisini kusursuz bilmek, Aralık–Şubat
anomalisinin (1 Mart'ta zaten kamuya açık) ötesinde bir şey katıyor mu?

- Yıllar: 2018–2026 (2017'nin Aralık 2016 verisi yok). n = 9.
- `kis` = Aralık(y−1)–Şubat(y) barajlı hidro anomalisi; `bahar_yaz` = Mart–Temmuz(y) anomalisi.
  Anomali = log(dönem toplamı / aynı dönemin diğer yıllardaki medyanı).
- Hedefler: (a) Mart–Temmuz ortalama PTF ($) yıllık log değişimi; (b) hidro sepetinin
  1 Mart–31 Temmuz BIST100'e göre log fazla getirisi.
- Ölçütler:
  1. `kis`, `bahar_yaz`ı ne kadar açıklıyor (r²)?
  2. `bahar_yaz`ın `kis`ten arındırılmış kısmının (artık) hedeflerle korelasyonu.
- **Karar kuralı:** Kar verisi toplanır (T-A2'ye geçilir) eğer
  (i) r²(`kis` → `bahar_yaz`) < 0,70 (karın katabileceği bir pay varsa) **ve**
  (ii) artık ile PTF değişimi korelasyonu ≤ −0,30 **veya** artık ile sepet getirisi korelasyonu ≥ +0,30.
  n = 9 olduğu için bu bir kapıdır, kanıt değildir.

**Sonuç (2026-10-21): GEÇTİ, kıl payı.**
- r²(kış → bahar-yaz) = 0,42 → Mart–Temmuz hidrosunun %58'i kış verisinden tahmin edilemiyor; karın katabileceği pay var.
- Artık ~ PTF yıllık: r = −0,26 (eşik −0,30, geçmedi). Artık ~ sepet: r = +0,34 (eşik +0,30, geçti).
- Uyarı: n = 9 ve sonucu büyük ölçüde 2026 taşıyor (artık +0,45, PTF −0,71). Bu bir kapı; kanıt değil.

### T-A2 — Kar verisinin gerçek testi (kayıt: 2026-10-21, kar verisi henüz yok)

Soru: 1 Mart'ta uydu/yeniden analiz kar verisi, kış hidrosunun söylediğinin ötesinde
Mart–Temmuz hidrosunu öngörüyor mu?

- Veri: `cikti/gee_kar_aylik.csv` (ERA5-Land, 2001–).
- `kar` sinyali (tek ve önceden sabit): beş havzanın (Fırat-Karasu, Fırat-Murat, Dicle üst,
  Çoruh, Seyhan-Ceyhan) **Şubat ortalama kar suyu eşdeğeri**nin eşit ağırlıklı ortalaması;
  log(değer / 2001'den bir önceki yıla kadarki Şubat medyanı). Yalnızca geçmişi kullanır.
- MODIS kar örtüsü ve kış yağışı yalnızca ikincil olarak raporlanır; karar vermez.
- Yıllar 2018–2026, `kis` ve `bahar_yaz` T-A1'deki gibi.
- **Karar kuralı:** GEÇER eğer
  (i) kısmi korelasyon r(`kar`, `bahar_yaz` | `kis`) ≥ +0,50 **ve**
  (ii) `kar`ın `kis`ten arındırılmış kısmı ile sepet fazla getirisi korelasyonu ≥ +0,30
  (T-A1'de yalnızca sepet tarafı geçtiği için PTF burada yalnızca raporlanır).
- n = 9 ile p < 0,005 mümkün değil. GEÇERSE sonuç "kanıt" değil, **ileriye dönük deneme**
  için izindir: 1 Mart 2027 sinyali fiyatlar görülmeden bu dosyaya yazılır, 31 Temmuz 2027'de
  değerlendirilir.

**Sonuç (2026-10-21): KALDI.** (`python kar_testi.py`)
- (i) Fiziksel kısım güçlü biçimde geçti: kısmi r(kar, bahar_yaz | kis) = +0,75; ham r = +0,86.
  Herhangi bir yıl çıkarılınca +0,67 ile +0,82 arasında kalıyor. 1 Mart'taki kar, Mart–Temmuz
  barajlı hidro üretimini kış verisinin söylediğinden çok daha iyi öngörüyor.
- (ii) Piyasa kısmı kaldı: kar artığı ~ sepet r = +0,09 (eşik +0,30). PTF ile r = +0,14 (yanlış yön).
- İkincil: MODIS kar örtüsü artığı ~ sepet r = +0,66 çıktı, ama kayıtta karar vermeyen ikincil
  ölçüydü ve fiziksel kısmı zayıf (+0,30). Sonradan seçmek çoklu test hatası olur; **kullanılmıyor**.
- Yorum: kar bilgisi gerçek ve erken bir hidro tahmini veriyor, fakat 2018–2026'da hidro hisse
  sepetinin Mart–Temmuz getirisine yansımamış. Elektrik vadelisi işlem görmediği için (bkz.
  `arastirma/viop_elektrik.md`) bu bilgiyi doğrudan kullanacak bir araç da yok.
- Test sayacı: +1 karar testi (+2 ikincil rapor) → ~27.

### T-F1 — Fırat su stoku doğrulaması (kayıt: 2026-10-21, veri yok)

- Veri: `cikti/gee_firat_aylik.csv` (Keban+Karakaya+Atatürk toplam su alanı, aylık).
- Önce fiziksel doğrulama: kapsama ≥ %80 olan aylarda alanın aylık değişimi ile sonraki 3 ayın
  barajlı hidro anomalisi (EPİAŞ) arasındaki korelasyon, o ayın hidro anomalisinden arındırıldıktan
  sonra ≥ +0,30 olmalı. Geçmezse Fırat akışı piyasa testine gitmez.

**Sonuç (2026-10-22): KALDI.** (`python firat_testi.py`) Kısmi r = +0,08 (n = 107 ay; eşik +0,30).
Ek rapor: yalnız Keban+Karakaya+Atatürk üretimiyle +0,16. Uydu alan ölçümü temiz ve mevsimselliği
net gösteriyor, ama aylık alan değişimi sonraki 3 ayın üretimi hakkında, o ayın üretiminin
söylediğinden fazlasını söylemiyor.

### T-C1 — Çelik sıcak piksel doğrulaması (kayıt: 2026-10-21, uydu verisi yok; üretim tablosu var)

- Veri: `cikti/gee_celik_sahne.csv` (tesis düzeyi; birim konumları bilinmiyor) ve
  `arastirma/celik_uretim.csv` (çeyreklik sıvı çelik; Ereğli = Grup − İsdemir).
- Ölçü (tek ve önceden sabit): bulut oranı < %10 olan sahnelerde `sicak_yogunluk`un çeyrek
  ortalaması. Çeyrekte 3'ten az temiz sahne varsa o çeyrek dışarıda kalır.
- Tesisler: İsdemir ve Ereğli (2018Q1–2026Q2). Kardemir yalnızca yıllık rakamla raporlanır.
- **Karar kuralı:** GEÇER eğer hem İsdemir'de hem Ereğli'de çeyreklik ölçü ile üretim
  arasındaki korelasyon ≥ +0,50 **ve** İsdemir deprem duruşunda (2023-02-06 → 2023-04-24) temiz
  sahnelerin ortalaması 2022 ortalamasının %20'sinin altında.
- GEÇERSE T-C2 (piyasa testi) kaydedilir: çeyrek bittiği gün uydu tahmini, sunum çıkmadan
  önce; ölçüt EREGL'in sunum günü fazla getirisi.

Uygulama notu (veri görülmeden önce): Sentinel-2'nin QA60 bulut maskesi 2022-02 – 2024-01
arasında boş geliyor; bulut oranı bu yüzden Google Cloud Score+ (cs < 0,6) ile ölçüldü.

**Sonuç (2026-10-22): KALDI.** (`python celik_testi.py`)
- Korelasyon: İsdemir r = +0,09, Ereğli r = +0,07 (n = 34 çeyrek; eşik +0,50).
- Deprem kontrolü: duruş döneminde ölçü 2022 ortalamasının %79'u (eşik < %20). Yani ölçü sıcak
  metali yakalamıyor; yazın yükselmesi parlak yüzeylerin (çatı, cüruf, toprak) eşiği geçtiğini
  gösteriyor. Bu bir **yöntem** başarısızlığı; fikrin kendisi test edilmiş sayılmaz. Farklı bir
  ölçü (ör. daha sıkı eşik, gece termal/VIIRS ateş verisi) denenirse yeni test numarası alır.

### T-M1 — TRALT açık ocak / yığın liçi doğrulaması (kayıt: 2026-10-21, uydu verisi yok; üretim tablosu var)

Bağlam: TRALT üretiminin çoğu Ovacık yeraltı madeninden geliyor (uydudan görünmez). Uydu
yalnızca açık ocak ve liç sahalarını görebilir: Himmetdede, Kaymaz, yeni açılan Mollakara.
Himmetdede ve Kaymaz üretimi 2021'den beri sürekli düşüyor; düzeyler arasındaki korelasyon
bu ortak eğilim yüzünden yanıltıcı olur, bu yüzden **değişimler** kullanılır.

- Veri: `cikti/gee_maden_aylik.csv` (kapsama ≥ 0,6 olan aylar), `arastirma/tralt_uretim.csv`.
- Ölçü: çeyrekteki aylık `ciplak_km2` ortalamasının bir önceki çeyreğe göre değişimi.
- Hedef: aynı sahanın döküm üretiminin (oz) bir sonraki çeyrekteki değişimi
  (Himmetdede → `himmetdede_lic_oz`, Kaymaz → `kaymaz_tesis_oz`).
- 4. çeyrekler hariç (raporlarda sistematik ve açıklanmamış düşük döküm; uydu bakılmadan kararlaştırıldı).
- Dönem 2021Q1–2026Q1, iki saha birlikte (n ≈ 30).
- **Karar kuralı:** Spearman korelasyonu ≥ +0,40 → GEÇER. Kontrol: Mastra 2024-04-30'da kapandı;
  sonrasında çıplak alan değişimi raporlanır (büyüme görülürse ölçü güvenilmez sayılır).
- GEÇSE de GEÇMESE de: Mollakara (açılış 2026) ileriye dönük izlenir; liç pedinin büyümesi
  aylık kaydedilir, şirket açıklamalarıyla karşılaştırılır.

**Sonuç (2026-10-22): KALDI.** (`python maden_testi.py`) Spearman = +0,20 (n = 20; eşik +0,40);
Himmetdede +0,15, Kaymaz +0,13. Mastra kontrolü temiz (kapanıştan sonra alan sabit: 1,19 → 1,16 km²).
Mollakara noktası 3 km yarıçaplı geniş bir alanı ölçüyor; kışın kar, yazın doğal çıplak bozkır
baskın. İleriye dönük izleme için sahanın gerçek sınırı gerekli.

## Durum özeti (2026-10-22)

Test sayacı ~30. Yeni kayıtlı testlerin hiçbiri karar ölçütünü geçmedi. Geçen tek şey fiziksel
bilgi: barajlarda alan ölçümü (Ömerli r = 0,90) ve kar → bahar hidrosu (kısmi r = 0,75).
İkisi de bugün işlem yapılabilen bir fiyata bağlanamadı.


İlk adım ikisinde de **doğrulama**: uydu ölçüsünün şirketin açıkladığı üretimle (çeyrek/yıl)
ilişkisi. Doğrulama kuralları üretim tabloları gelince, uydu verisine bakılmadan yazılır.

### T-L1 / T-L2 — Sululuk bilgisi daha likit hisselerde işe yarar mı? (kayıt: 2026-10-22, fiyat verisi henüz inmedi)

Mantık: sulu çeyreklerde PTF düşüyor (r = −0,47, sağlam). Bu, elektriği **maliyet** olarak
kullananlara iyi, hidroyla **rekabet eden** termik santrallere kötü olmalı. Hisseler veriye
bakılmadan, yalnızca bu mantıkla seçildi:

- **G1 – elektrik tüketicisi (beklenen yön: hidro ↑ → fazla getiri ↑):** IZMDC (İzmir Demir Çelik,
  ark ocağı), CEMTS (Çemtaş, ark ocağı). Kocaer çelik eritmediği (kütük alıyor) için alınmadı;
  EREGL/ISDMR/KRDMD entegre (yüksek fırın, kendi gazlarından elektrik) olduğu için alınmadı.
- **G2 – termik üretici (beklenen yön: hidro ↑ → fazla getiri ↓):** ODAS (Çan-2 linyit), CANTE
  (Çan-2), AKSEN (gaz + linyit; yurtdışı payı büyüyor), IZENR (ithal kömür; 2024'te halka açıldı).
- Her çeyrek, çeyrek başında işlem gören hisselerin eşit ağırlıklı BIST100'e göre log fazla getirisi.
- Likidite ön şartı: son 1 yılda günlük medyan işlem hacmi < 10 milyon TL olan hisse gruptan çıkarılır
  (sonuca bakmadan, yalnızca hacme göre).
- Sinyal: çeyreğin barajlı hidro anomalisi (mevsimlik testteki tanım), **mükemmel bilgi**.
- Dönem: 2017Ç1–2026Ç3.
- **Kapı (her grup ayrı):** (i) korelasyon beklenen yönde ve |r| ≥ 0,30; (ii) strateji ("lehte
  çeyrekte grubu tut, değilse BIST100"; değişim başına %0,2 maliyet) sinyalin zamanda kaydırılmış
  kopyalarının ≥ %95'ini geçer. Kapıyı geçen grup için gerçekçi sinyal (önceki çeyreğin hidrosu ve
  kar) ayrıca kaydedilip test edilir; o aşamada eşik p < 0,005 ya da ileriye dönük kayıt.
- Yalnız rapor (karar vermez): aynı testin PTF yıllık değişimiyle (mükemmel bilgi) sürümü.
- Test sayacı: +2.

**Sonuç (2026-10-22): ikisi de KALDI.** (`python likit_test.py`; 38 çeyrek, tüm hisseler likidite şartını geçti)
- G1 tüketici (IZMDC, CEMTS): r = +0,07; strateji %−5, kaydırılmış kopyaların %51'i.
- G2 termik (ODAS, CANTE, AKSEN, IZENR): r = +0,08 (beklenenin tersi yönde); strateji %−49, %35'i.
- Yalnız rapor: PTF yıllık değişimiyle G2 r = +0,27 (beklenen yönde ama eşik altı), G1 r = +0,09.
- Yorum: hidroyu kusursuz bilmek bile bu hisselerde işe yaramıyor. Hidro → elektrik fiyatı
  bağı güçlü, ama elektrik fiyatı → hisse bağı çeyrek ölçeğinde zayıf (enflasyon, faiz, kur ve
  ikili anlaşmalar baskın). Hidro/elektrik hattı bireysel yatırımcı için kapatıldı.
- Test sayacı: ~32.

### T-G1 — Bahar donu → meyve fiyatları (kayıt: 2026-10-22 21:20, TÜFE ve hava verisi henüz inmedi)

Mantık: çiçeklenme döneminde don, yerli meyve arzını düşürür; hasat sezonunda ve sonrasındaki
depolama döneminde meyve fiyatı genel fiyatlara göre yükselir. Önce bu **fiziksel/ekonomik halka**
sınanır; geçerse beklenti anketine göre sürpriz ve piyasa (faiz, endeksli tahvil) aşamasına geçilir.

- Don endeksi (yıl y): Open-Meteo arşivi (ERA5) günlük en düşük sıcaklık; 15 Mart–10 Mayıs arası
  Σ max(0, −Tmin) [°C·gün]; 9 meyve noktasının eşit ağırlıklı ortalaması: Malatya (38.35, 38.31),
  Eğirdir (37.87, 30.85), Niğde (37.97, 34.68), Karaman (37.18, 33.22), Amasya (40.65, 35.83),
  Bursa (40.19, 29.06), Manisa (38.61, 27.43), Kemalpaşa (38.43, 27.42), Akşehir (38.36, 31.41).
  Noktalar veri görülmeden, üretim bölgesi bilgisine göre seçildi.
- Bağımlı (yıl y): TÜİK TÜFE (EVDS) "meyve" alt endeksinin genel TÜFE'ye göre göreli değişimi,
  Mayıs(y) → Mayıs(y+1): R_y = Δlog(meyve) − Δlog(genel TÜFE). Yıllar 2004–2025 (n ≈ 22).
- Ana ölçü: Pearson r( log(1 + don_y), R_y ).
- **Kapı:** r ≥ +0,45 **ve** herhangi bir yıl çıkarıldığında en düşük r ≥ +0,25.
- Uyarı: 2014 ve 2025 donlarını ve o yıllardaki meyve pahalılığını önceden biliyoruz; bir-yıl-çıkar
  kontrolü bu yüzden kapının parçası.
- Yalnız rapor (karar vermez): (a) aylık gecikme profili (don yılında Haziran→ertesi Mayıs aylık
  göreli meyve enflasyonu); (b) kuraklık: Ekim(y−1)–Mayıs(y) yağış anomalisi (Konya 37.87/32.48,
  Polatlı 39.58/32.15, Şanlıurfa 37.16/38.79, Edirne 41.68/26.56) → "ekmek ve tahıllar" göreli
  değişimi aynı pencerede (beklenen r < 0); (c) sebze için T-G1'in aynısı.
- Test sayacı: +1 (+3 rapor) → ~33.

**Sonuç (2026-10-22): KALDI.** (`python gida_testi.py`; veri: EVDS TP.TUKFIY2025.* (2025=100, 2005'ten),
Open-Meteo ERA5-Land; ham veri `cikti/gida/`)
- Not: 2025=100 serisi 2005'te başlıyor → yıllar 2005–2025, n = 21 (kayıtta ~22 yazıyordu).
- Ana: r(log(1+don), meyve göreli) = **−0,36** (beklenenin tersi); bir-yıl-çıkar en düşük −0,52.
- Rapor: taze çekirdekli meyve (01163) −0,26; sebze −0,25; kuraklık → tahıl r = +0,07 (beklenen < 0).
- Rapor (a): en donlu 4 yılda (2022, 2009, 2025, 2021) göreli meyve fiyatı Nisan'da +3,9, Haziran–Temmuz'da
  +1,5/+1,9 puan daha yüksek, sonra geri dönüyor.
- Yorum: (1) Tasarım hatası: fiyat tepkisi Nisan–Mayıs'ta başlıyor (ör. 2025 Mart→Mayıs meyve +%25,
  genel +%4,6); Mayıs bazlı pencere tepkinin bir kısmını tabana koyuyor ve ardından gelen geri dönüşü ölçüyor.
  (2) Ölçüm sorunu: ERA5-Land noktaları bilinen don yıllarını iyi ayırmıyor (2014 endeksi ortalamanın
  altında; 2025 Malatya'da orta düzey); vadi tabanı donlarını ~9 km'lik ızgara yumuşatıyor olabilir.
  Pencereyi şimdi değiştirmek sonucu gördükten sonra seçmek olur; yeni bir sürüm yeni numara alır ve
  yalnız ileriye dönük (2027 baharı) ya da önce don → üretim (TÜİK bitkisel üretim) halkasıyla sınanır.
- Test sayacı: ~33.

### T-G2 — Bahar donu → meyve üretimi (kayıt: 2026-10-22 21:25, üretim verisi henüz inmedi)

Amaç: T-G1'in kalmasının nedeni ölçüm mü? Önce zincirin ilk halkası: don endeksi, yıllık meyve
üretimindeki düşüşü yakalıyor mu?
- Don endeksi: T-G1'deki ile birebir aynı (9 nokta, 15 Mart–10 Mayıs, log(1 + ortalama)).
- Üretim: Türkiye yıllık kayısı, elma, kiraz üretimi (ton; TÜİK, yoksa FAOSTAT). Her ürün için
  anomali_y = log(üretim_y) − önceki 3 yılın log üretim ortalaması; üç ürünün eşit ağırlıklı ortalaması.
  Yıllar 2004–2025 (verinin izin verdiği kadar).
- **Kapı:** r(don, üretim anomalisi) ≤ −0,45 **ve** bir-yıl-çıkar en yüksek r ≤ −0,25.
- Yalnız rapor: her ürün ayrı; kayısı ~ yalnız Malatya noktası.
- Kapı geçerse: ölçüm yeterli → T-G1'in fiyat testi Şubat bazlı yeni kayıtla yalnız ileriye dönük
  (2027 baharı). Kalırsa: ERA5-Land noktaları bu iş için yetersiz; istasyon/1 km yüzey sıcaklığı gerekir.
- Test sayacı: +1 → ~34.

**Sonuç (2026-10-22): KALDI.** (`python gida_uretim_testi.py`; TÜİK veri portalı taş/yumuşak çekirdekli
meyve tabloları 1988–2025 → `cikti/gida/tuik_meyve_uretim.csv`)
- Ana: r = −0,15 (eşik ≤ −0,45); bir-yıl-çıkar en yüksek +0,06. Kayısı −0,08, elma −0,12, kiraz −0,24;
  kayısı ~ yalnız Malatya −0,13.
- Üretimdeki büyük şoklar net: 2014 kayısı −99 log puan; 2025 kayısı −102, elma −70, kiraz −120.
  Don endeksi ise 2022'yi en donlu yıl gösteriyor (üretim normal) ve 2014'ü ortalamanın altında.
- Yorum: Fiziksel şok gerçek ve büyük, ama ERA5-Land nokta endeksi onu ölçmüyor. Muhtemel neden zamanlama:
  zarar, çiçeklenmeden **sonraki** dondan geliyor (sıcak Mart → erken çiçek → Nisan donu: 2014, 2025);
  2022'de soğuk Mart'ta don çiçeklenmeden önce geldi. Fenoloji ayarlı bir endeks bu iki yılı yakalayacak
  şekilde şimdi kurulursa iki olaya uydurulmuş olur → yalnız ileriye dönük. Ayrıca büyük don zararı
  günler içinde haberlere yansıdığı için piyasaya karşı bilgi avantajı sınırlı.
- Test sayacı: ~34.

### T-N2 — Kıyas: günlük elektrik üretimi sanayi üretimini önceden söylüyor mu? (kayıt: 2026-10-22 21:35)

Amaç: Uydu tabanlı bir sanayi/çelik göstergesinin geçmesi gereken çıta. EPİAŞ toplam elektrik üretimi
herkese açık ve ay biter bitmez bilinir. no2_nowcast.py'deki örneklem dışı çerçeve aynen: M1 = SÜE yıllık
(takvim arındırılmış) ~ SÜE(t−2); M3 = M1 + elektrik üretimi aylık yıllık değişimi(t).
- Kapı: örneklem dışı RMSE iyileşmesi ≥ %10 (NO2'nin aynı dönemi 2023-04→2026-08 ve tüm dönem ayrı raporlanır;
  karar 2023-04→2026-08 dönemine göre, NO2 ile karşılaştırılabilir olsun diye).
- Test sayacı: +1 → ~35.

**Sonuç (2026-10-22): KALDI.** (`python elektrik_sue_testi.py`)
- 2023-04→2026-08 (n = 41): RMSE M1 3,87 → M3 7,76 (iyileşme −%101; M3 ayların %17'sinde daha iyi).
- Tüm dönem (n = 79): 11,08 → 8,64 (+%22) ama yalnız ayların %37'sinde daha iyi; kazanç 2020 COVID
  şokundan. Eşzamanlı r(elektrik, SÜE) = 0,72.
- Yorum: Sıradan dönemlerde son açıklanan SÜE'yi geçmek çok zor; elektrik (ve NO2) yalnız büyük şoklarda
  bilgi katıyor. Uydudan çelik üretimi ölçmek toplam sanayi tahmini için umut vermiyor.
- Test sayacı: ~35.

### T-C2 — Landsat termal: çelik tesisi faaliyeti → bilanço günü fiyat tepkisi (kayıt: 2026-10-22 21:50, uydu verisi henüz inmedi)

Fikir: çeyrek içindeki tesis faaliyeti, bilanço açıklanmadan önce satış hacmini; dolayısıyla kâr sürprizini
gösterir. Ürün–hurda/cevher fiyat farkı zaten herkese açık, eksik parça hacim.
- Uydu: Landsat 8+9 Collection 2 L2 yüzey sıcaklığı (ST_B10, K), 2013-04 → 2026-09, Earth Engine.
  Sahne başına: tesis kutusunda açık piksellerin 90. yüzdeliği − çevre halkasının (merkezden 2–5 km,
  bulut/su/kar hariç) medyanı = **ΔT**. Tesis kutusunun ≥ %90'ı açıksa sahne kullanılır.
- Tesisler (veri görülmeden): IZMDC Aliağa (OSM bina: 38.7384–38.7419 K, 26.9263–26.9321 D; Habaş 1,5 km
  doğuda, kutuya girmiyor), İsdemir Payas, Erdemir Ereğli, Kardemir Karabük (bbox'lar `arastirma/celik_tesisler.csv`).
- Çeyrek sinyali: çeyrekteki geçerli sahnelerin ΔT ortalaması (≥ 2 sahne); **sürpriz** = bu değer − geçen yılın
  aynı çeyreği (mevsim etkisini atmak için).
- **Kapı 1 (ölçüm, piyasa yok):** İsdemir ve Ereğli (türetilmiş) için çeyreklik ΔT'nin yıllık değişimi ~
  sıvı çelik üretiminin yıllık log değişimi (`arastirma/celik_uretim.csv`), havuzlanmış r ≥ +0,40. Ek kontrol:
  İsdemir 2023-02-07 → 2023-04-23 deprem duruşundaki sahnelerin ΔT medyanı, diğer sahnelerin 10. yüzdeliğinin altında.
- **Kapı 2 (piyasa; yalnız Kapı 1 geçerse karar verir, kalırsa yine rapor edilir):** olay = KAP finansal rapor
  bildirimi (Research `report_dates.csv`); getiri = bildirimden önceki son kapanıştan bildirimden sonraki 2. işlem
  günü kapanışına, BIST100'e göre fazla log getiri. Hisse–tesis: IZMDC→IZMDC, ISDMR→İsdemir, EREGL→İsdemir+Ereğli
  ortalaması, KRDMD→Kardemir. Havuzlanmış Spearman r(sürpriz, fazla getiri) ≥ +0,25 **ve** 4 hisseden en az 3'ünde
  işaret pozitif.
- Test sayacı: +2 → ~37.

**Sonuç (2026-10-22): KALDI (iki kapı da).** (`python celik_landsat.py` → `python celik_landsat_testi.py`)
- Veri: 4031 sahne; aynı gün komşu karelerden gelen tekrarlar tek sayıldı. Kod düzeltmesi (sonuçtan önce, kural
  amacı korunarak): "≥ %90 açık" paydası sabit görüntü sayımı yerine tesisin tam açık sahnedeki piksel sayısı
  oldu (eski payda kenar piksellerini fazla sayıyor, hiçbir sahne geçmiyordu). Geçerli sahne 245–362/tesis.
- Tesisler çevresinden ortalama 9–11 K sıcak, ama bu fark üretimi izlemiyor.
- Kapı 1: r(ΔT yıllık değişim, üretim) = +0,05 (İsdemir +0,05, Ereğli +0,05; Kardemir n = 9, −0,65).
  Deprem duruşu (10 sahne): medyan ΔT 9,75 K; diğer sahnelerin 10. yüzdeliği 7,24 K → tesis tamamen dururken bile
  sıcaklık farkı normal aralıkta. Ölçülen şey proses ısısı değil, çatı/beton/cüruf yüzeylerinin güneşle ısınması.
- Kapı 2 (yalnız rapor): havuz Spearman +0,08 (n = 139); ISDMR +0,34, EREGL +0,10, KRDMD +0,08, IZMDC −0,18.
- Yorum: Gündüz 100 m termal bant, yüksek fırın/çelikhane faaliyetini yüzey ısınmasından ayıramıyor. Sentinel-2
  SWIR ile aynı sonuç. Gündüz uydu görüntüsüyle tesis faaliyeti hattı kapatıldı; kalan tek teknik yol gece
  ateş tespiti (VIIRS Nightfire, 750 m), ama tesis içi ayrım ve Türkiye'deki örnek sayısı onu da zayıflatıyor.
- Test sayacı: ~37.

### T-E1 — Santral üretiminden elektrik şirketlerinin gelirini önceden hesaplamak (kayıt: 2026-10-22 22:00, korelasyon hesaplanmadan)

Fikir: EPİAŞ santral bazlı saatlik üretim × saatlik PTF, çeyrek biter bitmez bilinir; elektrik satış gelirinin
doğrudan ölçüsüdür. Bilanço ~6–10 hafta sonra gelir.
- Gelir tahmini R_iq = Σ (santral saatlik üretim MWh × saatlik PTF TL) — `cikti/epias_santral_saatlik.csv`,
  `cikti/epias_ptf_saatlik.csv`, eşleşme `cikti/epias_santral_eslesme.csv` (yalnız hidro santraller).
- Raporlanan gelir: İş Yatırım satış gelirleri (3C), Research önbelleği; yılbaşından itibaren kümülatif (YTD).
- Karşılaştırma YTD bazında (3/6/9/12 ay): Δ = log(YTD_y / YTD_{y−1}), hem raporlananda hem tahminde.
  2022 ve sonrası **12 aylık** dönemler dışarıda (yıl sonu satırlarının sonradan TMS 29 ile üzerine yazılması).
- Ana grup (hidro ağırlıklı; veri görülmeden, kurulu güç bilgisine göre): AYDEM, ENTRA, ENDAE, MOGAN.
  Rapor grubu: AKFYE, ZOREN, ODAS (hidro payı düşük).
- **Kapı 1:** ana grupta havuzlanmış r(Δ tahmin, Δ raporlanan) ≥ +0,60 **ve** 4 şirketin en az 3'ünde r > 0.
  Rapor: yalnız üretim (fiyatsız) sürümü.
- **Kapı 2 (yalnız Kapı 1 geçerse karar):** halka arzdan sonraki bilançolar; sürpriz = tahminin çeyreklik yıllık
  log değişimi − bir önceki çeyreğinki (önceki çeyrek zaten açıklanmış); getiri T-C2 ile aynı (bildirimden önceki
  kapanış → 2. işlem günü, BIST100'e göre). Havuz Spearman ≥ +0,25. Olay sayısı az olacak (halka arzlar 2021+).
- Test sayacı: +2 → ~39.

**Sonuç (2026-10-22): Kapı 1 kâğıt üzerinde GEÇTİ ama kırılgan; Kapı 2 KALDI.** (`python elektrik_gelir_testi.py`,
`python elektrik_gelir_kapi2.py`)
- Kapı 1: ana grup havuz r = +0,63 (n = 40), 4/4 pozitif (AYDEM +0,70, ENDAE +0,43, ENTRA +0,33, MOGAN +0,22).
  Rapor: AYDEM'in 2022 gözlemleri (PTF patlaması) çıkarılınca r = +0,08; Spearman +0,32; yalnız üretim +0,35.
  Rapor grubu ODAS +0,82, ZOREN +0,80, AKFYE +0,21 — uzun TL serilerinde ortak enflasyon eğilimi korelasyonu şişiriyor.
- Kapı 2: 46 olay (AYDEM 21, MOGAN 10, ENTRA 9, ENDAE 6); havuz Spearman = +0,07 (eşik +0,25).
- Yorum: santral üretimi × PTF, olağanüstü fiyat yıllarında geliri yakalıyor, normal yıllarda yakalamıyor
  (YEKDEM'in dolar bazlı sabit fiyatı, ikili anlaşmalar, hidro dışı santraller, TMS 29). Bilanço günü tepkisini
  öngörmüyor. Kapatıldı.
- Test sayacı: ~39.

## Öncü göstergeler (amaç: resmi istatistikten önce bilgi; para kazanma şartı yok)

Ölçüt ham korelasyon değil: enflasyon, eğilim ve mevsimden arındırılmış değişimlerde ilişki ve örneklem dışında
basit tahmine (son değer / mevsim normali) göre iyileşme.

### T-I1 — Gece ışıkları → il bazında reel büyüme (kayıt: 2026-10-23 02:35, veri inmedi)

- Uydu: VIIRS DNB aylık (NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG, 2014-01 →). Piksel başına avg_rad; cf_cvg = 0 veya
  avg_rad < 0,5 nW/cm²/sr olan pikseller sıfır sayılır (arka plan/gürültü). İl sınırı: FAO GAUL 2015 düzey 1.
  İl-ay toplam ışık; yıllık değer = o yılın 12 ayının ortalaması (ayın il alanının < %90'ı kapsanmışsa ay atlanır;
  yıl için ≥ 9 ay gerekir).
- Resmi: TÜİK il bazında GSYH, zincirlenmiş hacim (reel). Hedef: Δlog reel GSYH_il,yıl.
- **Ana ölçü:** her yıl ulusal ortalama çıkarıldıktan sonra (ulusal büyüme çeyreklik GSYH ile zaten erken bilinir;
  ışığın katkısı büyümeyi iller arasında dağıtmak) r(Δlog ışık, Δlog reel GSYH), tüm il-yıllar havuzlanmış.
- **Kapı:** havuz r ≥ +0,20 **ve** yılların en az üçte ikisinde r > 0.
- Rapor: (a) uzun fark 2014 → son yıl (kesit, n = 81); (b) örneklem dışı: son yılın il büyüme sapmasını ışıkla tahmin
  vs "geçen yılın sapması" tahmini, RMSE; (c) deprem bölgesi 11 il, 2023 ışık ve GSYH değişimi.
- Test sayacı: +1 → ~40.

**Sonuç (2026-10-23): KALDI.** (`python gece_isik.py` → `python gece_isik_testi.py`; 80 il (GAUL'da Düzce Bolu
içinde), 800 il-yıl, 2015–2024)
- Ana: havuz r = +0,01; yıllara göre −0,14 ile +0,19 arası, 10 yılın 5'inde pozitif.
- Rapor: (a) uzun fark 2014→2024 r = +0,001; (b) örneklem dışı RMSE ışıkla 4,99, "ulusal ortalama" ile 4,98
  (katkı yok); (c) deprem bölgesi 2023: 11 il ışıkta ulusal ortalamanın +4,4 puan üstünde, il içi r = −0,14.
- Tanı: Hatay aylık ışığı Şubat 2023 depreminden sonra düşmüyor (Oca 123 bin, Şub 116 bin, Nis 136 bin). Ulusal
  toplam 2016 Aralık → 2017'de basamak gibi +%28 artıyor. İl ışığını büyük ölçüde sanayi/liman noktaları,
  belediyelerin LED dönüşümü (VIIRS mavi ışığı zayıf görür) ve yeniden yapım şantiyeleri belirliyor olabilir
  (test edilmedi). Hedef tarafı da gürültülü: TÜİK'e göre Hatay'ın reel GSYH'si 2023'te %8 arttı.
- Test sayacı: ~40.

### T-IV1 — Hidro → elektrik fiyatı, nedensel etki: araç değişken (2SLS) (kayıt: 2026-10-23 03:30, kontroller ve IV hesaplanmadan)

Amaç: işletmecinin suyu yüksek fiyatlı dönemlere kaydırması (ters nedensellik) ve ölçüm hatası düz regresyonu sıfıra
doğru saptırabilir. Hidronun yalnız hava kaynaklı kısmını kullanarak nedensel etkiyi tahmin et. Tahmin çalışması;
"geçti/kaldı" değil, önceden belirlenmiş şartlarla raporlanır.
- Frekans çeyreklik, 2018Ç1–2026Ç3 (n ≈ 35). Tüm değişkenler aynı çeyreğin bir yıl öncesine göre log fark (Δ4).
- Bağımlı: Δ4 log ortalama PTF ($). İçsel: Δ4 log **toplam hidro** (barajlı + akarsu; yağışın akarsu kanalı da hidroda kalsın).
- Araçlar: su girdisi W = 5 havzanın (Fırat-Karasu, Fırat-Murat, Dicle, Çoruh, Seyhan-Ceyhan; ERA5-Land) yağış + kar
  erimesi toplamı, havza ortalaması; Z1 = Δ4 log W_q, Z2 = Δ4 log W_(q−1).
- Kontroller: Δ4 log toplam üretim (talep vekili), Δ4 log rüzgar+güneş, Δ4 log dolar/TL, Δ4 log Avrupa gaz fiyatı
  (Dünya Bankası Pink Sheet), Δ4 ısıtma ve soğutma derece-günü (6 il eşit ağırlık: İstanbul, Ankara, İzmir, Bursa,
  Antalya, Adana; günlük ortalama sıcaklık, HDD taban 18 °C, CDD taban 22 °C; Open-Meteo/ERA5).
- Tahmin: 2SLS, Newey–West (4 gecikme) standart hata. Raporlanan: birinci aşama F (araçların ortak HAC Wald testi),
  β_IV ve %95 aralık, aynı kontrollerle EKK β, Hansen J (aşırı tanımlama), Wu–Hausman.
- Yorum şartları: F < 10 → zayıf araç; β_IV yorumlanmaz (yalnız indirgenmiş form raporlanır). Beklenti (önceden):
  β_IV < β_EKK (daha negatif).
- Sağlamlık (rapor): kontrolsüz; 2021–22 hariç; içsel = yalnız barajlı hidro; tek araç Z1.
- Test sayacı: +1 → ~41.

**Sonuç (2026-10-23):** (`python cikti/iv/iv.py`; veri: EPİAŞ, ERA5-Land havza yağış+erime, Dünya Bankası Pink Sheet
Avrupa gazı, Open-Meteo 6 il sıcaklığı, USDTRY)
- n = 35 çeyrek (2018Ç1–2026Ç3). Birinci aşama: Z1 t = 4,5, Z2 t = 5,7; kısmi R² 0,48; F = 20,4 (≥ 10, araçlar güçlü).
- **β_IV = −0,75** (t −2,9; %95 aralık −1,26 … −0,25) ↔ aynı kontrollerle **β_EKK = −0,40** (t −1,7).
  Önceden kayıtlı beklenti (β_IV daha negatif) tuttu. Hansen J p = 0,79 (aşırı tanımlama reddedilmiyor);
  Wu–Hausman p = 0,07.
- Sağlamlık: yalnız barajlı hidro −0,66 (t −3,1, F 18,4); 2021–22 hariç −0,51 (t −1,8, F 25,8);
  tek araç Z1 −0,83 (t −2,7, ama F 9,8 → zayıf); **kontrolsüz −0,31 (t −0,8)** — sonuç kontrollere (özellikle gaz
  fiyatı ve kur) bağlı. Örneklemde kurak 2021–22 gaz kriziyle çakıştığı için (birinci aşamada gaz katsayısı t −2,9)
  kontrolsüz IV'de dışlama şartı zaten savunulamaz.
- Not: F, ortak ki-kare / araç sayısı olarak hesaplandı (linearmodels ki-kare veriyor: 40,9 / 2).
- Test sayacı: ~41.

### Betimsel (karar testi değil, önceden kaydedilmedi) — Avrupa elektrik fiyatları ve PTF (2026-10-23)

Veri: Ember aylık toptan fiyatlar (Bulgaristan, Yunanistan, Almanya, €/MWh), PTF TL / EVDS EUR/TRY, Pink Sheet gaz.
`cikti/iv/global_elektrik_aylik.csv`. 2017-01 → 2026-09.
- 12 aylık log değişim korelasyonu (n = 105): BG 0,69 · GR 0,73 · DE 0,63 · gaz 0,63. Aylık değişimde zayıf (BG 0,28).
- Esneklik (Newey–West 12): PTF€ ~ BG = +0,61 (t 7,0), R² 0,48. Gaz eklenince gaz +0,01 (BG zaten taşıyor);
  hidro eklenince BG +0,65, hidro −0,29. Tavan öncesi (2022-04'ten önce) BG +0,49, sonrası +0,70.
- Seviye: 2017–19 TR ≈ BG (~40 €/MWh); 2022 TR 141 / BG 252; 2025 TR 59 / BG 107; 2026 TR 37 / BG 118.
- Yorum: ortak hareket büyük ölçüde ortak yakıt maliyeti (gaz, kömür) üzerinden; doğrudan ticaret kapasitesi küçük.
  Nedensel değil, betimsel.
- T-IV1 ek sağlamlık (sonradan, kayıt dışı; ana model değişmedi): Avrupa elektrik fiyatı (Δ4 log, $) kontrolü.
  + Almanya: β_IV −0,75 (değişmez; gazla r 0,97, bilgi katmıyor). + Bulgaristan: −0,84 (t −4,0, F 15,8, R² 0,75).
  + Yunanistan: −0,86 (t −4,1, F 15,8). Araçlarla korelasyon küçük (BG: Z1 0,08, Z2 0,25; DE: 0,03, 0,21).
  Balkan fiyatları Türkiye hidrosundan (ihracat) ve ortak havadan etkilenebileceği için "kötü kontrol" riski var →
  yalnız sağlamlık olarak raporlanır.

### T-IV2 — T-IV1'in ölçüm düzeltmesi (kayıt: 2026-10-23 04:30, yeni veriler inmedi)

T-IV1 ile birebir aynı tasarım; yalnız iki kontrolün ölçümü düzeltilir (T-IV1 sonuçları görüldükten sonra
kaydedildiği için bu bir ölçüm düzeltmesidir, yeni bir hipotez değil; iki sürüm de raporlanır):
- Talep: toplam üretim yerine **EPİAŞ gerçek zamanlı tüketim** (MWh, saatlik → çeyrek toplamı, Δ4 log).
- Gaz: Avrupa TTF yerine **BOTAŞ'ın elektrik üretim amaçlı (santral) satış tarifesi**, TL/Sm³ (ayın 15'inde
  geçerli tarife), aylık USD/TRY ortalamasıyla $'a çevrilir; çeyrek ortalaması, Δ4 log. Tarife ay içinde
  değiştiyse 15'inde geçerli olan alınır.
- Diğer her şey (bağımlı, içsel, araçlar, ısıtma/soğutma, kur, rüzgâr+güneş, 2SLS, Newey–West 4) aynı.
- Raporlanan: β_IV, %95 aralık, F, EKK; ayrıca BOTAŞ + TTF birlikte (rapor).
- Test sayacı: değişmez (aynı sorunun ölçüm düzeltmesi).

**T-IV2 sonucu (2026-10-23):** BOTAŞ elektrik üretim tarifesi bir alt ajanla derlendi (`cikti/iv/botas_elektrik_tarife.csv`,
notlar `botas_tarife_notlar.md`; 2017-01'den itibaren tam, 2019-04/05 boş → 2019Ç2 = Haziran; 2016-01…09 boş, kullanılmıyor).
TL/1000 Sm³ → aylık USD/TRY ile $; çeyrek ortalaması.
- **Ana (tüketim + BOTAŞ): β_IV = −0,63** (t −3,8; %95 −0,96 … −0,30), F = 30,4; β_EKK = −0,49 (t −5,3); R² 0,88;
  J p 0,37; Wu–Hausman p 0,23. BOTAŞ tarifesi geçişi +0,78 (t 9,0); TTF eklenince 0 (−0,06).
- Sağlamlık: barajlı −0,55 (t −3,8); 2021–22 hariç −0,59 (t −2,7); tek araç −0,74 (F 11,4); kontrolsüz −0,31 (değişmez).
- Önceki sürümle karşılaştırma: T-IV1 −0,75 (EKK −0,40); tüketim düzeltmesi tek başına −0,77.
- Yorum: Doğru gaz maliyeti (BOTAŞ) kontrol edilince EKK ile IV arasındaki fark büyük ölçüde kapandı (Hausman p 0,23).
  T-IV1'deki "IV ≈ 2 × EKK" farkının çoğu, TTF'nin kötü bir vekil olmasından (atlanmış değişken) geliyormuş;
  işletmeci tepkisinin payı küçük. Sağlam bulgu: hava kaynaklı %10 fazla hidro → PTF ~%6 düşük.

## Alternatif veriden finansal tahmin

Amaç: şirketlerin çeyrek sonuçlarını (satış, kâr) KAP'tan önce alternatif veriyle tahmin etmek. Önce kapı: sonucu
kusursuz bilmek bile bilanço gününde getiri sağlamıyorsa alternatif veri toplanmaz.

### T-P1 — Mükemmel bilgi kapısı: çeyrek sonucunu önceden bilmek bilanço günü getirisi sağlar mı? (kayıt: 2026-10-23 13:45, hiçbir sürpriz–getiri ilişkisi hesaplanmadan)

- Veri: `~/Desktop/Research` — İş Yatırım mali tabloları (YTD kümülatif), KAP yayın tarihleri (`report_dates.csv`),
  günlük fiyat (`close` düzeltilmiş kapanış, `end_deger` BIST100, `pd` piyasa değeri).
- Evren: fiyatı ve mali tablosu olan şirketler; banka profili ve "MALİ KURULUŞLAR" sektörü (holding, GYO, sigorta,
  aracı kurum) hariç. Evren bugünkü Yıldız Pazar (hayatta kalan) → sonuç bu etiketle okunur.
- Olay: her (kod, yıl, dönem) için `report_dates.csv`'deki ilk bildirim. **Mali çeyrekler 2016Ç2–2022Ç3** (yıl sonu
  satırlarının üzerine yazılması 2022Ç4'ten, TMS 29 2023Ç4'ten başlıyor; 2023Ç1–Ç3 yalnız rapor).
- Tek çeyrek değerler YTD farkından: Ç1 = 3 ay, Ç2 = 6 ay − 3 ay, Ç3 = 9 ay − 6 ay, Ç4 = 12 ay − 9 ay.
- Sürpriz ölçüleri (ikisi de ayrı karar verir):
  - **S_SATIS** = g_q − g_(q−1), g = log(satış_q / satış_(q−4)) (kalem 3C). Naif tahmin: son açıklanan çeyreğin yıllık
    büyümesi sürer. Satışı ≤ 0 olan çeyrek dışarı.
  - **S_KAR** = (NK_q − NK_(q−4)) / PD_ref; NK = ana ortaklık payı net kâr (3Z, yoksa 3L), tek çeyrek.
    Naif tahmin: geçen yılın aynı çeyreği.
- Zamanlama: yayın saati 18:10'dan önceyse ref = önceki işlem gününün kapanışı; 18:10 ve sonrası ise ref = yayın
  günü (işlem günü değilse son işlem günü) kapanışı. Gün 0 = ref'ten sonraki ilk işlem günü.
- Getiriler (BIST100'e göre log fazla getiri):
  - **A (açıklama, karar):** ref → gün 1 kapanışı.
  - B (kayma, rapor): gün 1 → gün 61 kapanışı.
  - P (çeyrek içi, rapor): çeyreğin son işlem günü kapanışı → ref.
- İstatistik: her mali çeyrek kohortunda (≥ 30 olay) Spearman IC(sürpriz, getiri); kohort ortalaması, t = ort/(sd/√n).
  Kohort içi 5'li dilimler: Q5 − Q1 ortalama getiri (getiriler havuzda %1–%99 kırpılır), kohortlar üzerinden ortalama.
- **Kapı (her ölçü için ayrı):** pencere A'da ortalama IC ≥ +0,10 **ve** t ≥ 3,0 **ve** Q5 − Q1 ≥ +%2,0.
  Gerekçe: gerçek bir alternatif veri tahmini sürprizle kabaca ρ ≈ 0,5 ilişkili olur, IC'yi yaklaşık yarıya indirir;
  yarısı kaldığında hâlâ işe yarar bir sinyal olmalı (gidiş–dönüş maliyet %0,4).
- Karar: geçen ölçü alternatif verinin hedefi olur (satış → hacim/fiyat verisi; kâr → marj verisi de gerekir).
  İkisi de kalırsa bilanço günü stratejisi için alternatif veri toplanmaz. Pencere P'de IC ≥ 0,10 ve t ≥ 3 ise bilgi
  açıklamadan önce fiyata giriyor demektir; bu ayrı bir soru olarak yeni numarayla kaydedilir.
- Rapor (karar vermez): B ve P pencereleri; alt dönemler 2016Ç2–2019Ç4 / 2020Ç1–2022Ç3; Ç4 ile Ç1–Ç3 ayrı;
  likidite (önceki 60 gün medyan TL hacim, kohort üst yarısı); 2023Ç1–Ç3; olay sayıları.
- Test sayacı: +2 → ~43.

**Sonuç (2026-10-23): S_KAR GEÇTİ (güçlü), S_SATIS KALDI.** (`python3 faktor/pz_testi.py` → `cikti/pz/`; 121 şirket,
2.338 olay, 26 kohort, kohort başına ~80–120 olay; yayın gecikmesi medyanı 40 gün)
- **S_KAR, pencere A:** IC +0,24 (t 10,3; kohortların %92'sinde pozitif); Q5 − Q1 **+%3,3** iki günde (t 8,1).
  Dilimler monoton: Q1 −%2,0 · Q2 −%1,4 · Q3 −%0,9 · Q4 −%0,2 · Q5 +%1,4.
- **S_SATIS, pencere A:** IC +0,072 (t 2,8); Q5 − Q1 +%1,0 → üç eşiğin üçünde de altında.
- Rapor: S_KAR — B (sonraki 60 gün) IC +0,08 (t 3,6), Q5 − Q1 +%3,7; P (çeyrek sonu → yayın) IC +0,19 (t 7,1),
  Q5 − Q1 +%6,7. Alt dönemler 0,25 / 0,23; yalnız Ç4 0,24; likit üst yarı 0,19 (Q5 − Q1 +%2,4); 2023Ç1–Ç3 0,17 (3 kohort).
  S_SATIS — B IC +0,08 (t 3,3), Q5 − Q1 +%3,8; P IC +0,08 (t 2,8). r_s(S_SATIS, S_KAR) = 0,16.
- Kontrol: 3 rastgele olayın A getirisi ham fiyat dosyasından elle yeniden hesaplandı, birebir aynı.
- Yorum: (1) Kâr sürprizi BIST'te güçlü fiyatlanıyor ve **bilginin çoğu yayından önce** fiyata giriyor (P'deki hareket
  A'nın iki katı). Alternatif veri ancak P penceresinde erken gelirse A'dan fazlasını yakalar. (2) Satış sürprizi tek
  başına bilanço gününde zayıf → yalnız hacim ölçen veri (OSD, DHMİ, GTİP miktarı) yetmez; **marj ve finansman/kur
  kalemleri** de tahmin edilmeli. (3) Satışta B'deki kayma (yavaş fiyatlama?) keşif sonrası gözlem; yeni numara gerekir.
  (4) Hayatta kalan evren; iki günlük tepkiyi az etkiler ama B ve P'yi şişirebilir.
- Test sayacı: ~43.

### T-P2 — Kâr sürprizinin kur kaynaklı kısmı, kamuya açık veriyle (kayıt: 2026-10-23 14:05, tahmin–sonuç ve tahmin–getiri ilişkisi hesaplanmadan)

Amaç: her alternatif verinin geçmesi gereken çıta. Türkiye'de net kârın oynaklığının büyük kısmı kur farkından gelir;
şirketin önceki raporda açıkladığı net döviz pozisyonu ve çeyreğin kur değişimi çeyrek biter bitmez bilinir.
Yalnız veri kapsamı ve kalem tutarlılığına bakıldı (4BE ile 4BEB bazı şirketlerde işaret/değer bakımından tutarsız;
4BEA "parasal net yabancı para pozisyonu" kur farkının kâr/zarara giden kısmını belirleyen kalemdir).

- Evren, olaylar, kohortlar, S_KAR, pencereler A/B/P ve zamanlama: T-P1 ile birebir aynı (`cikti/pz/olaylar.csv`).
- Pozisyon NFX: kalem **4BEA** (parasal net YP pozisyonu, TL; pozitif = net döviz varlığı). Tahmin anı t0 = çeyrek
  sonu; kullanılan pozisyon, KAP yayın tarihi ≤ t0 olan en son rapordaki pozisyon (normalde q−1, Ç4 raporu gecikirse
  q−2). Yayın tarihi bilinmiyorsa olay dışarı.
- Kur: USD/TRY (`dd_deger`), çeyrek sonu son işlem günü. d_q = fx_q / fx_(q−1) − 1.
- KUR_q = NFX(t0) × d_q; aynı formül bir yıl önceki çeyrek için (kendi t0'ındaki pozisyonla): KUR_(q−4).
- **Ŝ_KUR = (KUR_q − KUR_(q−4)) / PD_t0** (PD_t0 = çeyrek sonu piyasa değeri). Vergi yok sayılır (sıra tabanlı).
- **Kapı 1 (tahmin):** kohort ortalaması Spearman IC(Ŝ_KUR, S_KAR) ≥ +0,15 **ve** t ≥ 3,0.
- **Kapı 2 (piyasa; Kapı 1'den bağımsız raporlanır):** pencere T = çeyrek sonundan sonraki **ilk işlem günü kapanışı →
  gün 1 kapanışı** (yalnız t0'da bilinen bilgiyle işlem yapılabilir), BIST100'e göre log fazla getiri.
  Kohort ortalaması IC(Ŝ_KUR, T) ≥ +0,05 **ve** t ≥ 3,0 **ve** Q5 − Q1 ≥ +%2,0.
- Yorum kuralı: Kapı 1 geçer, Kapı 2 kalırsa piyasa kur etkisini zaten fiyatlıyor → alternatif veri kâr sürprizinin
  **kur dışı** kısmını hedeflemeli. İkisi de geçerse bu basit sinyal kendi başına alfa adayıdır (ileriye dönük kayıt).
- Rapor (karar vermez): A ve P pencereleri; kalem 4BEB ile aynı test; plasebo: şoksuz maruziyet NFX/PD ile IC(T);
  TL'nin çeyrekte > %5 değer kaybettiği kohortlar ayrı; S_KAR'ın Ŝ_KUR'dan arındırılmış kısmının (kohort içi sıra
  regresyonu artığı) A ile IC'si — alternatif veriye kalan pay.
- Test sayacı: +2 → ~45.

**Sonuç (2026-10-23): İKİ KAPI DA GEÇTİ; ama Kapı 2'nin getirisi kur maruziyetinden ayrıştırılamıyor.**
(`python3 faktor/pz2_kur.py` → `cikti/pz/kur_ozet.csv`; 1.718 olay, 21 kohort 2017Ç3–2022Ç3 — 2016Ç2–2017Ç2'de bir yıl
önceki pozisyonun yayın tarihi KAP'ta yok, kayıtlı kural gereği dışarı)
- **Kapı 1:** IC(Ŝ_KUR, S_KAR) = +0,25 (t 6,7; kohortların %95'inde pozitif). 4BEB ile +0,24. Plasebo (şoksuz maruziyet)
  +0,09 (t 1,5) → tahmin gücü kur şokundan geliyor.
- **Kapı 2:** IC(Ŝ_KUR, T) = +0,081 (t 3,7); Q5 − Q1 +%2,9 (t 2,4). 4BEB ile 0,066 (t 2,5).
- Rapor: **A penceresinde IC −0,01** (bilanço günü kur kısmına tepki yok); P +0,08. **S_KAR'ın kur dışı kalan kısmı
  A ile IC +0,24 (t 7,8)** — T-P1'deki +0,24 ile aynı: bilanço günü tepkisinin tamamı kur dışı sürprizden.
  TL'nin > %5 değer kaybettiği 12 kohortta Kapı 1 0,27, T 0,085.
- **Keşif sonrası kontrol (kayıt dışı, karar değiştirmez):** Ŝ_KUR birçok kohortta maruziyetle neredeyse aynı
  (kohort içi |r| 0,6–1,0). Pozisyonun T penceresindeki kur hareketinden mekanik etkisi (NFX/PD × pencere içi kur
  değişimi) kohort içinde çıkarılınca IC 0,081 → 0,035 (t 1,9). Ancak büyük kur kohortlarında (2018Ç3 gibi) iki
  değişken r ≈ ±0,99 olduğu için ayrıştırma bilgi vermiyor. T getirisinin "açıklanmış kur zararının yavaş fiyatlanması"
  mı yoksa "pencere içinde süren kur hareketine maruziyet" mi olduğu bu veriyle belirlenemiyor.
- Yorum: (1) Kâr sürprizinin kur kısmı çeyrek sonunda bilinir ve piyasa onu **bilanço gününden önce** fiyatlar.
  (2) Bilanço günü tepkisi tamamen **kur dışı (faaliyet) sürprizinden**; alternatif verinin hedefi bu. (3) Ŝ_KUR
  kayıtlı kural gereği yalnız ileriye dönük alfa adayı; maruziyet kontrolü (kur betası) yeni numarayla eklenmeden
  model sinyali sayılmaz.
- Test sayacı: ~45.

### T-P3 — Kur dışı sürprizi hangi kalem taşıyor? (kayıt: 2026-10-23 14:15, hiçbir kalem–getiri ilişkisi hesaplanmadan)

Amaç: alternatif verinin neyi ölçmesi gerektiğine karar vermek (hacim mi, marj mı, gider mi, finansman mı).
- Evren, olaylar, kohortlar (2016Ç2–2022Ç3), zamanlama ve pencere A: T-P1 ile birebir aynı.
- Tek çeyrek kalemler (YTD farkı), hepsi (X_q − X_(q−4)) / PD_ref:
  - D_SATIS: satış (3C)
  - D_BRUT: brüt kâr (3D)
  - D_FAAL: faaliyet kârı (3DF)
  - D_VOK: sürdürülen faaliyetler vergi öncesi kâr (3I)
  - S_KAR: T-P1'deki gibi (3Z, yoksa 3L)
- Bileşenler (toplamları S_KAR'a yakın; azınlık ve durdurulan faaliyetler kalanın içinde):
  B1 = D_BRUT · B2 = D_FAAL − D_BRUT (faaliyet giderleri + esas faaliyetlerden diğer gelir/gider; ticari kur farkı burada) ·
  B3 = D_VOK − D_FAAL (finansman, yatırım, özkaynak yöntemi) · B4 = S_KAR − D_VOK (vergi, azınlık, durdurulan).
- Ölçüler (pencere A, kohort başına ≥ 30 olay; dördü de dolu olaylar):
  (i) Tek değişkenli kohort Spearman IC: D_SATIS, D_BRUT, D_FAAL, D_VOK, S_KAR.
  (ii) Fama–MacBeth: her kohortta A (%1–%99 kırpılmış) ~ z(B1) + z(B2) + z(B3) + z(B4); bileşenler kohort içinde
  %1–%99 kırpılıp z-puanına çevrilir; katsayıların kohort ortalaması ve t = ort/(sd/√n).
- **Karar kuralı (sırayla):**
  1. IC(D_BRUT, A) ≥ +0,15 ve t ≥ 3 → hedef **brüt kâr**: alternatif veri = hacim + ürün/hammadde fiyat makası.
  2. Değilse, IC(D_FAAL, A) ≥ +0,15 ve t ≥ 3 → hedef **faaliyet kârı**; giderler/diğer faaliyet kalemleri de gerekir
     (alternatif veriyle zor; yeni değerlendirme).
  3. Değilse → tepki faaliyet altı kalemlerden (finansman, vergi); alternatif veri bilanço günü için öncelikli değil.
  Ek koşul (karar 1 için destek, rapor): FM'de B1 katsayısı t ≥ 2.
- Rapor (karar vermez): brüt marj değişimi (BK/Satış − bir yıl önceki, puan) IC'si — marj mı hacim mi;
  T-P2'deki Ŝ_KUR'un B2 ve B3 ile kohort içi sıra korelasyonu (kur farkı hangi satırda); yalnız likit üst yarı.
- Test sayacı: +2 → ~47.

**Sonuç (2026-10-23): KARAR 1 — hedef brüt kâr.** (`python3 faktor/pz3_kalem.py` → `cikti/pz/kalem_ozet.csv`; 2.304 olay,
26 kohort, 121 şirket. Bilgisayardaki Linux ortamı yeniden indirildiği için veriler buluta alınıp orada çalıştırıldı;
kod aynı.)
- Tek değişkenli IC (pencere A): satış değişimi 0,07 (t 2,8) · **brüt kâr 0,17 (t 5,3)** · faaliyet kârı 0,19 (t 6,1) ·
  vergi öncesi 0,24 (t 10,1) · net kâr 0,24 (t 10,3).
- Fama–MacBeth (z-puanı başına iki günlük getiri): B1 brüt kâr +%1,16 (t 6,8) · B2 faaliyet giderleri/diğer +%0,60
  (t 4,1) · B3 finansman/diğer +%0,70 (t 4,2) · B4 vergi/azınlık +%0,21 (t 1,3). Ek koşul (B1 t ≥ 2) sağlandı.
- Rapor: brüt marj değişimi (puan) IC 0,15 (t 5,5) — satış hacminden (0,07) çok daha güçlü: **marj hacimden önemli**.
  Kur sinyali Ŝ_KUR en çok B3 (0,24) ve B2 (0,13) ile ilişkili, B1 ile değil (−0,06) → kur farkı finansman ve diğer
  faaliyet satırlarında; brüt kâr kurdan büyük ölçüde temiz.
- **Uyarı (rapor):** likit üst yarıda brüt kâr IC 0,07 (t 1,7), faaliyet kârı 0,13, net kâr 0,18. Büyük/likit hisselerde
  brüt kâr tek başına tepkinin küçük bir kısmını açıklıyor; faaliyet giderleri ve finansman da gerekiyor.
- Yorum: Alternatif verinin hedefi **brüt marj** (ürün fiyatı − hammadde/enerji maliyeti) ve ancak ikinci sırada hacim.
  Ürün–girdi fiyat makasları (emtia, ithalat/ihracat birim değerleri, PTF, akaryakıt) hacim verisinden önce gelmeli.
  Likit hisselerde ek olarak gider ve finansman kalemleri modellenmeli.
- Test sayacı: ~47.

### T-P4 — Sektör fiyatları brüt marjı ve bilanço günü tepkisini öngörüyor mu? (kayıt: 2026-10-23 14:40, fiyat verisi henüz inmedi)

Amaç: T-P3'e göre hedef brüt marj. En basit kamuya açık marj göstergesi: şirketin sektörünün üretici fiyatlarının
genel üretici fiyatlarına göre değişimi (göreli fiyat). Çeyrek sonundan birkaç gün sonra bilinir.
- Evren: T-P1 ana olayları; yalnız `faktor/nace_eslesme.csv`'de NACE 2 haneli koduna eşlenen 78 şirket (imalat,
  madencilik, enerji). Eşleme veri görülmeden, şirketin ana faaliyetine göre yapıldı.
- Veri: Yİ-ÜFE (TÜİK, EVDS), aylık, NACE Rev.2 2 hane (B 05–09, C 10–33, D 35) ve genel endeks. Çeyrek ortalaması.
  Seri bulunamayan sektörün şirketleri dışarı. (Not: EVDS revize edilmiş/zincirlenmiş seriyi verir; ÜFE revizyonları
  küçüktür, kabul edilir.)
- **R_q = Δ4 log ÜFE_sektör(q) − Δ4 log ÜFE_genel(q)** (çeyrek ortalamaları; yıllık değişim çünkü D_MARJ ve D_BRUT de
  geçen yılın aynı çeyreğine göre).
- Hedefler: D_MARJ, D_BRUT (T-P3), getiri A (T-P1).
- **Kapı 1 (ölçüm):** kohort ortalaması Spearman IC(R, D_MARJ) ≥ +0,10 **ve** t ≥ 3,0.
- **Kapı 2 (piyasa):** IC(R, A) ≥ +0,05 **ve** t ≥ 3,0.
- Rapor: IC(R, D_BRUT), IC(R, S_KAR); pencere T5 = çeyrek sonundan sonraki 5. işlem günü kapanışı → gün 1 kapanışı;
  yalnız sektör çıktı fiyatı (Δ4 log ÜFE_sektör, göreli değil); sektör başına olay sayıları. Not: aynı sektördeki
  şirketler aynı değeri alır (~15 farklı değer) → kesit fiilen sektörler arası.
- Test sayacı: +2 → ~49.
- Veri notu (çalıştırmadan önce, 14:55): EVDS `bie_tufe1yi` (Yİ-ÜFE 2003=100) 2 hane serileri — genel T1; 06→T6, 07→T9,
  10→T16, 11→T26, 13→T30, 16→T41, 17→T44, 19→T49, 20→T52, 21→T59, 22→T61, 23→T64, 24→T73, 27→T93, 28→T99, 29→T105,
  31→T112, 35→T119. Bilgisayardaki tarayıcıdan EVDS API ile indirildi → `cikti/pz/yiufe_nace_aylik.csv` (2014-01–2023-12).

**Sonuç (2026-10-23): Kapı 1 GEÇTİ, Kapı 2 KALDI.** (`python3 faktor/pz4_ufe.py` → `cikti/pz/ufe_ozet.csv`; 1.569 olay,
78 şirket, 18 sektör, 26 kohort, kohort başına ~60 olay)
- **Kapı 1:** IC(R, D_MARJ) = +0,146 (t 5,9; kohortların %92'sinde pozitif) — sektör göreli fiyatı brüt marj
  değişimini öngörüyor. Rapor: D_BRUT 0,16 (t 5,4), S_KAR 0,19 (t 5,4).
- **Kapı 2:** IC(R, A) = −0,012 (t −0,4) — bilanço günü tepkisi yok.
- Rapor: T5 (çeyrek sonu + 5 işlem günü → gün 1) IC +0,085 (t 3,2): piyasa sektör fiyat bilgisini çeyrek sonu ile
  bilanço arasında fiyatlıyor (T-P2'deki kur sinyaliyle aynı örüntü; sektör momentumundan ayrıştırılmadı).
  Yalnız çıktı fiyatı (göreli değil) kohort içinde aynı sırayı verir (genel ÜFE ortak) → sonuçlar birebir aynı.
- **Keşif sonrası kontrol (kayıt dışı):** gerçekleşen brüt marj değişiminin A ile IC'si 0,16; sektör medyanı 0,09
  (t 3,8), sektör içi sıra 0,14 (t 4,2). Bilanço günü tepkisinin büyük kısmı şirkete özgü (sektör içi) marj
  sürprizinden; sektör medyanı az şirketli sektörlerde şirketin kendisine yakın olduğu için 0,09 üst sınırdır.
- Yorum: Kamuya açık sektör fiyatları marjı öngörüyor ama piyasa bunu bilanço gününden önce fiyatlıyor. Bilanço günü
  alfası için alternatif veri **şirkete özgü** olmalı (şirketin kendi ürün karması, hacmi, maliyeti); sektör düzeyinde
  emtia makası veya ÜFE tek başına yetmez. Sektör düzeyi bilgi ancak çeyrek sonu → bilanço penceresinde (T5) değer
  taşıyabilir; bu ayrı ve yeni numaralı bir test gerektirir (sektör momentumu kontrolüyle).
- Test sayacı: ~49.

### T-P5 — Şirkete özgü ihracat verisi (GTİP) satış sürprizini ve bilanço günü tepkisini öngörüyor mu? (kayıt: 2026-10-23 15:05, ihracat–finansal ilişkisi hesaplanmadan)

Veri: UN Comtrade (Türkiye'nin TÜİK'e dayalı aylık HS6 ticareti; yerleşik tarayıcıdan, ücretsiz önizleme API'si).
**Ön bulgu (veri erişim denetimi):** tek üreticili ürünlerde TÜİK veriyi gizliyor — akrilik elyaf ihracatı
(5501.30, 5503.30, 5506.30) ve akrilonitril ithalatı (2926.10) hiçbir ayda yayımlanmıyor. AKSA bu yüzden test edilemez.
En şirkete özgü veri tam da gizlilik nedeniyle yok. Erişim denetiminde 5 ay için birkaç kodun ihracat değeri görüldü
(yalnız varlık kontrolü; finansal tablolarla karşılaştırılmadı).
- Şirket → kodlar (veri görülmeden, ürün bilgisine göre; şirketin Türkiye ihracatındaki payı yüksek olan kodlar):
  KORDS → 5902.10, 5902.20 (lastik kord bezi) · SASA → 5503.20, 5501.20 (polyester elyaf) · PETKM → 3901.10, 3901.20,
  3904.10 (PE, PVC) · TTRAK → 8701.91–8701.95 (tarım traktörleri).
- Zamanlama: ay m'nin verisi m+1 ayının son gününden sonraki ilk işlem gününde bilinir sayılır (TÜİK takvimi).
  Bir olay için yalnız ref tarihinden önce bilinen aylar kullanılır; çeyreğin bilinen ayları ile bir yıl önceki aynı
  aylar karşılaştırılır (en az 2 ay gerekli).
- Proxy: X = kodların aylık ihracat değeri toplamı ($) × aylık ortalama USD/TRY (TL). g = log(X_q / X_(q−4)) (aynı aylar);
  **P_SATIS = g_q − g_(q−1)** (S_SATIS ile aynı yapı: önceki çeyreğin büyümesi sürer).
- Hedefler: S_SATIS (T-P1), getiri A (T-P1). Dönem: 2016Ç2–2022Ç3 ana olaylar.
- **Kapı 1:** havuz Pearson r(P_SATIS, S_SATIS) ≥ +0,30 **ve** 4 şirketin en az 3'ünde r > 0.
- **Kapı 2:** havuz Spearman r(P_SATIS, A) ≥ +0,20 **ve** en az 3 şirkette > 0.
- Rapor: P_SATIS ile S_KAR ve D_MARJ; birim değer ($/kg) yıllık değişimi ile D_MARJ; şirket bazında r ve n.
- Uyarı (önceden): ~100 olay, 4 şirket; KORDS ve PETKM'de ihracat gelirin küçük bir kısmı (Kordsa'nın yurtdışı
  fabrikaları konsolide). Güç düşük; kapı ancak büyük etkiyi yakalar.
- Test sayacı: +2 → ~51.
- Veri notu (çalıştırmadan önce, 15:25): `cikti/pz/comtrade_aylik.csv` (2014-01–2022-12, 1.059 satır). Traktör kodları
  8701.91–95 HS2017 ile geldi; 2016 ve öncesi yok → TTRAK olayları fiilen 2018Ç1'den başlar.

**Sonuç (2026-10-23): Kapı 1 GEÇTİ, Kapı 2 KALDI.** (`python3 faktor/pz5_gtip.py` → `cikti/pz/gtip_ozet.csv`; 104 olay,
87'sinde proxy dolu; 75'inde çeyreğin 3 ayı, 29'unda 2 ayı bilanço öncesi biliniyordu)
- **Kapı 1:** r(P_SATIS, S_SATIS) = +0,42 (n 87); KORDS +0,72 · SASA +0,54 · TTRAK +0,45 · PETKM +0,18 (4/4 pozitif).
  Şirkete özgü ihracat verisi satış sürprizini bilançodan önce yakalıyor.
- **Kapı 2:** Spearman r(P_SATIS, A) = +0,02; KORDS +0,25 · SASA +0,17 · TTRAK +0,02 · PETKM −0,35.
- Rapor: P_SATIS ile D_MARJ +0,40 (SASA +0,71), S_KAR +0,10; birim değer değişimi ile D_MARJ +0,12, A −0,06.
- Kontrol: SASA 2021Ç2 olayı ham Comtrade + kur verisinden elle yeniden hesaplandı, aynı (+0,400).
- Yorum: Ölçüm çalışıyor ama satış sürprizi bilanço gününde zaten zayıf fiyatlanıyor (T-P1: IC 0,07) ve bu
  ihracat verisi kamuya açık (TÜİK, ~30 gün gecikme): piyasa ya onu kullanıyor ya da satışa tepki vermiyor. Örneklem
  küçük (4 şirket); güç yalnız büyük etkiyi yakalar. En şirkete özgü kodlar (tek üretici) TÜİK gizliliği yüzünden yok.
- Test sayacı: ~51.

### T-P6 — Çeyrek sonu → bilanço sinyalleri momentum kontrolünden sonra kalıyor mu? (kayıt: 2026-10-23 16:25, kontrollü hiçbir regresyon çalıştırılmadan)

Keşif sonrası hipotez: T-P2'de Ŝ_KUR (pencere T, IC 0,081) ve T-P4'te sektör göreli fiyatı R (pencere T5, IC 0,085)
çeyrek sonu → bilanço getirisini öngördü. Soru: bu, hisse/sektör momentumunun yansıması mı? Aynı örneklemde
olduğu için geçse bile kanıt değil; geçerse ileriye dönük kayda alınır, kalırsa kapanır.
- Olaylar ve hedefler: T-P2 (`kur_olaylar.csv`, hedef T = çeyrek sonu + 1 işlem günü → gün 1) ve T-P4
  (`ufe_olaylar.csv`, hedef T5 = çeyrek sonu + 5 işlem günü → gün 1). BIST100'e göre log fazla getiri.
- Kontroller (hepsi pencere başında biliniyor; qi = çeyrek sonundaki son işlem günü):
  MOM_Q = qi−63 → qi fazla getiri (çeyreğin kendi getirisi) · MOM_12 = qi−252 → qi−21 ·
  SEKMOM = aynı kohortta aynı sektördeki diğer şirketlerin MOM_Q ortalaması (Ŝ_KUR için Research alt sektörü,
  R için NACE 2 hane; sektörde başka şirket yoksa 0).
- Yöntem: her kohortta tüm değişkenler sıraya çevrilip standartlaştırılır; hedef ~ sinyal + MOM_Q + MOM_12 + SEKMOM
  (EKK). Sinyal katsayısının kohort ortalaması ve t = ort/(sd/√n). Kohort başına ≥ 30 olay.
- **Kapı (her sinyal ayrı):** kontrollü katsayı ≥ +0,04 **ve** t ≥ 2,5.
- Karar: geçen sinyal `FAKTOR_PLANI.md`'ye ileriye dönük aday olarak eklenir (2026-11'den itibaren her çeyrek sonu
  sinyal, getiri görülmeden kayda yazılır; 8 çeyrek sonra değerlendirme). Kalan kapanır.
- Rapor: kontrolsüz katsayı; her kontrol tek başına; Ŝ_KUR için ek olarak NFX/PD (maruziyet) ve pencere içi mekanik kur
  etkisi (NFX/PD × pencere içi USD/TRY değişimi; işlem anında bilinmez, yalnız yorum için).
- Test sayacı: +2 → ~53.

**Sonuç (2026-10-23): Ŝ_KUR GEÇTİ, R KALDI (kıl payı).** (`python3 faktor/pz6_momentum.py` → `cikti/pz/mom_ozet.csv`)
- **Ŝ_KUR (pencere T):** kontrollü katsayı +0,081 (t 3,8) ↔ kontrolsüz +0,081 (t 3,7). Momentumla ilişkisi yok
  (sıra korelasyonu MOM_Q 0,00, MOM_12 −0,02, SEKMOM 0,00); tek tek kontroller 0,078–0,090.
- **R (pencere T5):** kontrollü +0,056 (t 2,49; eşik 2,5) ↔ kontrolsüz +0,085 (t 3,2). R momentumla ilişkili
  (MOM_Q 0,17, MOM_12 0,15, SEKMOM 0,22); etkinin üçte biri momentum.
- Rapor: Ŝ_KUR'a NFX/PD maruziyeti eklenince katsayı +0,20 (t 1,1), mekanik kur etkisi eklenince +0,13 (t 1,4) —
  iki durumda da çoklu doğrusallık (T-P2'deki gibi) yüzünden kestirim kararsız; maruziyet sorusu hâlâ açık.
- Karar: Ŝ_KUR `FAKTOR_PLANI.md`'ye ileriye dönük aday olarak eklendi (F-A5). R kapandı.
- Test sayacı: ~53.
