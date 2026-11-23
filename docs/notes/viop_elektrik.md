# VİOP Baz Yük Elektrik Vadeli (F_ELCBAS…) — durum araştırması

Tarih: 21.10.2026. Ortam notu: Bu oturumdaki ağ vekili borsaistanbul.com, seffaflik.epias.com.tr ve datastore dosyalarını doğrudan (curl) indirmeye izin vermedi. Bu yüzden veriler WebFetch ile açılan sayfalardan okundu. Ham bülten dosyası indirilip satır satır kontrol edilemedi.

## 1. Sonuç (özet)

**Bireysel yatırımcı için fiilen işlem yapılabilir değil.** Sözleşmeler kâğıt üzerinde listede duruyor, ama piyasada alıcı ya da satıcı emri yok ve işlem hacmi sıfır. Güven: **yüksek** (birbirinden bağımsız üç veri sağlayıcı aynı tabloyu gösteriyor).

Kanıtlar:

| Kaynak (açılan sayfa) | Sözleşme | Gösterilen (21.10.2026 19:15 anlık görüntüsü) |
|---|---|---|
| Foreks | F_ELCBAS1126 (Kasım 2026) | Son 3.320,00; hacim 0; alış/satış 0,00; açılış/yüksek/düşük 0 |
| Foreks | F_ELCBAS0327 (Mart 2027) | Son 2.959,60; hacim 0; alış/satış 0,00 |
| Foreks | F_ELCBASY (Aralık 2026 yıllık) | Son 3.300,00; hacim 0; alış/satış 0,00 |
| Foreks | F_ELCBASY (Aralık 2027 yıllık) | Son 3.500,00; hacim 0; alış/satış 0,00 |
| TradingView BIST:ELCBASY1! | sürekli yıllık (ön vade ELCBASYZ2026) | 3.300 TRY, "Piyasa kapalı", "İşlem yok", açık pozisyon 0.00 |
| Gedik Yatırım VİOP bülteni 01.04.2026 ve 24.04.2026 | — | Bültende elektrik sözleşmesi satırı **hiç yok**. Bülten endeks, döviz, metal ve pay vadelilerini içeriyor. |
| GCM Yatırım ELCBAS sayfası | — | Fiyat, hacim ve açık pozisyon alanları boş ("-") |
| NCM Invest ELCBAS sayfası | F_ELCBASY26, F_ELCBASY27 (ve eski Y21, Y22) | Fiyat, hacim ve açık pozisyon yok. Başlangıç teminatı Y26 için 134.877,90, Y27 için 128.413,02 |

Yorum: "Son fiyat" alanında görünen 3.300 / 3.500 / 2.959,60 gibi değerler işlem fiyatı değildir. Bunlar uzlaşma komitesinin taşıdığı ya da teorik olarak belirlenen fiyatlardır. Gün içi yüksek/düşük ve hacim sıfır, kotasyon (bid/ask) de yok. Açık pozisyonun sıfır olması (TradingView), kimsenin pozisyon taşımadığını gösteriyor. Bireysel yatırımcı emir girse bile karşı taraf bulamaz. Piyasa emri girerse de ±%10 fiyat limitine kadar kayma riski taşır.

## 2. Listelenme durumu (2026)

