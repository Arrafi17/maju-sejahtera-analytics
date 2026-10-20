# Laporan Keputusan - PT. Maju Sejahtera

> Dibuat otomatis oleh `main.py` (data simulasi, satuan Rp juta).

## 1. Data -> Informasi (Descriptive)
- Pendapatan +15.8%, laba bersih -11.0%,
  utang +300%, arus kas -0.2%.
- Kondisi belum bisa dinilai "baik" atau "buruk" hanya dari angka ini.

## 2. Informasi -> Insight (Diagnostic)
- Komponen penekan laba: HPP (-1,901), Beban bunga (-122), Biaya operasional (-115), Piutang macet (-102).
- Margin kotor turun dari 28.5% ke 25.4%,
  DSO naik dari 40 ke 50 hari.

## 3. Insight -> Prediksi (Predictive)
- Model terbaik: Regresi Logistik (ROC-AUC 0.73). Faktor risiko utama: Riwayat telat bayar, Segmen pelanggan, Lama berlangganan.

## 4. Prediksi -> Keputusan (Prescriptive)
| rekomendasi   |   pelanggan |   eksposur |   rugi |   manfaat |
|:--------------|------------:|-----------:|-------:|----------:|
| AMAN          |          16 |     3869.2 |  311.9 |       0   |
| BATASI        |          17 |      654.9 |  259.3 |     139.9 |
| WASPADA       |          25 |     2328   |  489.2 |     112.1 |

Estimasi manfaat bersih kebijakan kredit: **Rp 252,0 juta**.
