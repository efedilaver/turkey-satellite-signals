# results/

Testlerin özet çıktıları. Sütun adları Türkçe; testlerin tanımı için `docs/ARASTIRMA_PLANI.md`.

| Dosya | Test | Not |
|---|---|---|
| `tables/no2_karsilastirma.csv` | NO₂ anlık tahmini (keşif) | `iyilesme_%` = M2'nin M1'e göre RMSE iyileşmesi; negatif = daha kötü |
| `tables/mukemmel_bilgi.csv` | Haftalık hidro, mükemmel bilgi (keşif) | `rastgeleyi_gecme_*` = zamanda kaydırılmış kopyaların yüzde kaçını geçtiği |
| `tables/mevsimlik_test.csv` | Mevsimlik test (keşif) | Bu dışa aktarma için yeniden çalıştırıldı; `alt`/`ust` %90 aralığı |
| `tables/mevsimlik_test_yeniden_calistirma.txt`, `tables/kar_testi_yeniden_calistirma.txt` | Mevsimlik test, T-A1/T-A2 | Yeniden çalıştırmanın konsol çıktısı |
| `tables/likit_test.csv` | T-L1 / T-L2 | `yuzdelik` = kaydırılmış kopyalar içindeki yüzdelik |
| `tables/iv_sonuc.csv` | T-IV1 | **`F1` sütunu ki-kare istatistiğidir** (linearmodels); kayıttaki F = ki-kare / araç sayısı (ör. 40,9 / 2 = 20,4) |
| `tables/iv2_sonuc.csv` | T-IV1 / T-IV2 karşılaştırması | `F` doğrudan F değeridir |
| `tables/ozet.csv`, `tables/kohort.csv` | T-P1 | kohort ortalaması IC, t, Q5−Q1; `kohort.csv` kohort bazında IC |
| `tables/kur_ozet.csv` | T-P2 | |
| `tables/kalem_ozet.csv` | T-P3 | |
| `tables/ufe_ozet.csv` | T-P4 | |
| `tables/gtip_ozet.csv` | T-P5 | şirket bazında r ve n |
| `tables/mom_ozet.csv` | T-P6 | |
| `figures/*.png` | NO₂, haftalık ve mevsimlik testler | Etiketler Türkçe. `mukemmel_bilgi.png` başlığındaki "video", README'deki çıkış noktası videosudur. |

Firma bazında olay dosyaları (`*_olaylar.csv`) ve ham veriler lisans nedeniyle konmadı.