- Sözleşmeler hâlâ listede. Foreks'te 2026 Kasım aylık, 2027 Mart aylık ve 2026/2027 yıllık kodlar mevcut. Borsa İstanbul'un 2025 Entegre Faaliyet Raporu da (s.16) VİOP dayanak varlıkları arasında "elektrik"i sayıyor.
- Aynı rapor elektrik için ayrı bir hacim vermiyor. Yalnızca VİOP toplamını veriyor: 24,89 trilyon TL (2024: 16,51 trilyon TL). Raporda yeni enerji sözleşmesi planı da yok.
- Sözleşme yapısı (Borsa İstanbul "Enerji ve Emtia Sözleşmeleri" kılavuzu, Haziran 2018, ve GCM sayfası):
  - Aylık sözleşme: dayanak, teslim ayındaki saatlik PTF'lerin (GCM sayfasında "KPTF") aritmetik ortalaması. Büyüklük = ay saati × 0,1 MWh (30 günlük ayda 72 MWh). Fiyat adımı 0,10 TL/MWh. Nakdi uzlaşma, günlük fiyat limiti ±%10, işlem saatleri 09:30–18:10/18:15. Son işlem günü vade ayının son iş günü.
  - Çeyreklik (Q) ve yıllık (Y) sözleşmeler: Yıllık sözleşmenin büyüklüğü 876 MWh. Bu sözleşmeler vadeye gelince "basamaklandırma" ile daha kısa sözleşmelere bölünür: yıllık → çeyreklik → aylık ("Üç aylık ve yıllık elektrik sözleşmeleri basamaklandırma uygulaması" PDF'i).
- Veri dağıtıcı kodları (BIST sayfası): Bloomberg `TBEA Comdty`, Reuters `0#ELCBAS:`.

## 3. Piyasa yapıcı ve 2025–2026 haberleri

- Elektrik piyasa yapıcılığına dair bulunan tek belge eski (tarihsiz, 2015 dönemi) bir Finansinvest / FİNA Enerji Holding PDF'i. Belgede FİNA "ilk ve tek piyasa yapıcı" olarak geçiyor. Spread, miktar ya da tarih yükümlülüğü belirtilmemiş. Güncel bir elektrik piyasa yapıcısı **bulunamadı**.
- 2025–2026'daki VİOP piyasa yapıcılık değişiklikleri elektriği kapsamıyor:
  - 23.02.2026 tarihli BIST genel mektubu (02.03.2026'da yürürlüğe giriyor) yalnızca altın, gümüş, platin, paladyum ve bakır spread'lerini değiştiriyor.
  - 30.05.2025 tarihli BloombergHT haberi pay vadeli grup sınıflamasıyla ilgili (01.07.2025'te yürürlüğe giriyor).
- 2025–2026'da "yeni elektrik sözleşmesi" ya da "elektrik piyasa yapıcısı" haberi **bulunamadı**. Bu bir yokluk bulgusu olduğu için güven orta düzeyde.
- Paralel piyasa: EPİAŞ **Vadeli Elektrik Piyasası (VEP)** 01.06.2021'de açıldı (AA haberi). VEP'te aylık, çeyreklik ve yıllık baz yük kontratları işlem görüyor. Burada yalnızca lisanslı **piyasa katılımcıları** işlem yapabiliyor. Bireysel yatırımcının doğrudan erişimi yok. Elektrikte gerçek vadeli likidite VİOP'ta değil, VEP'te ve tezgâhüstü ikili anlaşmalarda.

## 4. Geçmiş günlük uzlaşma fiyatları ücretsiz indirilebilir mi?

- **Borsa İstanbul (VİOP):** "Bülten ve Piyasa Verileri" sayfasında şu dosyalar listeleniyor:
  - Günlük Bülten, Akşam Seansı Bülteni, Özet Bülten
  - Günsonu Pozisyon Dosyası
  - Mevcut Sözleşmeler
  - "Vadesonu Uzlaşma Fiyatları (Günlük)"
  - "Vadesonu Uzlaşma Fiyatları (BISTECH Öncesi)" (aylık, 2013–2017)
  - Basamaklandırma Dosyası

  Dosya ve dizin adresleri `https://www.borsaistanbul.com/files/datafilepaths_viop.zip` içinde. Sayfa ücret belirtmiyor, ama "Tarihsel verilere datastore.borsaistanbul.com adresinden ulaşılabilmektedir" diyor. Yani güncel günün dosyaları ücretsiz. **Uzun geçmiş seri Datastore'da ve ücretli.** Dosyalar bu oturumdan indirilemediği için format (CSV/ZIP) ve saklama süresi **doğrulanamadı**. Bu kısımda güven orta.
- **Pratik alternatifler:**
  - TradingView (BIST:ELCBAS1!, BIST:ELCBASY1!) grafikte geçmiş gösteriyor. Ancak işlem olmadığı için seri büyük ölçüde sabit uzlaşma fiyatlarından oluşuyor. Dışa aktarma ücretli planda.
  - Foreks sembol sayfaları yalnızca anlık değer gösteriyor.
  - Investing.com'da ELCBAS sayfası bulunamadı.
- **En iyi ücretsiz ve tarihsel vadeli elektrik fiyatı EPİAŞ VEP'te.** Şeffaflık Platformu API'si ücretsiz kayıtla (TGT) erişilebilir. Uç noktaların yolları eptr2 1.3.9 paket şemasından alındı ve hepsi POST:
  - `/v1/markets/pfm/data/ggf`: VEP Günlük Gösterge Fiyatı
  - `/v1/markets/pfm/data/open-position`: açık pozisyon
  - `/v1/markets/pfm/data/pfm-trade-value`: işlem hacmi
  - `/v1/markets/pfm/data/vep-matching-quantity`
  - `/v1/markets/pfm/data/pfm-transaction-history`
  - `/v1/markets/pfm/data/offer-price`

  Gövde: `startDate`, `endDate` (biçim `YYYY-MM-DDT00:00:00+03:00`). İsteğe bağlı alanlar: `loadType` ("Baz" / "Puant" / "Puant Dışı"), `year`, `deliveryPeriod`. eptr2 anahtarları: `vep-ggf`, `vep-open-positions`, `vep-trade-volume`, `vep-matching-quantity`, `vep-transaction-history`, `vep-price-summaries`. Bunlar baraj/HES sinyalini "vadeli piyasa beklentisi" ile karşılaştırmak için VİOP'tan çok daha anlamlı.

## 5. Proje için öneri

- Sinyali VİOP elektrik vadelisiyle paraya çevirmek mümkün değil, çünkü likidite yok. İşlem aracı olarak HES ağırlıklı hisseler (AYDEM, AYEN, AKENR vb.) kalıyor. PTF/GGF yalnızca açıklayıcı değişken olarak kullanılabilir.
- Vadeli fiyat beklentisi için EPİAŞ VEP GGF serisini `epias_indir.py`'ye eklemek mantıklı (aynı TGT ile çalışır).

## Açılan URL'ler

- https://www.gcmyatirim.com.tr/viop/viop-sozlesmeleri/diger-sozlesmeler/baz-yuk-elektrik-elcbas
- https://cdn.gedik.com/media/media/zskj0n0i/viop_bulten_24042026.pdf
- https://www.borsaistanbul.com/files/viop-finansinvest-elektrik-vadeli-islem-sozlesmeleri-piyasa-yapiciligi.pdf
- https://tr.tradingview.com/symbols/BIST-ELCBASY1!/
- https://www.borsaistanbul.com/files/VIOP_Enerji_Emtia_Sozlesmeleri.pdf
- https://www.borsaistanbul.com/files/uc-aylik-ve-yillik-elektrik-sozlesmeleri-basamaklandirma-uygulamasi.pdf
- https://www.foreks.com/sembol-detay/H898768/f-elcbas1126/elcbas11-30-kas-26-vadeli/
- https://www.foreks.com/sembol-detay/VELCBASY1/felcbasy-1/elcbasy-28-ara-26-vadeli/
- https://www.foreks.com/sembol-detay/H846748/f-elcbasy28/elcbasy-28-ara-27-vadeli/
- https://www.foreks.com/sembol-detay/H955016/f-elcbas0327/elcbas03-31-mar-27-vadeli/
- https://www.ncminvest.com.tr/viop-urunleri/elektrik/baz-yuk-elektrik-elcbas.htm
- https://borsaistanbul.com/veriler/viop
- https://www.borsaistanbul.com/veriler/vadeli-islem-ve-opsiyon-piyasasi-verileri/bulten-ve-piyasa-verileri
- https://borsaistanbul.com/en/data
- https://borsaistanbul.com/en/data/derivatives-market-data/bulletin-and-market-data
- https://borsaistanbul.com/en/announcement/13647/dissemination-level-1-data-contracts-currency-and-precious-metals-traded-viop-and-viop-end-day-trade-party-data
- https://borsaistanbul.com/piyasalar/viop/piyasa-isleyisi/veri-dagitici-kuruluslarda-viop-sozlesmeleri
- https://datastore.borsaistanbul.com/ (içerik boş döndü)
- https://www.borsaistanbul.com/files/faaliyet-raporu-2025.pdf
- https://borsaistanbul.com/files/20260223-44576-viop-piyasa-yap%C4%B1c%C4%B1l%C4%B1k-kurallar%C4%B1nda-de%C4%9Fi%C5%9Fiklikler.pdf
- https://www.bloomberght.com/borsa-istanbul-viop-piyasa-yapicilik-programinda-degisiklikleri-duyurdu-3749639
- https://www.gcmyatirim.com.tr/arastirma-analiz/uzman-gorusleri/2026-01-02-2025-yilinda-viop-piyasa-derinligi-zamanlama-ve-yatirimci-davranisi
- https://www.selmakaraduman.av.tr/enerji/viop-elektrik-sozlesmeleri-ve-buyuk-umutlar/
- https://www.aa.com.tr/tr/ekonomi/vadeli-elektrik-piyasasi-isleme-acildi-/2260648
- https://www.epias.com.tr/aylik-bulten/ekim-2025-elektrik-piyasalari-aylik-raporu/ (rapor gövdesi okunamadı)
- Açılamayanlar: https://www.borsaistanbul.com/tr/sayfa/324/enerji-vadeli-islem-sozlesmeleri (sunucu hatası), https://tr.tradingview.com/symbols/BIST-ELCBAS1!/ (hata)
- Ek: eptr2 1.3.9 (PyPI) içindeki `assets/eptr2_api_schema.json` (VEP uç noktaları)
