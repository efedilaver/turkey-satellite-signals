# docs/: tarihli test kaydı ve plan belgeleri

| Dosya | Ne |
|---|---|
| `ARASTIRMA_PLANI.md` | **Test kaydı.** Kayıtlı her test (T-A1 … T-P6) için karar kuralı sonuç hesaplanmadan yazıldı, sonuç altına eklendi. Projenin birincil kaynağıdır. |
| `FAKTOR_PLANI.md` | Sonraki çok faktörlü BIST modeli için plan (v2). Bu repoyla yalnızca **F-A5** eki ilgili: T-P2/T-P6'dan çıkan ileriye dönük kur sürprizi adayı. Geri kalanı ayrı bir çalışmanın planıdır; F-A/F-R testlerinin hiçbiri burada raporlanmıyor. |
| `FAKTOR_PLANI_v1_2026-10-22.md` | Aynı planın yerini alan v1 sürümü. Planın, testlerinden hiçbiri çalıştırılmadan revize edildiğini göstermek için saklandı. |
| `notes/` | Veri erişimi araştırma notları: EPİAŞ santral verisi, VİOP elektrik vadelisi, çelik tesisleri, TRALT maden sahaları, DAHITI altimetri, BOTAŞ gaz tarifeleri. |

## Bu dosyalar birkaç redaksiyon dışında birebir yayımlandı

Plan dosyaları ve notlar, tarihli kayıtlar kanıt değerini korusun diye çalışma klasöründen değiştirilmeden kopyalandı.
Redaksiyonlar:
1. `FAKTOR_PLANI.md` (bölüm 3, V4): bir API anahtarı dosyasının yerel yolu `[yerel dosya yolu çıkarıldı]` ile değiştirildi.
2. `notes/tralt_notlar.md` (ruhsat iptal davası): iki özel kişinin adı "iki bireysel davacı" ile değiştirildi.
3. `notes/tralt_notlar.md` (bölüm 1): şirketin sahiplik ve yönetim geçmişini anlatan zaman çizelgesi çıkarıldı; yerine
   analiz için gereken tek bilgi (unvan ve borsa kodunun KOZAL'dan TRALT'a değişmesi) kondu. Aynı nottaki ilgili bir
   haber bağlantısı ve bir ifade de çıkarıldı. Bu notlar tarihli test kaydının parçası değildir.

Bilinen eskilik: `ARASTIRMA_PLANI.md` başlığında "Son güncelleme: 2026-10-21" yazıyor; kayıtlar 2026-10-23'e kadar sürüyor.

## Tarih damgaları neyi kanıtlar, neyi kanıtlamaz

`kayıt:` tarih damgaları yerel bir dosyaya elle yazıldı. Bağımsız olarak doğrulanamazlar: üçüncü taraf zaman damgası
yok ve bu repo daha sonra tek bir başlangıç commit'iyle oluşturuldu. Bunları kriptografik ön kayıt kanıtı olarak değil,
iyi niyetle tutulmuş bir araştırma günlüğü olarak okuyun.

## Eski yol → yeni yol

Kayıt, betiklere ve çıktılara orijinal düz klasördeki adlarıyla atıf yapıyor. Bu repoda karşılıkları:

| Kayıtta | Bu repoda |
|---|---|
| `python hepsi.py`, `gee_topla.py`, `gece_isik.py`, `celik_landsat.py`, `epias_*.py`, `hisse_indir.py`, `tuketim_indir.py` | `src/collect/` |
| `baraj_takip.py`, `no2_nowcast.py`, `demo_sentetik.py` | `src/prototypes/` |
| `mukemmel_bilgi.py`, `mevsimlik_test.py`, `kar_testi.py`, `firat_testi.py`, `likit_test.py` | `studies/hydro_power/` |
| `celik_testi.py`, `celik_landsat_testi.py`, `maden_testi.py`, `elektrik_sue_testi.py`, `gece_isik_testi.py` | `studies/industry_mining/` |
| `elektrik_gelir_testi.py`, `elektrik_gelir_kapi2.py` | `studies/power_revenue/` |
| `gida_testi.py`, `gida_uretim_testi.py` | `studies/food/` |
| `faktor/pz_testi.py` … `faktor/pz6_momentum.py`, `faktor/panel_kur.py`, `faktor/nace_eslesme.csv` | `studies/earnings_surprise/` |
| `cikti/iv/iv.py` (T-IV1, T-IV2) | **korunmadı.** Dosya çalışma klasöründe boştu; yalnız sonuç tabloları var (`results/tables/iv_sonuc.csv`, `iv2_sonuc.csv`). |
| `arastirma/*.csv` | `data/reference/` |
| `arastirma/*.md` | `docs/notes/` |
| `cikti/` (çıktılar) | Çalışma sırasında yine `cikti/` (git'e girmez). Repoya konan kopyalar: uydudan türetilmiş seriler `data/derived/`, özet tablolar `results/tables/`, grafikler `results/figures/`. |
